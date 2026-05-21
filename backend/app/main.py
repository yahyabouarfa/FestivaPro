from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.session import SessionLocal
from app.middleware.audit import RequestIdMiddleware
from app.routes import auth, dashboard, health, resources
from app.services.auth_service import ensure_default_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if not settings.testing:
        db = SessionLocal()
        try:
            ensure_default_admin(db)
        finally:
            db.close()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RequestIdMiddleware)
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(resources.router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "FestivaPro Event Management API"}
