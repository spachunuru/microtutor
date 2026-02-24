from fastapi import APIRouter, HTTPException
from app.models import ProjectSubmitRequest
from app.services import project_service

router = APIRouter(prefix="/api")

USER_ID = 1


@router.get("/skills/{skill_id}/project")
def get_project(skill_id: int):
    try:
        return project_service.get_or_generate_project(skill_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate project: {e}")


@router.post("/projects/{project_id}/submit")
def submit_project(project_id: int, req: ProjectSubmitRequest):
    try:
        return project_service.submit_project(USER_ID, project_id, req.submission)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate submission: {e}")


@router.get("/projects/{project_id}/submissions")
def get_submissions(project_id: int):
    return project_service.get_submission_history(USER_ID, project_id)
