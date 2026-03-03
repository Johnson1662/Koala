"""
RAG 知识库服务

完全不依赖 LangChain（Python 3.14 兼容性问题），使用：
- pypdf        → PDF 解析
- httpx        → 网页抓取
- html.parser  → 网页文本提取（标准库）
- google-cloud-aiplatform → Vertex AI Embedding + Vector Search
"""

import hashlib
import re
from html.parser import HTMLParser
from io import BytesIO
from typing import Any

import httpx
from pypdf import PdfReader

from config import settings


# ── 文本切分（替代 LangChain RecursiveCharacterTextSplitter）─────────────────

def split_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """
    按段落/句子递归切分文本，尽量在自然边界切分。
    chunk_size: 每块最大字符数
    overlap: 相邻块重叠字符数（上下文连续性）
    """
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    # 分隔符优先级：段落 > 句子 > 逗号 > 空格
    separators = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", "，", ",", " "]
    chunks: list[str] = []

    def _split(t: str, seps: list[str]) -> None:
        if len(t) <= chunk_size:
            if t.strip():
                chunks.append(t.strip())
            return
        if not seps:
            # 强制切分
            for i in range(0, len(t), chunk_size - overlap):
                part = t[i : i + chunk_size]
                if part.strip():
                    chunks.append(part.strip())
            return

        sep = seps[0]
        parts = t.split(sep)
        current = ""
        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current.strip():
                    _split(current.strip(), seps[1:])
                current = part
        if current.strip():
            _split(current.strip(), seps[1:])

    _split(text, separators)

    # 添加 overlap：每块末尾与下一块开头重叠
    if overlap > 0 and len(chunks) > 1:
        overlapped: list[str] = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = chunks[i - 1][-overlap:]
            overlapped.append(tail + chunks[i])
        return overlapped

    return chunks


# ── PDF 解析 ─────────────────────────────────────────────────────────────────

def parse_pdf(content: bytes) -> list[dict[str, Any]]:
    """
    解析 PDF 文件，返回每页的文本块列表。
    每块：{ text, page_num, source_type: "pdf" }
    """
    reader = PdfReader(BytesIO(content))
    pages_chunks: list[dict[str, Any]] = []

    for page_num, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        raw_text = raw_text.strip()
        if not raw_text:
            continue
        chunks = split_text(raw_text)
        for chunk in chunks:
            pages_chunks.append({
                "text": chunk,
                "page_num": page_num,
                "source_type": "pdf",
            })

    return pages_chunks


# ── 网页解析 ─────────────────────────────────────────────────────────────────

class _TextExtractor(HTMLParser):
    """从 HTML 中提取纯文本，跳过 script/style 标签。"""

    _SKIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript"}

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth: int = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag.lower() in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self._parts.append(stripped)

    def get_text(self) -> str:
        return "\n".join(self._parts)


async def parse_url(url: str) -> list[dict[str, Any]]:
    """
    抓取网页并提取纯文本，返回文本块列表。
    每块：{ text, paragraph_num, source_type: "url", url }
    """
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "KoalaBot/1.0"})
        resp.raise_for_status()

    extractor = _TextExtractor()
    extractor.feed(resp.text)
    full_text = extractor.get_text()

    # 按段落切分（自然段落边界）
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", full_text) if p.strip()]
    chunks: list[dict[str, Any]] = []
    para_num = 0

    for paragraph in paragraphs:
        sub_chunks = split_text(paragraph)
        for chunk in sub_chunks:
            para_num += 1
            chunks.append({
                "text": chunk,
                "paragraph_num": para_num,
                "source_type": "url",
                "url": url,
            })

    return chunks


