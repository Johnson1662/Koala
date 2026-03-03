# CLAUDE.md — Koala 项目专属记忆 & 行为约束

> 本文件是 AI 助手的行为准则，每次对话开始时必须回顾。违反红线 → 立即重做。

---

## 项目一句话概述

**Koala** 是一个基于 Google ADK + Vertex AI Gemini 的沉浸式 AI 学习助手，参赛于 **Gemini Live Agent Challenge（Creative Storyteller 类别）**，核心能力：多模态闯关学习（文本/图像/SVG/语音混合）+ 实时 Bidi-streaming 语音反馈 + RAG 知识库（严格引用来源）。

---

## 当前技术栈（保持更新）

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | Python 3.11+ + FastAPI | 异步 API，WebSocket 语音流 |
| Agent 框架 | Google ADK (google-adk) | Bidi-streaming，Session/Tool 管理 |
| AI 核心 | Vertex AI Gemini（开发用 Gemini Live API） | gemini-2.0-flash-live-001 |
| RAG | LangChain + Vertex AI Embedding + Vector Search | PDF/网页解析、向量检索、严格引用 |
| 前端框架 | Next.js 14+（App Router）+ Tailwind CSS | 卡通考拉风格，响应式 |
| 存储 | Firestore（用户数据 + Session）+ Vertex AI Vector Search | 统一云端存储 |
| 认证 | Firebase Anonymous Auth | 游客模式，无需注册 |
| 部署 | Google Cloud Run + Vertex AI Endpoint + Firestore | 比赛必须云端运行 |
| 测试（后端） | pytest + pytest-asyncio | 目标覆盖率 ≥ 80% |
| 测试（前端） | Vitest + React Testing Library | 目标覆盖率 ≥ 75% |
| 代码风格 | ruff + black（后端）、eslint + prettier（前端） |  |

---

## 最高优先级原则（违反即重做）

1. **简单优先**：每个变更尽量最小影响、最少代码行。拒绝过度设计、过早抽象、炫技。
2. **不偷懒**：必须找到根因再修复。禁止"先跑通再说""后面再重构"的临时方案。
3. **最小影响**：只改必须改的部分。新增依赖、新抽象、新文件需给出充分理由。
4. **先计划后动手**：任何 3+ 步、涉及架构/接口/安全/数据模型的任务，必须进入**计划模式**（见下方工作流）。
5. **完成前强制验证**：未通过测试、未查日志、未演示正确行为 → 不得标记完成。问自己："资深工程师会 approve 这个 diff 吗？"
6. **需求不明确时强制反问**（红线）：见下方专用章节。
7. **每次修改代码后询问用户是否上传至远程仓库**（必须执行，不得跳过）。

---

## 需求不明确 / 模糊时的强制反问规则

当出现以下任一情况，**立即停止推进，不要猜测、不要补全、不要写代码**：

- 需求模糊/歧义（"优化一下""好看一点""快一点"无具体指标）
- 缺少关键信息（目标性能、浏览器兼容、数据规模、优先级、安全约束等）
- 前后矛盾（与之前指令 / 本文件 / 已有代码冲突）
- 重大决策（架构变更、新依赖、对外接口、安全、数据模型等）
- 你对意图把握 < 80%

**正确回复格式**（保持专业、简洁）：

1. 复述你当前理解（1–2 句）
2. 列出 2–4 个最关键、最具体的澄清问题（编号）
3. 明确声明："在得到明确答复前，我不会继续实现或修改代码。"

**禁止**：
- 说"我猜你是想…""要不先试试？"
- 自己脑补默认值继续
- 抛出 8+ 个问题轰炸
- 反问后偷偷写代码

---

## 非平凡任务工作流（3+ 步 / 架构相关 / 不明朗）

1. 先写计划 → `docs/todo.md`（包含步骤、可选项、权衡、风险）
2. 展示计划给我确认（或说"计划 ok，继续"）
3. 逐步执行，每大步后给高层总结（1–3 句）
4. 每步变更后说明行为差异 & 回归风险
5. 完成后：
   - `docs/todo.md` 标记完成 + 添加评审意见
   - 捕获教训 → 更新 `docs/lessons.md`（防止重复错误）
   - 询问用户是否上传至远程仓库

---

## Bug 修复铁律

- 收到 bug → **直接修**，不要问"复现步骤/日志"（除非完全不清楚）
- 顺序：读日志 → 错误栈 → 失败测试 → 根因 → 修复 + 加防护
- 修复后必须：
  - 通过原失败测试
  - 主动跑相关 CI / 全测试套件
  - 说明"根因 + 为什么不会再发生"
- 修复完成后询问用户是否上传至远程仓库

---

## Koala 项目特有约束

### ADK / 语音流
- WebSocket 语音流统一走 `/api/voice/stream`，**禁止**在前端直连 Vertex AI
- ADK `LiveRequestQueue` 必须在 WebSocket 断开时调用 `queue.close()`，防止资源泄漏
- 音频格式：前端发送 **WebM/Opus**，ADK 负责转换，后端不做额外音频处理
- 开发用 `GOOGLE_GENAI_USE_VERTEXAI=FALSE`（免费 API Key），生产切 `TRUE`，**Agent 代码禁止硬编码平台判断**

