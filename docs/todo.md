# Koala MVP 实施计划

**版本**：v1.0  
**更新日期**：2026年3月  
**目标**：Gemini Live Agent Challenge（Creative Storyteller）比赛提交版本

---

## 进度总览

| Phase | 内容 | 预估时间 | 状态 |
|-------|------|----------|----- |
| Phase 0 | 环境搭建 & 脚手架 | 0.5 天 | ✅ 完成 |
| Phase 1 | 后端 Auth + 基础 API | 1 天 | ✅ 完成 |
| Phase 2 | RAG 知识库 | 1.5 天 | ✅ 完成 |
| Phase 3 | ADK Agent + 关卡生成 | 2 天 | ✅ 完成 |
| Phase 4 | 前端 UI | 2 天 | ⬜ 未开始 |
| Phase 5 | 语音流 Bidi-streaming | 1.5 天 | ⬜ 未开始 |
| Phase 6 | 云端部署 + Demo | 1 天 | ⬜ 未开始 |

---

## Phase 0：环境搭建 & 脚手架（0.5 天）

**目标**：可以跑通 `python start.py`，前后端同时启动，健康检查通过。

### 后端脚手架

- [ ] 创建 `src/backend/` 目录结构：
  ```
  src/backend/
  ├── main.py               # FastAPI 入口，挂载所有路由
  ├── config.py             # 读取环境变量，集中配置
  ├── requirements.txt      # 锁版本（==），含 ADK + FastAPI + LangChain
  ├── .env.example          # 环境变量模板（不含真实值）
  ├── routers/
  │   ├── __init__.py
  │   ├── auth.py           # Firebase Anonymous Auth
  │   ├── courses.py        # 课程 CRUD
  │   ├── lessons.py        # 关卡生成 + 反馈
  │   ├── rag.py            # 知识库上传 + 查询
  │   └── voice.py          # WebSocket 语音流
  ├── services/
  │   ├── __init__.py
  │   ├── firestore.py      # Firestore 客户端封装
  │   ├── rag_service.py    # RAG 逻辑（Embedding + Vector Search）
  │   └── agent_service.py  # ADK Agent 初始化 + Runner
  ├── models/
  │   ├── __init__.py
  │   └── schemas.py        # Pydantic 数据模型
  └── tests/
      ├── __init__.py
      └── test_health.py    # 最基础的健康检查测试
  ```
- [ ] 编写 `requirements.txt`（锁版本）：
  - `fastapi==0.115.0`
  - `uvicorn[standard]==0.32.0`
  - `google-cloud-aiplatform==1.71.0`
  - `google-adk==0.5.0`（待确认最新稳定版）
  - `firebase-admin==6.5.0`
  - `langchain==0.3.7`
  - `langchain-community==0.3.7`
  - `langchain-text-splitters==0.3.2`
  - `pypdf==5.1.0`
  - `pydantic==2.9.2`
  - `python-dotenv==1.0.1`
  - `pytest==8.3.3`
  - `pytest-asyncio==0.24.0`
- [ ] 编写 `.env.example`（含全部必需环境变量，值为占位符）
- [ ] 编写 `main.py`：FastAPI 实例 + 根路由健康检查 `/`

### 前端脚手架

- [ ] 初始化 Next.js 14（App Router）项目到 `src/frontend/`：
  ```
  src/frontend/
  ├── package.json
  ├── next.config.js
  ├── tailwind.config.js
  ├── tsconfig.json
  ├── .eslintrc.json
  ├── .prettierrc
  ├── app/
  │   ├── layout.tsx        # 根布局（考拉主题字体/颜色）
  │   ├── page.tsx          # 首页（Home 主看板）
  │   ├── courses/
  │   │   ├── page.tsx      # 课程列表
  │   │   └── [id]/
  │   │       └── page.tsx  # 课程详情
  │   └── lessons/
  │       └── [id]/
  │           └── page.tsx  # 关卡页
  ├── components/
  │   ├── ui/               # 基础 UI 组件
  │   └── koala/            # 考拉专属组件（加载动画等）
  ├── src/
  │   └── api/              # 所有后端 API 调用封装（禁止组件裸 fetch）
  └── public/
      └── koala/            # 考拉图片资源
  ```
