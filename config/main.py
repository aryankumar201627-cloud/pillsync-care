from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from apps.database import engine
import apps.models as models
from apps.auth_routes import router as auth_router
from apps.medicine_routes import router as medicine_router
from apps.adherence_routes import router as adherence_router
from apps.scheduler import scheduler, check_due_medicines

# Create database tables automatically
models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to handle startup and shutdown events.
    Starts the AsyncIOScheduler background job on startup and shuts it down on exit.
    """
    # Register check_due_medicines background job to run every 60 seconds
    scheduler.add_job(
        check_due_medicines,
        "interval",
        seconds=60,
        id="check_due_medicines",
        replace_existing=True
    )
    scheduler.start()
    yield
    # Graceful shutdown of scheduler
    scheduler.shutdown(wait=False)

import os
from apps.dependencies import get_current_user
from apps.schemas import UserOut

app = FastAPI(
    title="PillSync Backend",
    description="API Gateway for Medicine Reminder & Medication Tracking Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
# Note: Browsers reject wildcard allow_origins=["*"] when allow_credentials=True.
# Explicit origins must be provided.
allowed_origins = [
    "https://pillsync-med.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Allow additional frontend URLs from environment variables if specified
env_frontend_url = os.getenv("FRONTEND_URL")
if env_frontend_url:
    for url in env_frontend_url.split(","):
        cleaned = url.strip().rstrip("/")
        if cleaned and cleaned not in allowed_origins:
            allowed_origins.append(cleaned)

env_cors_origins = os.getenv("CORS_ORIGINS")
if env_cors_origins:
    for url in env_cors_origins.split(","):
        cleaned = url.strip().rstrip("/")
        if cleaned and cleaned not in allowed_origins:
            allowed_origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers at root
app.include_router(auth_router)
app.include_router(medicine_router)
app.include_router(adherence_router)

# Also mount routers with /api/v1 prefix for client compatibility
app.include_router(auth_router, prefix="/api/v1")
app.include_router(medicine_router, prefix="/api/v1")
app.include_router(adherence_router, prefix="/api/v1")

# User profile aliases so /users/me and /api/v1/users/me both resolve smoothly
@app.get("/users/me", response_model=UserOut, tags=["Users"])
@app.get("/users/me/", response_model=UserOut, tags=["Users"])
@app.get("/api/v1/users/me", response_model=UserOut, tags=["Users"])
@app.get("/api/v1/users/me/", response_model=UserOut, tags=["Users"])
def get_current_user_profile_alias(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/")
def health_check():
    return {"status": "online", "message": "PillSync FastAPI Server is running smoothly!"}
