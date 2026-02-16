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

    # Build messages for Claude
    messages = [{"role": m["role"], "content": m["content"]} for m in req.history]
    messages.append({"role": "user", "content": req.message})

    response = tutor.chat(messages, skill_context)

    # Save messages
    if req.skill_id:
        execute(
            "INSERT INTO chat_messages (user_id, skill_id, role, content) VALUES (?, ?, 'user', ?)",
            (1, req.skill_id, req.message),
        )
        execute(
            "INSERT INTO chat_messages (user_id, skill_id, role, content) VALUES (?, ?, 'assistant', ?)",
            (1, req.skill_id, response),
        )

    return {"response": response}


@router.get("/chat/{skill_id}/history")
def get_chat_history(skill_id: int):
    rows = query(
        "SELECT role, content FROM chat_messages WHERE user_id = 1 AND skill_id = ? ORDER BY created_at",
        (skill_id,),
    )
    return {"messages": [dict(r) for r in rows]}
