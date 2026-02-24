import json

from fastapi import APIRouter, HTTPException
from app.models import LessonGenerateRequest, FeedbackSubmitRequest
from app.database import execute, query_one
from app.services import lesson_service, quiz_service

router = APIRouter(prefix="/api")


@router.post("/lessons/generate")
def generate_lesson(req: LessonGenerateRequest):
    try:
        return lesson_service.generate_lesson(req.skill_id, req.lesson_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate lesson: {e}")


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: int):
    lesson = lesson_service.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: int):
    lesson = lesson_service.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    lesson_service.complete_lesson(1, lesson_id)
    return {"status": "completed"}


@router.post("/lessons/{lesson_id}/quiz")
def generate_quiz(lesson_id: int):
    try:
        return quiz_service.generate_quiz(lesson_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {e}")


@router.get("/lessons/{lesson_id}/quiz")
def get_quiz(lesson_id: int):
    quiz = quiz_service.get_quiz(lesson_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="No quiz found for this lesson")
    return quiz


@router.post("/lessons/{lesson_id}/feedback")
def submit_feedback(lesson_id: int, req: FeedbackSubmitRequest):
    execute(
        """INSERT INTO user_feedback (user_id, content_type, content_id, tags_json, message)
           VALUES (?, 'lesson', ?, ?, ?)""",
        (1, lesson_id, json.dumps(req.tags), req.message),
    )
    return {"status": "submitted"}


@router.get("/lessons/{lesson_id}/feedback")
def get_lesson_feedback(lesson_id: int):
    row = query_one(
        """SELECT tags_json, message FROM user_feedback
           WHERE content_id = ? AND content_type = 'lesson' AND user_id = 1
           ORDER BY created_at DESC LIMIT 1""",
        (lesson_id,),
    )
    if not row:
        return {"submitted": False}
    return {"submitted": True, "tags": json.loads(row["tags_json"]), "message": row["message"]}
