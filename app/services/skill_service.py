import json
from app.database import execute, query, query_one
from app.ai import tutor


def preview_curriculum(name: str) -> dict:
    return tutor.generate_curriculum(name)


def create_skill(user_id: int, name: str, description: str, curriculum: list[dict]) -> dict:
    skill_id = execute(
        "INSERT INTO skills (user_id, name, description, curriculum_json) VALUES (?, ?, ?, ?)",
        (user_id, name, description, json.dumps(curriculum)),
    )

    # Create lesson stubs from curriculum
    for i, topic in enumerate(curriculum):
        execute(
            "INSERT INTO lessons (skill_id, topic, order_index, difficulty) VALUES (?, ?, ?, ?)",
            (skill_id, topic["title"], i + 1, 1),
        )

    # Check multi_skill achievement
    from app.database import get_db
    count = get_db().execute(
        "SELECT COUNT(*) FROM skills WHERE user_id = ? AND is_active = 1", (user_id,)
    ).fetchone()[0]
    if count >= 3:
        try:
            execute(
                "INSERT OR IGNORE INTO achievements (user_id, achievement_key) VALUES (?, ?)",
                (user_id, "multi_skill"),
            )
        except Exception:
            pass

    return {"id": skill_id, "name": name, "description": description}


def get_skills(user_id: int) -> list[dict]:
    rows = query(
        """SELECT s.*,
           (SELECT COUNT(*) FROM lessons WHERE skill_id = s.id) as total_lessons,
           (SELECT COUNT(*) FROM lessons WHERE skill_id = s.id AND status = 'completed') as lessons_completed
           FROM skills s WHERE s.user_id = ? AND s.is_active = 1 ORDER BY s.created_at DESC""",
        (user_id,),
    )
    return [dict(r) for r in rows]


def get_skill_detail(skill_id: int) -> dict:
    skill = query_one("SELECT * FROM skills WHERE id = ?", (skill_id,))
    lessons = query(
        "SELECT * FROM lessons WHERE skill_id = ? ORDER BY order_index",
        (skill_id,),
    )
    return {
        "skill": dict(skill) if skill else None,
        "lessons": [dict(l) for l in lessons],
    }
