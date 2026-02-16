import json
from app.ai.client import get_client
from app.ai.prompts import format_prompt
from app.config import settings


def _call(prompt: str, system: str = "You are an expert tutor.", expect_json: bool = True) -> str | dict:
    client = get_client()
    response = client.messages.create(
        model=settings.model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if expect_json:
        # Extract JSON from markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    return text


def generate_curriculum(skill_name: str, difficulty: str = "beginner") -> dict:
    prompt = format_prompt("curriculum", skill_name=skill_name, difficulty=difficulty)
    return _call(prompt)


def generate_lesson(skill_name: str, topic: str, difficulty: int, previous_topics: list[str]) -> dict:
    prev = ", ".join(previous_topics) if previous_topics else "None (this is the first lesson)"
    prompt = format_prompt(
        "lesson",
        skill_name=skill_name,
        topic=topic,
        difficulty=difficulty,
        previous_topics=prev,
    )
    return _call(prompt)


def generate_quiz(lesson_content: dict, difficulty: int) -> dict:
    prompt = format_prompt(
        "quiz",
        lesson_json=json.dumps(lesson_content, indent=2),
        difficulty=difficulty,
    )
    return _call(prompt)


def grade_answer(question: dict, user_answer: str) -> dict:
    prompt = format_prompt(
        "grade_answer",
        question=question["question"],
        correct_answer=question.get("correct_answer", ""),
        user_answer=user_answer,
    )
    return _call(prompt)


def chat(messages: list[dict], skill_context: str = "") -> str:
    system = format_prompt("tutor_chat", skill_context=skill_context)
    client = get_client()
    response = client.messages.create(
        model=settings.model,
        max_tokens=2048,
        system=system,
        messages=messages,
    )
    return response.content[0].text.strip()


def generate_review_cards(lesson_content: dict) -> list[dict]:
    prompt = format_prompt(
        "review_cards",
        lesson_json=json.dumps(lesson_content, indent=2),
    )
    result = _call(prompt)
    return result.get("cards", result) if isinstance(result, dict) else result
