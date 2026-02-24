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


@router.get("/progress/charts")
def get_chart_data():
    from datetime import date, timedelta
    today = date.today()
    days = [(today - timedelta(days=29 - i)).isoformat() for i in range(30)]

    lesson_activity = query(
        """SELECT date(completed_at) as day, COUNT(*) as count
           FROM lesson_attempts
           WHERE user_id = 1 AND completed_at IS NOT NULL
             AND completed_at >= date('now', '-30 days')
           GROUP BY day""",
    )
    quiz_activity = query(
        """SELECT date(completed_at) as day, COUNT(*) as count
           FROM quiz_attempts
           WHERE user_id = 1
             AND completed_at >= date('now', '-30 days')
           GROUP BY day""",
    )
    quiz_scores = query(
        """SELECT date(completed_at) as day, score
           FROM quiz_attempts
           WHERE user_id = 1
           ORDER BY completed_at ASC
           LIMIT 20""",
    )
    skills_progress = query(
        """SELECT s.name,
                  COUNT(l.id) as total_lessons,
                  SUM(CASE WHEN l.status = 'completed' THEN 1 ELSE 0 END) as completed_lessons
           FROM skills s
           LEFT JOIN lessons l ON l.skill_id = s.id
           WHERE s.user_id = 1 AND s.is_active = 1
           GROUP BY s.id, s.name""",
    )

    lesson_by_day = {r["day"]: r["count"] for r in lesson_activity}
    quiz_by_day = {r["day"]: r["count"] for r in quiz_activity}

    return {
        "activity": {
            "labels": days,
            "lessons": [lesson_by_day.get(d, 0) for d in days],
            "quizzes": [quiz_by_day.get(d, 0) for d in days],
        },
        "quiz_scores": {
            "labels": [r["day"] for r in quiz_scores],
            "scores": [round(r["score"] * 100) for r in quiz_scores],
        },
        "skills": {
            "labels": [r["name"] for r in skills_progress],
            "completed": [r["completed_lessons"] or 0 for r in skills_progress],
            "total": [r["total_lessons"] or 0 for r in skills_progress],
        },
    }


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
