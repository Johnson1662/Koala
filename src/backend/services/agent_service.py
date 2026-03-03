import json
import re
from typing import Any

import vertexai
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from vertexai.generative_models import GenerativeModel

from config import settings
from services.rag_service import RAGService

_FLASH = "gemini-2.0-flash-001"
_session_service = InMemorySessionService()
_rag_service = RAGService()


def _init_vertexai() -> None:
    vertexai.init(
        project=settings.vertex_project_id,
        location=settings.vertex_location,
    )


_init_vertexai()


def _make_rag_tool(course_id: str) -> FunctionTool:
    async def rag_search(query: str) -> str:
        """在用户知识库中检索相关内容，返回带来源引用的 top-5 chunk。"""
        return await _rag_service.search(query, course_id)

    return FunctionTool(rag_search)


OUTLINE_INSTRUCTION = """你是课程大纲设计专家。
根据用户提供的学习需求和知识库内容，设计一套完整的课程大纲。

输出严格为 JSON，格式如下：
{
  "chapters": [
    {
      "chapter_id": 1,
      "title": "章节标题",
      "lessons": [
        { "lesson_id": "1-1", "title": "关卡标题", "summary": "一句话描述" }
      ]
    }
  ]
}

规则：
- 章节数量 3-6 个，每章 2-4 个关卡
- 由浅入深，符合认知规律
- 标题简洁有趣，像游戏关卡名
- 必须调用 rag_search 工具获取知识库内容后再设计
- 只输出 JSON，不加任何解释"""

LESSON_PLANNER_INSTRUCTION = """你是关卡内容规划师。
根据关卡主题和知识库内容，规划 20-25 个 steps 的学习流程骨架。

输出严格为 JSON 数组，每个 step 格式：
{
  "step_id": 1,
  "type": "text|svg|image|question-choice|question-fill|question-open",
  "topic": "这个 step 要讲/考的具体知识点",
  "content": "文本内容（text 类型填完整内容，其他类型填占位说明）",
  "source": "（来源：用户PDF，第N页）或（来源：网址，段落N）"
}

类型分布规则（必须遵守）：
- text：8-10 个，讲解核心概念，语气温柔口语化，像朋友聊天
- svg：2-3 个，标注需要动画可视化的知识点（填 topic 即可，content 填"[SVG待生成]"）
- image：1-2 个，标注需要图示的知识点（content 填图片描述）
- question-choice：3-4 个，选择题（content 填题干，options/answer 留空，标注"[习题待生成]"）
- question-fill：2-3 个，填空题
- question-open：1-2 个，开放题，放在关卡末尾

排列节奏：2-3 个 text → 1 个 svg/image → 1-2 个 text → 1 个题目，如此循环
必须调用 rag_search 获取知识内容，content 里必须包含来源引用
只输出 JSON 数组，不加任何解释"""

SVG_INSTRUCTION = """你是 SVG 教学动画设计师。
根据 lesson_plan 中所有 type=svg 的 steps，为每个生成完整的 SVG 动画代码。

输出严格为 JSON 数组，每项格式：
{
  "step_id": <对应的 step_id>,
  "svg_code": "<svg xmlns=...>完整 SVG 代码</svg>"
}

SVG 设计规则：
- 尺寸固定 800×450（宽×高）
- 必须有 CSS animation 或 SMIL 动画，不能是静态图
- 配色使用考拉主题色：绿 #5C8A3C、棕 #8B6347、米白 #FBF7F0
- 动画时长 3-8 秒，loop 或 once 均可
- 用简洁的图形+文字标注解释概念，不要复杂艺术画
- 只输出 JSON 数组，不加任何解释"""

