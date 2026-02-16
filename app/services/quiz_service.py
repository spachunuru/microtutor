import json
from app.database import execute, query_one
from app.ai import tutor


def generate_quiz(lesson_id: int) -> dict:
    lesson = query_one("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    content = json.loads(lesson["content_json"]) if lesson and lesson["content_json"] else {}

    result = tutor.generate_quiz(content, lesson["difficulty"] or 1)
    questions = result.get("questions", [])

    quiz_id = execute(
        "INSERT INTO quizzes (lesson_id, questions_json) VALUES (?, ?)",
        (lesson_id, json.dumps(questions)),
    )

    return {"quiz_id": quiz_id, "skill_id": lesson["skill_id"], "questions": questions}


def get_quiz(lesson_id: int) -> dict | None:
    row = query_one(
        "SELECT * FROM quizzes WHERE lesson_id = ? ORDER BY created_at DESC LIMIT 1",
        (lesson_id,),
    )
    if not row:
        return None
    lesson = query_one("SELECT skill_id FROM lessons WHERE id = ?", (lesson_id,))
    return {
        "quiz_id": row["id"],
        "skill_id": lesson["skill_id"] if lesson else None,
        "questions": json.loads(row["questions_json"]),
    }


def grade_answer(question: dict, answer: str) -> dict:
    return tutor.grade_answer(question, answer)


def submit_quiz(user_id: int, quiz_id: int, answers: dict, score: float) -> dict:
    from app.services.gamification import (
        add_xp, update_streak, check_achievements,
        XP_CORRECT_ANSWER, XP_PERFECT_QUIZ,
    )

    correct_count = sum(1 for a in answers.values() if a.get("correct"))
    total = len(answers)

    xp = correct_count * XP_CORRECT_ANSWER
    if score >= 1.0:
        xp += XP_PERFECT_QUIZ

    execute(
        "INSERT INTO quiz_attempts (user_id, quiz_id, answers_json, score, xp_earned) VALUES (?, ?, ?, ?, ?)",
        (user_id, quiz_id, json.dumps(answers), score, xp),
    )

    execute(
        "UPDATE user_progress SET quizzes_completed = quizzes_completed + 1 WHERE user_id = ?",
        (user_id,),
    )

    add_xp(user_id, xp)
    update_streak(user_id)

    # Check for perfect score achievement
    if score >= 1.0:
        try:
            execute(
                "INSERT OR IGNORE INTO achievements (user_id, achievement_key) VALUES (?, ?)",
                (user_id, "perfect_score"),
            )
        except Exception:
            pass

    new_achievements = check_achievements(user_id)

    return {"xp_earned": xp, "new_achievements": new_achievements}
