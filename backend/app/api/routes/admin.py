import json
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from random import shuffle
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import case, func, select, text
from sqlalchemy.exc import IntegrityError
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.api.deps import DbSession, require_admin
from app.core.security import hash_password
from app.models import (
    AuditLog,
    Bar,
    BarAssignment,
    BarNightStock,
    BarNightSummary,
    BartenderCash,
    BartenderSale,
    Event,
    EventNight,
    EventSalary,
    EventStock,
    NightBarAssignment,
    PdfReport,
    PriceHistory,
    Product,
    ProductCategory,
    ProfitSnapshot,
    User,
)
from app.schemas.common import ApiMessage, MoneySummary
from app.schemas.operations import (
    AssignmentCreate,
    AssignmentRead,
    AuditLogRead,
    BarCreate,
    BarFinancialSummary,
    BarNightStockRead,
    BarNightSummaryRead,
    BarRead,
    BarUpdate,
    BartenderCashRead,
    BartenderLeaderboardItem,
    BartenderSaleRead,
    BeginNightInput,
    EndOfNightInput,
    EndOfNightResult,
    EventComparisonItem,
    EventCreate,
    EventInsight,
    EventNightRead,
    EventRead,
    EventStockBalance,
    EventStockRead,
    EventStockUpsert,
    EventUpdate,
    LowStockAlert,
    NightAssignmentInput,
    NightBarAssignmentRead,
    OpeningStockInput,
    PdfReportRead,
    PriceHistoryRead,
    ProductCategoryCreate,
    ProductCategoryRead,
    ProductCreate,
    ProductRankingItem,
    ProductRead,
    ProductUpdate,
    ProfitSnapshotRead,
    RandomBarNightAssignmentRequest,
    RandomAssignmentRequest,
    WasteItem,
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
        elif field == "start_date":
            setattr(record, "event_date", value)
            setattr(record, "start_date", value)
        elif field == "total_nights_planned":
            setattr(record, "total_nights", value)
            setattr(record, "total_nights_planned", value)
        else:
            setattr(record, field, value)


def require_employee(db: DbSession, user_id: int) -> User:
    user = get_or_404(db, User, user_id)
    if user.role != "employee":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only employees can be assigned to bars.")
    return user


def require_event_open(event: Event) -> None:
    if event.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cet événement est clôturé. Aucune modification n’est autorisée.")


def event_for_bar(db: DbSession, bar: Bar) -> Event:
    return get_or_404(db, Event, bar.event_id)


def event_for_night(db: DbSession, night: EventNight) -> Event:
    return get_or_404(db, Event, night.event_id)


def log_audit(db: DbSession, user: User, action: str, entity_type: str, entity_id: int | None, details: dict | None = None) -> None:
    db.add(
        AuditLog(
            user_id=user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(details or {}, default=str),
        )
    )


def money(value) -> Decimal:
    return Decimal(value or 0)


def latest_assignment_ids(db: DbSession, event_id: int | None = None):
    query = db.query(func.max(EventSalary.id).label("id"))
    if event_id:
        query = query.filter(EventSalary.event_id == event_id)
    return query.group_by(EventSalary.event_id, EventSalary.user_id).subquery()


def current_assignment_query(db: DbSession, event_id: int | None = None, user_id: int | None = None):
    latest = latest_assignment_ids(db, event_id)
    query = db.query(EventSalary).join(latest, EventSalary.id == latest.c.id)
    if event_id:
        query = query.filter(EventSalary.event_id == event_id)
    if user_id:
        query = query.filter(EventSalary.user_id == user_id)
    return query


def validate_assignment(db: DbSession, event_id: int, bar_id: int, user_id: int) -> Bar:
    event = get_or_404(db, Event, event_id)
    if event.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Closed events cannot be reassigned.")
    bar = get_or_404(db, Bar, bar_id)
    if bar.event_id != event_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Bar does not belong to the selected event.")
    require_employee(db, user_id)
    return bar


def ensure_bar_assignment(db: DbSession, bar_id: int, user_id: int) -> BarAssignment:
    assignment = db.query(BarAssignment).filter(BarAssignment.bar_id == bar_id, BarAssignment.user_id == user_id).first()
    if not assignment:
        assignment = BarAssignment(bar_id=bar_id, user_id=user_id)
        db.add(assignment)
        db.flush()
    return assignment


def event_stock_drawn(db: DbSession, event_id: int, product_id: int, exclude_bar_id: int | None = None, exclude_night_id: int | None = None) -> Decimal:
    drawn_expr = case(
        (EventNight.night_number == 1, BarNightStock.qty_opening + BarNightStock.qty_top_up),
        else_=BarNightStock.qty_top_up,
    )
    query = (
        db.query(func.coalesce(func.sum(drawn_expr), 0))
        .join(EventNight, EventNight.id == BarNightStock.event_night_id)
        .join(Bar, Bar.id == BarNightStock.bar_id)
        .filter(Bar.event_id == event_id, BarNightStock.product_id == product_id)
    )
    if exclude_bar_id and exclude_night_id:
        query = query.filter(~((BarNightStock.bar_id == exclude_bar_id) & (BarNightStock.event_night_id == exclude_night_id)))
    return money(query.scalar())


def validate_night_can_open(db: DbSession, night: EventNight) -> None:
    if night.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Closed nights cannot be edited.")
    if night.night_number <= 1:
        return
    previous = (
        db.query(EventNight)
        .filter(EventNight.event_id == night.event_id, EventNight.night_number == night.night_number - 1)
        .first()
    )
    if not previous or previous.status != "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot open night N+1 before night N is closed.")


def snapshot_bar(db: DbSession, event_id: int, night_id: int, bar_id: int) -> ProfitSnapshot:
    summary = db.query(BarNightSummary).filter(BarNightSummary.event_night_id == night_id, BarNightSummary.bar_id == bar_id).first()
    if not summary:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot snapshot a bar before its end-of-night summary exists.")
    snapshot = ProfitSnapshot(
        event_id=event_id,
        event_night_id=night_id,
        bar_id=bar_id,
        expected_revenue=summary.expected_cash,
        actual_revenue=summary.total_cash_collected,
        expected_profit=summary.expected_profit,
        actual_profit=summary.gross_profit,
        staff_cost=summary.staff_cost,
        net_profit=summary.net_profit,
        snapshot_level="night",
    )
    db.add(snapshot)
    return snapshot


def snapshot_event(db: DbSession, event_id: int, night_id: int) -> ProfitSnapshot:
    summaries = (
        db.query(BarNightSummary)
        .join(EventNight, EventNight.id == BarNightSummary.event_night_id)
        .filter(EventNight.event_id == event_id, BarNightSummary.is_closed.is_(True))
        .all()
    )
    staff_cost = sum(money(row.staff_cost) for row in summaries)
    actual_revenue = sum(money(row.total_cash_collected) for row in summaries)
    actual_profit_before_staff = sum(money(row.gross_profit) for row in summaries)
    expected_revenue = sum(money(row.expected_cash) for row in summaries)
    expected_profit = sum(money(row.expected_profit) for row in summaries)
    snapshot = ProfitSnapshot(
        event_id=event_id,
        event_night_id=night_id,
        bar_id=None,
        expected_revenue=expected_revenue,
        actual_revenue=actual_revenue,
        expected_profit=expected_profit,
        actual_profit=actual_profit_before_staff,
        staff_cost=staff_cost,
        net_profit=actual_profit_before_staff - staff_cost,
        snapshot_level="event",
    )
    db.add(snapshot)
    return snapshot


