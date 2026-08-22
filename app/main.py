import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db.session import Base, engine


# ============================================================
# PROJECT PATHS
# ============================================================

# main.py:
#
# project/
# ├── app/
# │   └── main.py
# ├── uploads/
# │   ├── passports/
# │   ├── cards/
# │   └── qr/
#
# Therefore:
#
# Path(__file__).resolve().parent.parent
#
# points to the project root.
#
BASE_DIR = Path(__file__).resolve().parent.parent

UPLOADS_DIR = BASE_DIR / "uploads"
PASSPORTS_DIR = UPLOADS_DIR / "passports"
CARDS_DIR = UPLOADS_DIR / "cards"
QR_DIR = UPLOADS_DIR / "qr"


# ============================================================
# CREATE DIRECTORIES
# ============================================================

for directory in (
    UPLOADS_DIR,
    PASSPORTS_DIR,
    CARDS_DIR,
    QR_DIR,
):
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# PUBLIC BACKEND URL
# ============================================================

# Railway:
#
# BACKEND_URL=https://ypadn-backend-production.up.railway.app
#
# Local:
#
# BACKEND_URL=http://localhost:8000
#
BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000",
).strip().rstrip("/")


# ============================================================
# DATABASE MODELS
# ============================================================

# IMPORTANT:
# Import models before create_all()

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
# STORE APPLICATION CONFIG
# ============================================================

app.state.base_dir = BASE_DIR
app.state.uploads_dir = UPLOADS_DIR
app.state.passports_dir = PASSPORTS_DIR
app.state.cards_dir = CARDS_DIR
app.state.qr_dir = QR_DIR
app.state.backend_url = BACKEND_URL


# ============================================================
# CORS
# ============================================================

frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    (
        "http://localhost:5173,"
        "http://localhost:3000,"
        "https://ypadn.vercel.app"
    ),
).split(",")

frontend_origins = [
    origin.strip().rstrip("/")
    for origin in frontend_origins
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,

    # Vercel preview deployments
    allow_origin_regex=r"https://.*\.vercel\.app",

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATIC UPLOAD FILES
# ============================================================

# ============================================================
# IMPORTANT
# ============================================================
#
# Physical filesystem:
#
# /app/uploads/passports/YPADN-000007.jpg
#
# Public URL:
#
# /uploads/passports/YPADN-000007.jpg
#
# Full Railway URL:
#
# https://ypadn-backend-production.up.railway.app/
# uploads/passports/YPADN-000007.jpg
#
# NEVER expose:
#
# /app/uploads/...
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
        "backend_url": BACKEND_URL,
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

        "backend_url": BACKEND_URL,

        "base_directory": str(
            BASE_DIR
        ),

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
    Debug endpoint.

    Shows files physically present inside
    the Railway container.

    Do NOT use this endpoint from the frontend.
    """

    passports = []
    cards = []
    qr_codes = []

    # --------------------------------------------------------
    # PASSPORTS
    # --------------------------------------------------------

    if PASSPORTS_DIR.exists():

        passports = sorted(
            [
                file.name
                for file in PASSPORTS_DIR.iterdir()
                if file.is_file()
            ]
        )

    # --------------------------------------------------------
    # CARDS
    # --------------------------------------------------------

    if CARDS_DIR.exists():

        cards = sorted(
            [
                file.name
                for file in CARDS_DIR.iterdir()
                if file.is_file()
            ]
        )

    # --------------------------------------------------------
    # QR CODES
    # --------------------------------------------------------

    if QR_DIR.exists():

        qr_codes = sorted(
            [
                file.name
                for file in QR_DIR.iterdir()
                if file.is_file()
            ]
        )

    # --------------------------------------------------------
    # PUBLIC URLS
    # --------------------------------------------------------

    passport_urls = [
        f"{BACKEND_URL}/uploads/passports/{filename}"
        for filename in passports
    ]

    card_urls = [
        f"{BACKEND_URL}/uploads/cards/{filename}"
        for filename in cards
    ]

    qr_urls = [
        f"{BACKEND_URL}/uploads/qr/{filename}"
        for filename in qr_codes
    ]

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "success": True,

        "backend_url": BACKEND_URL,

        "base_directory": str(
            BASE_DIR
        ),

        "uploads_directory": str(
            UPLOADS_DIR
        ),

        "passports": passports,

        "cards": cards,

        "qr_codes": qr_codes,

        "public_urls": {
            "passports": passport_urls,
            "cards": card_urls,
            "qr_codes": qr_urls,
        },

        "counts": {
            "passports": len(passports),
            "cards": len(cards),
            "qr_codes": len(qr_codes),
        },
    }


# ============================================================
# FILE TEST ENDPOINT
# ============================================================

@app.get("/uploads-test")
def uploads_test():
    """
    Quick test confirming that the upload directories
    are available to FastAPI.
    """

    return {
        "success": True,

        "message": "Upload system is available.",

        "directories": {
            "uploads": str(UPLOADS_DIR),
            "passports": str(PASSPORTS_DIR),
            "cards": str(CARDS_DIR),
            "qr": str(QR_DIR),
        },

        "public_paths": {
            "passports": "/uploads/passports/",
            "cards": "/uploads/cards/",
            "qr": "/uploads/qr/",
        },
    }