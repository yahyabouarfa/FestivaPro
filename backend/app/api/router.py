from fastapi import APIRouter

from app.api.routes import admin, auth, employee, reports

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(reports.router)
api_router.include_router(employee.router)
