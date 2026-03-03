# 05 - ADK 技术文档与比赛指南

**项目名称**：Koala - 你的下一代 AI 学习助手  
**版本**：v0.1  
**编写日期**：2026年3月  
**作者**：Johnson  
**目标**：整理 Gemini Live Agent Challenge 官方技术文档，为项目开发提供 ADK 技术指导。

---

## 1. 比赛类别与项目定位

### 1.1 比赛三个类别

| 类别 | 核心焦点 | 关键技术要求 |
|------|----------|--------------|
| **Live Agents** | 实时交互（音频/视觉） | Gemini Live API 或 ADK |
| **Creative Storyteller** | 多模态故事创作（文本+图像+音频+视频混合输出） | Gemini interleaved/mixed output |
| **UI Navigator** | 视觉 UI 理解与交互 | Gemini multimodal 解释屏幕/执行操作 |

### 1.2 Koala 项目选择：**Creative Storyteller**

Koala 是一个多模态学习应用，生成包含文本、图像、SVG 动画、语音的混合内容，符合 **Creative Storyteller** 类别要求：
- ✅ 使用 Gemini 的 interleaved/mixed output 能力
- ✅ 多模态内容生成（文本+图像+音频混合）
- ✅ Agent 托管在 Google Cloud

---

## 2. ADK (Agent Development Kit) 核心概念

### 2.1 什么是 ADK？

ADK 是 Google 官方提供的生产级框架，用于构建 **Bidi-streaming（双向流）** 应用。它将数月的基础设施开发简化为声明式配置。

**对比**：直接使用 Live API vs 使用 ADK

| 特性 | 原始 Live API | ADK Gemini Live API Toolkit |
|------|---------------|------------------------------|
| Agent 框架 | ❌ 不可用 | ✅ 单/多 Agent、工作流 |
| Tool 执行 | 手动处理 | ✅ 自动执行 |
| 连接管理 | 手动重连 | ✅ 自动重连 |
| 事件模型 | 自定义 | ✅ 统一事件模型 |
| Session 持久化 | 手动实现 | ✅ SQL/Firestore/Vertex AI |

### 2.2 Bidi-streaming（双向流）

**核心特性**：
- **双向通信**：用户和 AI 同时发送数据，无需等待完整响应
- **自然中断**：用户可以随时打断 AI 的回答
- **多模态支持**：同时处理音频、视频、文本

**与传统的区别**：
- Server-Side Streaming：单向服务器→客户端
- Token-Level Streaming：逐词输出，但需等待完成
- **Bidi-streaming**：真正的双向实时对话

---

## 3. ADK 架构

### 3.1 整体架构（三层）

```
┌─────────────────────────────────────────────────────────┐
│  Application Layer (你拥有)                               │
│  - FastAPI + WebSocket 服务器                           │
│  - Agent 定义（指令、工具、行为）                        │
├─────────────────────────────────────────────────────────┤
│  ADK Orchestration (ADK 处理)                          │
│  - LiveRequestQueue: 消息缓冲和排序                      │
│  - Runner: Session 生命周期管理                          │
│  - Agent: 内部 LLM 流程编排                             │
├─────────────────────────────────────────────────────────┤
│  Google AI Backbone                                    │
│  - Gemini Live API (开发阶段)                           │
│  - Vertex AI Live API (生产阶段)                        │
└─────────────────────────────────────────────────────────┘
```

### 3.2 核心组件

| 组件 | 作用 |
|------|------|
| **Agent** | 定义 AI 的模型、工具、人格 |
| **SessionService** | 管理会话状态（内存/数据库） |
| **Runner** | 编排所有 Session |
| **LiveRequestQueue** | 缓冲上游消息（文本/音频/视频） |
| **RunConfig** | 配置会话行为（模态、转录、会话恢复） |

---

## 4. 四阶段应用生命周期

### Phase 1: 应用初始化（应用启动时执行一次）

```python
# 1. 定义 Agent
agent = Agent(
    model="gemini-2.0-flash-live-001",
    name="koala_tutor",
    instruction="你是温柔的考拉学习伙伴 Koala..."
)

# 2. 创建 SessionService（开发用内存，生产用数据库）
session_service = InMemorySessionService()

# 3. 创建 Runner
runner = Runner(
    agent=agent,
    session_service=session_service,
    app_name="koala"
)
```

### Phase 2: Session 初始化（用户连接时）

```python
# 1. 获取或创建 Session
session = await session_service.get_or_create_session(
    user_id="user_123",
    session_id="session_456"
)

# 2. 创建 RunConfig
config = RunConfig(
    response_modalities=["TEXT", "AUDIO"],
    streaming_mode="BIDI",
    session_resumption=True
)

# 3. 创建 LiveRequestQueue
queue = LiveRequestQueue()
```

