from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class User(BaseModel):
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeSource(BaseModel):
    source_type: Literal["pdf", "url"]
    source_name: str
    url: str | None = None


class Course(BaseModel):
    course_id: str
    user_id: str
    topic: str
    knowledge_sources: list[KnowledgeSource] = []
    outline: list[dict] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LessonStep(BaseModel):
    step_id: int
    type: Literal["text", "image", "svg", "question-choice", "question-fill", "question-open"]
    content: str
    options: list[str] = []
    answer: str | None = None
    explanation: str | None = None
    source: str | None = None


class Lesson(BaseModel):
    lesson_id: str
    course_id: str
    title: str
    steps: list[LessonStep] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Progress(BaseModel):
    user_id: str
    course_id: str
    lesson_id: str
    completed_steps: list[int] = []
    completed: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class XPLog(BaseModel):
    user_id: str
    course_id: str
    lesson_id: str
    xp_delta: int
    reason: Literal["correct_answer", "streak_bonus"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
