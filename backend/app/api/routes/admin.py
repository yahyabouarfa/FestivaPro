from decimal import Decimal
from random import shuffle
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.api.deps import DbSession, require_admin
from app.core.security import hash_password
from app.models import (
    Bar,
    BarStock,
    Event,
    EventProductPrice,
    Product,
    Sale,
    StaffAssignment,
    StockMovement,
    User,
)
from app.schemas.common import ApiMessage, MoneySummary
from app.schemas.operations import (
    AssignmentCreate,
    AssignmentRead,
    BarCreate,
    BarRead,
    BarUpdate,
    EventCreate,
    EventRead,
    EventUpdate,
    PriceRead,
    PriceUpsert,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    RandomAssignmentRequest,
    SaleCreate,
    SaleRead,
    StockMovementCreate,
    StockMovementRead,
    StockRead,
    StockUpsert,
)
from app.schemas.users import UserCreate, UserRead, UserUpdate

AdminUser = Annotated[User, Depends(require_admin)]
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def commit_or_409(db: DbSession) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A record with these unique values already exists.") from exc


def get_or_404(db: DbSession, model: type, record_id: int):
    record = db.get(model, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found.")
    return record


def apply_updates(record, payload) -> None:
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "password":
            setattr(record, "hashed_password", hash_password(value))
        else:
            setattr(record, field, value)


@router.get("/users", response_model=list[UserRead])
def list_users(db: DbSession, _: AdminUser, role: str | None = Query(default=None, pattern="^(admin|employee)$")):
    query = db.query(User).order_by(User.full_name)
    if role:
        query = query.filter(User.role == role)
    return query.all()


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DbSession, _: AdminUser):
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone_number=payload.phone_number,
        role=payload.role,
        hashed_password=hash_password(payload.password),
        is_active=payload.is_active,
    )
    db.add(user)
    commit_or_409(db)
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db: DbSession, _: AdminUser):
    user = get_or_404(db, User, user_id)
    apply_updates(user, payload)
    commit_or_409(db)
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", response_model=ApiMessage)
def delete_user(user_id: int, db: DbSession, current_user: AdminUser):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admins cannot delete their own account.")
    user = get_or_404(db, User, user_id)
    db.delete(user)
    commit_or_409(db)
    return ApiMessage(message="User deleted.")


@router.get("/events", response_model=list[EventRead])
def list_events(db: DbSession, _: AdminUser):
    return db.query(Event).order_by(Event.starts_at.desc()).all()


@router.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: DbSession, _: AdminUser):
    if payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Event end time must be after start time.")
    event = Event(**payload.model_dump())
    db.add(event)
    commit_or_409(db)
    db.refresh(event)
    return event


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(event_id: int, payload: EventUpdate, db: DbSession, _: AdminUser):
    event = get_or_404(db, Event, event_id)
    apply_updates(event, payload)
    if event.ends_at <= event.starts_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Event end time must be after start time.")
    commit_or_409(db)
    db.refresh(event)
    return event


@router.delete("/events/{event_id}", response_model=ApiMessage)
def delete_event(event_id: int, db: DbSession, _: AdminUser):
    event = get_or_404(db, Event, event_id)
    db.delete(event)
    commit_or_409(db)
    return ApiMessage(message="Event deleted.")


@router.get("/bars", response_model=list[BarRead])
def list_bars(db: DbSession, _: AdminUser, event_id: int | None = None):
    query = db.query(Bar).order_by(Bar.name)
    if event_id:
        query = query.filter(Bar.event_id == event_id)
    return query.all()


@router.post("/bars", response_model=BarRead, status_code=status.HTTP_201_CREATED)
def create_bar(payload: BarCreate, db: DbSession, _: AdminUser):
    get_or_404(db, Event, payload.event_id)
    bar = Bar(**payload.model_dump())
    db.add(bar)
    commit_or_409(db)
    db.refresh(bar)
    return bar


