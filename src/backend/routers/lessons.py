import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.firestore import FirestoreService
from services.agent_service import generate_lesson as _generate_lesson, process_feedback as _process_feedback
from services.xp_service import record_answer

router = APIRouter()


def _get_db() -> FirestoreService:
    return FirestoreService()


class GenerateLessonRequest(BaseModel):
    course_id: str
    lesson_id: str
    lesson_title: str
    lesson_summary: str
    lesson_adjustment: str = ""


class LessonResponse(BaseModel):
    lesson_id: str
    course_id: str
    title: str
    steps: list[dict]
    created_at: str


class SubmitAnswerRequest(BaseModel):
    user_id: str
    course_id: str
    step_id: int
    answer: str
    correct_answer: str
    current_streak: int = 0


class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    xp_earned: int
    streak: int
    explanation: str = ""


class SubmitFeedbackRequest(BaseModel):
    user_id: str
    course_id: str
    lesson_id: str
    user_feedback: str
    user_needs: str


class SubmitFeedbackResponse(BaseModel):
    updated_outline: dict
    lesson_adjustment: str


@router.post("/generate", response_model=LessonResponse, status_code=201)
async def generate_lesson(
    body: GenerateLessonRequest,
    db: FirestoreService = Depends(_get_db),
) -> LessonResponse:
    steps = await _generate_lesson(
        course_id=body.course_id,
        lesson_id=body.lesson_id,
        lesson_title=body.lesson_title,
        lesson_summary=body.lesson_summary,
        lesson_adjustment=body.lesson_adjustment,
    )

    if not steps:
        raise HTTPException(status_code=500, detail="关卡内容生成失败，请重试")

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "lesson_id": body.lesson_id,
        "course_id": body.course_id,
        "title": body.lesson_title,
        "steps": steps,
        "created_at": now,
    }
    await db.set("lessons", body.lesson_id, doc)

    return LessonResponse(**doc)


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: str,
    db: FirestoreService = Depends(_get_db),
) -> LessonResponse:
    doc = await db.get("lessons", lesson_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return LessonResponse(**doc)


@router.post("/{lesson_id}/answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    lesson_id: str,
    body: SubmitAnswerRequest,
    db: FirestoreService = Depends(_get_db),
) -> SubmitAnswerResponse:
    is_correct = body.answer.strip().lower() == body.correct_answer.strip().lower()

    xp_result = await record_answer(
        db=db,
        user_id=body.user_id,
        course_id=body.course_id,
        lesson_id=lesson_id,
        is_correct=is_correct,
        current_streak=body.current_streak,
    )

    await db.set(
        "progress",
        f"{body.user_id}_{lesson_id}_{body.step_id}",
        {
            "user_id": body.user_id,
            "course_id": body.course_id,
            "lesson_id": lesson_id,
            "step_id": body.step_id,
            "is_correct": is_correct,
            "answered_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return SubmitAnswerResponse(
        is_correct=is_correct,
        xp_earned=xp_result["xp_earned"],
        streak=xp_result["streak"],
    )


@router.post("/{lesson_id}/feedback", response_model=SubmitFeedbackResponse)
async def submit_feedback(
    lesson_id: str,
    body: SubmitFeedbackRequest,
    db: FirestoreService = Depends(_get_db),
) -> SubmitFeedbackResponse:
    course_doc = await db.get("courses", body.course_id)
    if not course_doc:
        raise HTTPException(status_code=404, detail="Course not found")

    current_outline = course_doc.get("outline", {})

    await db.set(
        "feedback",
        f"{body.user_id}_{lesson_id}_{uuid.uuid4().hex[:8]}",
        {
            "user_id": body.user_id,
            "course_id": body.course_id,
            "lesson_id": lesson_id,
            "feedback": body.user_feedback,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    result = await _process_feedback(
        course_id=body.course_id,
        current_outline=current_outline,
        completed_lesson_id=lesson_id,
        user_feedback=body.user_feedback,
        user_needs=body.user_needs,
    )

    updated_outline = result.get("updated_outline", current_outline)
    lesson_adjustment = result.get("lesson_adjustment", "")

    await db.update("courses", body.course_id, {"outline": updated_outline})

    return SubmitFeedbackResponse(
        updated_outline=updated_outline,
        lesson_adjustment=lesson_adjustment,
    )