def latest_event_snapshot(db: DbSession, event_id: int) -> ProfitSnapshot | None:
    return (
        db.query(ProfitSnapshot)
        .filter(ProfitSnapshot.event_id == event_id, ProfitSnapshot.snapshot_level == "event", ProfitSnapshot.bar_id.is_(None))
        .order_by(ProfitSnapshot.created_at.desc(), ProfitSnapshot.id.desc())
        .first()
    )


def event_money_summary(db: DbSession, event_id: int) -> MoneySummary:
    snapshot = latest_event_snapshot(db, event_id)
    if not snapshot:
        return MoneySummary(revenue=Decimal(0), cost=Decimal(0), salaries=Decimal(0), profit=Decimal(0))
    cost = money(snapshot.actual_revenue) - money(snapshot.actual_profit)
    return MoneySummary(revenue=snapshot.actual_revenue, cost=cost, salaries=snapshot.staff_cost, profit=snapshot.net_profit)


def safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value).strip("_")


def pdf_bytes(title: str, sections: list[tuple[str, list[str], list[list[object]]]]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = [Paragraph("<b>FestivaPro</b>", styles["Title"]), Paragraph(title, styles["Heading2"]), Spacer(1, 10)]
    for heading, headers, rows in sections:
        story.append(Paragraph(heading, styles["Heading3"]))
        table = Table([headers, *rows], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#171124")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d8d2e8")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f3ff")]),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.extend([table, Spacer(1, 12)])
    story.append(Paragraph("Responsable du bar : ____________________    Responsable du stock : ____________________", styles["Normal"]))
    story.append(Paragraph("Signature: ___________________________    Signature: ___________________________", styles["Normal"]))
    story.append(Paragraph("Date: ________________________________    Date: ________________________________", styles["Normal"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Ce rapport a été généré par FestivaPro et doit être vérifié et signé avant archivage.", styles["Italic"]))
    doc.build(story)
    return buffer.getvalue()


def generate_bar_pdf(db: DbSession, event: Event, night: EventNight, bar: Bar) -> PdfReport:
    responsible = db.get(User, bar.responsible_user_id)
    assignments = (
        db.query(NightBarAssignment, User)
        .join(User, User.id == NightBarAssignment.user_id)
        .filter(NightBarAssignment.event_night_id == night.id, NightBarAssignment.bar_id == bar.id)
        .order_by(NightBarAssignment.role.desc(), User.full_name)
        .all()
    )
    stock_rows = (
        db.query(BarNightStock, Product)
        .join(Product, Product.id == BarNightStock.product_id)
        .filter(BarNightStock.event_night_id == night.id, BarNightStock.bar_id == bar.id)
        .order_by(Product.name)
        .all()
    )
    cash_rows = {row.user_id: row for row in db.query(BartenderCash).filter(BartenderCash.event_night_id == night.id, BartenderCash.bar_id == bar.id).all()}
    summary = db.query(BarNightSummary).filter(BarNightSummary.event_night_id == night.id, BarNightSummary.bar_id == bar.id).first()
    staff = [[user.full_name, "responsable" if assignment.role == "responsible" else "employé", assignment.salary_amount, cash_rows.get(user.id).cash_collected if cash_rows.get(user.id) else Decimal(0)] for assignment, user in assignments]
    stock = [
        [
            product.name,
            item.qty_opening,
            item.qty_top_up,
            item.qty_closing or 0,
            item.qty_used,
            item.bought_price,
            money(item.qty_used) * money(item.bought_price),
            item.selling_price,
            money(item.qty_used) * money(item.selling_price),
        ]
        for item, product in stock_rows
    ]
    financial = [
        ["Cash attendu", summary.expected_cash if summary else 0],
        ["Cash encaissé", summary.total_cash_collected if summary else 0],
        ["Écart de caisse", summary.cash_discrepancy if summary else 0],
        ["Coût du stock", summary.stock_cost if summary else 0],
        ["Coût du personnel", summary.staff_cost if summary else 0],
        ["Profit brut", summary.gross_profit if summary else 0],
        ["Profit net", summary.net_profit if summary else 0],
    ]
    data = pdf_bytes(
        f"{event.name} | {bar.name} | Night {night.night_number} | {night.date} | {event.location}",
        [
            ("Personnel", ["Nom", "Rôle", "Salaire", "Cash encaissé"], [[responsible.full_name if responsible else "-", "responsable", 0, "-"], *staff]),
            ("Stock utilisé", ["Produit", "Ouverture", "Réassort", "Fermeture", "Utilisé", "Prix d’achat", "Coût total", "Prix de vente", "Revenu attendu"], stock),
            ("Rapprochement financier", ["Indicateur", "Valeur"], financial),
        ],
    )
    return PdfReport(
        event_id=event.id,
        event_night_id=night.id,
        bar_id=bar.id,
        report_type="bar_night",
        filename=f"{safe_filename(event.name)}_Night{night.night_number}_{safe_filename(bar.name)}_Report.pdf",
        data=data,
    )


def generate_night_pdf(db: DbSession, event: Event, night: EventNight) -> PdfReport:
    rows = (
        db.query(BarNightSummary, Bar)
        .join(Bar, Bar.id == BarNightSummary.bar_id)
        .filter(BarNightSummary.event_night_id == night.id)
        .order_by(Bar.name)
        .all()
    )
    table_rows = [[bar.name, row.total_cash_collected, row.expected_cash, row.cash_discrepancy, row.stock_cost, row.staff_cost, row.net_profit] for row, bar in rows]
    totals = [
        "TOTAL",
        sum(money(row.total_cash_collected) for row, _ in rows),
        sum(money(row.expected_cash) for row, _ in rows),
        sum(money(row.cash_discrepancy) for row, _ in rows),
        sum(money(row.stock_cost) for row, _ in rows),
        sum(money(row.staff_cost) for row, _ in rows),
        sum(money(row.net_profit) for row, _ in rows),
    ]
    data = pdf_bytes(
        f"{event.name} | Night {night.night_number} | {night.date}",
        [("Tous les bars", ["Bar", "Cash encaissé", "Cash attendu", "Écart", "Coût stock", "Coût personnel", "Profit net"], [*table_rows, totals])],
    )
    return PdfReport(event_id=event.id, event_night_id=night.id, bar_id=None, report_type="night", filename=f"{safe_filename(event.name)}_Night{night.night_number}_AllBars_Report.pdf", data=data)


def generate_event_pdf(db: DbSession, event: Event) -> PdfReport:
    night_rows = db.execute(
        text(
            """
            SELECT en.night_number, SUM(s.total_cash_collected) AS cash, SUM(s.expected_cash) AS expected_cash,
                   SUM(s.cash_discrepancy) AS discrepancy, SUM(s.stock_cost) AS stock_cost,
                   SUM(s.staff_cost) AS staff_cost, SUM(s.net_profit) AS net_profit
            FROM event_nights en
            LEFT JOIN bar_night_summary s ON s.event_night_id = en.id
            WHERE en.event_id = :event_id
            GROUP BY en.id, en.night_number
            ORDER BY en.night_number
            """
        ),
        {"event_id": event.id},
    ).mappings().all()
    bar_rows = db.execute(
        text(
            """
            SELECT b.name AS bar_name, SUM(s.total_cash_collected) AS cash, SUM(s.stock_cost) AS stock_cost,
                   SUM(s.staff_cost) AS staff_cost, SUM(s.net_profit) AS net_profit,
                   AVG(s.cash_discrepancy) AS avg_discrepancy
            FROM bars b
            LEFT JOIN bar_night_summary s ON s.bar_id = b.id
            WHERE b.event_id = :event_id
            GROUP BY b.id, b.name
            ORDER BY net_profit DESC
            """
        ),
        {"event_id": event.id},
    ).mappings().all()
    data = pdf_bytes(
        f"{event.name} | {event.location} | {event.start_date} | {event.total_nights_planned} nights",
        [
            ("Synthèse nuit par nuit", ["Nuit", "Cash total", "Cash attendu", "Écart", "Coût stock", "Coût personnel", "Profit net"], [[row["night_number"], row["cash"] or 0, row["expected_cash"] or 0, row["discrepancy"] or 0, row["stock_cost"] or 0, row["staff_cost"] or 0, row["net_profit"] or 0] for row in night_rows]),
            ("Synthèse bar par bar", ["Bar", "Cash total", "Coût stock", "Coût personnel", "Profit net", "Écart moyen"], [[row["bar_name"], row["cash"] or 0, row["stock_cost"] or 0, row["staff_cost"] or 0, row["net_profit"] or 0, row["avg_discrepancy"] or 0] for row in bar_rows]),
        ],
    )
    return PdfReport(event_id=event.id, event_night_id=None, bar_id=None, report_type="event", filename=f"{safe_filename(event.name)}_FullEvent_Report.pdf", data=data)


def bar_financial_rows(db: DbSession, event_id: int) -> list[dict]:
    rows = (
        db.query(ProfitSnapshot, Bar)
        .join(Bar, Bar.id == ProfitSnapshot.bar_id)
        .filter(ProfitSnapshot.event_id == event_id, ProfitSnapshot.snapshot_level == "night", ProfitSnapshot.bar_id.is_not(None))
        .all()
    )
    grouped: dict[int, dict] = {}
    salaries: dict[int, Decimal] = {}
    for item in current_assignment_query(db, event_id=event_id).all():
        salaries[item.bar_id] = salaries.get(item.bar_id, Decimal(0)) + money(item.salary_amount)
    for snapshot, bar in rows:
        current = grouped.setdefault(
            bar.id,
            {"bar_id": bar.id, "bar_name": bar.name, "gross_revenue": Decimal(0), "total_cost": Decimal(0), "staff_cost": Decimal(0), "profit": Decimal(0)},
        )
        current["gross_revenue"] += money(snapshot.actual_revenue)
        current["total_cost"] += money(snapshot.actual_revenue) - money(snapshot.actual_profit)
    for row in grouped.values():
        row["staff_cost"] = salaries.get(row["bar_id"], Decimal(0))
        row["profit"] = row["gross_revenue"] - row["total_cost"] - row["staff_cost"]
    return sorted(grouped.values(), key=lambda item: (item["profit"], item["gross_revenue"]), reverse=True)


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
    db.delete(get_or_404(db, User, user_id))
    commit_or_409(db)
    return ApiMessage(message="User deleted.")


@router.get("/events", response_model=list[EventRead])
def list_events(db: DbSession, _: AdminUser):
    return db.query(Event).order_by(Event.event_date.desc(), Event.start_time.desc()).all()


@router.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: DbSession, current_user: AdminUser):
    event = Event(
        name=payload.name,
        location=payload.location,
        event_date=payload.start_date,
        start_date=payload.start_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        total_nights=payload.total_nights_planned,
        total_nights_planned=payload.total_nights_planned,
        status="upcoming",
        attendance_count=payload.attendance_count,
        created_by=current_user.id,
    )
    db.add(event)
    db.flush()
    log_audit(db, current_user, "create_event", "events", event.id, payload.model_dump())
    commit_or_409(db)
    db.refresh(event)
    return event


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(event_id: int, payload: EventUpdate, db: DbSession, current_user: AdminUser):
    event = get_or_404(db, Event, event_id)
    require_event_open(event)
    if payload.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Utilisez la clôture officielle de l’événement pour générer les rapports et verrouiller les données.")
    apply_updates(event, payload)
    log_audit(db, current_user, "update_event", "events", event.id, payload.model_dump(exclude_unset=True))
    commit_or_409(db)
    db.refresh(event)
    return event


@router.delete("/events/{event_id}", response_model=ApiMessage)
def delete_event(event_id: int, db: DbSession, _: AdminUser):
    event = get_or_404(db, Event, event_id)
    require_event_open(event)
    db.delete(event)
    commit_or_409(db)
    return ApiMessage(message="Event deleted.")


@router.get("/event-nights", response_model=list[EventNightRead])
def list_event_nights(db: DbSession, _: AdminUser, event_id: int | None = None):
    query = db.query(EventNight).order_by(EventNight.event_id.desc(), EventNight.night_number)
    if event_id:
        query = query.filter(EventNight.event_id == event_id)
    return query.all()


@router.post("/event-nights", response_model=EventNightRead, status_code=status.HTTP_201_CREATED)
def begin_night(payload: BeginNightInput, db: DbSession, current_user: AdminUser):
    event = get_or_404(db, Event, payload.event_id)
    if event.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot add a new night to a closed event.")
    active = db.query(EventNight).filter(EventNight.event_id == event.id, EventNight.status == "active").first()
    if active:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only one night can be active at a time.")
    last_night = db.query(EventNight).filter(EventNight.event_id == event.id).order_by(EventNight.night_number.desc()).first()
    if last_night and last_night.status != "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot begin a new night if the previous night is not fully closed.")
    next_number = (last_night.night_number + 1) if last_night else 1
    if next_number > event.total_nights_planned:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="All planned nights have already been created.")
    night = EventNight(event_id=event.id, night_number=next_number, date=payload.date, status="active")
    db.add(night)
    if event.status == "upcoming":
        event.status = "active"
    db.flush()
    previous = db.query(EventNight).filter(EventNight.event_id == event.id, EventNight.night_number == next_number - 1).first()
    if previous:
        for stock in db.query(BarNightStock).filter(BarNightStock.event_night_id == previous.id).all():
            db.add(
                BarNightStock(
                    event_night_id=night.id,
                    bar_id=stock.bar_id,
                    product_id=stock.product_id,
                    qty_opening=stock.qty_closing or 0,
                    qty_top_up=0,
                    bought_price=stock.bought_price,
                    selling_price=stock.selling_price,
                )
            )
    log_audit(db, current_user, "open_night", "event_nights", night.id, payload.model_dump())
    commit_or_409(db)
    db.refresh(night)
    return night


@router.post("/events/{event_id}/close", response_model=ApiMessage)
def close_event(event_id: int, db: DbSession, current_user: AdminUser):
    event = get_or_404(db, Event, event_id)
    if event.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cet événement est déjà clôturé.")
    active = db.query(EventNight).filter(EventNight.event_id == event.id, EventNight.status == "active").first()
    if active:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot close an event while any night is active.")
    open_nights = db.query(EventNight).filter(EventNight.event_id == event.id, EventNight.status != "closed").count()
    if open_nights:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot close event until all created nights are closed.")
    event.status = "closed"
    log_audit(db, current_user, "close_event", "events", event.id, {"event_id": event.id})
    report = generate_event_pdf(db, event)
    db.add(report)
    commit_or_409(db)
    return ApiMessage(message="Event closed and full event PDF generated.")


@router.get("/bars", response_model=list[BarRead])
def list_bars(db: DbSession, _: AdminUser, event_id: int | None = None):
    query = db.query(Bar).order_by(Bar.name)
    if event_id:
        query = query.filter(Bar.event_id == event_id)
    return query.all()


@router.post("/bars", response_model=BarRead, status_code=status.HTTP_201_CREATED)
def create_bar(payload: BarCreate, db: DbSession, current_user: AdminUser):
    event = get_or_404(db, Event, payload.event_id)
    if event.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot add bars to a closed event.")
    require_employee(db, payload.responsible_user_id)
    bar = Bar(**payload.model_dump())
    db.add(bar)
    db.flush()
    ensure_bar_assignment(db, bar.id, payload.responsible_user_id)
    log_audit(db, current_user, "create_bar", "bars", bar.id, payload.model_dump())
    commit_or_409(db)
    db.refresh(bar)
    return bar


@router.patch("/bars/{bar_id}", response_model=BarRead)
def update_bar(bar_id: int, payload: BarUpdate, db: DbSession, current_user: AdminUser):
    bar = get_or_404(db, Bar, bar_id)
    require_event_open(event_for_bar(db, bar))
    if payload.event_id:
        target_event = get_or_404(db, Event, payload.event_id)
        require_event_open(target_event)
    if payload.responsible_user_id:
        require_employee(db, payload.responsible_user_id)
    apply_updates(bar, payload)
    if payload.responsible_user_id:
        ensure_bar_assignment(db, bar.id, payload.responsible_user_id)
    log_audit(db, current_user, "update_bar", "bars", bar.id, payload.model_dump(exclude_unset=True))
    commit_or_409(db)
    db.refresh(bar)
    return bar


@router.delete("/bars/{bar_id}", response_model=ApiMessage)
def delete_bar(bar_id: int, db: DbSession, _: AdminUser):
    bar = get_or_404(db, Bar, bar_id)
    require_event_open(event_for_bar(db, bar))
    db.delete(bar)
    commit_or_409(db)
    return ApiMessage(message="Bar deleted.")


@router.get("/product-categories", response_model=list[ProductCategoryRead])
def list_categories(db: DbSession, _: AdminUser):
    return db.query(ProductCategory).order_by(ProductCategory.name).all()


@router.post("/product-categories", response_model=ProductCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: ProductCategoryCreate, db: DbSession, _: AdminUser):
    category = ProductCategory(**payload.model_dump())
    db.add(category)
    commit_or_409(db)
    db.refresh(category)
    return category


@router.get("/products", response_model=list[ProductRead])
def list_products(db: DbSession, _: AdminUser):
    return db.query(Product).order_by(Product.name).all()


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: DbSession, _: AdminUser):
    get_or_404(db, ProductCategory, payload.category_id)
    product = Product(**payload.model_dump())
    db.add(product)
    commit_or_409(db)
    db.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: DbSession, _: AdminUser):
    product = get_or_404(db, Product, product_id)
    if payload.category_id:
        get_or_404(db, ProductCategory, payload.category_id)
    apply_updates(product, payload)
    commit_or_409(db)
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", response_model=ApiMessage)
def delete_product(product_id: int, db: DbSession, _: AdminUser):
    db.delete(get_or_404(db, Product, product_id))
    commit_or_409(db)
    return ApiMessage(message="Product deleted.")


