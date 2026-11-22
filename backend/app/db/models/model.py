"""Tabel `models`: registri model aktif & pembanding.

Partial unique index `uq_models_single_active` menjamin hanya ada SATU baris
dengan `model_status = 'active'` pada PostgreSQL maupun SQLite.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, JSON, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utc_now

if TYPE_CHECKING:
    from app.db.models.prediction import Prediction

# JSONB di PostgreSQL, JSON biasa di SQLite (untuk tes lokal).
JsonType = JSON().with_variant(JSONB(), "postgresql")

MODEL_STATUSES = ("active", "comparator", "archived")


class Model(Base):
    __tablename__ = "models"
    __table_args__ = (
        CheckConstraint(
            "model_status IN ('active', 'comparator', 'archived')",
            name="model_status_valid",
        ),
        Index(
            "uq_models_single_active",
            "model_status",
            unique=True,
            postgresql_where=text("model_status = 'active'"),
            sqlite_where=text("model_status = 'active'"),
        ),
    )

    model_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    best_params: Mapped[dict[str, Any]] = mapped_column(
        JsonType, nullable=False, default=dict
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="comparator"
    )
    trained_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    predictions: Mapped[list["Prediction"]] = relationship(back_populates="model")

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return (
            f"<Model model_id={self.model_id} name={self.model_name!r} "
            f"version={self.model_version!r} status={self.model_status!r}>"
        )
