"""initial schema (5 tabel, index, partial unique index, RLS)

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-11-22
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# JSONB di PostgreSQL, JSON biasa di SQLite (tes lokal).
JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")

TABLES = ("users", "models", "sar_priorities", "input_data", "predictions")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    op.create_table(
        "models",
        sa.Column("model_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_name", sa.String(length=50), nullable=False),
        sa.Column("best_params", JSON_TYPE, nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("model_status", sa.String(length=20), nullable=False),
        sa.Column("trained_date", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("model_id", name=op.f("pk_models")),
        sa.CheckConstraint(
            "model_status IN ('active', 'comparator', 'archived')",
            name=op.f("ck_models_model_status_valid"),
        ),
    )
    # Maksimal satu model aktif (partial unique index).
    op.create_index(
        "uq_models_single_active",
        "models",
        ["model_status"],
        unique=True,
        postgresql_where=sa.text("model_status = 'active'"),
        sqlite_where=sa.text("model_status = 'active'"),
    )

    op.create_table(
        "sar_priorities",
        sa.Column("sar_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("predicted_class", sa.String(length=10), nullable=False),
        sa.Column("sar_priority_level", sa.String(length=20), nullable=False),
        sa.Column("sar_recommendation", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("sar_id", name=op.f("pk_sar_priorities")),
        sa.UniqueConstraint(
            "predicted_class", name=op.f("uq_sar_priorities_predicted_class")
        ),
    )

    op.create_table(
        "input_data",
        sa.Column("input_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("landslide_category", sa.String(length=50), nullable=False),
        sa.Column("landslide_trigger", sa.String(length=50), nullable=False),
        sa.Column("landslide_setting", sa.String(length=50), nullable=False),
        sa.Column("location_accuracy", sa.String(length=50), nullable=False),
        sa.Column("nama_wilayah", sa.String(length=255), nullable=True),
        sa.Column("geocoding_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            name=op.f("fk_input_data_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("input_id", name=op.f("pk_input_data")),
        sa.CheckConstraint(
            "geocoding_status IN ('success', 'not_found', 'error')",
            name=op.f("ck_input_data_geocoding_status_valid"),
        ),
    )
    op.create_index(
        "ix_input_data_user_created", "input_data", ["user_id", "created_at"]
    )
    op.create_index(
        "ix_input_data_user_region", "input_data", ["user_id", "nama_wilayah"]
    )

    op.create_table(
        "predictions",
        sa.Column("prediction_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("input_id", sa.Integer(), nullable=False),
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("predicted_class", sa.String(length=10), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("probabilities", JSON_TYPE, nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="success",
        ),
        sa.Column("prediction_date", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["input_id"],
            ["input_data.input_id"],
            name=op.f("fk_predictions_input_id_input_data"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["model_id"],
            ["models.model_id"],
            name=op.f("fk_predictions_model_id_models"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["predicted_class"],
            ["sar_priorities.predicted_class"],
            name=op.f("fk_predictions_predicted_class_sar_priorities"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("prediction_id", name=op.f("pk_predictions")),
        sa.CheckConstraint(
            "status IN ('success', 'failed')",
            name=op.f("ck_predictions_prediction_status_valid"),
        ),
    )
    op.create_index("ix_predictions_input_id", "predictions", ["input_id"])
    op.create_index("ix_predictions_model_id", "predictions", ["model_id"])
    op.create_index(
        "ix_predictions_predicted_class", "predictions", ["predicted_class"]
    )

    # Supabase: aktifkan RLS tanpa policy (akses hanya via backend/service role).
    if op.get_bind().dialect.name == "postgresql":
        for table in TABLES:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for table in TABLES:
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_index("ix_predictions_predicted_class", table_name="predictions")
    op.drop_index("ix_predictions_model_id", table_name="predictions")
    op.drop_index("ix_predictions_input_id", table_name="predictions")
    op.drop_table("predictions")

    op.drop_index("ix_input_data_user_region", table_name="input_data")
    op.drop_index("ix_input_data_user_created", table_name="input_data")
    op.drop_table("input_data")

    op.drop_table("sar_priorities")

    op.drop_index("uq_models_single_active", table_name="models")
    op.drop_table("models")

    op.drop_table("users")