@router.get("/event-stock", response_model=list[EventStockRead])
def list_event_stock(db: DbSession, _: AdminUser, event_id: int | None = None):
    query = db.query(EventStock).order_by(EventStock.event_id.desc(), EventStock.product_id)
    if event_id:
        query = query.filter(EventStock.event_id == event_id)
    return query.all()


@router.get("/event-stock-balance", response_model=list[EventStockBalance])
def list_event_stock_balance(db: DbSession, _: AdminUser, event_id: int):
    rows = db.query(EventStock).filter(EventStock.event_id == event_id).order_by(EventStock.product_id).all()
    return [
        EventStockBalance(
            event_id=event_id,
            product_id=row.product_id,
            total_qty_purchased=row.total_qty_purchased,
            allocated_to_bars=event_stock_drawn(db, event_id, row.product_id),
            available=money(row.total_qty_purchased) - event_stock_drawn(db, event_id, row.product_id),
        )
        for row in rows
    ]


@router.post("/event-stock", response_model=EventStockRead)
def upsert_event_stock(payload: EventStockUpsert, db: DbSession, current_user: AdminUser):
    event = get_or_404(db, Event, payload.event_id)
    require_event_open(event)
    get_or_404(db, Product, payload.product_id)
    stock = db.query(EventStock).filter(EventStock.event_id == payload.event_id, EventStock.product_id == payload.product_id).first()
    if not stock:
        stock = EventStock(**payload.model_dump())
        db.add(stock)
        db.flush()
        db.add(
            PriceHistory(
                event_stock_id=stock.id,
                event_id=stock.event_id,
                product_id=stock.product_id,
                old_selling_price=None,
                new_selling_price=stock.selling_price,
                changed_by_id=current_user.id,
            )
        )
        log_audit(db, current_user, "create_event_stock", "event_stock", stock.id, payload.model_dump())
    else:
        old_price = stock.selling_price
        stock.total_qty_purchased = payload.total_qty_purchased
        stock.bought_price = payload.bought_price
        stock.selling_price = payload.selling_price
        if old_price != payload.selling_price:
            db.add(
                PriceHistory(
                    event_stock_id=stock.id,
                    event_id=stock.event_id,
                    product_id=stock.product_id,
                    old_selling_price=old_price,
                    new_selling_price=payload.selling_price,
                    changed_by_id=current_user.id,
                )
            )
        log_audit(db, current_user, "edit_event_stock", "event_stock", stock.id, {"old_selling_price": old_price, **payload.model_dump()})
    if event_stock_drawn(db, payload.event_id, payload.product_id) > payload.total_qty_purchased:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Stock total cannot be lower than quantities already allocated to bars.")
    commit_or_409(db)
    db.refresh(stock)
    return stock


