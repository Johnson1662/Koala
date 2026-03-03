import uuid
from fastapi import APIRouter
from pydantic import BaseModel

from services.firestore import FirestoreService
router = APIRouter()
_db = FirestoreService()


class AnonymousAuthResponse(BaseModel):
    user_id: str


@router.post("/anonymous", response_model=AnonymousAuthResponse)
async def anonymous_login() -> AnonymousAuthResponse:
    user_id = str(uuid.uuid4())
    await _db.set("users", user_id, {"user_id": user_id})
    return AnonymousAuthResponse(user_id=user_id)