- [ ] 配置 Tailwind CSS 考拉主题色（绿/棕/米白）
- [ ] 配置 ESLint + Prettier

### 启动脚本

- [ ] 编写 `start.py`（项目根目录）：
  - 检查 Python 版本 ≥ 3.11
  - 检查 Node.js 版本
  - 检查必需环境变量（`GOOGLE_API_KEY` 或 `GOOGLE_APPLICATION_CREDENTIALS`）
  - 并行启动后端（uvicorn，端口 8000）+ 前端（npm run dev，端口 3000）
  - 统一日志输出（带颜色区分前后端）

**验收标准**：
- `python start.py` 启动，前后端均无报错
- `GET http://localhost:8000/` 返回 `{"status": "ok"}`
- `GET http://localhost:3000/` 返回考拉风格首页（哪怕是空白骨架）

---

## Phase 1：后端 Auth + 基础 API（1 天）

**目标**：Firebase 匿名认证可用，课程 CRUD 接口通过测试。

### 任务清单

- [ ] `routers/auth.py`：
  - `POST /auth/anonymous` → Firebase 生成匿名用户 Token
  - 返回 `{ user_id, token }`
- [ ] `services/firestore.py`：
  - 初始化 Firebase Admin SDK（`GOOGLE_APPLICATION_CREDENTIALS`）
  - 封装 Firestore CRUD（get / set / update / delete / query）
  - Collection 命名严格按规范：`users`、`courses`、`progress`、`feedback`、`xp_logs`
- [ ] `models/schemas.py`：
  - `User`、`Course`、`LessonStep`、`Progress`、`XPLog` Pydantic 模型
  - 全部有类型注解
- [ ] `routers/courses.py`：
  - `POST /courses` → 创建课程（主题 + 知识源元数据）
  - `GET /courses` → 列出用户所有课程
  - `GET /courses/{id}` → 课程详情（含大纲）
  - `DELETE /courses/{id}` → 删除课程 + 清空相关 progress/feedback/xp_logs
- [ ] 测试：`tests/test_courses.py`（CRUD 基础覆盖）

**验收标准**：
- `pytest tests/` 全部通过
- Firestore 中实际写入/读取数据可验证

---

## Phase 2：RAG 知识库（1.5 天）

**目标**：上传 PDF/网页 → 构建向量索引 → 检索 top-5 chunk，严格带来源引用。

### 任务清单

- [ ] `routers/rag.py`：
  - `POST /rag/upload` → 接收 PDF 文件或网页 URL
  - `GET /rag/status/{course_id}` → 知识库构建状态
- [ ] `services/rag_service.py`：
  - PDF 解析：`LangChain PDFLoader`（pypdf 后端）
  - 网页解析：`LangChain WebBaseLoader`
  - 文本切分：`RecursiveCharacterTextSplitter`（chunk_size=400，overlap=50）
  - Embedding：Vertex AI Text Embedding API（`textembedding-gecko@003`）
  - 向量存储：Vertex AI Vector Search（Index + Endpoint）
  - 元数据格式：`{ course_id, source_type, source_name, page_num, chunk_text }`
- [ ] `services/rag_service.py` → `search(query, course_id) -> list[Chunk]`：
  - 嵌入查询 → Vector Search 检索 top-5（固定，不得调高）
  - 返回带引用格式的 context 字符串
- [ ] ADK Tool 注册（在 `agent_service.py` 中）：
  ```python
  @tool
  def rag_search_tool(query: str, course_id: str) -> str:
      ...
  ```
- [ ] 测试：`tests/test_rag.py`（上传 → 检索 → 验证引用格式）

