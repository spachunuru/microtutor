import math
from datetime import date

from app.database import query_one, execute

# XP rewards
XP_LESSON_COMPLETE = 50
XP_CORRECT_ANSWER = 20
XP_PERFECT_QUIZ = 50
XP_REVIEW_CARD = 10
XP_DAILY_STREAK = 25
XP_EXERCISE_COMPLETE = 15

# Achievement definitions: key -> (name, description)
ACHIEVEMENTS = {
    "first_lesson": ("First Steps", "Complete your first lesson"),
    "first_quiz": ("Quiz Whiz", "Complete your first quiz"),
    "perfect_score": ("Perfectionist", "Get 100% on a quiz"),
    "streak_3": ("On a Roll", "3-day learning streak"),
    "streak_7": ("Week Warrior", "7-day learning streak"),
    "streak_30": ("Monthly Master", "30-day learning streak"),
    "lessons_10": ("Dedicated Learner", "Complete 10 lessons"),
    "lessons_50": ("Knowledge Seeker", "Complete 50 lessons"),
    "xp_1000": ("XP Milestone", "Earn 1,000 XP"),
    "first_review": ("Memory Keeper", "Complete your first review"),
    "multi_skill": ("Renaissance Learner", "Start learning 3 skills"),
}


def xp_for_level(level: int) -> int:
    return round(100 * math.pow(level, 1.5))


def level_from_xp(total_xp: int) -> int:
    level = 1
    while xp_for_level(level + 1) <= total_xp:
        level += 1
    return level


def add_xp(user_id: int, xp: int) -> dict:
    progress = query_one("SELECT * FROM user_progress WHERE user_id = ?", (user_id,))
    new_xp = (progress["total_xp"] or 0) + xp
    new_level = level_from_xp(new_xp)

    execute(
        "UPDATE user_progress SET total_xp = ?, level = ? WHERE user_id = ?",
        (new_xp, new_level, user_id),
    )
    return {"total_xp": new_xp, "level": new_level, "xp_added": xp}


def update_streak(user_id: int):
    progress = query_one("SELECT * FROM user_progress WHERE user_id = ?", (user_id,))
    today = date.today().isoformat()
    last = progress["last_activity_date"]

    if last == today:
        return  # Already counted today

    yesterday = date.today().toordinal() - 1
    if last and date.fromisoformat(last).toordinal() == yesterday:
        new_streak = (progress["current_streak"] or 0) + 1
    else:
        new_streak = 1

    longest = max(new_streak, progress["longest_streak"] or 0)

    execute(
        "UPDATE user_progress SET current_streak = ?, longest_streak = ?, last_activity_date = ? WHERE user_id = ?",
        (new_streak, longest, today, user_id),
    )

    # Streak bonus XP
    if new_streak > 1:
        add_xp(user_id, XP_DAILY_STREAK)


def check_achievements(user_id: int) -> list[dict]:
    progress = query_one("SELECT * FROM user_progress WHERE user_id = ?", (user_id,))
    new_achievements = []

    checks = {
        "first_lesson": (progress["lessons_completed"] or 0) >= 1,
        "first_quiz": (progress["quizzes_completed"] or 0) >= 1,
        "streak_3": (progress["current_streak"] or 0) >= 3,
        "streak_7": (progress["current_streak"] or 0) >= 7,
        "streak_30": (progress["current_streak"] or 0) >= 30,
        "lessons_10": (progress["lessons_completed"] or 0) >= 10,
        "lessons_50": (progress["lessons_completed"] or 0) >= 50,
        "xp_1000": (progress["total_xp"] or 0) >= 1000,
        "first_review": (progress["reviews_completed"] or 0) >= 1,
    }

    for key, condition in checks.items():
        if condition:
            try:
                execute(
                    "INSERT OR IGNORE INTO achievements (user_id, achievement_key) VALUES (?, ?)",
                    (user_id, key),
                )
                # Check if it was actually inserted (new)
                from app.database import get_db
                if get_db().execute(
                    "SELECT changes()"
                ).fetchone()[0] > 0:
                    name, desc = ACHIEVEMENTS[key]
                    new_achievements.append({"key": key, "name": name, "description": desc})
            except Exception:
                pass

    return new_achievements
