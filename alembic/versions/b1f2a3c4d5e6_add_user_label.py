"""add optional label column to users

Revision ID: b1f2a3c4d5e6
Revises: 806dba90588f
Create Date: 2026-06-22

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b1f2a3c4d5e6"
down_revision = "806dba90588f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("label", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "label")
