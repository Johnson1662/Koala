from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from main import app

from routers.courses import _get_db as _courses_get_db

client = TestClient(app)
MOCK_USER_ID = "test-user-123"
MOCK_COURSE_ID = "test-course-456"


@pytest.fixture
def mock_auth_db():
    with patch("routers.auth._db") as db:
        db.set = AsyncMock()
        yield db


@pytest.fixture
def mock_courses_db():
    db = MagicMock()
    db.set = AsyncMock()
    db.get = AsyncMock(return_value=None)
    db.query = AsyncMock(return_value=[])
    db.delete = AsyncMock()
    db.delete_where = AsyncMock()
    app.dependency_overrides[_courses_get_db] = lambda: db
    yield db
    app.dependency_overrides.clear()


def test_anonymous_login(mock_auth_db):
    response = client.post("/auth/anonymous")
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert len(data["user_id"]) == 36
    mock_auth_db.set.assert_awaited_once()


def test_create_course(mock_courses_db):
    response = client.post(
        "/courses",
        json={"user_id": MOCK_USER_ID, "topic": "Python 基础"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["topic"] == "Python 基础"
    assert data["user_id"] == MOCK_USER_ID
    assert data["outline"] == []
    assert "course_id" in data
    mock_courses_db.set.assert_awaited_once()


def test_list_courses(mock_courses_db):
    mock_courses_db.query = AsyncMock(
        return_value=[
            {
                "course_id": MOCK_COURSE_ID,
                "user_id": MOCK_USER_ID,
                "topic": "Python 基础",
                "outline": [],
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    response = client.get(f"/courses?user_id={MOCK_USER_ID}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["topic"] == "Python 基础"


def test_get_course(mock_courses_db):
    mock_courses_db.get = AsyncMock(
        return_value={
            "course_id": MOCK_COURSE_ID,
            "user_id": MOCK_USER_ID,
            "topic": "Python 基础",
            "outline": [],
            "created_at": "2026-01-01T00:00:00+00:00",
        }
    )
    response = client.get(f"/courses/{MOCK_COURSE_ID}")
    assert response.status_code == 200
    assert response.json()["course_id"] == MOCK_COURSE_ID


def test_get_course_not_found(mock_courses_db):
    mock_courses_db.get = AsyncMock(return_value=None)
    response = client.get("/courses/nonexistent")
    assert response.status_code == 404


def test_delete_course(mock_courses_db):
    mock_courses_db.get = AsyncMock(
        return_value={
            "course_id": MOCK_COURSE_ID,
            "user_id": MOCK_USER_ID,
            "topic": "Python 基础",
            "outline": [],
            "created_at": "2026-01-01T00:00:00+00:00",
        }
    )
    response = client.delete(f"/courses/{MOCK_COURSE_ID}")
    assert response.status_code == 204
    mock_courses_db.delete.assert_awaited_once_with("courses", MOCK_COURSE_ID)
    assert mock_courses_db.delete_where.await_count == 5


def test_delete_course_not_found(mock_courses_db):
    mock_courses_db.get = AsyncMock(return_value=None)
    response = client.delete("/courses/nonexistent")
    assert response.status_code == 404
