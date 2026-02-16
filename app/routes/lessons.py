from fastapi import APIRouter
from app.models import LessonGenerateRequest, LessonCompleteRequest
from app.services import lesson_service, quiz_service

router = APIRouter(prefix="/api")


@router.post("/lessons/generate")
def generate_lesson(req: LessonGenerateRequest):
    return lesson_service.generate_lesson(req.skill_id, req.lesson_id)


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: int):
    lesson = lesson_service.get_lesson(lesson_id)
    if not lesson:
        return {"error": "Lesson not found"}
    return lesson


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: int):
    lesson_service.complete_lesson(1, lesson_id)
    return {"status": "completed"}


@router.post("/lessons/{lesson_id}/quiz")
def generate_quiz(lesson_id: int):
    return quiz_service.generate_quiz(lesson_id)


@router.get("/lessons/{lesson_id}/quiz")
def get_quiz(lesson_id: int):
    quiz = quiz_service.get_quiz(lesson_id)
    if not quiz:
        return {"error": "No quiz found"}
    return quiz
