# 03 - 技术选型文档（Tech Stack）

**项目名称**：Koala - 你的下一代 AI 学习助手  
**版本**：v0.5（ADK 框架 + Vertex AI Vector Search + Firebase Anonymous Auth）  
**编写日期**：2026年3月  
**作者**：Johnson  
**目标**：明确前后端、AI、存储、部署等技术选型及理由，确保本地开发高效、云端部署稳定，并最大化适配 Gemini Live Agent Challenge 的要求。

## 1. 总体原则

- **统一存储**：所有数据存 Firestore，无需双模式切换
- **游客模式**：无需登录，所有数据关联设备 ID
- **云端部署**：全 Google Cloud 原生、实时性强、比赛加分
- **技术栈**：尽量少、成熟、社区活跃、易与 Vertex AI 集成
- **前后端分离**：前端专注交互，后端专注逻辑/AI/存储
- **比赛导向**：必须使用 Vertex AI Gemini + Google Cloud 服务

## 2. 前端技术选型

| 技术            | 版本/工具               | 理由                                                                 | 替代方案（不选原因）          |
|-----------------|--------------------------|----------------------------------------------------------------------|-------------------------------|
| 框架            | Next.js 14+ (App Router) | 支持 SSR/SSG、路由简单、SEO 友好、部署到 Vercel 或 Cloud Run 方便 | React CRA（构建慢）、Vue（生态不如） |
| 样式            | Tailwind CSS             | 快速写卡通风格、考拉主题颜色/动画、组件复用强                        | CSS Modules（太原始）、CSS-in-JS（体积大） |
| 表单            | React Hook Form          | 表单验证简单、性能好、易与 Zod 结合                                  | Formik（太重）                |
| 语音录制        | Web Audio API + MediaRecorder | 浏览器原生支持实时录音、流式传输到后端                               | Recorder.js（过时）           |
| HTTP 客户端     | Axios 或 fetch           | 简单可靠，支持 WebSocket（语音实时流）                                | -                             |

**前端目标**：卡通考拉风格、响应式、激发学习兴趣，参考 Brilliant 但更温暖。

## 3. 后端技术选型

| 技术            | 版本/工具               | 理由                                                                 | 替代方案（不选原因）          |
|-----------------|--------------------------|----------------------------------------------------------------------|-------------------------------|
| 框架            | FastAPI (Python 3.11+)   | 异步高性能、自动 Swagger 文档、易集成 ADK + Vertex AI、Pydantic 验证强     | Flask（同步慢）、Django（太重） |
| AI SDK          | google-cloud-aiplatform + google-adk | 官方 Vertex AI SDK 支持 Gemini 模型调用、Embedding、Live API；ADK 简化 Bidi-streaming Agent 开发 | 直接 Gemini API（缺少企业级功能） |
| Agent 框架      | Google ADK (Agent Development Kit) | 官方推荐框架，简化 Bidi-streaming 双向流 Agent 开发，内置 Session 管理、Tool 执行、自动重连 | 手动实现 Live API（数月基础设施开发） |
| RAG 工具        | LangChain                | 快速构建 RAG 链、支持 Vertex AI Embedding + Vector Search            | LlamaIndex（生态稍弱）        |
| 向量检索      | Vertex AI Vector Search（Google Cloud 原生） | 高效向量索引 + 相似度检索，余弦相似度                    | Firestore 手动计算（已放弃） |
| 认证            | Firebase Anonymous Auth | 游客模式，无需注册，数据关联匿名用户 ID                               | 自建 UUID（已放弃）          |
| 存储            | Firestore（统一）        | 所有用户数据存 Firestore                                             | SQLite（已放弃）           |

**后端目标**：高效处理 RAG、实时语音流、生成关卡内容。

## 4. 存储层（Firestore + Vertex AI Vector Search）

- **用户数据（Firestore）**：
  - 所有用户数据（进度、XP、反馈、课程）存 Firestore
  - 实时同步：进度、XP、反馈即时更新
- **向量存储与检索（Vertex AI Vector Search）**：
  - 文档向量存储在 Vertex AI Vector Search
  - 高效相似度检索（余弦相似度）
- **认证**：Firebase Anonymous Auth → 匿名用户 ID → 关联 Firestore 数据
- 本地开发和云端部署都需要配置 GCP 凭证

## 5. AI 核心（Vertex AI Gemini）

- **模型**：Gemini 1.5 Flash（速度优先）或 1.5 Pro（深度推理）
- **功能**：
  - 多模态生成（文本 + 图像 + 语音输出）
  - 实时语音反馈（Gemini Live API，支持中断、情感）
  - RAG 检索增强（结合 Vertex AI Embedding）
- **集成方式**：google-cloud-aiplatform SDK
- **提示工程**：系统 prompt 强调“严格引用来源”“个性化反馈”“关卡 20+ step”

## 6. 部署与运维

| 环境       | 部署方式                  | 关键服务                              | 备注                       |
|------------|---------------------------|---------------------------------------|----------------------------|
| 本地开发   | 直接运行                  | Next.js dev + FastAPI uvicorn         | 需配置 GCP 凭证使用 Firestore |
| 云端/比赛  | Google Cloud Run          | 前后端容器化 + Vertex AI Endpoint     | 比赛提交必须云端           |
| 数据库     | Firestore                 | 实时 NoSQL                            | 云端唯一存储               |
| 环境变量   | .env / Cloud Run 设置     | STORAGE_MODE、VERTEX_AI_PROJECT_ID 等 | 双模式切换核心             |

## 7. 为什么不选其他技术？

- 不选 PostgreSQL：本地部署麻烦，云端 Cloud SQL 成本高，不如 Firestore 实时且免费额度够用。
- 不选纯 Gemini API：缺少 Vertex AI 的企业级功能和比赛加分点。
- 不选 Docker 本地开发：增加复杂度，SQLite 更轻量。

---

**文档版本历史**：
- v0.1 2026-03-03：初稿
- v0.2 2026-03-03：明确双模式存储 + Vertex AI 重点说明
- v0.3 2026-03-03：统一 Firestore 存储 + 游客模式
- v0.4 2026-03-03：Vertex AI Vector Search + Firebase Anonymous Auth
- v0.5 2026-03-03：加入 ADK 框架，明确 Creative Storyteller 类别

下一阶段：基于本技术选型，编写 04-rag-gemini.md 详细集成细节（ADK 版）。