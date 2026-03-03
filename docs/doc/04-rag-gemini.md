# 04 - RAG 与 Vertex AI Gemini 集成文档（ADK 版）

**项目名称**：Koala - 你的下一代 AI 学习助手  
**版本**：v0.5（ADK 框架 + Vertex AI Vector Search + WebM 音频 + 多模态生成）  
**编写日期**：2026年3月  
**作者**：Johnson  
**目标**：说明基于 ADK 的 RAG 知识库构建流程和 Vertex AI Gemini 的核心集成方式，确保所有生成内容严格引用来源，支持本地开发与云端比赛部署。

## 1. RAG 核心流程（Vertex AI 向量检索）

使用 **Vertex AI Embedding API** 生成向量 + **Vertex AI Vector Search** 存储和检索。

1. 用户上传知识源（PDF / 网页链接）或选择"自动联网权威内容"
2. 后端使用 **LangChain PDFLoader** 解析 PDF、**LangChain WebBaseLoader** 解析网页 → 切分成 chunk（每 chunk 约 300–500 token）
3. 每个 chunk 调用 **Vertex AI Text Embedding API** 生成向量
4. 向量 + 元数据（来源、页码、原文片段）存入 **Vertex AI Vector Search**（高效索引 + 检索）
5. 用户提问时：
   - 用 Vertex AI Embedding 嵌入问题
   - 在 Vertex AI Vector Search 中检索 top-5 相关 chunk（余弦相似度）
   - 将检索结果作为 context 注入 ADK Agent 的 prompt
   - ADK Agent 调用 Gemini `generate_content` 生成答案
6. **严格引用规则**：每条关键信息后必须标注来源，例如：
   - （来源：用户上传 PDF，第 5 页）
   - （来源：网页 https://xxx.com，段落 3）

**无知识源时**：联网搜索权威来源（Google Search API 或内置工具），记录引用链接。

## 2. ADK Agent 集成

### 2.1 ADK Koala Agent 定义

```python
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.live import RunConfig

# 定义 Koala Agent
agent = Agent(
    model="gemini-2.0-flash-live-001",  # 开发用；生产切换到 Vertex AI Live API
    name="koala_tutor",
    instruction="""你是温柔的考拉学习伙伴 Koala。
规则：
1. 所有回答必须 100% 基于提供的知识库 chunk 或权威来源，禁止编造。
2. 每条关键信息后必须标注来源，如（来源：用户PDF，第3页）。
3. 关卡 step 必须多模态混合：文本 + 图像/SVG描述 + 交互题型。
4. 每个关卡至少 20 个 step，节奏根据用户反馈调整。
5. 用温暖、口语化语气，像朋友聊天。""",
    tools=[rag_search_tool, generate_lesson_tool],  # ADK Tool 注册
)

session_service = InMemorySessionService()  # 开发用内存；生产用 Firestore SessionService

runner = Runner(
    agent=agent,
    session_service=session_service,
    app_name="koala"
)
```

### 2.2 ADK 双向流（Bidi-streaming）语音处理

```python
from google.adk.live import LiveRequestQueue

async def websocket_handler(websocket, user_id: str, session_id: str):
    queue = LiveRequestQueue()
    config = RunConfig(
        response_modalities=["TEXT", "AUDIO"],
        streaming_mode="BIDI",
        session_resumption=True
    )

    async for event in runner.run_live(
        user_id=user_id,
        session_id=session_id,
        live_request_queue=queue,
        run_config=config
    ):
        if event.type == "text":
            await websocket.send_text(event.content)
        elif event.type == "audio":
            await websocket.send_bytes(event.inline_data)

    # 接收用户语音流
    async def receive_audio():
        async for message in websocket.iter_bytes():
            queue.send_audio(message)  # WebM/Opus → ADK 自动处理
```

### 2.3 ADK Tool：RAG 检索

```python
from google.adk.tools import tool

@tool
def rag_search_tool(query: str, course_id: str) -> str:
    """在用户知识库中检索相关内容，返回带来源引用的 top-5 chunk。"""
    # 1. 嵌入查询
    embedding = vertex_ai_embed(query)
    # 2. Vector Search 检索
    results = vector_search.query(embedding, top_k=5, filter={"course_id": course_id})
    # 3. 格式化带引用的 context
    context = "\n".join([
        f"[来源：{r.source}，第{r.page}页] {r.content}"
        for r in results
    ])
    return context
```

## 3. Vertex AI Gemini 集成要点

- **开发模型**：`gemini-2.0-flash-live-001`（Gemini Live API，免费 API Key）
- **生产模型**：Vertex AI Live API（通过环境变量切换，无需改代码）
- **实时语音反馈**：ADK Bidi-streaming（自动重连、Session 持久化、Tool 执行）

### 主要调用场景

1. **生成课程大纲**  
   输入：主题 + 学习需求 + RAG tool 检索结果  
   输出：章节 + 关卡列表（JSON 格式）
   - **动态调整**：每完成一个关卡，根据用户反馈重新生成后续关卡大纲

2. **生成关卡内容（多模态）**  
   输入：当前关卡主题 + 上一关反馈 + RAG top-k chunk  
   输出：JSON 数组（20+ step），**一次性生成全部**，前端分页加载，每个 step 包含：
   - type: text / image / svg / question-choice / question-fill / question-open
   - content: 内容或题干
   - **多模态生成**：Gemini 直接生成图像描述/SVG 代码/语音描述
   - 语音朗读：自动生成语音描述（Gemini 多模态输出）

3. **实时语音自言自语反馈**  
   输入：用户语音流（WebSocket 传输，**WebM/Opus 格式**，ADK 处理转换）  
   输出：实时文本/语音回应 + 情感判断（e.g. "你似乎很困惑，我再解释一遍"）

## 4. 开发/生产环境切换（ADK 零代码切换）

```bash
# 开发阶段：.env.development
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_api_key_here

# 生产阶段：.env.production
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
```

ADK 通过环境变量自动切换底层平台，**Agent 代码无需改动**。

## 5. 依赖与环境变量

**Python 依赖**（requirements.txt）：
```
fastapi
uvicorn
google-cloud-aiplatform
google-adk                  # ADK 框架
langchain
langchain-community         # 包含 PDFLoader、WebBaseLoader 等工具
langchain-text-splitters    # 文本分块
pypdf2                      # 备用 PDF 解析
```

**环境变量**（.env）：
```
# 开发阶段
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_api_key_here

# 生产阶段
GOOGLE_GENAI_USE_VERTEXAI=TRUE
VERTEX_AI_PROJECT_ID=你的项目ID
VERTEX_AI_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=路径到service-account.json
```

---

**文档版本历史**：
- v0.4 2026-03-03：Vertex AI Vector Search + WebM 音频 + 多模态生成
- v0.5 2026-03-03：迁移到 ADK 框架，增加 Bidi-streaming 集成、ADK Tool 示例、零代码环境切换
