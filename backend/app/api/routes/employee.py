from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func

from app.api.deps import CurrentUser, DbSession, require_employee
from app.models import Bar, BarNightStock, BarNightSummary, BartenderCash, Event, EventNight, NightBarAssignment, Product, ProductCategory, User
from app.schemas.operations import BarRead, EmployeeDashboard, EventRead, NightBarAssignmentRead

router = APIRouter(prefix="/employee", tags=["employee"], dependencies=[Depends(require_employee)])


def latest_assignment(db: DbSession, user_id: int, event_id: int | None = None) -> NightBarAssignment | None:
    query = (
        db.query(NightBarAssignment)
        .join(EventNight, EventNight.id == NightBarAssignment.event_night_id)
        .join(Event, Event.id == EventNight.event_id)
        .filter(NightBarAssignment.user_id == user_id)
        .order_by((EventNight.status == "active").desc(), EventNight.date.desc(), NightBarAssignment.id.desc())
    )
    if event_id:
        query = query.filter(Event.id == event_id)
    return query.first()


@router.get("/dashboard", response_model=EmployeeDashboard)
def dashboard(db: DbSession, current_user: CurrentUser):
    assignment = latest_assignment(db, current_user.id)
    if not assignment:
        return EmployeeDashboard(assignment=None, bar=None, event=None, prices=[], contribution=Decimal(0))

    bar = db.get(Bar, assignment.bar_id)
    night = db.get(EventNight, assignment.event_night_id)
    event = db.get(Event, night.event_id) if night else None
    responsible = db.get(User, bar.responsible_user_id) if bar else None
    previous_assignment = (
        db.query(NightBarAssignment)
        .join(EventNight, EventNight.id == NightBarAssignment.event_night_id)
        .filter(EventNight.event_id == night.event_id, NightBarAssignment.user_id == current_user.id, NightBarAssignment.id < assignment.id)
        .order_by(NightBarAssignment.id.desc())
        .first()
        if night
        else None
    )
    reassignment_notice = None
    if previous_assignment and previous_assignment.bar_id != assignment.bar_id and bar:
        previous_bar = db.get(Bar, previous_assignment.bar_id)
        reassignment_notice = f"Réaffecté de {previous_bar.name if previous_bar else 'un autre bar'} vers {bar.name}."

    price_rows = (
        db.query(BarNightStock, Product, ProductCategory)
        .join(Product, Product.id == BarNightStock.product_id)
        .join(ProductCategory, ProductCategory.id == Product.category_id)
        .filter(BarNightStock.event_night_id == assignment.event_night_id, BarNightStock.bar_id == assignment.bar_id)
        .order_by(ProductCategory.name, Product.name)
        .all()
        if event
        else []
    )
    cash = (
        db.query(BartenderCash)
        .filter(BartenderCash.event_night_id == assignment.event_night_id, BartenderCash.bar_id == assignment.bar_id, BartenderCash.user_id == current_user.id)
        .first()
    )
    bar_summary = db.query(BarNightSummary).filter(BarNightSummary.event_night_id == assignment.event_night_id, BarNightSummary.bar_id == assignment.bar_id).first()
    contribution = cash.cash_collected if cash else Decimal(0)
    units_sold = Decimal(0)
    contribution_pct = ((contribution / bar_summary.total_cash_collected) * Decimal(100)).quantize(Decimal("0.01")) if bar_summary and bar_summary.total_cash_collected else Decimal(0)

    return EmployeeDashboard(
        assignment=NightBarAssignmentRead.model_validate(assignment),
        bar=BarRead.model_validate(bar) if bar else None,
        event=EventRead.model_validate(event) if event else None,
        responsible_person=responsible.full_name if responsible else None,
        prices=[
            {
                "product_id": event_stock.product_id,
                "product_name": product.name,
                "category_name": category.name,
                "unit": product.unit,
                "price": event_stock.selling_price,
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
    cash = (
        db.query(BartenderCash)
        .filter(BartenderCash.event_night_id == assignment.event_night_id, BartenderCash.bar_id == assignment.bar_id, BartenderCash.user_id == current_user.id)
        .first()
    )
    bar_total = (
        db.query(func.coalesce(func.sum(BartenderCash.cash_collected), 0))
        .filter(BartenderCash.event_night_id == assignment.event_night_id, BartenderCash.bar_id == assignment.bar_id)
        .scalar()
    )
    return {
        "event_id": event_id,
        "employee_id": current_user.id,
        "bar_id": assignment.bar_id,
        "total": cash.cash_collected if cash else Decimal(0),
        "units_sold": Decimal(0),
        "contribution_pct": ((cash.cash_collected / Decimal(bar_total or 0)) * Decimal(100)).quantize(Decimal("0.01")) if cash and Decimal(bar_total or 0) else Decimal(0),
        "bar_total": Decimal(bar_total or 0),
        "items": [],
    }
