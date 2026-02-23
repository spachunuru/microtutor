from pydantic import BaseModel, Field


class SkillPreviewRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class SkillCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str
    curriculum: list[dict]


class LessonGenerateRequest(BaseModel):
    skill_id: int
    lesson_id: int


class LessonCompleteRequest(BaseModel):
    pass


class QuizGradeRequest(BaseModel):
    question: dict
    answer: str = Field(..., min_length=1, max_length=2000)


class QuizSubmitRequest(BaseModel):
    quiz_id: int
    answers: dict
    score: float = Field(..., ge=0.0, le=1.0)


class ChatRequest(BaseModel):
    skill_id: int | None = None
    lesson_id: int | None = None
    message: str = Field(..., min_length=1, max_length=5000)
    history: list[dict] = []


class ExerciseEvaluateRequest(BaseModel):
    exercise: dict
    submission: str = Field(..., min_length=1, max_length=10000)
    output: str | None = None


class ReviewRateRequest(BaseModel):
    quality: int = Field(..., ge=0, le=5)