# ── Embedding（Vertex AI）────────────────────────────────────────────────────

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    调用 Vertex AI Text Embedding API，返回向量列表。
    批量处理（每批最多 5 条，API 限制）。
    """
    from google.cloud import aiplatform
    from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

    aiplatform.init(
        project=settings.vertex_project_id,
        location=settings.vertex_location,
    )
    model = TextEmbeddingModel.from_pretrained(settings.embedding_model)

    all_embeddings: list[list[float]] = []
    batch_size = 5

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        inputs = [TextEmbeddingInput(text=t) for t in batch]
        results = model.get_embeddings(inputs)
        all_embeddings.extend([r.values for r in results])

    return all_embeddings


# ── Vector Search（Vertex AI）────────────────────────────────────────────────

def upsert_to_vector_search(
    course_id: str,
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
) -> None:
    """
    将 chunk 向量写入 Vertex AI Vector Search Index。
    datapoint_id 格式：{course_id}_{chunk_hash}
    """
    from google.cloud import aiplatform

    aiplatform.init(
        project=settings.vertex_project_id,
        location=settings.vertex_location,
    )
    index = aiplatform.MatchingEngineIndex(
        index_name=settings.vector_search_index_id
    )

    datapoints = []
    for chunk, embedding in zip(chunks, embeddings):
        chunk_hash = hashlib.md5(chunk["text"].encode()).hexdigest()[:8]
        dp_id = f"{course_id}_{chunk_hash}"
        datapoints.append(
            aiplatform.gapic.IndexDatapoint(
                datapoint_id=dp_id,
                feature_vector=embedding,
                restricts=[
                    aiplatform.gapic.IndexDatapoint.Restriction(
                        namespace="course_id",
                        allow_list=[course_id],
                    )
                ],
            )
        )

    index.upsert_datapoints(datapoints=datapoints)


def search_vector(
    query_embedding: list[float],
    course_id: str,
    top_k: int = 5,
) -> list[str]:
    """
    在 Vector Search 中检索最相关的 datapoint_ids（top-5 固定）。
    """
    from google.cloud import aiplatform

    aiplatform.init(
        project=settings.vertex_project_id,
        location=settings.vertex_location,
    )
    endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=settings.vector_search_endpoint_id
    )
    response = endpoint.find_neighbors(
        deployed_index_id=settings.vector_search_index_id,
        queries=[query_embedding],
        num_neighbors=top_k,
        filter=[
            aiplatform.matching_engine.matching_engine_index_endpoint.Namespace(
                name="course_id", allow_tokens=[course_id]
            )
        ],
    )
    return [neighbor.id for neighbor in response[0]]


# ── 引用格式化 ────────────────────────────────────────────────────────────────

def format_citation(chunk: dict[str, Any]) -> str:
    """
    生成标准来源引用字符串。
    PDF：（来源：用户PDF，第N页）
    URL：（来源：网页URL，段落N）
    """
    if chunk.get("source_type") == "pdf":
        return f"（来源：用户PDF，第{chunk.get('page_num', '?')}页）"
    elif chunk.get("source_type") == "url":
        url = chunk.get("url", "未知网址")
        para = chunk.get("paragraph_num", "?")
        return f"（来源：{url}，段落{para}）"
    return "（来源：未知）"


def build_rag_context(chunks: list[dict[str, Any]]) -> str:
    """
    将检索到的 chunks 拼接成带引用的 context 字符串，供 Agent 使用。
    """
    parts: list[str] = []
    for chunk in chunks:
        citation = format_citation(chunk)
        parts.append(f"{chunk['text']} {citation}")
    return "\n\n".join(parts)


# ── 主入口：处理上传 ──────────────────────────────────────────────────────────

class RAGService:
    """
    RAG 知识库服务。
    开发模式（use_vertex_ai=False）：仅解析文本，跳过 Embedding/Vector Search。
    生产模式（use_vertex_ai=True）：全流程 Vertex AI。
    """

    async def ingest_pdf(
        self, course_id: str, filename: str, content: bytes
    ) -> dict[str, Any]:
        """处理 PDF 上传，返回摘要信息。"""
        chunks = parse_pdf(content)
        if not chunks:
            return {"course_id": course_id, "chunks": 0, "source": filename}

        if settings.use_vertex_ai:
            texts = [c["text"] for c in chunks]
            embeddings = get_embeddings(texts)
            upsert_to_vector_search(course_id, chunks, embeddings)

        return {
            "course_id": course_id,
            "chunks": len(chunks),
            "source": filename,
            "source_type": "pdf",
        }

    async def ingest_url(self, course_id: str, url: str) -> dict[str, Any]:
        """处理网页 URL，返回摘要信息。"""
        chunks = await parse_url(url)
        if not chunks:
            return {"course_id": course_id, "chunks": 0, "source": url}

        if settings.use_vertex_ai:
            texts = [c["text"] for c in chunks]
            embeddings = get_embeddings(texts)
            upsert_to_vector_search(course_id, chunks, embeddings)

        return {
            "course_id": course_id,
            "chunks": len(chunks),
            "source": url,
            "source_type": "url",
        }

    async def search(self, query: str, course_id: str, chunks_store: list[dict] | None = None) -> str:
        """
        检索并返回带引用的 context 字符串。
        开发模式：直接从 chunks_store（内存）中做关键词匹配。
        生产模式：Vertex AI Vector Search top-5。
        """
        if not settings.use_vertex_ai:
            # 开发模式：简单关键词匹配（不依赖 Vertex AI）
            if not chunks_store:
                return "（知识库中未找到相关内容）"
            query_lower = query.lower()
            matched = [
                c for c in chunks_store
                if any(word in c["text"].lower() for word in query_lower.split())
            ]
            top = matched[: settings.rag_top_k]
            if not top:
                return "（知识库中未找到相关内容）"
            return build_rag_context(top)

        # 生产模式：Vertex AI Embedding + Vector Search
        query_emb = get_embeddings([query])[0]
        dp_ids = search_vector(query_emb, course_id, top_k=settings.rag_top_k)
        if not dp_ids:
            return "（知识库中未找到相关内容）"

        # dp_id 格式 {course_id}_{chunk_hash}，需要从 Firestore 取回原始 chunk
        # （生产阶段：写入时同步写 Firestore rag_chunks collection）
        return f"（检索到 {len(dp_ids)} 个相关片段，来源已标注）"


def get_rag_service() -> RAGService:
    return RAGService()
