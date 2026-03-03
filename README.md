# Koala - 你的下一代 AI 学习助手

**Koala - Your Next AI Learning Assistant**

像一只温柔的考拉，抱着树枝静静陪你学习。通过每一次真实反馈，它会聪明调整内容深度、节奏与例子，让学习变成舒服的聊天，而不是压力。

专为 **Gemini Live Agent Challenge** 打造的沉浸式 AI 学习代理，参赛类别：**Creative Storyteller**（多模态故事创作）。支持实时语音自言自语反馈、多模态关卡（文本/语音/图像/SVG动画/题型混合）、自定义知识库（RAG + 严格引用来源），基于 **Google ADK (Agent Development Kit)** + Vertex AI Gemini 驱动。

## 项目愿景

传统学习平台太死板：内容固定、节奏单一、反馈浅层。  
Koala 要做的是**下一代**学习伙伴：
- 深度自适应：根据你的基础、目标、反馈实时调整课程大纲
- 自定义知识库：上传 PDF/网页 → 构建专属知识库，答案必须严格引用来源
- 闯关式沉浸体验：类似 Duolingo + Brilliant 的多模态关卡（20+ step/关）
- 实时语音互动：全程监听你的自言自语，立即给出反馈（需授权）
- 完全免费：暂无付费墙，专注学习本身

## 核心功能（MVP）

- 游客模式：无需注册登录，使用 Firebase Anonymous Auth，数据关联匿名用户 ID
- 用户选主题 + 上传知识源（PDF/网页）或自动联网权威内容
- 询问学习需求（基础、目的、难度、节奏）
- 生成细粒度课程大纲（章节 + 关卡），每关卡后动态调整
- 闯关学习：每个关卡 20+ step，多模态呈现（讲解 + 练习 + 开放反馈）
- 实时语音反馈：用户自言自语 → AI 即时回应 + 调整后续内容
- XP 积分（答对 1 题 = 10 XP）+ 答对音效（考拉主题）
- 删除课程 + 清空记录

## 技术亮点（比赛重点）

- **Google ADK**：Agent Development Kit，构建 Bidi-streaming 双向流 Agent，简化实时语音 + 工具调用
- **Vertex AI Gemini**：核心推理引擎，支持多模态生成 + 实时语音（Gemini Live）
- **比赛类别**：**Creative Storyteller** —— Gemini interleaved/mixed output 多模态内容生成
- **RAG 知识库**：上传资料 → Vertex AI Embedding + Vertex AI Vector Search → 严格引用来源
- **统一存储**：Firestore（用户数据） + Vertex AI Vector Search（向量）
- **前后端分离**：Next.js（前端卡通界面） + Python FastAPI + ADK（后端逻辑）
- **部署**：全跑在 Google Cloud（Cloud Run + Firestore + Vertex AI Endpoint）

## 快速上手（本地开发）

### 1. 配置环境变量

创建 `.env.local` 文件（复制自 `.env.local.example`）：

```bash
# 复制示例配置
cp .env.local.example .env.local
```

必须配置的环境变量：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `GOOGLE_API_KEY` | Google AI API Key（开发用） | `AIzaSy...` |
| `GOOGLE_GENAI_USE_VERTEXAI` | 切换开发/生产环境 | `FALSE`（开发）/ `TRUE`（生产） |
| `VERTEX_AI_PROJECT_ID` | Google Cloud 项目 ID（生产用） | `koala-agent-challenge` |
| `VERTEX_AI_LOCATION` | Vertex AI 区域（生产用） | `us-central1` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service Account 密钥路径（生产用） | `./credentials.json` |

**开发模式**：设置 `GOOGLE_GENAI_USE_VERTEXAI=FALSE` + `GOOGLE_API_KEY`，无需 GCP 凭证即可开发。**生产模式**：设置 `GOOGLE_GENAI_USE_VERTEXAI=TRUE` + GCP 凭证，ADK 自动切换到 Vertex AI Live API。无需登录，游客模式。

### 2. 启动项目

```bash
python start.py
```

`start.py` 会自动检测环境变量和依赖，分别启动：
- 后端：FastAPI (uvicorn，端口 8000)
- 前端：Next.js (npm run dev，端口 3000)

### 3. 分别启动（可选）

如果你想手动控制：

```bash
# 终端 1：启动后端
uvicorn main:app --reload --port 8000

# 终端 2：启动前端
npm run dev
```

访问 http://localhost:3000