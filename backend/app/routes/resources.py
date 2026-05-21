from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models import domain as models
from app.models.domain import User
from app.repositories.crud import CRUDRepository
from app.schemas import domain as schemas
from app.services.domain_service import DomainService

router = APIRouter(tags=["resources"], dependencies=[Depends(get_current_user)])


def add_crud_routes(*, path: str, entity: str, model: type, create_schema: type, update_schema: type, read_schema: type) -> None:
    service = DomainService(entity, CRUDRepository(model))

    def list_items(offset: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[Any]:
        return service.list(db, offset=offset, limit=limit)

    def get_item(item_id: int, db: Session = Depends(get_db)) -> Any:
        return service.get_or_404(db, item_id)

    def create_item(payload: Any = Body(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Any:
        return service.create(db, payload, user)

    def update_item(item_id: int, payload: Any = Body(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Any:
        return service.update(db, item_id, payload, user)

    def delete_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, bool]:
        service.delete(db, item_id, user)
        return {"deleted": True}

    create_item.__annotations__["payload"] = create_schema
    update_item.__annotations__["payload"] = update_schema
    router.add_api_route(path, list_items, methods=["GET"], response_model=list[read_schema])
    router.add_api_route(f"{path}/{{item_id}}", get_item, methods=["GET"], response_model=read_schema)
    router.add_api_route(path, create_item, methods=["POST"], response_model=read_schema, status_code=status.HTTP_201_CREATED)
    router.add_api_route(f"{path}/{{item_id}}", update_item, methods=["PATCH"], response_model=read_schema)
    router.add_api_route(f"{path}/{{item_id}}", delete_item, methods=["DELETE"])


add_crud_routes(path="/events", entity="event", model=models.Event, create_schema=schemas.EventCreate, update_schema=schemas.EventUpdate, read_schema=schemas.EventRead)
add_crud_routes(path="/bars", entity="bar", model=models.Bar, create_schema=schemas.BarCreate, update_schema=schemas.BarUpdate, read_schema=schemas.BarRead)
add_crud_routes(path="/employees", entity="employee", model=models.Employee, create_schema=schemas.EmployeeCreate, update_schema=schemas.EmployeeUpdate, read_schema=schemas.EmployeeRead)
add_crud_routes(path="/stock", entity="stock_item", model=models.StockItem, create_schema=schemas.StockItemCreate, update_schema=schemas.StockItemUpdate, read_schema=schemas.StockItemRead)
add_crud_routes(path="/equipment", entity="equipment_item", model=models.EquipmentItem, create_schema=schemas.EquipmentItemCreate, update_schema=schemas.EquipmentItemUpdate, read_schema=schemas.EquipmentItemRead)
add_crud_routes(path="/salaries", entity="salary", model=models.Salary, create_schema=schemas.SalaryCreate, update_schema=schemas.SalaryUpdate, read_schema=schemas.SalaryRead)
add_crud_routes(path="/contributions", entity="bartender_contribution", model=models.BartenderContribution, create_schema=schemas.BartenderContributionCreate, update_schema=schemas.BartenderContributionUpdate, read_schema=schemas.BartenderContributionRead)
add_crud_routes(path="/profits", entity="profit_entry", model=models.ProfitEntry, create_schema=schemas.ProfitEntryCreate, update_schema=schemas.ProfitEntryUpdate, read_schema=schemas.ProfitEntryRead)
add_crud_routes(path="/night-management", entity="night_log", model=models.NightLog, create_schema=schemas.NightLogCreate, update_schema=schemas.NightLogUpdate, read_schema=schemas.NightLogRead)
add_crud_routes(path="/reports", entity="report", model=models.Report, create_schema=schemas.ReportCreate, update_schema=schemas.ReportUpdate, read_schema=schemas.ReportRead)
add_crud_routes(path="/notifications", entity="notification", model=models.Notification, create_schema=schemas.NotificationCreate, update_schema=schemas.NotificationUpdate, read_schema=schemas.NotificationRead)


@router.get("/audit-logs", response_model=list[schemas.AuditLogRead])
def list_audit_logs(offset: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[Any]:
    return CRUDRepository(models.AuditLog).list(db, offset=offset, limit=min(limit, 250))


@router.delete("/audit-logs/{item_id}", status_code=status.HTTP_403_FORBIDDEN)
def audit_delete_forbidden(item_id: int) -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Audit logs are immutable")
