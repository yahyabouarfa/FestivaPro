from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.api.deps import DbSession, require_admin
from app.services.reporting import all_bars_report, full_event_report, per_bar_report, report_bundle

router = APIRouter(prefix="/admin/reports", tags=["reports"], dependencies=[Depends(require_admin)])


def file_response(report):
    return Response(
        content=report.data,
        media_type=report.content_type,
        headers={"Content-Disposition": f'attachment; filename="{report.filename}"'},
    )


def validate_file_type(file_type: str) -> str:
    if file_type not in {"pdf", "xlsx"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Report type must be pdf or xlsx.")
    return file_type


@router.get("/bar/{bar_id}/{file_type}")
def download_bar_report(bar_id: int, file_type: str, db: DbSession):
    return file_response(per_bar_report(db, bar_id, validate_file_type(file_type)))


@router.get("/event/{event_id}/bars/{file_type}")
def download_all_bars_report(event_id: int, file_type: str, db: DbSession):
    return file_response(all_bars_report(db, event_id, validate_file_type(file_type)))


@router.get("/event/{event_id}/full/{file_type}")
def download_full_event_report(event_id: int, file_type: str, db: DbSession):
    return file_response(full_event_report(db, event_id, validate_file_type(file_type)))


@router.get("/event/{event_id}/bundle")
def download_report_bundle(event_id: int, db: DbSession):
    return file_response(report_bundle(db, event_id))
