"""initial schema

Revision ID: 202605240001
Revises:
Create Date: 2026-05-24
"""

from collections.abc import Sequence
from datetime import date, time
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

revision: str = "202605240001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PASSWORD_HASH = "$2b$12$C6UzMDM.H6dfI/f/IKcEeO6c7jo1dfmjdgKiSmTsgZ7CeJc3prN9a"


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=40), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_tokens_token_hash"), "refresh_tokens", ["token_hash"], unique=True)
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("location", sa.String(length=80), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('upcoming', 'active', 'closed')", name="ck_events_status"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_created_by"), "events", ["created_by"], unique=False)
    op.create_index(op.f("ix_events_status"), "events", ["status"], unique=False)

    op.create_table(
        "product_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_product_categories_name"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("unit IN ('bottle', 'can', 'unit')", name="ck_products_unit"),
        sa.ForeignKeyConstraint(["category_id"], ["product_categories.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "category_id", name="uq_products_name_category"),
    )
    op.create_index(op.f("ix_products_category_id"), "products", ["category_id"], unique=False)

    op.create_table(
        "bars",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("responsible_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["responsible_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "name", name="uq_bars_event_name"),
    )
    op.create_index(op.f("ix_bars_event_id"), "bars", ["event_id"], unique=False)
    op.create_index(op.f("ix_bars_responsible_user_id"), "bars", ["responsible_user_id"], unique=False)

    op.create_table(
        "bar_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bar_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bar_id", "user_id", name="uq_bar_assignment_user"),
    )
    op.create_index("ix_bar_assignments_user_bar", "bar_assignments", ["user_id", "bar_id"], unique=False)
    op.create_index(op.f("ix_bar_assignments_bar_id"), "bar_assignments", ["bar_id"], unique=False)
    op.create_index(op.f("ix_bar_assignments_user_id"), "bar_assignments", ["user_id"], unique=False)

    op.create_table(
        "event_stock",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("bought_price_per_unit", sa.Numeric(10, 2), nullable=False),
        sa.Column("selling_price_per_unit", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "product_id", name="uq_event_stock_product"),
    )
    op.create_index(op.f("ix_event_stock_event_id"), "event_stock", ["event_id"], unique=False)
    op.create_index(op.f("ix_event_stock_product_id"), "event_stock", ["product_id"], unique=False)

    op.create_table(
        "bar_stock",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bar_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity_allocated", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity_sold", sa.Numeric(10, 2), sa.Computed("quantity_allocated - quantity_remaining"), nullable=False),
        sa.Column("quantity_remaining", sa.Numeric(10, 2), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bar_id", "product_id", name="uq_bar_stock_product"),
    )
    op.create_index(op.f("ix_bar_stock_bar_id"), "bar_stock", ["bar_id"], unique=False)
    op.create_index(op.f("ix_bar_stock_product_id"), "bar_stock", ["product_id"], unique=False)

    op.execute(
        """
        CREATE VIEW bar_stock_financials AS
        SELECT
          bs.id AS bar_stock_id,
          b.event_id,
          bs.bar_id,
          bs.product_id,
          bs.quantity_allocated,
          bs.quantity_remaining,
          bs.quantity_sold,
          es.bought_price_per_unit,
          es.selling_price_per_unit,
          (bs.quantity_sold * es.selling_price_per_unit) AS revenue,
          (bs.quantity_sold * es.bought_price_per_unit) AS cost,
          ((bs.quantity_sold * es.selling_price_per_unit) - (bs.quantity_sold * es.bought_price_per_unit)) AS profit
        FROM bar_stock bs
        JOIN bars b ON b.id = bs.bar_id
        JOIN event_stock es ON es.event_id = b.event_id AND es.product_id = bs.product_id
        """
    )

    seed_data()


def seed_data() -> None:
    users = sa.table(
        "users",
        sa.column("id", sa.Integer),
        sa.column("full_name", sa.String),
        sa.column("email", sa.String),
        sa.column("phone_number", sa.String),
        sa.column("role", sa.String),
        sa.column("hashed_password", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    events = sa.table(
        "events",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("location", sa.String),
        sa.column("event_date", sa.Date),
        sa.column("start_time", sa.Time),
        sa.column("end_time", sa.Time),
        sa.column("status", sa.String),
        sa.column("created_by", sa.Integer),
    )
    categories = sa.table("product_categories", sa.column("id", sa.Integer), sa.column("name", sa.String))
    products = sa.table(
        "products",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("category_id", sa.Integer),
        sa.column("unit", sa.String),
    )
    bars = sa.table(
        "bars",
        sa.column("id", sa.Integer),
        sa.column("event_id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("responsible_user_id", sa.Integer),
    )
    assignments = sa.table("bar_assignments", sa.column("id", sa.Integer), sa.column("bar_id", sa.Integer), sa.column("user_id", sa.Integer))
    event_stock = sa.table(
        "event_stock",
        sa.column("id", sa.Integer),
        sa.column("event_id", sa.Integer),
        sa.column("product_id", sa.Integer),
        sa.column("quantity_total", sa.Numeric),
        sa.column("bought_price_per_unit", sa.Numeric),
        sa.column("selling_price_per_unit", sa.Numeric),
    )
    bar_stock = sa.table(
        "bar_stock",
        sa.column("id", sa.Integer),
        sa.column("bar_id", sa.Integer),
        sa.column("product_id", sa.Integer),
        sa.column("quantity_allocated", sa.Numeric),
        sa.column("quantity_remaining", sa.Numeric),
    )

    op.bulk_insert(
        users,
        [
            {"id": 1, "full_name": "Festival Admin", "email": "admin@festivapro.local", "phone_number": "+212600000001", "role": "admin", "hashed_password": PASSWORD_HASH, "is_active": True},
            *[
                {
                    "id": index + 2,
                    "full_name": name,
                    "email": f"employee{index + 1}@festivapro.local",
                    "phone_number": f"+212600000{index + 10:03d}",
                    "role": "employee",
                    "hashed_password": PASSWORD_HASH,
                    "is_active": True,
                }
                for index, name in enumerate(
                    [
                        "Yassine Amrani",
                        "Salma Idrissi",
                        "Omar Benali",
                        "Nadia Berrada",
                        "Mehdi El Fassi",
                        "Imane Tazi",
                        "Hassan Alaoui",
                        "Sara Moutawakil",
                        "Rachid Mansouri",
                        "Lina Sabri",
                        "Karim Lahlou",
                        "Meryem Chraibi",
                        "Anas El Mansouri",
                        "Hajar Bennani",
                        "Youssef Akhannouch",
                        "Aya El Amrani",
                        "Reda Bennis",
                        "Mouna Serghini",
                    ]
                )
            ],
        ],
    )
    op.bulk_insert(
        events,
        [
            {"id": 1, "name": "Casa Nights Festival", "location": "Casablanca", "event_date": date(2026, 6, 5), "start_time": time(18, 0), "end_time": time(2, 0), "status": "upcoming", "created_by": 1},
            {"id": 2, "name": "Marrakech Desert Beats", "location": "Marrakech", "event_date": date(2026, 6, 12), "start_time": time(19, 0), "end_time": time(3, 0), "status": "upcoming", "created_by": 1},
            {"id": 3, "name": "Agadir Beach Sessions", "location": "Agadir", "event_date": date(2026, 6, 19), "start_time": time(17, 30), "end_time": time(1, 30), "status": "upcoming", "created_by": 1},
            {"id": 4, "name": "Rabat Stage Live", "location": "Rabat", "event_date": date(2026, 6, 26), "start_time": time(18, 30), "end_time": time(2, 30), "status": "upcoming", "created_by": 1},
            {"id": 5, "name": "Tanger Harbor Sound", "location": "Tanger", "event_date": date(2026, 7, 3), "start_time": time(19, 30), "end_time": time(3, 30), "status": "upcoming", "created_by": 1},
        ],
    )
    op.bulk_insert(categories, [{"id": 1, "name": "Beer"}, {"id": 2, "name": "Hard Alcohol"}, {"id": 3, "name": "Soda"}, {"id": 4, "name": "Consumables"}])
    op.bulk_insert(
        products,
        [
            {"id": 1, "name": "Gold Special", "category_id": 1, "unit": "can"},
            {"id": 2, "name": "Casablanca", "category_id": 1, "unit": "bottle"},
            {"id": 3, "name": "Gordon's", "category_id": 2, "unit": "bottle"},
            {"id": 4, "name": "Tanqueray", "category_id": 2, "unit": "bottle"},
            {"id": 5, "name": "Smirnoff", "category_id": 2, "unit": "bottle"},
            {"id": 6, "name": "Belvedere", "category_id": 2, "unit": "bottle"},
            {"id": 7, "name": "Red Label", "category_id": 2, "unit": "bottle"},
            {"id": 8, "name": "Black Label", "category_id": 2, "unit": "bottle"},
            {"id": 9, "name": "Jose Cuervo Tequila", "category_id": 2, "unit": "bottle"},
            {"id": 10, "name": "Coca-Cola", "category_id": 3, "unit": "can"},
            {"id": 11, "name": "Sprite", "category_id": 3, "unit": "can"},
            {"id": 12, "name": "Water", "category_id": 3, "unit": "bottle"},
            {"id": 13, "name": "Tonic", "category_id": 3, "unit": "can"},
            {"id": 14, "name": "Goblets", "category_id": 4, "unit": "unit"},
            {"id": 15, "name": "Ice", "category_id": 4, "unit": "unit"},
            {"id": 16, "name": "Napkins", "category_id": 4, "unit": "unit"},
            {"id": 17, "name": "Straws", "category_id": 4, "unit": "unit"},
        ],
    )

    bar_rows = []
    bar_names = ["Main Bar", "VIP Bar", "Garden Bar", "Terrace Bar", "Beach Bar", "Lounge Bar", "North Bar", "Harbor Bar"]
    bar_id = 1
    bars_per_event = {1: 3, 2: 4, 3: 3, 4: 2, 5: 3}
    for event_id, count in bars_per_event.items():
        for index in range(count):
            bar_rows.append({"id": bar_id, "event_id": event_id, "name": bar_names[(event_id + index) % len(bar_names)], "responsible_user_id": 2 + ((bar_id - 1) % 18)})
            bar_id += 1
    op.bulk_insert(bars, bar_rows)

    assignment_rows = []
    assignment_id = 1
    for row in bar_rows:
        first_employee = 2 + ((row["id"] * 3) % 18)
        employee_ids = [2 + ((first_employee - 2 + offset) % 18) for offset in range(3)]
        if row["responsible_user_id"] not in employee_ids:
            employee_ids[0] = row["responsible_user_id"]
        for employee_id in employee_ids:
            assignment_rows.append({"id": assignment_id, "bar_id": row["id"], "user_id": employee_id})
            assignment_id += 1
    op.bulk_insert(assignments, assignment_rows)

    base_prices = {
        1: (Decimal("12.00"), Decimal("30.00")),
        2: (Decimal("14.00"), Decimal("35.00")),
        3: (Decimal("150.00"), Decimal("350.00")),
        4: (Decimal("230.00"), Decimal("520.00")),
        5: (Decimal("120.00"), Decimal("320.00")),
        6: (Decimal("360.00"), Decimal("760.00")),
        7: (Decimal("180.00"), Decimal("420.00")),
        8: (Decimal("310.00"), Decimal("680.00")),
        9: (Decimal("190.00"), Decimal("450.00")),
        10: (Decimal("5.00"), Decimal("15.00")),
        11: (Decimal("5.00"), Decimal("15.00")),
        12: (Decimal("3.00"), Decimal("10.00")),
        13: (Decimal("6.00"), Decimal("18.00")),
        14: (Decimal("0.60"), Decimal("1.00")),
        15: (Decimal("8.00"), Decimal("12.00")),
        16: (Decimal("0.20"), Decimal("0.50")),
        17: (Decimal("0.10"), Decimal("0.30")),
    }
    event_stock_rows = []
    event_stock_id = 1
    for event_id in range(1, 6):
        for product_id in range(1, 18):
            multiplier = Decimal("1.00") + (Decimal(event_id - 1) * Decimal("0.05"))
            base_cost, base_sell = base_prices[product_id]
            event_stock_rows.append(
                {
                    "id": event_stock_id,
                    "event_id": event_id,
                    "product_id": product_id,
                    "quantity_total": Decimal(120 + event_id * 20 + product_id * 3),
                    "bought_price_per_unit": (base_cost * multiplier).quantize(Decimal("0.01")),
                    "selling_price_per_unit": (base_sell * multiplier).quantize(Decimal("0.01")),
                }
            )
            event_stock_id += 1
    op.bulk_insert(event_stock, event_stock_rows)

    stock_rows = []
    stock_id = 1
    for row in bar_rows:
        for product_id in range(1, 18):
            allocated = Decimal(18 + (row["id"] % 4) * 4 + (product_id % 5) * 3)
            remaining = allocated - Decimal(4 + (row["id"] + product_id) % 9)
            if remaining < 0:
                remaining = Decimal(0)
            stock_rows.append(
                {
                    "id": stock_id,
                    "bar_id": row["id"],
                    "product_id": product_id,
                    "quantity_allocated": allocated,
                    "quantity_remaining": remaining,
                }
            )
            stock_id += 1
    op.bulk_insert(bar_stock, stock_rows)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS bar_stock_financials")
    op.drop_table("bar_stock")
    op.drop_table("event_stock")
    op.drop_table("bar_assignments")
    op.drop_table("bars")
    op.drop_table("products")
    op.drop_table("product_categories")
    op.drop_table("events")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
