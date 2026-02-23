from datetime import datetime, timedelta
from app.database import execute, query


def get_review_queue(user_id: int) -> list[dict]:
    rows = query(
        """SELECT rc.*, l.topic AS lesson_topic
           FROM review_cards rc
           LEFT JOIN lessons l ON rc.lesson_id = l.id
           WHERE rc.user_id = ? AND rc.next_review_at <= datetime('now')
           ORDER BY rc.next_review_at""",
        (user_id,),
    )
    return [dict(r) for r in rows]


def rate_card(user_id: int, card_id: int, quality: int) -> dict:
    """Update card scheduling based on SM-2 algorithm.
    quality: 0=Again, 3=Hard, 4=Good, 5=Easy
    """
    from app.database import query_one
    card = query_one("SELECT * FROM review_cards WHERE id = ? AND user_id = ?", (card_id, user_id))
    if not card:
        return {"error": "Card not found"}

    ease_factor = card["ease_factor"] or 2.5
    interval_days = card["interval_days"] or 1
    repetitions = card["repetitions"] or 0

    if quality < 3:  # "Again"
        repetitions = 0
        interval_days = 1
    else:
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 6
        else:
            interval_days = round(interval_days * ease_factor)
        repetitions += 1

    # Update ease factor
    ease_factor = max(1.3, ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

    now = datetime.utcnow()
    next_review = now + timedelta(days=interval_days)

    execute(
        """UPDATE review_cards SET
           ease_factor = ?, interval_days = ?, repetitions = ?,
           next_review_at = ?, last_reviewed_at = ?
           WHERE id = ?""",
        (ease_factor, interval_days, repetitions, next_review.isoformat(), now.isoformat(), card_id),
    )

    # Award XP for review
    from app.services.gamification import add_xp, update_streak, check_achievements, XP_REVIEW_CARD
    xp = XP_REVIEW_CARD if quality >= 3 else 0
    if xp:
        add_xp(user_id, xp)

    # Update review count
    execute(
        "UPDATE user_progress SET reviews_completed = reviews_completed + 1 WHERE user_id = ?",
        (user_id,),
    )
    update_streak(user_id)

    new_achievements = check_achievements(user_id)

    return {"xp_earned": xp, "next_review_days": interval_days, "new_achievements": new_achievements}


def get_progress_service(user_id: int) -> dict:
    from app.database import query_one
    row = query_one("SELECT * FROM user_progress WHERE user_id = ?", (user_id,))
    return dict(row) if row else {}
