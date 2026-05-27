"""night only bar responsibles

Revision ID: 202605250006
Revises: 202605250005
Create Date: 2026-05-25 00:06:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202605250006"
down_revision = "202605250005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("bars")}
    if "responsible_user_id" in columns:
        op.alter_column("bars", "responsible_user_id", existing_type=sa.Integer(), nullable=True)
        op.execute("UPDATE bars SET responsible_user_id = NULL")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("bars")}
    if "responsible_user_id" in columns:
        op.execute(
            """
            UPDATE bars b
            JOIN (SELECT id FROM users WHERE role = 'employee' ORDER BY id LIMIT 1) u
              ON 1 = 1
            SET b.responsible_user_id = u.id
            WHERE b.responsible_user_id IS NULL
            """
        )
        op.alter_column("bars", "responsible_user_id", existing_type=sa.Integer(), nullable=False)
