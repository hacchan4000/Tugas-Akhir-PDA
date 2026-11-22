"""Tabel `predictions`: hasil inferensi model + prioritas SAR."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utc_now

if TYPE_CHECKING:
    from app.db.models.input_data import InputData
    from app.db.models.model import Model
    from app.db.models.sar_priority import SarPriority

JsonType = JSON().with_variant(JSONB(), "postgresql")

PREDICTION_STATUSES = ("success", "failed")


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed')",
            name="prediction_status_valid",
        ),
    )

    prediction_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    input_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("input_data.input_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("models.model_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # FK ke kolom UNIQUE (bukan PK) -> master SAR tidak bisa dihapus selama dipakai.
    predicted_class: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("sar_priorities.predicted_class", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    probabilities: Mapped[dict[str, Any]] = mapped_column(
        JsonType, nullable=False, default=dict
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="success", server_default="success"
    )
    prediction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    input_data: Mapped["InputData"] = relationship(back_populates="predictions")
    model: Mapped["Model"] = relationship(back_populates="predictions")
    sar_priority: Mapped["SarPriority"] = relationship(back_populates="predictions")

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return (
            f"<Prediction prediction_id={self.prediction_id} "
            f"class={self.predicted_class!r}>"
        )
