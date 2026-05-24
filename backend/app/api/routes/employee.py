from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func

from app.api.deps import CurrentUser, DbSession, require_employee
from app.models import Bar, BarStock, BartenderSale, Event, EventSalary, EventStock, Product, ProductCategory, User
from app.schemas.operations import AssignmentRead, BarRead, EmployeeDashboard, EventRead

router = APIRouter(prefix="/employee", tags=["employee"], dependencies=[Depends(require_employee)])


def latest_assignment(db: DbSession, user_id: int, event_id: int | None = None) -> EventSalary | None:
    query = (
        db.query(EventSalary)
        .join(Event, Event.id == EventSalary.event_id)
        .filter(EventSalary.user_id == user_id)
        .order_by(Event.event_date.desc(), Event.start_time.desc(), EventSalary.id.desc())
    )
    if event_id:
        query = query.filter(EventSalary.event_id == event_id)
    return query.first()


@router.get("/dashboard", response_model=EmployeeDashboard)
def dashboard(db: DbSession, current_user: CurrentUser):
    assignment = latest_assignment(db, current_user.id)
    if not assignment:
        return EmployeeDashboard(assignment=None, bar=None, event=None, prices=[], contribution=Decimal(0))

    bar = db.get(Bar, assignment.bar_id)
    event = db.get(Event, assignment.event_id)
    responsible = db.get(User, bar.responsible_user_id) if bar else None
    previous_assignment = (
        db.query(EventSalary)
        .filter(EventSalary.event_id == assignment.event_id, EventSalary.user_id == current_user.id, EventSalary.id < assignment.id)
        .order_by(EventSalary.id.desc())
        .first()
    )
    reassignment_notice = None
    if previous_assignment and previous_assignment.bar_id != assignment.bar_id and bar:
        previous_bar = db.get(Bar, previous_assignment.bar_id)
        reassignment_notice = f"Reassigned from {previous_bar.name if previous_bar else 'another bar'} to {bar.name}."

    price_rows = (
        db.query(EventStock, Product, ProductCategory)
        .join(Product, Product.id == EventStock.product_id)
        .join(ProductCategory, ProductCategory.id == Product.category_id)
        .join(BarStock, (BarStock.product_id == EventStock.product_id) & (BarStock.bar_id == assignment.bar_id))
        .filter(EventStock.event_id == assignment.event_id)
        .order_by(ProductCategory.name, Product.name)
        .all()
        if event
        else []
    )
    sale = (
        db.query(BartenderSale)
        .filter(BartenderSale.event_id == assignment.event_id, BartenderSale.bar_id == assignment.bar_id, BartenderSale.user_id == current_user.id)
        .first()
    )
    contribution = sale.sales_amount if sale else Decimal(0)
    units_sold = sale.units_sold if sale else Decimal(0)
    contribution_pct = sale.contribution_pct if sale else Decimal(0)

    return EmployeeDashboard(
        assignment=AssignmentRead.model_validate(assignment),
        bar=BarRead.model_validate(bar) if bar else None,
        event=EventRead.model_validate(event) if event else None,
        responsible_person=responsible.full_name if responsible else None,
        prices=[
            {
                "product_id": event_stock.product_id,
                "product_name": product.name,
                "category_name": category.name,
                "unit": product.unit,
                "price": event_stock.selling_price_per_unit,
            }
            for event_stock, product, category in price_rows
        ],
        contribution=contribution,
        units_sold=units_sold,
        contribution_pct=contribution_pct,
        reassignment_notice=reassignment_notice,
    )


@router.get("/contribution")
def contribution(db: DbSession, current_user: CurrentUser, event_id: int):
    assignment = latest_assignment(db, current_user.id, event_id)
    if not assignment:
        return {"event_id": event_id, "employee_id": current_user.id, "total": Decimal(0), "items": []}
    sale = (
        db.query(BartenderSale)
        .filter(BartenderSale.event_id == event_id, BartenderSale.bar_id == assignment.bar_id, BartenderSale.user_id == current_user.id)
        .first()
    )
    bar_total = (
        db.query(func.coalesce(func.sum(BarStock.quantity_sold * EventStock.selling_price_per_unit), 0))
        .join(Bar, Bar.id == BarStock.bar_id)
        .join(EventStock, (EventStock.event_id == Bar.event_id) & (EventStock.product_id == BarStock.product_id))
        .filter(Bar.event_id == event_id, BarStock.bar_id == assignment.bar_id)
        .scalar()
    )
    return {
        "event_id": event_id,
        "employee_id": current_user.id,
        "bar_id": assignment.bar_id,
        "total": sale.sales_amount if sale else Decimal(0),
        "units_sold": sale.units_sold if sale else Decimal(0),
        "contribution_pct": sale.contribution_pct if sale else Decimal(0),
        "bar_total": Decimal(bar_total or 0),
        "items": [],
    }
