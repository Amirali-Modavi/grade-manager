from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.database import initialize_database
from backend.routes.students import router as students_router
from backend.routes.reports import router as reports_router

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Grade Manager API",
    description="Grade Manager with SQLite database storage",
    version="0.5.0",
    lifespan=lifespan,
)
app.include_router(students_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Grade Manager API is running with SQLite"}


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