**验收标准**：
- 上传一个 PDF → Vector Search 中有向量 → 查询返回包含来源标注的 context
- 引用格式：`（来源：用户PDF，第N页）` 或 `（来源：网页URL，段落N）`
- top-5 固定，不得超出

---

## Phase 3：ADK Agent + 关卡生成（2 天）

**目标**：koala_tutor Agent 可生成大纲 + 一次性生成 20+ step 关卡内容（JSON），XP 计算正确。

### 任务清单

- [ ] `services/agent_service.py`：
  - 初始化 ADK Agent（`koala_tutor`，模型 `gemini-2.0-flash-live-001`）
  - 注册 Tools：`rag_search_tool`、`generate_lesson_tool`
  - 创建 Runner + SessionService（开发用 InMemory）
- [ ] `routers/courses.py` 扩展：
  - `POST /courses/{id}/outline` → 调用 Agent 生成课程大纲（章节 + 关卡列表）
  - `POST /courses/{id}/outline/adjust` → 关卡完成后动态调整后续大纲
- [ ] `routers/lessons.py`：
  - `POST /lessons/generate` → 传入关卡主题 + RAG context → 一次性生成 20+ step JSON
  - `POST /lessons/{id}/feedback` → 记录用户反馈 + 触发大纲动态调整
  - `POST /lessons/{id}/answer` → 记录答题结果 + 计算 XP
- [ ] XP 计算（`services/xp_service.py`）：
  - 答对 1 题 = 10 XP（固定）
  - 连续答对 3 题 = 额外 10 XP
  - 写入 Firestore `xp_logs` collection
- [ ] Lesson step JSON 格式：
  ```json
  {
    "step_id": 1,
    "type": "text|image|svg|question-choice|question-fill|question-open",
    "content": "...",
    "options": ["A", "B", "C", "D"],
    "answer": "A",
    "explanation": "...",
    "source": "（来源：用户PDF，第3页）"
  }
  ```
- [ ] System prompt 工程：强调 20+ step、多模态混合、严格引用来源、温柔口语化语气
- [ ] 测试：`tests/test_agent.py`（大纲生成 + 关卡生成格式验证 + XP 计算）

**验收标准**：
- 给定主题 → 返回合法 JSON 大纲
- 生成关卡 → step 数量 ≥ 20，类型多样（至少含 text + question-choice）
- XP 计算：答对 3 连击后 xp_logs 中有 bonus 记录

---

## Phase 4：前端 UI（2 天）

**目标**：考拉主题完整 UI，可浏览课程、进入关卡、完成做题交互。

### 任务清单

- [ ] `src/api/` 封装所有后端 API：
  - `auth.ts`：匿名登录
  - `courses.ts`：创建/列出/删除课程，生成大纲
  - `lessons.ts`：生成关卡、提交答案、提交反馈
  - `rag.ts`：上传知识源
- [ ] `components/koala/KoalaLoader.tsx`：考拉抱树枝转圈加载动画（**禁止用通用 spinner**）
- [ ] `app/page.tsx`（Home）：
  - XP 显示
  - 进行中课程卡片
  - 新建课程入口
- [ ] `app/courses/page.tsx`（课程列表）：
  - 课程卡片（主题、关卡数、完成进度）
  - 创建新课程流程（主题选择 → 知识源上传 → 需求问卷 → 生成大纲）
- [ ] `app/courses/[id]/page.tsx`（课程详情）：
  - 大纲预览（章节 + 关卡列表）
  - 开始/继续学习按钮
  - 删除课程按钮
- [ ] `app/lessons/[id]/page.tsx`（关卡页）：
  - Step 分页展示（前端分页，不重新请求）
  - 各 step 类型渲染：`text`（Markdown）、`image`（alt + 描述）、`svg`（内联 SVG）、`question-*`（交互题）
  - 答题反馈（对/错动画 + 来源引用展示）
  - XP 动画（答对时 +10 XP 弹出）
  - 关卡末尾反馈表单
- [ ] 颜色主题（Tailwind config）：
  - primary: `#5C8A3C`（考拉绿）
  - secondary: `#8B6347`（考拉棕）
  - background: `#FBF7F0`（米白）
