import uuid
from datetime import datetime, timezone
from typing import Any

from services.firestore import FirestoreService

XP_PER_CORRECT = 10
XP_STREAK_BONUS = 10
STREAK_THRESHOLD = 3


async def record_answer(
    db: FirestoreService,
    user_id: str,
    course_id: str,
    lesson_id: str,
    is_correct: bool,
    current_streak: int,
) -> dict[str, Any]:
    xp_earned = 0
    streak_after = current_streak + 1 if is_correct else 0
    logs: list[dict[str, Any]] = []

    if is_correct:
        xp_earned += XP_PER_CORRECT
        logs.append({
            "log_id": str(uuid.uuid4()),
            "user_id": user_id,
            "course_id": course_id,
            "lesson_id": lesson_id,
            "xp_delta": XP_PER_CORRECT,
            "reason": "correct_answer",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        if streak_after % STREAK_THRESHOLD == 0:
            xp_earned += XP_STREAK_BONUS
            logs.append({
                "log_id": str(uuid.uuid4()),
                "user_id": user_id,
                "course_id": course_id,
                "lesson_id": lesson_id,
                "xp_delta": XP_STREAK_BONUS,
                "reason": "streak_bonus",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    for log in logs:
        await db.set("xp_logs", log["log_id"], log)

    return {
        "xp_earned": xp_earned,
        "streak": streak_after,
        "logs": logs,
    }


async def get_user_total_xp(db: FirestoreService, user_id: str) -> int:
    logs = await db.query("xp_logs", "user_id", user_id)
    return sum(log.get("xp_delta", 0) for log in logs)
