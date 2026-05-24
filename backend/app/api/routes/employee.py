from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.api.deps import CurrentUser, DbSession, require_employee
from app.models import Bar, BarAssignment, Event, EventStock, Product, ProductCategory
from app.schemas.operations import AssignmentRead, BarRead, EmployeeDashboard, EventRead

router = APIRouter(prefix="/employee", tags=["employee"], dependencies=[Depends(require_employee)])


@router.get("/dashboard", response_model=EmployeeDashboard)
def dashboard(db: DbSession, current_user: CurrentUser):
    assignment = (
        db.query(BarAssignment)
        .join(Bar, Bar.id == BarAssignment.bar_id)
        .join(Event, Event.id == Bar.event_id)
        .filter(BarAssignment.user_id == current_user.id)
        .order_by(Event.event_date.desc(), Event.start_time.desc())
        .first()
    )
    if not assignment:
        return EmployeeDashboard(assignment=None, bar=None, event=None, prices=[], contribution=Decimal(0))

    bar = db.get(Bar, assignment.bar_id)
    event = db.get(Event, bar.event_id) if bar else None
    price_rows = (
        db.query(EventStock, Product, ProductCategory)
        .join(Product, Product.id == EventStock.product_id)
        .join(ProductCategory, ProductCategory.id == Product.category_id)
        .filter(EventStock.event_id == event.id)
        .order_by(ProductCategory.name, Product.name)
        .all()
        if event
        else []
    )
    contribution = db.execute(
        text("SELECT COALESCE(SUM(revenue), 0) FROM bar_stock_financials WHERE bar_id = :bar_id"),
        {"bar_id": assignment.bar_id},
    ).scalar()
    return EmployeeDashboard(
        assignment=AssignmentRead.model_validate(assignment),
        bar=BarRead.model_validate(bar) if bar else None,
        event=EventRead.model_validate(event) if event else None,
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
        contribution=Decimal(contribution or 0),
    )


@router.get("/contribution")
def contribution(db: DbSession, current_user: CurrentUser, event_id: int):
    assignment = (
        db.query(BarAssignment)
        .join(Bar, Bar.id == BarAssignment.bar_id)
        .filter(BarAssignment.user_id == current_user.id, Bar.event_id == event_id)
        .first()
    )
    if not assignment:
        return {"event_id": event_id, "employee_id": current_user.id, "total": Decimal(0), "items": []}
    rows = db.execute(
        text(
            """
            SELECT product_id, quantity_sold, revenue
            FROM bar_stock_financials
            WHERE bar_id = :bar_id
            ORDER BY product_id
            """
        ),
        {"bar_id": assignment.bar_id},
    ).mappings().all()
    total = sum(Decimal(row["revenue"] or 0) for row in rows)
    return {
        "event_id": event_id,
        "employee_id": current_user.id,
        "total": total,
        "items": [{"product_id": row["product_id"], "quantity": row["quantity_sold"], "revenue": row["revenue"]} for row in rows],
    }
