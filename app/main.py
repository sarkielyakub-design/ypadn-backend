import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import Base, engine


# ============================================================
# PATHS
# ============================================================

# Project root
#
# If this file is:
#
# project/
# ├── app/
# │   └── main.py
# └── uploads/
#
# then parent.parent points to project/
#
BASE_DIR = Path(__file__).resolve().parent.parent

UPLOADS_DIR = BASE_DIR / "uploads"

PASSPORTS_DIR = UPLOADS_DIR / "passports"
CARDS_DIR = UPLOADS_DIR / "cards"
QR_DIR = UPLOADS_DIR / "qr"


# ============================================================
# CREATE UPLOAD DIRECTORIES
# ============================================================

UPLOADS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

PASSPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

CARDS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

QR_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# DATABASE MODELS
# ============================================================

# IMPORTANT:
# Import models BEFORE create_all()

from app.models.user import User
from app.models.member import Member


# ============================================================
# DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)


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
    title=(
        "Youth Political Awareness & "
        "Development Network API"
    ),
    description=(
        "YPADN Membership Management API"
    ),
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

frontend_origins = [
    origin.strip()
    for origin in frontend_origins
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,

    allow_origins=frontend_origins,

    # Allow Vercel deployments
    allow_origin_regex=(
        r"https://.*\.vercel\.app"
    ),

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# STATIC FILES
# ============================================================

# ============================================================
# PUBLIC UPLOAD URLS
# ============================================================
#
# Filesystem:
#
# /app/uploads/passports/YPADN-000007.jpg
#
# Public URL:
#
# /uploads/passports/YPADN-000007.jpg
#
# Therefore:
#
# https://your-backend.railway.app/
# uploads/passports/YPADN-000007.jpg
#
# ============================================================

app.mount(
    "/uploads",
    StaticFiles(
        directory=str(UPLOADS_DIR),
        check_dir=True,
    ),
    name="uploads",
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    auth_router
)

app.include_router(
    member_router
)

app.include_router(
    admin_router
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": (
            "Youth Political Awareness & "
            "Development Network API Running"
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

        "uploads_directory": str(
            UPLOADS_DIR
        ),

        "uploads_exists": (
            UPLOADS_DIR.exists()
        ),

        "passports_directory": str(
            PASSPORTS_DIR
        ),

        "passports_exists": (
            PASSPORTS_DIR.exists()
        ),

        "cards_directory": str(
            CARDS_DIR
        ),

        "cards_exists": (
            CARDS_DIR.exists()
        ),

        "qr_directory": str(
            QR_DIR
        ),

        "qr_exists": (
            QR_DIR.exists()
        ),
    }


# ============================================================
# DEBUG UPLOADS
# ============================================================

@app.get("/uploads-debug")
def uploads_debug():
    """
    Debug endpoint to verify files actually exist
    inside the Railway container.

    This should NOT be used by the frontend.
    """

    passports = []

    if PASSPORTS_DIR.exists():

        passports = [
            file.name
            for file in PASSPORTS_DIR.iterdir()
            if file.is_file()
        ]

    cards = []

    if CARDS_DIR.exists():

        cards = [
            file.name
            for file in CARDS_DIR.iterdir()
            if file.is_file()
        ]

    qr_codes = []

    if QR_DIR.exists():

        qr_codes = [
            file.name
            for file in QR_DIR.iterdir()
            if file.is_file()
        ]

    return {
        "success": True,

        "base_directory": str(
            BASE_DIR
        ),

        "uploads_directory": str(
            UPLOADS_DIR
        ),

        "passports": passports,

        "cards": cards,

        "qr_codes": qr_codes,

        "counts": {
            "passports": len(passports),
            "cards": len(cards),
            "qr_codes": len(qr_codes),
        },
    }