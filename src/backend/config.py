"""
Koala Backend — 集中配置
所有环境变量从此处读取，其他模块 import config 即可。
"""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── Google AI / ADK ──────────────────────────────────────────────────────
    # 开发：GOOGLE_GENAI_USE_VERTEXAI=FALSE + GOOGLE_API_KEY
    # 生产：GOOGLE_GENAI_USE_VERTEXAI=TRUE  + GCP 凭证
    use_vertex_ai: bool = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")

    # ── Vertex AI（生产）────────────────────────────────────────────────────
    vertex_project_id: str = os.getenv("VERTEX_AI_PROJECT_ID", "")
    vertex_location: str = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    google_application_credentials: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    # ── ADK Agent ────────────────────────────────────────────────────────────
    adk_model: str = "gemini-2.0-flash-live-001"
    adk_app_name: str = "koala"

    # ── Vector Search ────────────────────────────────────────────────────────
    vector_search_index_id: str = os.getenv("VECTOR_SEARCH_INDEX_ID", "")
    vector_search_endpoint_id: str = os.getenv("VECTOR_SEARCH_ENDPOINT_ID", "")
    embedding_model: str = "textembedding-gecko@003"
    rag_top_k: int = 5  # 固定 top-5，禁止调高

    # ── Firebase / Firestore ──────────────────────────────────────────────────
    firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
