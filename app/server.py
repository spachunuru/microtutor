from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import get_db
from app.routes import skills, lessons, quizzes, chat, review, progress, exercises, projects

app = FastAPI(title="MicroTutor", version="0.1.0")

STATIC_DIR = Path(__file__).parent.parent / "static"

# Register API routes
app.include_router(skills.router)
app.include_router(lessons.router)
app.include_router(quizzes.router)
app.include_router(chat.router)
app.include_router(review.router)
app.include_router(progress.router)
app.include_router(exercises.router)
app.include_router(projects.router)


@app.on_event("startup")
def startup():
    get_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/{path:path}")
def serve_spa(path: str):
    return FileResponse(str(STATIC_DIR / "index.html"))
