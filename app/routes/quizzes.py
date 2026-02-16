from fastapi import APIRouter
from app.models import QuizGradeRequest, QuizSubmitRequest
from app.services import quiz_service

router = APIRouter(prefix="/api")


@router.post("/quizzes/grade")
def grade_answer(req: QuizGradeRequest):
    return quiz_service.grade_answer(req.question, req.answer)


@router.post("/quizzes/submit")
def submit_quiz(req: QuizSubmitRequest):
    return quiz_service.submit_quiz(1, req.quiz_id, req.answers, req.score)
