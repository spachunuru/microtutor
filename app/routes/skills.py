from fastapi import APIRouter
from app.models import SkillPreviewRequest, SkillCreateRequest
from app.services import skill_service

router = APIRouter(prefix="/api")


@router.post("/skills/preview")
def preview_skill(req: SkillPreviewRequest):
    return skill_service.preview_curriculum(req.name)


@router.post("/skills")
def create_skill(req: SkillCreateRequest):
    return skill_service.create_skill(1, req.name, req.description, req.curriculum)


@router.get("/skills")
def list_skills():
    return skill_service.get_skills(1)


@router.get("/skills/{skill_id}")
def get_skill(skill_id: int):
    return skill_service.get_skill_detail(skill_id)
