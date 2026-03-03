import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.firestore import FirestoreService
from services.agent_service import generate_outline as _generate_outline

router = APIRouter()


def _get_db() -> FirestoreService:
    return FirestoreService()


class CreateCourseRequest(BaseModel):
    user_id: str
    topic: str


class CourseResponse(BaseModel):
    course_id: str
    user_id: str
    topic: str
    outline: list[dict]
    created_at: str


class GenerateOutlineRequest(BaseModel):
    user_needs: str


class GenerateOutlineResponse(BaseModel):
    course_id: str
    outline: dict
    lesson_adjustment: str = ""


@router.post("", response_model=CourseResponse, status_code=201)
async def create_course(
    body: CreateCourseRequest,
    db: FirestoreService = Depends(_get_db),
) -> CourseResponse:
    course_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "course_id": course_id,
        "user_id": body.user_id,
        "topic": body.topic,
        "outline": [],
        "created_at": now,
    }
    await db.set("courses", course_id, doc)
    return CourseResponse(**doc)


@router.get("", response_model=list[CourseResponse])
async def list_courses(
    user_id: str,
    db: FirestoreService = Depends(_get_db),
) -> list[CourseResponse]:
    docs = await db.query("courses", "user_id", user_id)
    return [CourseResponse(**d) for d in docs]


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    db: FirestoreService = Depends(_get_db),
) -> CourseResponse:
    doc = await db.get("courses", course_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseResponse(**doc)


@router.delete("/{course_id}", status_code=204)
async def delete_course(
    course_id: str,
    db: FirestoreService = Depends(_get_db),
) -> None:
    doc = await db.get("courses", course_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Course not found")
    await db.delete("courses", course_id)
    for collection in ("progress", "feedback", "xp_logs", "rag_sources", "lessons"):
        await db.delete_where(collection, "course_id", course_id)


@router.post("/{course_id}/outline", response_model=GenerateOutlineResponse)
async def generate_course_outline(
    course_id: str,
    body: GenerateOutlineRequest,
    db: FirestoreService = Depends(_get_db),
) -> GenerateOutlineResponse:
    doc = await db.get("courses", course_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Course not found")

    outline = await _generate_outline(
        course_id=course_id,
        topic=doc["topic"],
        user_needs=body.user_needs,
    )

    await db.update("courses", course_id, {
        "outline": outline,
        "user_needs": body.user_needs,
    })

    return GenerateOutlineResponse(
        course_id=course_id,
        outline=outline,
    )
