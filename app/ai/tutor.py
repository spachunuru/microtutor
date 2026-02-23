import json
from app.ai.client import get_client
from app.ai.prompts import format_prompt
from app.config import settings


def _call(prompt: str, system: str = "You are an expert tutor.", expect_json: bool = True, max_tokens: int = 4096) -> str | dict:
    client = get_client()
    response = client.messages.create(
        model=settings.model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if expect_json:
        # Extract JSON from markdown code blocks if present.
        # Use rfind for the closing ``` to avoid matching backticks
        # inside JSON string values (e.g. markdown code examples).
        if "```json" in text:
            start = text.index("```json") + len("```json")
            end = text.rfind("```")
            text = text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + len("```")
            end = text.rfind("```")
            text = text[start:end].strip()
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
    return _call(prompt, max_tokens=8192)


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


def evaluate_exercise(exercise: dict, submission: str, output: str | None = None) -> dict:
    output_section = ""
    if output:
        output_section = f"Execution output:\n```\n{output}\n```"

    prompt = format_prompt(
        "evaluate_exercise",
        exercise_type=exercise.get("type", "code"),
        exercise_title=exercise.get("title", ""),
        exercise_instructions=exercise.get("instructions", ""),
        expected_output=exercise.get("expected_output", "N/A"),
        submission=submission,
        output_section=output_section,
    )
    return _call(prompt)


def generate_resources(topic: str, skill_name: str, papers: list[dict]) -> dict:
    prompt = format_prompt("resources", topic=topic, skill_name=skill_name)
    result = _call(prompt, max_tokens=1024)
    result["papers"] = papers
    return result


def generate_review_cards(lesson_content: dict) -> list[dict]:
    prompt = format_prompt(
        "review_cards",
        lesson_json=json.dumps(lesson_content, indent=2),
    )
    result = _call(prompt)
    return result.get("cards", result) if isinstance(result, dict) else result
