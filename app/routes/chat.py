import json

from fastapi import APIRouter
from app.models import ChatRequest
from app.ai import tutor
from app.database import query, query_one, execute

router = APIRouter(prefix="/api")


@router.post("/chat")
def chat(req: ChatRequest):
    skill_context = ""
    if req.skill_id:
        skill = query_one("SELECT * FROM skills WHERE id = ?", (req.skill_id,))
        if skill:
            skill_context = f"You are helping the learner with: {skill['name']}. {skill['description'] or ''}"

    valid_lesson_id = None
    if req.lesson_id:
        lesson = query_one("SELECT * FROM lessons WHERE id = ?", (req.lesson_id,))
        if lesson:
            valid_lesson_id = req.lesson_id
        if lesson and lesson["content_json"]:
            content = json.loads(lesson["content_json"]) if isinstance(lesson["content_json"], str) else lesson["content_json"]
            parts = []
            if content.get("topic"):
                parts.append(f"Current lesson topic: {content['topic']}")
            if content.get("objective"):
                parts.append(f"Objective: {content['objective']}")
            if content.get("key_points"):
                points = "\n".join(f"- {p}" for p in content["key_points"])
                parts.append(f"Key points:\n{points}")
            if content.get("exercises"):
                ex_lines = []
                for ex in content["exercises"]:
                    title = ex.get("title", "Untitled")
                    instructions = ex.get("instructions", "")
                    ex_lines.append(f"- {title}: {instructions}")
                parts.append(f"Exercises:\n" + "\n".join(ex_lines))
            if parts:
                skill_context += "\n\n" + "\n".join(parts)

    # Build messages for Claude
    messages = [{"role": m["role"], "content": m["content"]} for m in req.history]
    messages.append({"role": "user", "content": req.message})

    response = tutor.chat(messages, skill_context)

    # Save messages
    if req.skill_id or valid_lesson_id:
        execute(
            "INSERT INTO chat_messages (user_id, skill_id, lesson_id, role, content) VALUES (?, ?, ?, 'user', ?)",
            (1, req.skill_id, valid_lesson_id, req.message),
        )
        execute(
            "INSERT INTO chat_messages (user_id, skill_id, lesson_id, role, content) VALUES (?, ?, ?, 'assistant', ?)",
            (1, req.skill_id, valid_lesson_id, response),
        )

    return {"response": response}


@router.get("/chat/{skill_id}/history")
def get_chat_history(skill_id: int):
    rows = query(
        "SELECT role, content FROM chat_messages WHERE user_id = 1 AND skill_id = ? ORDER BY created_at",
        (skill_id,),
    )
    return {"messages": [dict(r) for r in rows]}
