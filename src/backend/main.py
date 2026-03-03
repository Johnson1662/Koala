"""
Koala Backend — FastAPI 入口
启动：uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, courses, lessons, rag, voice

app = FastAPI(
    title="Koala API",
    description="Koala AI 学习助手后端 — Gemini Live Agent Challenge",
    version="0.1.0",
)

# CORS：允许本地前端开发访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(lessons.router, prefix="/lessons", tags=["lessons"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])


@app.get("/", tags=["health"])
async def health_check() -> dict[str, str]:
    """健康检查端点"""
    return {"status": "ok", "service": "koala-backend"}
