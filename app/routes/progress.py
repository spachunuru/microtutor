from fastapi import APIRouter
from app.database import query, query_one
from app.services.gamification import ACHIEVEMENTS

router = APIRouter(prefix="/api")


@router.get("/progress")
def get_progress():
    row = query_one("SELECT * FROM user_progress WHERE user_id = 1")
    return dict(row) if row else {}


@router.get("/achievements")
def get_achievements():
    unlocked = query("SELECT achievement_key FROM achievements WHERE user_id = 1")
    unlocked_keys = {r["achievement_key"] for r in unlocked}

    result = []
    for key, (name, description) in ACHIEVEMENTS.items():
        result.append({
            "key": key,
            "name": name,
            "description": description,
            "unlocked": key in unlocked_keys,
        })
    return result