### RAG / 知识库
- 每条生成内容必须附来源标注，格式：`（来源：用户PDF，第N页）` 或 `（来源：网页URL，段落N）`
- **禁止**在没有知识库 chunk 支撑时生成关键性陈述（宁可说"知识库中未找到相关内容"）
- Vector Search 查询默认 top-5，不得随意调高（成本控制）

### 关卡内容生成
- 每个关卡 20+ step，**一次性生成全部**，禁止流式追加（前端分页加载）
- Step 类型枚举：`text | image | svg | question-choice | question-fill | question-open`
- XP 规则：答对 1 题 = 10 XP，连续答对 3 题 = 额外 10 XP，**禁止**改动此规则

### 存储
- 所有用户数据统一走 **Firestore**，禁止在任何环境使用 SQLite 或本地文件
- 向量数据统一走 **Vertex AI Vector Search**，禁止使用 Firestore 手动存向量
- Firestore collection 命名：`users`、`courses`、`progress`、`feedback`、`xp_logs`

### 前端
- 卡通考拉风格：温暖色调（绿/棕/米白），不得引入冷色系大面积背景
- 加载动画：考拉抱着树枝转圈，禁止用通用 spinner 替代
- 语音权限：必须明确提示用户授权，拒绝录音时降级为纯文本模式（禁止强制要求）

---

## 代码风格 & 质量红线

### 通用
- 命名：清晰 > 简短，禁止无意义缩写（除行业标准如 i18n、ADK、RAG）
- 函数/组件：单一职责，Python 函数 ≤ 40 行，React 组件 ≤ 200 行
- 错误处理：显式（抛出 / Result 类型 / 专用错误类），禁止空 `except` / 空 `catch`
- 日志：关键路径加结构化日志（`user_id`、`course_id`、`session_id`）

### Python（后端）
- 类型注解：所有函数参数和返回值必须有类型注解
- 异步：FastAPI 路由全部 `async def`，禁止在异步上下文中调用同步阻塞 IO
- 依赖管理：`requirements.txt` 锁定版本（`==`），不得用 `>=` 松散约束
- 格式化：`ruff format` + `ruff check`，CI 必须通过

### TypeScript / React（前端）
- 禁止 `as any`、`@ts-ignore`、`@ts-expect-error`
- 禁止直接操作 DOM（用 React ref）
- API 调用统一封装在 `src/api/` 目录，组件内禁止裸 `fetch`/`axios`
- 格式化：`prettier` + `eslint`，CI 必须通过

---

## 自我改进闭环（必须执行）

- 每次被纠正风格/逻辑/流程 → 立即更新本文件对应部分，或追加到 `docs/lessons.md`
- 会话开始时回顾最近 3–5 条 lessons，避免重复错误
- 反复犯错 → 主动提出更强约束，征求同意后写入

---

## 追求优雅（平衡版）

- 非平凡修改前，暂停问："有没有更简单、更优雅、职责更单一的方式？"
- 如果有更好方案，先提出对比，而不是直接写代码

---

## 禁止行为（红线）

- 不要问"要不要加 xxx""你确定吗"（除架构级决策）
- 不要写临时/丑陋代码说"后面重构"
- 不要无理由引入新依赖（每个新依赖必须说明：为什么不用现有库？）
- 不要一次性改 10+ 文件（拆小 PR）
- 不要绕过现有错误边界 / logging / auth / rate-limit
- 不要硬编码 API Key、项目 ID、凭证路径（统一走环境变量）
- 不要在 Agent 代码中硬编码 `GOOGLE_GENAI_USE_VERTEXAI` 判断（环境变量负责切换）

---

## 提交规范（Conventional Commits）

```
feat:     新功能
fix:      Bug 修复
refactor: 重构（不改行为）
docs:     文档更新
test:     测试相关
chore:    构建/依赖/配置
style:    格式调整（不改逻辑）
```

示例：`feat(rag): add top-5 Vector Search retrieval with source citation`

---

## 关键文档索引

| 文档 | 路径 | 内容 |
|------|------|------|
| 需求文档 | `docs/doc/01-requirements.md` | 用户故事、MVP 范围、非功能需求 |
| 架构文档 | `docs/doc/02-architecture.md` | 系统架构、数据流、前后端分层 |
| 技术选型 | `docs/doc/03-tech-stack.md` | 技术选择理由、替代方案对比 |
| RAG 集成 | `docs/doc/04-rag-gemini.md` | ADK Agent 定义、RAG 流程、代码示例 |
| ADK 技术 | `docs/doc/05-adk-technical-docs.md` | ADK 核心概念、比赛要求、评分标准 |
| 经验教训 | `docs/lessons.md` | 历史错误记录（会话开始时回顾） |

---

## 最后最高指令（贯穿始终）

**基于我已知的一切信息，实现最优雅、最小、最可靠的解决方案。**

**每次修改代码后，必须询问用户："是否需要将本次修改上传至远程仓库？"**
