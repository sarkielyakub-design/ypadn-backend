import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import Base, engine

# Import models BEFORE create_all()
from app.models.user import User
from app.models.member import Member

# Create tables
Base.metadata.create_all(bind=engine)

# Create default admin
from app.init_admin import create_default_admin
create_default_admin()

# Import routers
from app.api.routes.auth import router as auth_router
from app.api.routes.member import router as member_router
from app.api.routes.admin import router as admin_router

app = FastAPI(
    title="Youth Political Awareness & Development Network API",
    version="1.0.0"
)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(","),
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# STATIC FILES
# =========================
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

# =========================
# ROUTERS
# =========================
app.include_router(auth_router)
app.include_router(member_router)
app.include_router(admin_router)

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {
        "success": True,
        "message": "Youth Political Awareness & Development Network API Running"
    }

# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }