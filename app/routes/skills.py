from fastapi import APIRouter, HTTPException
from app.models import SkillPreviewRequest, SkillCreateRequest
from app.services import skill_service

router = APIRouter(prefix="/api")


@router.post("/skills/preview")
def preview_skill(req: SkillPreviewRequest):
    try:
        return skill_service.preview_curriculum(req.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate curriculum: {e}")


@router.post("/skills")
def create_skill(req: SkillCreateRequest):
    return skill_service.create_skill(1, req.name, req.description, req.curriculum)


@router.get("/skills")
def list_skills():
    return skill_service.get_skills(1)


@router.get("/skills/{skill_id}")
def get_skill(skill_id: int):
    detail = skill_service.get_skill_detail(skill_id)
    if not detail["skill"]:
        raise HTTPException(status_code=404, detail="Skill not found")
    return detail


@router.post("/skills/{skill_id}/delete")
def delete_skill(skill_id: int):
    skill_service.delete_skill(skill_id)
    return {"status": "deleted"}
