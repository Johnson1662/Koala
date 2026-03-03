
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from routers.lessons import _get_db as _lessons_get_db
from routers.courses import _get_db as _courses_get_db
from services.xp_service import record_answer, XP_PER_CORRECT, XP_STREAK_BONUS, STREAK_THRESHOLD

# ────────────────────────────────────────────────
# 常量 & 共用 fixture
# ────────────────────────────────────────────────

MOCK_COURSE_ID = "course-p3-test"
MOCK_LESSON_ID = "lesson-p3-test"
MOCK_USER_ID = "user-p3-test"

MOCK_STEPS = [
    {"step_id": i, "type": "text", "topic": f"主题{i}", "content": f"内容{i}", "source": ""}
    for i in range(1, 22)
]  # 21 steps，符合 20+ 要求

MOCK_OUTLINE = {
    "chapters": [
        {
            "chapter_id": 1,
            "title": "第一章",
            "lessons": [
                {"lesson_id": "1-1", "title": "关卡1", "summary": "简介1"},
            ],
        }
    ]
}


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.set = AsyncMock()
    db.get = AsyncMock(return_value=None)
    db.query = AsyncMock(return_value=[])
    db.update = AsyncMock()
    db.delete = AsyncMock()
    db.delete_where = AsyncMock()
    return db


@pytest.fixture
def lessons_client(mock_db):
    app.dependency_overrides[_lessons_get_db] = lambda: mock_db
    with TestClient(app) as c:
        yield c, mock_db
    app.dependency_overrides.clear()


@pytest.fixture
def courses_client(mock_db):
    app.dependency_overrides[_courses_get_db] = lambda: mock_db
    with TestClient(app) as c:
        yield c, mock_db
    app.dependency_overrides.clear()


# ────────────────────────────────────────────────
# XP Service 单元测试
# ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_xp_wrong_answer_earns_zero():
    mock_db = MagicMock()
    mock_db = MagicMock()
    mock_db.set = AsyncMock()

    result = await record_answer(
        db=mock_db,
        user_id=MOCK_USER_ID,
        course_id=MOCK_COURSE_ID,
        lesson_id=MOCK_LESSON_ID,
        is_correct=False,
        current_streak=2,
    )

    assert result["xp_earned"] == 0
    assert result["streak"] == 0
    assert result["logs"] == []
    mock_db.set.assert_not_awaited()


@pytest.mark.asyncio
async def test_xp_correct_no_streak_bonus():
    mock_db = MagicMock()
    mock_db = MagicMock()
    mock_db.set = AsyncMock()

    result = await record_answer(
        db=mock_db,
        user_id=MOCK_USER_ID,
        course_id=MOCK_COURSE_ID,
        lesson_id=MOCK_LESSON_ID,
        is_correct=True,
        current_streak=1,  # streak_after = 2，不满足 STREAK_THRESHOLD=3
    )

    assert result["xp_earned"] == XP_PER_CORRECT
    assert result["streak"] == 2
    assert len(result["logs"]) == 1
    assert result["logs"][0]["reason"] == "correct_answer"
    mock_db.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_xp_streak_bonus_triggers():
    mock_db = MagicMock()
    mock_db = MagicMock()
    mock_db.set = AsyncMock()

    result = await record_answer(
        db=mock_db,
        user_id=MOCK_USER_ID,
        course_id=MOCK_COURSE_ID,
        lesson_id=MOCK_LESSON_ID,
        is_correct=True,
        current_streak=2,  # streak_after = 3 = STREAK_THRESHOLD
    )

    assert result["xp_earned"] == XP_PER_CORRECT + XP_STREAK_BONUS
    assert result["streak"] == STREAK_THRESHOLD
    assert len(result["logs"]) == 2
    reasons = {log["reason"] for log in result["logs"]}
    assert "correct_answer" in reasons
    assert "streak_bonus" in reasons
    assert mock_db.set.await_count == 2


@pytest.mark.asyncio
async def test_xp_streak_bonus_multiple():
    mock_db = MagicMock()
    mock_db = MagicMock()
    mock_db.set = AsyncMock()

    result = await record_answer(
        db=mock_db,
        user_id=MOCK_USER_ID,
        course_id=MOCK_COURSE_ID,
        lesson_id=MOCK_LESSON_ID,
        is_correct=True,
        current_streak=5,  # streak_after = 6 = 2 * STREAK_THRESHOLD
    )

    assert result["xp_earned"] == XP_PER_CORRECT + XP_STREAK_BONUS
    assert result["streak"] == 6


