"""initial schema

Revision ID: 806dba90588f
Revises:
Create Date: 2026-06-21 21:14:28.585413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '806dba90588f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    user_role = postgresql.ENUM("admin", "operator", name="user_role")
    attendance_status = postgresql.ENUM("present", "absent", name="attendance_status")
    audit_event_type = postgresql.ENUM(
        "register",
        "train_enroll",
        "recognize_attempt",
        "recognize_success",
        "recognize_reject_liveness",
        "recognize_reject_threshold",
        "login",
        "login_failed",
        "attendance_write",
        name="audit_event_type",
    )
    audit_result = postgresql.ENUM("success", "failure", "rejected", name="audit_result")

    # Each ENUM type below is referenced by exactly one table's column, so
    # `create_table`'s default create_type=True creates it inline — no need
    # to call .create() separately (doing both emits duplicate CREATE TYPE).

    op.create_table(
        "identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("external_id", sa.String(length=32), nullable=False),
        sa.Column("full_name", sa.String(length=128), nullable=False),
        sa.Column("extra_metadata", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_unique_constraint("uq_identities_external_id", "identities", ["external_id"])
    op.create_index("ix_identities_external_id", "identities", ["external_id"])

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="operator"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "face_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "identity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("embedding", Vector(512), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("source_image_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_face_embeddings_identity_id", "face_embeddings", ["identity_id"])

    op.create_table(
        "attendance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "identity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("time_recorded", sa.Time, nullable=True),
        sa.Column("status", attendance_status, nullable=False, server_default="absent"),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("identity_id", "date", name="uq_attendance_identity_date"),
    )
    op.create_index("ix_attendance_records_identity_id", "attendance_records", ["identity_id"])
    op.create_index("ix_attendance_records_date", "attendance_records", ["date"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", audit_event_type, nullable=False),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "identity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("result", audit_result, nullable=False),
        sa.Column("detail", postgresql.JSONB, nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("audit_log")
    op.drop_table("attendance_records")
    op.drop_table("face_embeddings")
    op.drop_table("users")
    op.drop_table("identities")

    postgresql.ENUM(name="audit_result").drop(op.get_bind())
    postgresql.ENUM(name="audit_event_type").drop(op.get_bind())
    postgresql.ENUM(name="attendance_status").drop(op.get_bind())
    postgresql.ENUM(name="user_role").drop(op.get_bind())
