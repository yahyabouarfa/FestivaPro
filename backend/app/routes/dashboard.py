from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.schemas.common import DashboardSummary
from app.services.analytics_service import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> dict:
    return get_dashboard_summary(db)