QUIZ_INSTRUCTION = """你是习题设计专家。
根据 lesson_plan 中所有 type=question-* 的 steps，为每个生成完整的习题内容。

输出严格为 JSON 数组，每项格式：
{
  "step_id": <对应的 step_id>,
  "content": "题干",
  "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
  "answer": "A",
  "explanation": "解析，必须引用知识库来源"
}

习题规则：
- question-choice：4 选 1，选项长度相近，干扰项合理
- question-fill：content 用 ___ 表示填空位，answer 填正确答案
- question-open：content 是开放性问题，answer 填评分要点（3-5 条）
- 答案必须 100% 正确，可验证
- 解析必须包含来源引用 （来源：...）
- 只输出 JSON 数组，不加任何解释"""

VERIFIER_INSTRUCTION = """你是内容核实专家。
核验 lesson 的完整内容是否符合以下标准，如有问题直接修正后输出。

核验项目：
1. 事实准确性：text 和 quiz 内容是否符合知识库来源，无幻觉
2. 答案正确性：每道题的 answer 是否确实正确
3. SVG 合理性：svg_code 是否是合法 SVG，动画是否能反映知识点
4. 文本自然度：text 内容是否口语化自然，不像机器翻译
5. 来源引用：每个 text step 和 quiz explanation 是否都有 （来源：...）

输出完整修正后的 steps JSON 数组（与 lesson_plan 格式相同，包含所有字段）。
如果某项没问题则原样保留。只输出 JSON 数组，不加任何解释。"""

FEEDBACK_INSTRUCTION = """你是学习路径优化专家。
根据用户的反馈，对课程大纲进行最小化调整。

你会收到：
- current_outline: 当前课程大纲 JSON
- completed_lesson_id: 刚完成的关卡 ID
- user_feedback: 用户的文字反馈
- user_needs: 用户的原始学习需求

调整原则：
- 最小化改动：只调整后续未完成的关卡
- 如果用户觉得太难 → 在下一关前插入复习关卡，降低难度梯度
- 如果用户觉得太简单 → 跳过基础关卡，增加进阶内容
- 如果用户有特定疑问 → 在下一关开头增加专项解答 step
- 保留已完成关卡不变

输出两部分：
1. updated_outline: 调整后的大纲 JSON（格式与输入相同）
2. lesson_adjustment: 给下一关卡设计 agent 的补充指令（字符串）

输出格式：
{
  "updated_outline": { ... },
  "lesson_adjustment": "..."
}
只输出 JSON，不加任何解释。"""


def _build_lesson_pipeline(course_id: str) -> SequentialAgent:
    rag_tool = _make_rag_tool(course_id)

    lesson_planner = LlmAgent(
        name="lesson_planner",
        model=_FLASH,
        instruction=LESSON_PLANNER_INSTRUCTION,
        tools=[rag_tool],
        output_key="lesson_plan",
    )

    svg_designer = LlmAgent(
        name="svg_designer",
        model=_FLASH,
        instruction=SVG_INSTRUCTION,
        output_key="svg_results",
    )

    quiz_designer = LlmAgent(
        name="quiz_designer",
        model=_FLASH,
        instruction=QUIZ_INSTRUCTION,
        output_key="quiz_results",
    )

    parallel_designers = ParallelAgent(
        name="parallel_designers",
        sub_agents=[svg_designer, quiz_designer],
    )

    verifier = LlmAgent(
        name="verifier",
        model=_FLASH,
        instruction=VERIFIER_INSTRUCTION,
        tools=[rag_tool],
        output_key="verified_steps",
    )

    return SequentialAgent(
        name="lesson_pipeline",
        sub_agents=[lesson_planner, parallel_designers, verifier],
    )


def _build_outline_agent(course_id: str) -> LlmAgent:
    return LlmAgent(
        name="outline_agent",
        model=_FLASH,
        instruction=OUTLINE_INSTRUCTION,
        tools=[_make_rag_tool(course_id)],
        output_key="outline",
    )


def _build_feedback_agent() -> LlmAgent:
    return LlmAgent(
        name="feedback_agent",
        model=_FLASH,
        instruction=FEEDBACK_INSTRUCTION,
        output_key="feedback_result",
    )


