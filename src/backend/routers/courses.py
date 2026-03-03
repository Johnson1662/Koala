import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.firestore import FirestoreService
router = APIRouter()
_db = FirestoreService()


class CreateCourseRequest(BaseModel):
    user_id: str
    topic: str


class CourseResponse(BaseModel):
    course_id: str
    user_id: str
    topic: str
    outline: list[dict]
    created_at: str


@router.post("", response_model=CourseResponse, status_code=201)
async def create_course(body: CreateCourseRequest) -> CourseResponse:
    course_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "course_id": course_id,
        "user_id": body.user_id,
        "topic": body.topic,
        "outline": [],
        "created_at": now,
    }
    await _db.set("courses", course_id, doc)
    return CourseResponse(**doc)


@router.get("", response_model=list[CourseResponse])
async def list_courses(user_id: str) -> list[CourseResponse]:
    docs = await _db.query("courses", "user_id", user_id)
    return [CourseResponse(**d) for d in docs]


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: str) -> CourseResponse:
    doc = await _db.get("courses", course_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseResponse(**doc)


@router.delete("/{course_id}", status_code=204)
async def delete_course(course_id: str) -> None:
    doc = await _db.get("courses", course_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Course not found")
    await _db.delete("courses", course_id)
    for collection in ("progress", "feedback", "xp_logs"):
        await _db.delete_where(collection, "course_id", course_id)
