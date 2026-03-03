import os
from functools import lru_cache
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import AsyncClient

from config import settings


def _init_firebase() -> None:
    if firebase_admin._apps:
        return
    cred_path = settings.google_application_credentials
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
    else:
        cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})


@lru_cache
def get_db() -> AsyncClient:
    _init_firebase()
    return firestore.AsyncClient(project=settings.firebase_project_id)


class FirestoreService:
    def __init__(self) -> None:
        self.db = get_db()

    async def set(self, collection: str, doc_id: str, data: dict[str, Any]) -> None:
        await self.db.collection(collection).document(doc_id).set(data)

    async def get(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        doc = await self.db.collection(collection).document(doc_id).get()
        return doc.to_dict() if doc.exists else None

    async def update(self, collection: str, doc_id: str, data: dict[str, Any]) -> None:
        await self.db.collection(collection).document(doc_id).update(data)

    async def delete(self, collection: str, doc_id: str) -> None:
        await self.db.collection(collection).document(doc_id).delete()

    async def query(
        self,
        collection: str,
        field: str,
        value: Any,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        docs = (
            await self.db.collection(collection)
            .where(field, "==", value)
            .limit(limit)
            .get()
        )
        return [d.to_dict() for d in docs if d.exists]

    async def delete_where(self, collection: str, field: str, value: Any) -> None:
        docs = await self.db.collection(collection).where(field, "==", value).get()
        for doc in docs:
            await doc.reference.delete()