@router.patch("/bars/{bar_id}", response_model=BarRead)
def update_bar(bar_id: int, payload: BarUpdate, db: DbSession, _: AdminUser):
    bar = get_or_404(db, Bar, bar_id)
    if payload.event_id:
        get_or_404(db, Event, payload.event_id)
    apply_updates(bar, payload)
    commit_or_409(db)
    db.refresh(bar)
    return bar


@router.delete("/bars/{bar_id}", response_model=ApiMessage)
def delete_bar(bar_id: int, db: DbSession, _: AdminUser):
    bar = get_or_404(db, Bar, bar_id)
    db.delete(bar)
    commit_or_409(db)
    return ApiMessage(message="Bar deleted.")


@router.get("/products", response_model=list[ProductRead])
def list_products(db: DbSession, _: AdminUser):
    return db.query(Product).order_by(Product.name).all()


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: DbSession, _: AdminUser):
    product = Product(**payload.model_dump())
    db.add(product)
    commit_or_409(db)
    db.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: DbSession, _: AdminUser):
    product = get_or_404(db, Product, product_id)
    apply_updates(product, payload)
    commit_or_409(db)
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", response_model=ApiMessage)
def delete_product(product_id: int, db: DbSession, _: AdminUser):
    product = get_or_404(db, Product, product_id)
    db.delete(product)
    commit_or_409(db)
    return ApiMessage(message="Product deleted.")


@router.get("/prices", response_model=list[PriceRead])
def list_prices(db: DbSession, _: AdminUser, event_id: int | None = None):
    query = db.query(EventProductPrice).order_by(EventProductPrice.event_id.desc())
    if event_id:
        query = query.filter(EventProductPrice.event_id == event_id)
    return query.all()


@router.post("/prices", response_model=PriceRead)
def upsert_price(payload: PriceUpsert, db: DbSession, _: AdminUser):
    get_or_404(db, Event, payload.event_id)
    get_or_404(db, Product, payload.product_id)
    price = (
        db.query(EventProductPrice)
        .filter(EventProductPrice.event_id == payload.event_id, EventProductPrice.product_id == payload.product_id)
        .first()
    )
    if not price:
        price = EventProductPrice(**payload.model_dump())
        db.add(price)
    else:
        price.price = payload.price
        price.cost_price = payload.cost_price
    commit_or_409(db)
    db.refresh(price)
    return price


@router.get("/assignments", response_model=list[AssignmentRead])
def list_assignments(db: DbSession, _: AdminUser, event_id: int | None = None, user_id: int | None = None):
    query = db.query(StaffAssignment).order_by(StaffAssignment.created_at.desc())
    if event_id:
        query = query.filter(StaffAssignment.event_id == event_id)
    if user_id:
        query = query.filter(StaffAssignment.user_id == user_id)
    return query.all()


