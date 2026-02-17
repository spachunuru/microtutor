from fastapi import APIRouter

from app.ai.tutor import evaluate_exercise
from app.models import ExerciseEvaluateRequest
from app.services.gamification import add_xp, update_streak, check_achievements, XP_EXERCISE_COMPLETE

router = APIRouter(prefix="/api/exercises", tags=["exercises"])

USER_ID = 1


@router.post("/evaluate")
def evaluate(req: ExerciseEvaluateRequest):
    result = evaluate_exercise(req.exercise, req.submission, req.output)

    xp_earned = 0
    new_achievements = []

    if result.get("correct"):
        xp_result = add_xp(USER_ID, XP_EXERCISE_COMPLETE)
        xp_earned = xp_result["xp_added"]
        update_streak(USER_ID)
        new_achievements = check_achievements(USER_ID)

    return {
        "correct": result.get("correct", False),
        "feedback": result.get("feedback", ""),
        "hints": result.get("hints", []),
        "xp_earned": xp_earned,
        "new_achievements": new_achievements,
    }
