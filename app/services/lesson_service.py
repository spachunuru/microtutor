import json
from app.database import execute, query, query_one
from app.ai import tutor


def generate_lesson(skill_id: int, lesson_id: int) -> dict:
    lesson = query_one("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    skill = query_one("SELECT * FROM skills WHERE id = ?", (skill_id,))

    # Get previously completed topics
    previous = query(
        "SELECT topic FROM lessons WHERE skill_id = ? AND order_index < ? AND status = 'completed' ORDER BY order_index",
        (skill_id, lesson["order_index"]),
    )
    previous_topics = [r["topic"] for r in previous]

    content = tutor.generate_lesson(
        skill_name=skill["name"],
        topic=lesson["topic"],
        difficulty=lesson["difficulty"] or 1,
        previous_topics=previous_topics,
    )

    execute(
        "UPDATE lessons SET content_json = ?, summary = ? WHERE id = ?",
        (json.dumps(content), content.get("summary", ""), lesson_id),
    )

    return {"id": lesson_id, **content}


def get_lesson(lesson_id: int) -> dict | None:
    row = query_one("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    return dict(row) if row else None


def complete_lesson(user_id: int, lesson_id: int):
    # Check if already completed — prevent double XP and duplicate review cards
    lesson = query_one("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    if lesson and lesson["status"] == "completed":
        return {"already_completed": True, "xp_earned": 0}

    execute("UPDATE lessons SET status = 'completed' WHERE id = ?", (lesson_id,))

    # Record attempt
    execute(
        "INSERT INTO lesson_attempts (user_id, lesson_id, completed_at) VALUES (?, ?, datetime('now'))",
        (user_id, lesson_id),
    )

    # Update progress
    execute(
        "UPDATE user_progress SET lessons_completed = lessons_completed + 1 WHERE user_id = ?",
        (user_id,),
    )

    # Add XP and update streak
    from app.services.gamification import add_xp, update_streak, XP_LESSON_COMPLETE
    add_xp(user_id, XP_LESSON_COMPLETE)
    update_streak(user_id)

    # Generate review cards
    if lesson and lesson["content_json"]:
        try:
            content = json.loads(lesson["content_json"])
            cards = tutor.generate_review_cards(content)
            for card in cards:
                execute(
                    "INSERT INTO review_cards (user_id, lesson_id, question, answer) VALUES (?, ?, ?, ?)",
                    (user_id, lesson_id, card["question"], card["answer"]),
                )
        except Exception as e:
            print(f"Failed to generate review cards: {e}")

    return {"already_completed": False, "xp_earned": XP_LESSON_COMPLETE}