@router.post("/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment(payload: AssignmentCreate, db: DbSession, _: AdminUser):
    bar = get_or_404(db, Bar, payload.bar_id)
    user = get_or_404(db, User, payload.user_id)
    if bar.event_id != payload.event_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Bar does not belong to the selected event.")
    if user.role != "employee":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only employees can be assigned to bars.")
    assignment = (
        db.query(StaffAssignment)
        .filter(StaffAssignment.event_id == payload.event_id, StaffAssignment.user_id == payload.user_id)
        .first()
    )
    if not assignment:
        assignment = StaffAssignment(**payload.model_dump())
        db.add(assignment)
    else:
        assignment.bar_id = payload.bar_id
        assignment.shift_salary = payload.shift_salary
    commit_or_409(db)
    db.refresh(assignment)
    return assignment


@router.post("/assignments/random", response_model=list[AssignmentRead])
def random_assignments(payload: RandomAssignmentRequest, db: DbSession, _: AdminUser):
    get_or_404(db, Event, payload.event_id)
    bars = db.query(Bar).filter(Bar.event_id == payload.event_id).order_by(Bar.name).all()
    employees = db.query(User).filter(User.role == "employee", User.is_active.is_(True)).order_by(User.full_name).all()
    if not bars:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Create at least one bar before random assignment.")
    if not employees:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Create at least one active employee before random assignment.")
    shuffle(employees)
    saved: list[StaffAssignment] = []
    for index, employee in enumerate(employees):
        bar = bars[index % len(bars)]
        assignment = (
            db.query(StaffAssignment)
            .filter(StaffAssignment.event_id == payload.event_id, StaffAssignment.user_id == employee.id)
            .first()
        )
        if not assignment:
            assignment = StaffAssignment(event_id=payload.event_id, user_id=employee.id, bar_id=bar.id, shift_salary=payload.shift_salary)
            db.add(assignment)
        else:
            assignment.bar_id = bar.id
            assignment.shift_salary = payload.shift_salary
        saved.append(assignment)
    commit_or_409(db)
    return saved


@router.get("/stock", response_model=list[StockRead])
def list_stock(db: DbSession, _: AdminUser, bar_id: int | None = None):
    query = db.query(BarStock).order_by(BarStock.bar_id, BarStock.product_id)
    if bar_id:
        query = query.filter(BarStock.bar_id == bar_id)
    return query.all()


@router.post("/stock", response_model=StockRead)
def upsert_stock(payload: StockUpsert, db: DbSession, _: AdminUser):
    get_or_404(db, Bar, payload.bar_id)
    get_or_404(db, Product, payload.product_id)
    stock = db.query(BarStock).filter(BarStock.bar_id == payload.bar_id, BarStock.product_id == payload.product_id).first()
    if not stock:
        stock = BarStock(**payload.model_dump())
        db.add(stock)
    else:
        stock.opening_quantity = payload.opening_quantity
        stock.current_quantity = payload.current_quantity
    commit_or_409(db)
    db.refresh(stock)
    return stock


@router.post("/stock/movements", response_model=StockMovementRead, status_code=status.HTTP_201_CREATED)
def create_stock_movement(payload: StockMovementCreate, db: DbSession, current_user: AdminUser):
    stock = db.query(BarStock).filter(BarStock.bar_id == payload.bar_id, BarStock.product_id == payload.product_id).first()
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock item not found for this bar and product.")
    stock.current_quantity += payload.quantity_change
    movement = StockMovement(**payload.model_dump(), created_by_id=current_user.id)
    db.add(movement)
    commit_or_409(db)
    db.refresh(movement)
    return movement


@router.post("/sales", response_model=SaleRead, status_code=status.HTTP_201_CREATED)
def create_sale(payload: SaleCreate, db: DbSession, _: AdminUser):
    assignment = (
        db.query(StaffAssignment)
        .filter(StaffAssignment.event_id == payload.event_id, StaffAssignment.user_id == payload.employee_id, StaffAssignment.bar_id == payload.bar_id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Employee is not assigned to this bar for this event.")
    sale = Sale(**payload.model_dump())
    db.add(sale)
    stock = db.query(BarStock).filter(BarStock.bar_id == payload.bar_id, BarStock.product_id == payload.product_id).first()
    if stock:
        stock.current_quantity -= payload.quantity
    commit_or_409(db)
    db.refresh(sale)
    return sale


@router.get("/reports/summary", response_model=MoneySummary)
def financial_summary(db: DbSession, _: AdminUser, event_id: int):
    revenue = db.query(func.coalesce(func.sum(Sale.quantity * Sale.unit_price), 0)).filter(Sale.event_id == event_id).scalar()
    cost = (
        db.query(func.coalesce(func.sum(Sale.quantity * EventProductPrice.cost_price), 0))
        .join(EventProductPrice, (EventProductPrice.event_id == Sale.event_id) & (EventProductPrice.product_id == Sale.product_id))
        .filter(Sale.event_id == event_id)
        .scalar()
    )
    salaries = db.query(func.coalesce(func.sum(StaffAssignment.shift_salary), 0)).filter(StaffAssignment.event_id == event_id).scalar()
    revenue = Decimal(revenue or 0)
    cost = Decimal(cost or 0)
    salaries = Decimal(salaries or 0)
    return MoneySummary(revenue=revenue, cost=cost, salaries=salaries, profit=revenue - cost - salaries)