def _extract_json(text: str) -> Any:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


async def generate_outline(
    course_id: str,
    topic: str,
    user_needs: str,
) -> dict[str, Any]:
    agent = _build_outline_agent(course_id)
    runner = Runner(
        agent=agent,
        session_service=_session_service,
        app_name=settings.adk_app_name,
    )
    session = await _session_service.create_session(
        app_name=settings.adk_app_name,
        user_id=course_id,
    )
    prompt = f"主题：{topic}\n学习需求：{user_needs}\n请设计课程大纲。"

    from google.genai.types import Content, Part
    final_text = ""
    async for event in runner.run_async(
        user_id=course_id,
        session_id=session.id,
        new_message=Content(role="user", parts=[Part(text=prompt)]),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text or ""

    if not final_text:
        state = await _session_service.get_session(
            app_name=settings.adk_app_name,
            user_id=course_id,
            session_id=session.id,
        )
        final_text = (state.state or {}).get("outline", "") if state else ""

    return _extract_json(final_text)


async def generate_lesson(
    course_id: str,
    lesson_id: str,
    lesson_title: str,
    lesson_summary: str,
    lesson_adjustment: str = "",
) -> list[dict[str, Any]]:
    pipeline = _build_lesson_pipeline(course_id)
    runner = Runner(
        agent=pipeline,
        session_service=_session_service,
        app_name=settings.adk_app_name,
    )
    session = await _session_service.create_session(
        app_name=settings.adk_app_name,
        user_id=course_id,
    )
    adjustment_note = f"\n补充指令：{lesson_adjustment}" if lesson_adjustment else ""
    prompt = (
        f"关卡标题：{lesson_title}\n"
        f"关卡简介：{lesson_summary}\n"
        f"关卡ID：{lesson_id}"
        f"{adjustment_note}\n"
        "请生成完整关卡内容（20+ steps）。"
    )

    from google.genai.types import Content, Part
    async for event in runner.run_async(
        user_id=course_id,
        session_id=session.id,
        new_message=Content(role="user", parts=[Part(text=prompt)]),
    ):
        pass

    state = await _session_service.get_session(
        app_name=settings.adk_app_name,
        user_id=course_id,
        session_id=session.id,
    )
    state_dict = (state.state or {}) if state else {}

    verified_raw = state_dict.get("verified_steps", "")
    if verified_raw:
        return _extract_json(verified_raw)

    lesson_plan_raw = state_dict.get("lesson_plan", "")
    if lesson_plan_raw:
        return _extract_json(lesson_plan_raw)

    return []


async def process_feedback(
    course_id: str,
    current_outline: dict[str, Any],
    completed_lesson_id: str,
    user_feedback: str,
    user_needs: str,
) -> dict[str, Any]:
    agent = _build_feedback_agent()
    runner = Runner(
        agent=agent,
        session_service=_session_service,
        app_name=settings.adk_app_name,
    )
    session = await _session_service.create_session(
        app_name=settings.adk_app_name,
        user_id=course_id,
    )
    prompt = (
        f"current_outline: {json.dumps(current_outline, ensure_ascii=False)}\n"
        f"completed_lesson_id: {completed_lesson_id}\n"
        f"user_feedback: {user_feedback}\n"
        f"user_needs: {user_needs}"
    )

    from google.genai.types import Content, Part
    final_text = ""
    async for event in runner.run_async(
        user_id=course_id,
        session_id=session.id,
        new_message=Content(role="user", parts=[Part(text=prompt)]),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text or ""

    if not final_text:
        state = await _session_service.get_session(
            app_name=settings.adk_app_name,
            user_id=course_id,
            session_id=session.id,
        )
        final_text = (state.state or {}).get("feedback_result", "") if state else ""

    return _extract_json(final_text)
