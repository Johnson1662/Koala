from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from services.firestore import FirestoreService
from services.rag_service import RAGService, get_rag_service

router = APIRouter()


class UploadResponse(BaseModel):
    course_id: str
    source_type: str
    source: str
    chunks: int
    status: str


class RAGStatusResponse(BaseModel):
    course_id: str
    sources: list[dict]
    total_chunks: int
    ready: bool


def _get_firestore() -> FirestoreService:
    return FirestoreService()


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_knowledge_source(
    course_id: Annotated[str, Form()],
    source_type: Annotated[str, Form()],
    url: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
    rag: RAGService = Depends(get_rag_service),
    db: FirestoreService = Depends(_get_firestore),
) -> UploadResponse:
    if source_type not in ("pdf", "url"):
        raise HTTPException(status_code=422, detail="source_type 必须是 pdf 或 url")

    if source_type == "pdf":
        if file is None:
            raise HTTPException(status_code=422, detail="PDF 上传需要提供 file 字段")
        content = await file.read()
        result = await rag.ingest_pdf(course_id, file.filename or "unknown.pdf", content)
    else:
        if not url:
            raise HTTPException(status_code=422, detail="URL 上传需要提供 url 字段")
        result = await rag.ingest_url(course_id, url)

    await db.set(
        "rag_sources",
        f"{course_id}_{result['source']}",
        {
            "course_id": course_id,
            "source_type": result["source_type"],
            "source": result["source"],
            "chunks": result["chunks"],
            "status": "ready",
        },
    )

    return UploadResponse(
        course_id=course_id,
        source_type=result["source_type"],
        source=result["source"],
        chunks=result["chunks"],
        status="ready",
    )


@router.get("/status/{course_id}", response_model=RAGStatusResponse)
async def get_rag_status(
    course_id: str,
    db: FirestoreService = Depends(_get_firestore),
) -> RAGStatusResponse:
    sources = await db.query("rag_sources", "course_id", course_id)
    total_chunks = sum(s.get("chunks", 0) for s in sources)
    return RAGStatusResponse(
        course_id=course_id,
        sources=sources,
        total_chunks=total_chunks,
        ready=total_chunks > 0,
    )
