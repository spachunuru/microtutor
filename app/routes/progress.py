import json
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import Response
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


@router.get("/progress/export")
def export_progress():
    progress = query_one("SELECT * FROM user_progress WHERE user_id = 1")
    skills = query(
        """SELECT s.name, s.description, s.created_at,
           (SELECT COUNT(*) FROM lessons WHERE skill_id = s.id) as total_lessons,
           (SELECT COUNT(*) FROM lessons WHERE skill_id = s.id AND status = 'completed') as completed_lessons
           FROM skills s WHERE s.user_id = 1 AND s.is_active = 1""",
    )
    unlocked = query("SELECT achievement_key FROM achievements WHERE user_id = 1")

    export_data = {
        "exported_at": datetime.now().isoformat(),
        "progress": dict(progress) if progress else {},
        "skills": [dict(s) for s in skills],
        "achievements": [dict(a) for a in unlocked],
    }

    return Response(
        content=json.dumps(export_data, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=microtutor-progress.json"},
    )
