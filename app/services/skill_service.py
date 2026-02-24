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


def delete_skill(skill_id: int):
    # Delete related data
    execute("DELETE FROM chat_messages WHERE skill_id = ?", (skill_id,))
    # Get lesson IDs for this skill
    lessons = query("SELECT id FROM lessons WHERE skill_id = ?", (skill_id,))
    for lesson in lessons:
        execute("DELETE FROM review_cards WHERE lesson_id = ?", (lesson["id"],))
        # Delete quiz attempts before quizzes (foreign key)
        quizzes = query("SELECT id FROM quizzes WHERE lesson_id = ?", (lesson["id"],))
        for quiz in quizzes:
            execute("DELETE FROM quiz_attempts WHERE quiz_id = ?", (quiz["id"],))
        execute("DELETE FROM quizzes WHERE lesson_id = ?", (lesson["id"],))
        execute("DELETE FROM lesson_attempts WHERE lesson_id = ?", (lesson["id"],))
    execute("DELETE FROM lessons WHERE skill_id = ?", (skill_id,))
    execute("DELETE FROM skills WHERE id = ?", (skill_id,))


def get_or_generate_cheat_sheet(skill_id: int, force: bool = False) -> str:
    skill = query_one("SELECT * FROM skills WHERE id = ?", (skill_id,))
    if not skill:
        raise ValueError("Skill not found")

    if skill["cheatsheet"] and not force:
        return skill["cheatsheet"]

    lessons = query(
        "SELECT topic, content_json FROM lessons WHERE skill_id = ? AND content_json IS NOT NULL ORDER BY order_index",
        (skill_id,),
    )
    if not lessons:
        raise ValueError("No generated lessons found. Generate at least one lesson first.")

    summaries = []
    for lesson in lessons:
        content = json.loads(lesson["content_json"])
        parts = [f"## {lesson['topic']}"]
        if content.get("key_points"):
            parts.append("Key points: " + "; ".join(content["key_points"]))
        if content.get("summary"):
            parts.append("Summary: " + content["summary"])
        summaries.append("\n".join(parts))

    cheatsheet = tutor.generate_cheat_sheet(skill["name"], "\n\n".join(summaries))
    execute("UPDATE skills SET cheatsheet = ? WHERE id = ?", (cheatsheet, skill_id))
    return cheatsheet


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