### Phase 3: 双向流（WebSocket 连接期间）

```python
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=queue,
    run_config=config
):
    # 处理 7 种事件类型：
    # - text, audio, transcription, metadata, tool_call, tool_response, error
    if event.type == "text":
        await websocket.send_text(event.content)
    elif event.type == "audio":
        await websocket.send_audio(event.inline_data)
```

### Phase 4: Session 终止

```python
# 优雅关闭
await queue.close()
# Session 状态已自动持久化
```

---

## 5. 开发/生产环境切换

ADK 通过环境变量切换平台，**无需修改代码**：

### 开发阶段（Gemini Live API）

```bash
# .env.development
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_api_key_here
```

**优点**：
- 快速原型开发
- 免费 API Key
- 无需 Google Cloud 配置

### 生产阶段（Vertex AI Live API）

```bash
# .env.production
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
```

**优点**：
- 企业级基础设施
- 高级监控和日志
- 集成 Google Cloud 服务

---

## 6. 多模态能力

### 6.1 音频

| 类型 | 规格 |
|------|------|
| 输入 | 16-bit PCM, mono, 16kHz |
| 输出 | 16-bit PCM, mono, 24kHz |
| 推荐块大小 | 50-100ms (1,600-3,200 bytes) |

### 6.2 图像/视频

- 格式：JPEG
- 分辨率：768×768（推荐）
- 帧率：最高 1 FPS

### 6.3 模型架构

| 模型 | 特点 |
|------|------|
| **Native Audio** (gemini-2.5-flash-native-audio-preview) | 端到端音频处理，更自然的语调，支持情感对话 |
| **Half-Cascade** (gemini-2.0-flash-live-001) | 音频→文本→音频，支持 TEXT 和 AUDIO 两种响应 |

---

## 7. 比赛提交要求

### 7.1 必需材料

| 材料 | 说明 |
|------|------|
| 项目代码 | 公开 GitHub 仓库 |
| README.md | 详细启动步骤 |
| 架构图 | Mermaid 或图片 |
| Demo 视频 | ≤4 分钟，展示实际功能 |
| GCP 部署证明 | 控制台截图或录制 |

### 7.2 加分项（可选）

- 📝 博客/视频教程（发布到 Medium/Dev.to/YouTube）
- 🤖 自动化部署（Terraform/脚本）
- 👥 GDG 成员身份

### 7.3 评分标准

| 维度 | 权重 | 重点 |
|------|------|------|
| 创新与多模态体验 | 40% | 突破"文本框"范式、自然沉浸式交互 |
| 技术实现与架构 | 30% | Google Cloud 原生、ADK/GenAI SDK、避免幻觉 |
| Demo 与演示 | 30% | 清晰问题/解决方案、架构图、云部署证明 |

---

## 8. 参考资源

### 8.1 官方文档

- [ADK 文档](https://google.github.io/adk-docs/)
- [Gemini Live API 指南](https://ai.google.dev/gemini-api/docs/live-guide)
- [Vertex AI Live API 概述](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api)

### 8.2 代码示例

- [ADK Bidi Demo](https://github.com/google/adk-samples/tree/main/python/agents/bidi-demo)
- [Live API 示例](https://github.com/GoogleCloudPlatform/generative-ai/tree/main/gemini/multimodal-live-api)
- [沉浸式语言学习 App](https://github.com/ZackAkil/immersive-language-learning-with-live-api)

### 8.3 学习资源

- [ADK Bidi-streaming 5 分钟入门](https://www.youtube.com/watch?v=vLUkAGeLR1k)
- [ADK 视觉指南 (Medium)](https://medium.com/google-cloud/adk-bidi-streaming-a-visual-guide-to-real-time-multimodal-ai-agent-development-62dd08c81399)

---

## 9. Koala 技术选型总结

| 项目 | 选型 | 理由 |
|------|------|------|
| 比赛类别 | **Creative Storyteller** | 多模态内容生成 |
| 开发框架 | **ADK (Python)** | 官方推荐，简化开发 |
| Agent 运行时 | **Vertex AI Live API** | 生产部署 |
| 开发环境 | **Gemini Live API** | 快速原型 |
| Session 存储 | **Firestore** | 向量+用户数据统一 |
| 认证 | **Firebase Anonymous Auth** | 游客模式 |

---

**文档版本历史**：
- v0.1 2026-03-03：初稿，整理 ADK 技术文档与比赛指南
