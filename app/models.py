from pydantic import BaseModel


class SkillPreviewRequest(BaseModel):
    name: str


class SkillCreateRequest(BaseModel):
    name: str
    description: str
    curriculum: list[dict]


class LessonGenerateRequest(BaseModel):
    skill_id: int
    lesson_id: int


class LessonCompleteRequest(BaseModel):
    pass


class QuizGradeRequest(BaseModel):
    question: dict
    answer: str


class QuizSubmitRequest(BaseModel):
    quiz_id: int
    answers: dict
    score: float


class ChatRequest(BaseModel):
    skill_id: int | None = None
    message: str
    history: list[dict] = []


class ReviewRateRequest(BaseModel):
    quality: int