- [ ] 测试：Vitest + RTL 覆盖核心组件

**验收标准**：
- 全流程可手动走通：登录 → 创建课程 → 上传知识源 → 生成大纲 → 进入关卡 → 答题 → 看到 XP 变化
- 加载时显示考拉动画（非通用 spinner）
- 语音权限未授权时，语音区域降级为文本输入（不崩溃）

---

## Phase 5：语音流 Bidi-streaming（1.5 天）

**目标**：用户自言自语 → 后端实时处理 → 前端显示 AI 反馈，延迟 < 2 秒。

### 任务清单

- [ ] `routers/voice.py`：
  - `WebSocket /api/voice/stream` 端点
  - 接收 WebM/Opus 音频块（前端 MediaRecorder 输出）
  - 创建 `LiveRequestQueue` → 传给 ADK Runner
  - 转发 ADK 事件（text/audio）回 WebSocket
  - **必须在 WebSocket 断开时调用 `queue.close()`**（防止资源泄漏）
- [ ] `components/koala/VoiceInput.tsx`：
  - 明确提示用户授权麦克风
  - 授权 → MediaRecorder 录音 → WebSocket 流式传输
  - 拒绝授权 → 降级为文本输入模式（不强制）
  - 显示实时转写文本 + AI 反馈
- [ ] 集成到关卡页（`app/lessons/[id]/page.tsx`）：
  - 语音区域嵌入关卡底部
  - AI 反馈弹出（覆盖在当前 step 上方）
- [ ] 错误处理：
  - WebSocket 断线重连（最多 3 次）
  - 音频格式不兼容时给出用户提示

**验收标准**：
- 开启语音 → 说话 → 2 秒内看到 AI 文字回应
- 断开 WebSocket → 后端无资源泄漏（日志确认 `queue.close()` 调用）
- 拒绝录音 → 降级文本模式，页面不崩溃

---

## Phase 6：云端部署 + Demo（1 天）

**目标**：项目运行在 Google Cloud，可提供 Demo 视频所需的稳定演示环境。

### 任务清单

- [ ] `src/backend/Dockerfile`：
  - 基于 `python:3.11-slim`
  - 安装 requirements.txt
  - 暴露端口 8000
  - 启动命令：`uvicorn main:app --host 0.0.0.0 --port 8000`
- [ ] `src/frontend/Dockerfile`：
  - 基于 `node:20-alpine`
  - 构建 Next.js 产物
  - 暴露端口 3000
- [ ] `cloudbuild.yaml` 或 `deploy.sh`：自动化部署到 Cloud Run
- [ ] Firestore 安全规则：
  - 匿名用户只能读写自己的数据
  - 禁止跨用户访问
- [ ] 环境变量配置（Cloud Run Secrets Manager）：
  - `GOOGLE_API_KEY` / `GOOGLE_APPLICATION_CREDENTIALS`
  - `VERTEX_AI_PROJECT_ID`、`VERTEX_AI_LOCATION`
- [ ] Demo 视频准备：
  - 流程：上传 PDF → 知识库构建 → 询问需求 → 生成大纲 → 进入关卡 → 开启语音 → 展示实时反馈 → XP 变化
  - 时长 ≤ 4 分钟
  - 字幕/解说说明多模态能力和 ADK 技术亮点
- [ ] README.md 更新：云端部署步骤、架构图最终版、GCP 截图

**验收标准**：
- `curl https://[cloud-run-url]/` 返回 `{"status": "ok"}`
- 前端可访问，全流程可演示
- Demo 视频 ≤ 4 分钟，覆盖评分维度（创新 40% + 技术 30% + 演示 30%）

---