@router.get("/price-history", response_model=list[PriceHistoryRead])
def list_price_history(db: DbSession, _: AdminUser, event_id: int | None = None, product_id: int | None = None):
    query = db.query(PriceHistory).order_by(PriceHistory.changed_at.desc())
    if event_id:
        query = query.filter(PriceHistory.event_id == event_id)
    if product_id:
        query = query.filter(PriceHistory.product_id == product_id)
    return query.all()


@router.get("/audit-logs", response_model=list[AuditLogRead])
def list_audit_logs(db: DbSession, _: AdminUser, limit: int = Query(default=50, ge=1, le=500)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()


@router.get("/assignments", response_model=list[AssignmentRead])
def list_assignments(db: DbSession, _: AdminUser, event_id: int | None = None, user_id: int | None = None):
    return current_assignment_query(db, event_id=event_id, user_id=user_id).order_by(EventSalary.created_at.desc()).all()


@router.post("/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment(payload: AssignmentCreate, db: DbSession, current_user: AdminUser):
    validate_assignment(db, payload.event_id, payload.bar_id, payload.user_id)
    ensure_bar_assignment(db, payload.bar_id, payload.user_id)
    assignment = EventSalary(**payload.model_dump())
    db.add(assignment)
    db.flush()
    log_audit(db, current_user, "assign_staff_salary", "event_salaries", assignment.id, payload.model_dump())
    commit_or_409(db)
    db.refresh(assignment)
    return assignment


@router.post("/assignments/random", response_model=list[AssignmentRead])
def random_assignments(payload: RandomAssignmentRequest, db: DbSession, current_user: AdminUser):
    event = get_or_404(db, Event, payload.event_id)
    if event.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Closed events cannot be reassigned.")
    bars = db.query(Bar).filter(Bar.event_id == payload.event_id).order_by(Bar.name).all()
    employees = db.query(User).filter(User.role == "employee", User.is_active.is_(True)).order_by(User.full_name).all()
    if not bars:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Create at least one bar before random assignment.")
    if not employees:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Create at least one active employee before random assignment.")
    shuffle(employees)
    saved: list[EventSalary] = []
    for index, employee in enumerate(employees):
        bar = bars[index % len(bars)]
        ensure_bar_assignment(db, bar.id, employee.id)
        assignment = EventSalary(event_id=payload.event_id, user_id=employee.id, bar_id=bar.id, salary_amount=payload.salary_amount)
        db.add(assignment)
        saved.append(assignment)
    log_audit(db, current_user, "random_assign_staff", "events", payload.event_id, {"employee_count": len(employees), "bar_count": len(bars)})
    commit_or_409(db)
    return saved


@router.get("/night-assignments", response_model=list[NightBarAssignmentRead])
def list_night_assignments(db: DbSession, _: AdminUser, event_night_id: int | None = None, bar_id: int | None = None):
    query = db.query(NightBarAssignment).order_by(NightBarAssignment.event_night_id.desc(), NightBarAssignment.bar_id, NightBarAssignment.role)
    if event_night_id:
        query = query.filter(NightBarAssignment.event_night_id == event_night_id)
    if bar_id:
        query = query.filter(NightBarAssignment.bar_id == bar_id)
    return query.all()


@router.post("/night-assignments", response_model=list[NightBarAssignmentRead])
def save_night_assignments(payload: NightAssignmentInput, db: DbSession, current_user: AdminUser):
    night = get_or_404(db, EventNight, payload.event_night_id)
    bar = get_or_404(db, Bar, payload.bar_id)
    require_event_open(event_for_night(db, night))
    if night.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Closed nights cannot be edited.")
    if bar.event_id != night.event_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Bar does not belong to this night.")
    summary = db.query(BarNightSummary).filter(BarNightSummary.event_night_id == night.id, BarNightSummary.bar_id == bar.id, BarNightSummary.is_closed.is_(True)).first()
    if summary:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot edit assignments after this bar is closed.")
    if any(item.role == "responsible" for item in payload.assignments):
        db.query(NightBarAssignment).filter(
            NightBarAssignment.event_night_id == night.id,
            NightBarAssignment.bar_id == bar.id,
            NightBarAssignment.role == "responsible",
        ).delete(synchronize_session=False)
    saved: list[NightBarAssignment] = []
    for item in payload.assignments:
        require_employee(db, item.user_id)
        assignment = (
            db.query(NightBarAssignment)
            .filter(NightBarAssignment.event_night_id == night.id, NightBarAssignment.bar_id == bar.id, NightBarAssignment.user_id == item.user_id, NightBarAssignment.role == item.role)
            .first()
        )
        if not assignment:
            assignment = NightBarAssignment(event_night_id=night.id, bar_id=bar.id, user_id=item.user_id, role=item.role)
            db.add(assignment)
        assignment.salary_amount = item.salary_amount
        saved.append(assignment)
    log_audit(db, current_user, "edit_night_assignments", "event_nights", night.id, payload.model_dump())
    commit_or_409(db)
    return saved


@router.post("/night-assignments/random-bar", response_model=list[NightBarAssignmentRead])
def random_bar_night_assignments(payload: RandomBarNightAssignmentRequest, db: DbSession, current_user: AdminUser):
    night = get_or_404(db, EventNight, payload.event_night_id)
    bar = get_or_404(db, Bar, payload.bar_id)
    require_event_open(event_for_night(db, night))
    if bar.event_id != night.event_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Bar does not belong to this night.")
    if night.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Closed nights cannot be edited.")
    summary = db.query(BarNightSummary).filter(BarNightSummary.event_night_id == night.id, BarNightSummary.bar_id == bar.id, BarNightSummary.is_closed.is_(True)).first()
    if summary:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot edit assignments after this bar is closed.")

    already_assigned = select(NightBarAssignment.user_id).filter(NightBarAssignment.event_night_id == night.id)
    employees = (
        db.query(User)
        .filter(User.role == "employee", User.is_active.is_(True), User.id.not_in(already_assigned))
        .order_by(func.rand())
        .limit(payload.employee_count)
        .all()
    )
    if len(employees) < payload.employee_count:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Not enough available employees for that random assignment count.")

    saved: list[NightBarAssignment] = []
    for employee in employees:
        assignment = (
            db.query(NightBarAssignment)
            .filter(NightBarAssignment.event_night_id == night.id, NightBarAssignment.bar_id == bar.id, NightBarAssignment.user_id == employee.id, NightBarAssignment.role == "bartender")
            .first()
        )
        if not assignment:
            assignment = NightBarAssignment(event_night_id=night.id, bar_id=bar.id, user_id=employee.id, role="bartender")
            db.add(assignment)
        assignment.salary_amount = payload.salary_amount
        saved.append(assignment)
    log_audit(db, current_user, "random_bar_night_assignments", "event_nights", night.id, payload.model_dump())
    commit_or_409(db)
    return saved


@router.post("/night-assignments/random", response_model=list[NightBarAssignmentRead])
def random_night_assignments(db: DbSession, current_user: AdminUser, event_night_id: int, salary_amount: Decimal = Query(default=Decimal(0), ge=0)):
    night = get_or_404(db, EventNight, event_night_id)
    require_event_open(event_for_night(db, night))
    if night.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Closed nights cannot be edited.")
    bars = db.query(Bar).filter(Bar.event_id == night.event_id).order_by(Bar.name).all()
    employees = db.query(User).filter(User.role == "employee", User.is_active.is_(True)).order_by(User.full_name).all()
    if not bars or not employees:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Create bars and active employees before random assignment.")
    shuffle(employees)
    saved: list[NightBarAssignment] = []
    for index, employee in enumerate(employees):
        bar = bars[index % len(bars)]
        role = "responsible" if employee.id == bar.responsible_user_id else "bartender"
        assignment = NightBarAssignment(event_night_id=night.id, bar_id=bar.id, user_id=employee.id, role=role, salary_amount=salary_amount)
        db.add(assignment)
        saved.append(assignment)
    log_audit(db, current_user, "random_night_assignments", "event_nights", night.id, {"salary_amount": salary_amount})
    commit_or_409(db)
    return saved


@router.get("/stock", response_model=list[BarNightStockRead])
def list_stock(db: DbSession, _: AdminUser, event_night_id: int | None = None, bar_id: int | None = None):
    query = db.query(BarNightStock).order_by(BarNightStock.event_night_id.desc(), BarNightStock.bar_id, BarNightStock.product_id)
    if event_night_id:
        query = query.filter(BarNightStock.event_night_id == event_night_id)
    if bar_id:
        query = query.filter(BarNightStock.bar_id == bar_id)
    return query.all()


@router.post("/opening-stock", response_model=list[BarNightStockRead])
def save_opening_stock(payload: OpeningStockInput, db: DbSession, current_user: AdminUser):
    night = get_or_404(db, EventNight, payload.event_night_id)
    bar = get_or_404(db, Bar, payload.bar_id)
    require_event_open(event_for_night(db, night))
    if bar.event_id != night.event_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Bar does not belong to this event night.")
    validate_night_can_open(db, night)
    saved: list[BarNightStock] = []
    for item in payload.items:
        event_stock = db.query(EventStock).filter(EventStock.event_id == night.event_id, EventStock.product_id == item.product_id).first()
        if not event_stock:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Create event stock for product {item.product_id} before allocating it.")
        existing = (
            db.query(BarNightStock)
            .filter(BarNightStock.event_night_id == night.id, BarNightStock.bar_id == bar.id, BarNightStock.product_id == item.product_id)
            .first()
        )
        if existing and existing.is_locked:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Locked night stock cannot be edited.")
        if existing and night.night_number > 1 and item.qty_opening < existing.qty_opening:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Opening stock for night 2+ cannot be decreased below carried quantity.")
        already_drawn = event_stock_drawn(db, night.event_id, item.product_id, exclude_bar_id=bar.id, exclude_night_id=night.id)
        requested_draw = item.qty_opening + item.qty_top_up if night.night_number == 1 else item.qty_top_up
        if already_drawn + requested_draw > event_stock.total_qty_purchased:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot allocate more stock to bars than exists in the event pool.")
        if not existing:
            existing = BarNightStock(event_night_id=night.id, bar_id=bar.id, product_id=item.product_id)
            db.add(existing)
        existing.qty_opening = item.qty_opening
        existing.qty_top_up = item.qty_top_up
        existing.bought_price = item.bought_price or event_stock.bought_price
        existing.selling_price = item.selling_price or event_stock.selling_price
        saved.append(existing)
    if night.status == "upcoming":
        night.status = "active"
    db.flush()
    log_audit(db, current_user, "edit_opening_stock", "event_nights", night.id, payload.model_dump())
    commit_or_409(db)
    return saved


@router.get("/bartender-sales", response_model=list[BartenderSaleRead])
def list_bartender_sales(db: DbSession, _: AdminUser, event_id: int | None = None, bar_id: int | None = None):
    query = db.query(BartenderSale).order_by(BartenderSale.recorded_at.desc())
    if event_id:
        query = query.filter(BartenderSale.event_id == event_id)
    if bar_id:
        query = query.filter(BartenderSale.bar_id == bar_id)
    return query.all()


@router.post("/end-of-night", response_model=EndOfNightResult)
def record_end_of_night(payload: EndOfNightInput, db: DbSession, current_user: AdminUser):
    night = get_or_404(db, EventNight, payload.event_night_id)
    bar = get_or_404(db, Bar, payload.bar_id)
    require_event_open(event_for_night(db, night))
    if bar.event_id != night.event_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Bar does not belong to this event night.")
    existing_summary = db.query(BarNightSummary).filter(BarNightSummary.event_night_id == night.id, BarNightSummary.bar_id == bar.id, BarNightSummary.is_closed.is_(True)).first()
    if existing_summary:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot edit any field after this bar is closed for the night.")
    updated_stock: list[BarNightStock] = []
    for item in payload.stock_items:
        stock = (
            db.query(BarNightStock)
            .filter(BarNightStock.event_night_id == night.id, BarNightStock.bar_id == bar.id, BarNightStock.product_id == item.product_id)
            .first()
        )
        if not stock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Opening stock not found for product {item.product_id}.")
        if stock.is_locked:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot edit qty_closing after this night is locked.")
        if item.qty_closing > stock.qty_opening + stock.qty_top_up:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Closing quantity cannot exceed opening plus top-up.")
        stock.qty_closing = item.qty_closing
        updated_stock.append(stock)
    db.flush()

    saved_cash: list[BartenderCash] = []
    for item in payload.bartender_cash:
        assignment = (
            db.query(NightBarAssignment)
            .filter(NightBarAssignment.event_night_id == night.id, NightBarAssignment.bar_id == bar.id, NightBarAssignment.user_id == item.user_id)
            .first()
        )
        if not assignment:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cash can only be entered for bartenders assigned to this bar and night.")
        cash = (
            db.query(BartenderCash)
            .filter(BartenderCash.event_night_id == night.id, BartenderCash.bar_id == bar.id, BartenderCash.user_id == item.user_id)
            .first()
        )
        if not cash:
            cash = BartenderCash(event_night_id=night.id, bar_id=bar.id, user_id=item.user_id)
            db.add(cash)
        cash.cash_collected = item.cash_collected
        saved_cash.append(cash)

    db.flush()
    stock_rows = db.query(BarNightStock).filter(BarNightStock.event_night_id == night.id, BarNightStock.bar_id == bar.id).all()
    expected_cash = sum(money(row.qty_used) * money(row.selling_price) for row in stock_rows)
    stock_cost = sum(money(row.qty_used) * money(row.bought_price) for row in stock_rows)
    total_cash_collected = sum(money(row.cash_collected) for row in saved_cash)
    staff_cost = (
        db.query(func.coalesce(func.sum(NightBarAssignment.salary_amount), 0))
        .filter(NightBarAssignment.event_night_id == night.id, NightBarAssignment.bar_id == bar.id)
        .scalar()
    )
    staff_cost = money(staff_cost)
    summary = db.query(BarNightSummary).filter(BarNightSummary.event_night_id == night.id, BarNightSummary.bar_id == bar.id).first()
    if not summary:
        summary = BarNightSummary(event_night_id=night.id, bar_id=bar.id)
        db.add(summary)
    summary.total_cash_collected = total_cash_collected
    summary.expected_cash = expected_cash
    summary.cash_discrepancy = expected_cash - total_cash_collected
    summary.stock_cost = stock_cost
    summary.staff_cost = staff_cost
    summary.gross_profit = total_cash_collected - stock_cost
    summary.net_profit = total_cash_collected - stock_cost - staff_cost
    summary.expected_profit = expected_cash - stock_cost - staff_cost
    summary.is_closed = True
    summary.closed_at = func.now()
    for row in stock_rows:
        row.is_locked = True

    log_audit(db, current_user, "submit_bar_end_of_night", "bars", bar.id, {"event_night_id": night.id, "cash_entries": len(payload.bartender_cash), "stock_items": len(payload.stock_items)})
    commit_or_409(db)
    db.refresh(summary)
    return EndOfNightResult(stock=updated_stock, bartender_cash=saved_cash, summary=summary)


@router.post("/event-nights/{night_id}/close", response_model=ApiMessage)
def close_night(night_id: int, db: DbSession, current_user: AdminUser):
    night = get_or_404(db, EventNight, night_id)
    require_event_open(event_for_night(db, night))
    if night.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Night is already closed.")
    bars = db.query(Bar).filter(Bar.event_id == night.event_id).order_by(Bar.id).all()
    if not bars:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot close a night without bars.")
    for bar in bars:
        summary = db.query(BarNightSummary).filter(BarNightSummary.event_night_id == night.id, BarNightSummary.bar_id == bar.id, BarNightSummary.is_closed.is_(True)).first()
        if not summary:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot close the night until all bars have submitted qty_closing.")
    try:
        db.query(ProfitSnapshot).filter(ProfitSnapshot.event_night_id == night.id).delete(synchronize_session=False)
        db.query(PdfReport).filter(PdfReport.event_night_id == night.id).delete(synchronize_session=False)
        event = get_or_404(db, Event, night.event_id)
        for bar in bars:
            snapshot_bar(db, night.event_id, night.id, bar.id)
            db.add(generate_bar_pdf(db, event, night, bar))
        db.flush()
        snapshot_event(db, night.event_id, night.id)
        db.add(generate_night_pdf(db, event, night))
        db.query(BarNightStock).filter(BarNightStock.event_night_id == night.id).update({"is_locked": True}, synchronize_session=False)
        night.status = "closed"
        next_night = (
            db.query(EventNight)
            .filter(EventNight.event_id == night.event_id, EventNight.night_number == night.night_number + 1)
            .first()
        )
        if next_night:
            for stock in db.query(BarNightStock).filter(BarNightStock.event_night_id == night.id).all():
                exists = (
                    db.query(BarNightStock)
                    .filter(BarNightStock.event_night_id == next_night.id, BarNightStock.bar_id == stock.bar_id, BarNightStock.product_id == stock.product_id)
                    .first()
                )
                if not exists:
                    db.add(
                        BarNightStock(
                            event_night_id=next_night.id,
                            bar_id=stock.bar_id,
                            product_id=stock.product_id,
                            qty_opening=stock.qty_closing or 0,
                            qty_top_up=0,
                            bought_price=stock.bought_price,
                            selling_price=stock.selling_price,
                        )
                    )
            next_night.status = "upcoming"
        log_audit(db, current_user, "close_night", "event_nights", night.id, {"event_id": night.event_id, "night_number": night.night_number})
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Closing night failed; all carryover changes were rolled back.") from exc
    return ApiMessage(message="Night closed and carryover created.")


@router.get("/profit-snapshots", response_model=list[ProfitSnapshotRead])
def list_profit_snapshots(db: DbSession, _: AdminUser, event_id: int | None = None, event_night_id: int | None = None, bar_id: int | None = None):
    query = db.query(ProfitSnapshot).order_by(ProfitSnapshot.created_at.desc(), ProfitSnapshot.id.desc())
    if event_id:
        query = query.filter(ProfitSnapshot.event_id == event_id)
    if event_night_id:
        query = query.filter(ProfitSnapshot.event_night_id == event_night_id)
    if bar_id:
        query = query.filter(ProfitSnapshot.bar_id == bar_id)
    return query.all()


@router.get("/bar-night-summaries", response_model=list[BarNightSummaryRead])
def list_bar_night_summaries(db: DbSession, _: AdminUser, event_night_id: int | None = None, bar_id: int | None = None):
    query = db.query(BarNightSummary).order_by(BarNightSummary.event_night_id.desc(), BarNightSummary.bar_id)
    if event_night_id:
        query = query.filter(BarNightSummary.event_night_id == event_night_id)
    if bar_id:
        query = query.filter(BarNightSummary.bar_id == bar_id)
    return query.all()


@router.get("/bartender-cash", response_model=list[BartenderCashRead])
def list_bartender_cash(db: DbSession, _: AdminUser, event_night_id: int | None = None, bar_id: int | None = None, user_id: int | None = None):
    query = db.query(BartenderCash).order_by(BartenderCash.recorded_at.desc())
    if event_night_id:
        query = query.filter(BartenderCash.event_night_id == event_night_id)
    if bar_id:
        query = query.filter(BartenderCash.bar_id == bar_id)
    if user_id:
        query = query.filter(BartenderCash.user_id == user_id)
    return query.all()


@router.get("/pdf-reports", response_model=list[PdfReportRead])
def list_pdf_reports(db: DbSession, _: AdminUser, event_id: int | None = None, event_night_id: int | None = None, bar_id: int | None = None):
    query = db.query(PdfReport).order_by(PdfReport.generated_at.desc(), PdfReport.id.desc())
    if event_id:
        query = query.filter(PdfReport.event_id == event_id)
    if event_night_id:
        query = query.filter(PdfReport.event_night_id == event_night_id)
    if bar_id:
        query = query.filter(PdfReport.bar_id == bar_id)
    return query.all()


@router.get("/pdf-reports/{report_id}")
def download_pdf_report(report_id: int, db: DbSession, _: AdminUser):
    report = get_or_404(db, PdfReport, report_id)
    return Response(content=report.data, media_type=report.content_type, headers={"Content-Disposition": f'attachment; filename="{report.filename}"'})


@router.get("/reports/summary", response_model=MoneySummary)
def financial_summary(db: DbSession, _: AdminUser, event_id: int):
    return event_money_summary(db, event_id)


@router.get("/reports/bar-financials", response_model=list[BarFinancialSummary])
def bar_financials(db: DbSession, _: AdminUser, event_id: int):
    return [BarFinancialSummary(**row) for row in bar_financial_rows(db, event_id)]


@router.get("/reports/best-sellers", response_model=list[ProductRankingItem])
def best_sellers(db: DbSession, _: AdminUser, event_id: int, bar_id: int | None = None):
    where_bar = "AND b.id = :bar_id" if bar_id else ""
    group_bar = "b.id, b.name," if bar_id else ""
    select_bar = "b.id AS bar_id, b.name AS bar_name," if bar_id else "NULL AS bar_id, NULL AS bar_name,"
    params = {"event_id": event_id}
    if bar_id:
        params["bar_id"] = bar_id
    rows = db.execute(
        text(
            f"""
            SELECT
              p.id AS product_id,
              p.name AS product_name,
              {select_bar}
              SUM(bns.qty_sold) AS quantity_sold,
              SUM(bns.qty_sold * es.selling_price) AS revenue
            FROM bar_night_stock bns
            JOIN event_nights en ON en.id = bns.event_night_id
            JOIN bars b ON b.id = bns.bar_id
            JOIN products p ON p.id = bns.product_id
            JOIN event_stock es ON es.event_id = b.event_id AND es.product_id = bns.product_id
            WHERE b.event_id = :event_id {where_bar}
            GROUP BY {group_bar} p.id, p.name
            ORDER BY quantity_sold DESC, revenue DESC
            """
        ),
        params,
    ).mappings().all()
    return [ProductRankingItem(**dict(row)) for row in rows]


@router.get("/reports/low-stock", response_model=list[LowStockAlert])
def low_stock_alerts(db: DbSession, _: AdminUser, event_id: int):
    rows = db.execute(
        text(
            """
            SELECT
              b.id AS bar_id,
              b.name AS bar_name,
              p.id AS product_id,
              p.name AS product_name,
              (bns.qty_opening + bns.qty_top_up) AS quantity_allocated,
              bns.qty_closing AS quantity_remaining,
              CASE WHEN (bns.qty_opening + bns.qty_top_up) = 0 THEN 0
                   ELSE (bns.qty_closing / (bns.qty_opening + bns.qty_top_up)) * 100 END AS remaining_pct
            FROM bar_night_stock bns
            JOIN event_nights en ON en.id = bns.event_night_id
            JOIN bars b ON b.id = bns.bar_id
            JOIN products p ON p.id = bns.product_id
            WHERE b.event_id = :event_id
              AND bns.qty_closing IS NOT NULL
              AND (bns.qty_opening + bns.qty_top_up) > 0
              AND bns.qty_closing < ((bns.qty_opening + bns.qty_top_up) * 0.10)
            ORDER BY remaining_pct ASC, b.name, p.name
            """
        ),
        {"event_id": event_id},
    ).mappings().all()
    return [LowStockAlert(**dict(row)) for row in rows]


@router.get("/reports/waste", response_model=list[WasteItem])
def waste_tracker(db: DbSession, _: AdminUser, event_id: int):
    latest_closed = (
        db.query(EventNight)
        .filter(EventNight.event_id == event_id, EventNight.status == "closed")
        .order_by(EventNight.night_number.desc())
        .first()
    )
    if not latest_closed:
        return []
    rows = db.execute(
        text(
            """
            SELECT
              b.id AS bar_id,
              b.name AS bar_name,
              p.id AS product_id,
              p.name AS product_name,
              bns.qty_closing AS quantity_remaining,
              bns.qty_closing * es.bought_price AS estimated_cost
            FROM bar_night_stock bns
            JOIN bars b ON b.id = bns.bar_id
            JOIN products p ON p.id = bns.product_id
            JOIN event_stock es ON es.event_id = b.event_id AND es.product_id = bns.product_id
            WHERE b.event_id = :event_id AND bns.event_night_id = :night_id AND bns.qty_closing > 0
            ORDER BY estimated_cost DESC
            """
        ),
        {"event_id": event_id, "night_id": latest_closed.id},
    ).mappings().all()
    return [WasteItem(**dict(row)) for row in rows]


@router.get("/reports/bartender-leaderboard", response_model=list[BartenderLeaderboardItem])
def bartender_leaderboard(db: DbSession, _: AdminUser, event_id: int | None = None):
    rows = db.execute(
        text(
            """
            SELECT
              u.id AS user_id,
              u.full_name,
              COUNT(DISTINCT bs.event_id) AS events_worked,
              COALESCE(SUM(bs.units_sold), 0) AS total_units,
              COALESCE(SUM(bs.sales_amount), 0) AS total_sales
            FROM users u
            JOIN bartender_sales bs ON bs.user_id = u.id
            WHERE (:event_id IS NULL OR bs.event_id = :event_id)
            GROUP BY u.id, u.full_name
            ORDER BY total_sales DESC, total_units DESC
            """
        ),
        {"event_id": event_id},
    ).mappings().all()
    return [BartenderLeaderboardItem(**dict(row)) for row in rows]


@router.get("/reports/event-insights", response_model=EventInsight)
def event_insights(db: DbSession, _: AdminUser, event_id: int):
    summary = event_money_summary(db, event_id)
    bar_rows = [BarFinancialSummary(**row) for row in bar_financial_rows(db, event_id)]
    best = best_sellers(db, _, event_id)
    leaderboard = bartender_leaderboard(db, _, event_id)
    return EventInsight(
        event_id=event_id,
        revenue=summary.revenue,
        cost=summary.cost,
        salaries=summary.salaries,
        profit=summary.profit,
        top_performing_bar=bar_rows[0] if bar_rows else None,
        top_selling_product=best[0] if best else None,
        highest_earning_bartender=leaderboard[0] if leaderboard else None,
        low_stock_alerts=low_stock_alerts(db, _, event_id),
        best_sellers=best,
        waste=waste_tracker(db, _, event_id),
    )


@router.get("/reports/event-comparison", response_model=list[EventComparisonItem])
def event_comparison(db: DbSession, _: AdminUser, event_ids: list[int] | None = Query(default=None)):
    query = db.query(Event).order_by(Event.event_date.desc())
    if event_ids:
        query = query.filter(Event.id.in_(event_ids))
    results: list[EventComparisonItem] = []
    for event in query.all():
        summary = event_money_summary(db, event.id)
        revenue_per_attendee = (summary.revenue / Decimal(event.attendance_count)).quantize(Decimal("0.01")) if event.attendance_count else Decimal(0)
        results.append(
            EventComparisonItem(
                event_id=event.id,
                event_name=event.name,
                event_date=event.event_date,
                attendance_count=event.attendance_count,
                revenue=summary.revenue,
                cost=summary.cost,
                salaries=summary.salaries,
                profit=summary.profit,
                revenue_per_attendee=revenue_per_attendee,
            )
        )
    return results
