from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app
from routers.rag import _get_firestore, get_rag_service
from services.rag_service import (
    build_rag_context,
    format_citation,
    parse_pdf,
    split_text,
)

MOCK_COURSE_ID = "course-rag-test"

MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>>>>>endobj\n"
    b"4 0 obj<</Length 44>>\nstream\nBT /F1 12 Tf 100 700 Td (Koala test) Tj ET\nendstream\nendobj\n"
    b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000311 00000 n \n"
    b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n406\n%%EOF"
)


@pytest.fixture
def mock_db():
    """返回一个 mock FirestoreService 实例。"""
    db = MagicMock()
    db.set = AsyncMock()
    db.query = AsyncMock(return_value=[])
    return db


@pytest.fixture
def mock_rag():
    """返回一个 mock RAGService 实例。"""
    rag = MagicMock()
    rag.ingest_pdf = AsyncMock()
    rag.ingest_url = AsyncMock()
    return rag


@pytest.fixture
def client_with_overrides(mock_db, mock_rag):
    """提供带有 dependency_overrides 的 TestClient，测试结束后清理。"""
    app.dependency_overrides[_get_firestore] = lambda: mock_db
    app.dependency_overrides[get_rag_service] = lambda: mock_rag
    with TestClient(app) as c:
        yield c, mock_db, mock_rag
    app.dependency_overrides.clear()


@pytest.fixture
def client_db_only(mock_db):
    """仅 override _get_firestore 的 TestClient（用于 status 端点）。"""
    app.dependency_overrides[_get_firestore] = lambda: mock_db
    with TestClient(app) as c:
        yield c, mock_db
    app.dependency_overrides.clear()


# ────────────────────────────────
# 纯函数单元测试
# ────────────────────────────────

def test_split_text_short():
    result = split_text("Hello world", chunk_size=400)
    assert result == ["Hello world"]


def test_split_text_splits_on_newline():
    text = "段落一内容。\n\n段落二内容。\n\n段落三内容。"
    result = split_text(text, chunk_size=10, overlap=0)
    assert len(result) >= 3
    for chunk in result:
        assert len(chunk) <= 15


def test_split_text_empty():
    assert split_text("") == []
    assert split_text("   ") == []


def test_format_citation_pdf():
    chunk = {"source_type": "pdf", "page_num": 3}
    citation = format_citation(chunk)
    assert "来源：用户PDF" in citation
    assert "第3页" in citation


def test_format_citation_url():
    chunk = {"source_type": "url", "url": "https://example.com", "paragraph_num": 5}
    citation = format_citation(chunk)
    assert "来源：https://example.com" in citation
    assert "段落5" in citation


def test_format_citation_unknown():
    citation = format_citation({"source_type": "other"})
    assert "来源：未知" in citation


def test_build_rag_context():
    chunks = [
        {"text": "Python 是编程语言", "source_type": "pdf", "page_num": 1},
        {"text": "变量赋值用等号", "source_type": "url", "url": "https://docs.python.org", "paragraph_num": 2},
    ]
    context = build_rag_context(chunks)
    assert "Python 是编程语言" in context
    assert "来源：用户PDF，第1页" in context
    assert "变量赋值用等号" in context
    assert "来源：https://docs.python.org，段落2" in context


def test_parse_pdf_minimal():
    chunks = parse_pdf(MINIMAL_PDF)
    assert isinstance(chunks, list)
    for c in chunks:
        assert c["source_type"] == "pdf"
        assert "page_num" in c
        assert "text" in c


# ────────────────────────────────
# Endpoint 集成测试
# ────────────────────────────────

def test_upload_pdf_endpoint(client_with_overrides):
    client, mock_db, mock_rag = client_with_overrides
    mock_rag.ingest_pdf.return_value = {
        "course_id": MOCK_COURSE_ID,
        "chunks": 5,
        "source": "test.pdf",
        "source_type": "pdf",
    }

    fake_pdf = b"%PDF-1.4 fake content"
    response = client.post(
        "/rag/upload",
        data={"course_id": MOCK_COURSE_ID, "source_type": "pdf"},
        files={"file": ("test.pdf", fake_pdf, "application/pdf")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["course_id"] == MOCK_COURSE_ID
    assert data["chunks"] == 5
    assert data["source_type"] == "pdf"
    assert data["status"] == "ready"
    mock_rag.ingest_pdf.assert_awaited_once()
    mock_db.set.assert_awaited_once()


def test_upload_url_endpoint(client_with_overrides):
    client, mock_db, mock_rag = client_with_overrides
    mock_rag.ingest_url.return_value = {
        "course_id": MOCK_COURSE_ID,
        "chunks": 8,
        "source": "https://example.com",
        "source_type": "url",
    }

    response = client.post(
        "/rag/upload",
        data={
            "course_id": MOCK_COURSE_ID,
            "source_type": "url",
            "url": "https://example.com",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["source_type"] == "url"
    assert data["chunks"] == 8
    mock_rag.ingest_url.assert_awaited_once()
    mock_db.set.assert_awaited_once()


def test_upload_invalid_source_type(client_with_overrides):
    client, _, _ = client_with_overrides
    response = client.post(
        "/rag/upload",
        data={"course_id": MOCK_COURSE_ID, "source_type": "invalid"},
    )
    assert response.status_code == 422


def test_rag_status_empty(client_db_only):
    client, mock_db = client_db_only
    mock_db.query = AsyncMock(return_value=[])
    response = client.get(f"/rag/status/{MOCK_COURSE_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is False
    assert data["total_chunks"] == 0


def test_rag_status_with_sources(client_db_only):
    client, mock_db = client_db_only
    mock_db.query = AsyncMock(return_value=[
        {"course_id": MOCK_COURSE_ID, "source": "doc.pdf", "chunks": 12, "source_type": "pdf"},
        {"course_id": MOCK_COURSE_ID, "source": "https://example.com", "chunks": 7, "source_type": "url"},
    ])
    response = client.get(f"/rag/status/{MOCK_COURSE_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert data["total_chunks"] == 19
    assert len(data["sources"]) == 2