## 风险与注意事项

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Vertex AI Vector Search 初始化耗时 | 延误 Phase 2 | 提前创建 Index，开发期可用 Faiss 本地替代（仅测试） |
| ADK 版本不稳定 | Phase 3/5 | 锁定版本，遇问题查 GitHub Issues |
| 关卡 JSON 格式不稳定 | Phase 3 | 强制 JSON Schema 校验，失败重试最多 2 次 |
| WebSocket 音频延迟 > 2 秒 | Phase 5 | 减小音频块大小（50ms），优先 TEXT 模态 |
| Cloud Run 冷启动慢 | Phase 6 | 设置最小实例数 = 1 |

---

## 完成后评审意见

_（每个 Phase 完成后在此记录）_

### Phase 0 完成（2026-03-03）

**后端**：FastAPI 脚手架 + 5 个占位路由 + Pydantic 模型 + 健康检查测试（1 passed）✅  
**前端**：Next.js 15 + Tailwind CSS v4 构建通过（6 个页面正常生成）✅  
- 升级路径：Next.js 14 → 15，Tailwind CSS v3 → v4  
- 动态路由页面已更新为 Next.js 15 异步 params 格式  
- `tailwind.config.ts` 已删除（v4 改用 CSS `@theme` 指令）  
- `globals.css` 改用 `@import "tailwindcss"` + `@theme` 定义考拉主题色  
**启动脚本**：`start.py` 可并行启动前后端 ✅

### Phase 1 完成（2026-03-03）

**后端 Auth**：`POST /auth/anonymous` 正常生成 UUID + 写入 Firestore ✅  
**Firestore 服务**：`FirestoreService` 封装完整（set/get/update/delete/query/delete_where）✅  
**课程 CRUD**：`POST/GET/DELETE /courses` 含级联删除（progress/feedback/xp_logs）✅  
**测试**：8 passed（test_health + test_phase1，使用 mock Firestore，不依赖真实网络）✅  
- 版本冲突修复：`fastapi==0.115.0` → `>=0.124.1`（与 google-adk==1.26.0 兼容）  
- 版本修复：`pydantic==2.9.2` → `==2.12.5`（Python 3.14 预编译 wheel 存在）  
- langchain 系列延迟安装（Phase 2 RAG 时再装，避免安装超时）

### Phase 2 完成（2026-03-03）

**RAG Service**：`split_text` + `parse_pdf` + `parse_url` + `format_citation` + `build_rag_context` + `RAGService`，完全不依赖 LangChain ✅  
**Endpoints**：`POST /rag/upload`（PDF/URL）+ `GET /rag/status/{course_id}` ✅  
**测试**：21 passed（test_health + test_phase1 + test_rag）✅  
- 根本决策：完全放弃 LangChain（不兼容 Python 3.14），改用原生 pypdf + httpx + html.parser  
- 测试 mock 修复：FastAPI `Depends` 必须用 `app.dependency_overrides`，不能用 `patch("module.func")`  
- 开发模式：RAG 跳过 Embedding/Vector Search，用关键词匹配替代；生产模式走 Vertex AI

### Phase 3 完成（2026-03-04）

**Agent Service**：6 Agent 流水线（outline_agent → lesson_planner → ParallelAgent(svg+quiz) → verifier → feedback_agent）✅  
**XP Service**：`record_answer()` 正确实现（答对+10 XP，3连击额外+10 XP，写入 xp_logs）✅  
**Lessons 路由**：`POST /lessons/generate`、`GET /lessons/{id}`、`POST /lessons/{id}/answer`、`POST /lessons/{id}/feedback` ✅  
**Courses 路由扩展**：`POST /courses/{id}/outline` 调用 Agent 生成大纲并回写 Firestore ✅  
**测试**：39 passed（test_health + test_phase1 + test_rag + test_phase3）✅  
- courses.py 重构为 `Depends(_get_db)` 模式，test_phase1.py 同步更新 mock 方式  
- delete_course 现在级联删除 5 个 collection（progress/feedback/xp_logs/rag_sources/lessons）  
**.env 更新**：统一切换到 `GOOGLE_GENAI_USE_VERTEXAI=TRUE` + `VERTEX_AI_PROJECT_ID=openlearner-488611`
