from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func

from app.api.deps import CurrentUser, DbSession, require_employee
from app.models import Bar, Event, EventProductPrice, Product, Sale, StaffAssignment
from app.schemas.operations import BarRead, EmployeeDashboard, EventRead

router = APIRouter(prefix="/employee", tags=["employee"], dependencies=[Depends(require_employee)])


@router.get("/dashboard", response_model=EmployeeDashboard)
def dashboard(db: DbSession, current_user: CurrentUser):
    assignment = (
        db.query(StaffAssignment)
        .join(Event, Event.id == StaffAssignment.event_id)
        .filter(StaffAssignment.user_id == current_user.id)
        .order_by(Event.starts_at.desc())
        .first()
    )
    if not assignment:
        return EmployeeDashboard(assignment=None, bar=None, event=None, prices=[], contribution=Decimal(0))

    bar = db.get(Bar, assignment.bar_id)
    event = db.get(Event, assignment.event_id)
    price_rows = (
        db.query(EventProductPrice, Product)
        .join(Product, Product.id == EventProductPrice.product_id)
        .filter(EventProductPrice.event_id == assignment.event_id, Product.is_active.is_(True))
        .order_by(Product.name)
        .all()
    )
    contribution = (
        db.query(func.coalesce(func.sum(Sale.quantity * Sale.unit_price), 0))
        .filter(Sale.event_id == assignment.event_id, Sale.employee_id == current_user.id)
        .scalar()
    )
    return EmployeeDashboard(
        assignment=assignment,
        bar=BarRead.model_validate(bar) if bar else None,
        event=EventRead.model_validate(event) if event else None,
        prices=[
            {
                "product_id": price.product_id,
                "product_name": product.name,
                "sku": product.sku,
                "unit": product.unit,
                "price": price.price,
            }
            for price, product in price_rows
        ],
        contribution=Decimal(contribution or 0),
    )


@router.get("/contribution")
def contribution(db: DbSession, current_user: CurrentUser, event_id: int):
    rows = (
        db.query(Sale.product_id, func.sum(Sale.quantity).label("quantity"), func.sum(Sale.quantity * Sale.unit_price).label("revenue"))
        .filter(Sale.event_id == event_id, Sale.employee_id == current_user.id)
        .group_by(Sale.product_id)
        .all()
    )
    total = sum(Decimal(row.revenue or 0) for row in rows)
    return {
        "event_id": event_id,
        "employee_id": current_user.id,
        "total": total,
        "items": [{"product_id": row.product_id, "quantity": row.quantity, "revenue": row.revenue} for row in rows],
    }
