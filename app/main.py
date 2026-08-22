import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import Base, engine

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOADS_DIR = BASE_DIR / "uploads"

# Make sure uploads directory exists
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# DATABASE MODELS
# ============================================================

# Import models BEFORE create_all()
from app.models.user import User
from app.models.member import Member


# ============================================================
# DATABASE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# DEFAULT ADMIN
# ============================================================

from app.init_admin import create_default_admin

create_default_admin()


# ============================================================
# ROUTERS
# ============================================================

from app.api.routes.auth import router as auth_router
from app.api.routes.member import router as member_router
from app.api.routes.admin import router as admin_router


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Youth Political Awareness & Development Network API",
    description="YPADN Membership Management API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")

frontend_origins = [
    origin.strip()
    for origin in frontend_origins
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,

    allow_origins=frontend_origins,

    # Allows Vercel preview/production deployments
    allow_origin_regex=r"https://.*\.vercel\.app",

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# STATIC FILES
# ============================================================

# Public URL:
#
# https://your-backend.railway.app/uploads/filename.jpg
#
# Local:
#
# http://localhost:8000/uploads/filename.jpg

app.mount(
    "/uploads",
    StaticFiles(
        directory=str(UPLOADS_DIR)
    ),
    name="uploads",
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)

app.include_router(member_router)

app.include_router(admin_router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": (
            "Youth Political Awareness & Development "
            "Network API Running"
        ),
        "version": "1.0.0",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ypadn-backend",
    }


# ============================================================
# UPLOADS HEALTH CHECK
# ============================================================

@app.get("/uploads-health")
def uploads_health():
    return {
        "success": True,
        "uploads_directory": str(UPLOADS_DIR),
        "exists": UPLOADS_DIR.exists(),
    }