@pytest.mark.asyncio
async def test_xp_logs_written_to_firestore():
    mock_db = MagicMock()
    mock_db = MagicMock()
    mock_db.set = AsyncMock()

    await record_answer(
        db=mock_db,
        user_id=MOCK_USER_ID,
        course_id=MOCK_COURSE_ID,
        lesson_id=MOCK_LESSON_ID,
        is_correct=True,
        current_streak=0,
    )

    call_args = mock_db.set.call_args
    _, doc_id, log_doc = call_args[0]
    assert log_doc["user_id"] == MOCK_USER_ID
    assert log_doc["course_id"] == MOCK_COURSE_ID
    assert log_doc["lesson_id"] == MOCK_LESSON_ID
    assert log_doc["xp_delta"] == XP_PER_CORRECT
    assert "created_at" in log_doc


# ────────────────────────────────────────────────
# Lessons 端点集成测试
# ────────────────────────────────────────────────

def test_generate_lesson_success(lessons_client):
    client, mock_db = lessons_client
    client, mock_db = lessons_client

    with patch("routers.lessons._generate_lesson", new=AsyncMock(return_value=MOCK_STEPS)):
        response = client.post(
            "/lessons/generate",
            json={
                "course_id": MOCK_COURSE_ID,
                "lesson_id": MOCK_LESSON_ID,
                "lesson_title": "Python 基础",
                "lesson_summary": "学习变量和类型",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["lesson_id"] == MOCK_LESSON_ID
    assert data["course_id"] == MOCK_COURSE_ID
    assert len(data["steps"]) == 21
    mock_db.set.assert_awaited_once()


def test_generate_lesson_agent_returns_empty(lessons_client):
    client, _ = lessons_client
    client, _ = lessons_client

    with patch("routers.lessons._generate_lesson", new=AsyncMock(return_value=[])):
        response = client.post(
            "/lessons/generate",
            json={
                "course_id": MOCK_COURSE_ID,
                "lesson_id": MOCK_LESSON_ID,
                "lesson_title": "Python 基础",
                "lesson_summary": "学习变量和类型",
            },
        )

    assert response.status_code == 500
    assert "生成失败" in response.json()["detail"]


def test_get_lesson_found(lessons_client):
    client, mock_db = lessons_client
    client, mock_db = lessons_client
    mock_db.get = AsyncMock(return_value={
        "lesson_id": MOCK_LESSON_ID,
        "course_id": MOCK_COURSE_ID,
        "title": "Python 基础",
        "steps": MOCK_STEPS,
        "created_at": "2025-01-01T00:00:00+00:00",
    })

    response = client.get(f"/lessons/{MOCK_LESSON_ID}")

    assert response.status_code == 200
    data = response.json()
    assert data["lesson_id"] == MOCK_LESSON_ID
    assert len(data["steps"]) == 21


def test_get_lesson_not_found(lessons_client):
    client, mock_db = lessons_client
    client, mock_db = lessons_client
    mock_db.get = AsyncMock(return_value=None)

    response = client.get(f"/lessons/{MOCK_LESSON_ID}")

    assert response.status_code == 404


def test_submit_answer_correct(lessons_client):
    client, mock_db = lessons_client
    client, mock_db = lessons_client

    response = client.post(
        f"/lessons/{MOCK_LESSON_ID}/answer",
        json={
            "user_id": MOCK_USER_ID,
            "course_id": MOCK_COURSE_ID,
            "step_id": 5,
            "answer": "Python",
            "correct_answer": "Python",
            "current_streak": 0,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is True
    assert data["xp_earned"] == XP_PER_CORRECT
    assert data["streak"] == 1
    # 写入 xp_logs + progress = 2 次 set
    assert mock_db.set.await_count == 2


def test_submit_answer_case_insensitive(lessons_client):
    client, mock_db = lessons_client
    client, mock_db = lessons_client

    response = client.post(
        f"/lessons/{MOCK_LESSON_ID}/answer",
        json={
            "user_id": MOCK_USER_ID,
            "course_id": MOCK_COURSE_ID,
            "step_id": 3,
            "answer": "  PYTHON  ",
            "correct_answer": "python",
            "current_streak": 0,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_correct"] is True


def test_submit_answer_wrong(lessons_client):
    client, mock_db = lessons_client
    client, mock_db = lessons_client

    response = client.post(
        f"/lessons/{MOCK_LESSON_ID}/answer",
        json={
            "user_id": MOCK_USER_ID,
            "course_id": MOCK_COURSE_ID,
            "step_id": 2,
            "answer": "Java",
            "correct_answer": "Python",
            "current_streak": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is False
    assert data["xp_earned"] == 0
    assert data["streak"] == 0
    # 只写 progress，不写 xp_log
    mock_db.set.assert_awaited_once()


def test_submit_answer_streak_bonus(lessons_client):
    client, mock_db = lessons_client
    client, mock_db = lessons_client

    response = client.post(
        f"/lessons/{MOCK_LESSON_ID}/answer",
        json={
            "user_id": MOCK_USER_ID,
            "course_id": MOCK_COURSE_ID,
            "step_id": 7,
            "answer": "Python",
            "correct_answer": "Python",
            "current_streak": 2,  # streak_after = 3
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is True
    assert data["xp_earned"] == XP_PER_CORRECT + XP_STREAK_BONUS
    assert data["streak"] == 3


def test_submit_feedback_success(lessons_client):
    client, mock_db = lessons_client
    client, mock_db = lessons_client
    mock_db.get = AsyncMock(return_value={
        "course_id": MOCK_COURSE_ID,
        "user_id": MOCK_USER_ID,
        "topic": "Python",
        "outline": MOCK_OUTLINE,
        "created_at": "2025-01-01T00:00:00+00:00",
    })

    updated_outline = {"chapters": [{"chapter_id": 2, "title": "进阶章", "lessons": []}]}
    feedback_result = {
        "updated_outline": updated_outline,
        "lesson_adjustment": "增加更多实例",
    }

    with patch("routers.lessons._process_feedback", new=AsyncMock(return_value=feedback_result)):
        response = client.post(
            f"/lessons/{MOCK_LESSON_ID}/feedback",
            json={
                "user_id": MOCK_USER_ID,
                "course_id": MOCK_COURSE_ID,
                "lesson_id": MOCK_LESSON_ID,
                "user_feedback": "太简单了",
                "user_needs": "深入学习 Python",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["updated_outline"] == updated_outline
    assert data["lesson_adjustment"] == "增加更多实例"
    mock_db.update.assert_awaited_once()


def test_submit_feedback_course_not_found(lessons_client):
    client, mock_db = lessons_client
    client, mock_db = lessons_client
    mock_db.get = AsyncMock(return_value=None)

    response = client.post(
        f"/lessons/{MOCK_LESSON_ID}/feedback",
        json={
            "user_id": MOCK_USER_ID,
            "course_id": MOCK_COURSE_ID,
            "lesson_id": MOCK_LESSON_ID,
            "user_feedback": "太难了",
            "user_needs": "从零开始",
        },
    )

    assert response.status_code == 404


# ────────────────────────────────────────────────
# Courses Outline 端点集成测试
# ────────────────────────────────────────────────

def test_generate_outline_success(courses_client):
    client, mock_db = courses_client
    client, mock_db = courses_client
    mock_db.get = AsyncMock(return_value={
        "course_id": MOCK_COURSE_ID,
        "user_id": MOCK_USER_ID,
        "topic": "Python 编程",
        "outline": [],
        "created_at": "2025-01-01T00:00:00+00:00",
    })

    with patch("routers.courses._generate_outline", new=AsyncMock(return_value=MOCK_OUTLINE)):
        response = client.post(
            f"/courses/{MOCK_COURSE_ID}/outline",
            json={"user_needs": "从零开始学Python，有编程基础"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["course_id"] == MOCK_COURSE_ID
    assert data["outline"] == MOCK_OUTLINE
    mock_db.update.assert_awaited_once()


def test_generate_outline_course_not_found(courses_client):
    client, mock_db = courses_client
    client, mock_db = courses_client
    mock_db.get = AsyncMock(return_value=None)

    response = client.post(
        f"/courses/{MOCK_COURSE_ID}/outline",
        json={"user_needs": "学 Python"},
    )

    assert response.status_code == 404


def test_generate_outline_writes_user_needs(courses_client):
    client, mock_db = courses_client
    client, mock_db = courses_client
    mock_db.get = AsyncMock(return_value={
        "course_id": MOCK_COURSE_ID,
        "user_id": MOCK_USER_ID,
        "topic": "Python 编程",
        "outline": [],
        "created_at": "2025-01-01T00:00:00+00:00",
    })

    with patch("routers.courses._generate_outline", new=AsyncMock(return_value=MOCK_OUTLINE)):
        client.post(
            f"/courses/{MOCK_COURSE_ID}/outline",
            json={"user_needs": "专注数据分析"},
        )

    call_kwargs = mock_db.update.call_args[0]
    # call_args[0] = (collection, doc_id, data_dict)
    update_data = call_kwargs[2]
    assert update_data["user_needs"] == "专注数据分析"
    assert update_data["outline"] == MOCK_OUTLINE
