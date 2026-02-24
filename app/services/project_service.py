import json
from app.database import execute, query, query_one
from app.ai import tutor

_CODING_KEYWORDS = {
    "python", "javascript", "typescript", "programming", "coding", "software",
    "algorithm", "data science", "machine learning", "web development",
    "java", "rust", "sql", "backend", "frontend", "api", "database",
    "deep learning", "neural", "pytorch", "tensorflow",
}


def _infer_submission_type(skill: dict) -> str:
    text = (skill.get("name", "") + " " + skill.get("description", "")).lower()
    if any(kw in text for kw in _CODING_KEYWORDS):
        return "code"
    return "text"


def get_or_generate_project(skill_id: int) -> dict:
    existing = query_one(
        "SELECT * FROM skill_projects WHERE skill_id = ? ORDER BY created_at DESC LIMIT 1",
        (skill_id,),
    )
    if existing:
        brief = json.loads(existing["description_json"])
        skill = query_one("SELECT * FROM skills WHERE id = ?", (skill_id,))
        brief.setdefault("submission_type", _infer_submission_type(dict(skill)) if skill else "text")
        return {"id": existing["id"], **brief}

    skill = query_one("SELECT * FROM skills WHERE id = ?", (skill_id,))
    if not skill:
        raise ValueError("Skill not found")

    curriculum = json.loads(skill["curriculum_json"] or "[]")
    curriculum_overview = ", ".join(t.get("title", "") for t in curriculum)

    lessons = query(
        "SELECT topic, status FROM lessons WHERE skill_id = ? ORDER BY order_index",
        (skill_id,),
    )
    lesson_topics = "\n".join(
        f"- {l['topic']} ({'completed' if l['status'] == 'completed' else 'available'})"
        for l in lessons
    )

    submission_type = _infer_submission_type(dict(skill))
    brief = tutor.generate_project_brief(
        skill_name=skill["name"],
        curriculum_overview=curriculum_overview,
        lesson_topics=lesson_topics,
        submission_type=submission_type,
    )
    # Ensure submission_type is always present (AI may omit it)
    brief.setdefault("submission_type", submission_type)

    project_id = execute(
        "INSERT INTO skill_projects (skill_id, description_json) VALUES (?, ?)",
        (skill_id, json.dumps(brief)),
    )
    return {"id": project_id, **brief}


def submit_project(user_id: int, project_id: int, submission: str) -> dict:
    project = query_one("SELECT * FROM skill_projects WHERE id = ?", (project_id,))
    if not project:
        raise ValueError("Project not found")

    skill = query_one("SELECT * FROM skills WHERE id = ?", (project["skill_id"],))
    brief = json.loads(project["description_json"])
    requirements_text = "\n".join(f"- {r}" for r in brief.get("requirements", []))

    result = tutor.evaluate_project(
        skill_name=skill["name"] if skill else "Unknown",
        project_title=brief.get("title", ""),
        project_description=brief.get("description", ""),
        requirements=requirements_text,
        evaluation_criteria=brief.get("evaluation_criteria", ""),
        submission=submission,
    )

    passed = result.get("passed", False)
    xp_earned = 0

    prior_pass = query_one(
        "SELECT id FROM skill_project_submissions WHERE user_id = ? AND project_id = ? AND passed = 1",
        (user_id, project_id),
    )
    if passed and not prior_pass:
        from app.services.gamification import add_xp, update_streak, XP_PROJECT_PASS
        add_xp(user_id, XP_PROJECT_PASS)
        update_streak(user_id)
        xp_earned = XP_PROJECT_PASS

    execute(
        """INSERT INTO skill_project_submissions
           (user_id, project_id, submission, feedback_json, xp_earned, passed)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, project_id, submission, json.dumps(result), xp_earned, int(passed)),
    )

    return {
        "passed": passed,
        "xp_earned": xp_earned,
        "feedback": result.get("feedback", ""),
        "strengths": result.get("strengths", []),
        "suggestions": result.get("suggestions", []),
        "areas_for_improvement": result.get("areas_for_improvement", []),
        "score": result.get("score", 0),
    }


def get_submission_history(user_id: int, project_id: int) -> list[dict]:
    rows = query(
        """SELECT id, passed, xp_earned, feedback_json, completed_at
           FROM skill_project_submissions
           WHERE user_id = ? AND project_id = ?
           ORDER BY completed_at DESC""",
        (user_id, project_id),
    )
    return [dict(r) for r in rows]
