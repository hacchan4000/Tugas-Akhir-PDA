"""Tabel `input_data`: input form operator + hasil reverse geocoding."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    String,
    desc,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utc_now

if TYPE_CHECKING:
    from app.db.models.prediction import Prediction
    from app.db.models.user import User

GEOCODING_STATUSES = ("success", "not_found", "error")


class InputData(Base):
    __tablename__ = "input_data"
    __table_args__ = (
        CheckConstraint(
            "geocoding_status IN ('success', 'not_found', 'error')",
            name="geocoding_status_valid",
        ),
        # SPEC 3.1: index (user_id, created_at DESC) untuk riwayat terbaru dulu.
        Index("ix_input_data_user_created", "user_id", desc("created_at")),
        # Filter/pencarian wilayah per user.
        Index("ix_input_data_user_region", "user_id", "nama_wilayah"),
    )

    input_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    latitude: Mapped[float] = mapped_column(Double, nullable=False)
    longitude: Mapped[float] = mapped_column(Double, nullable=False)
    landslide_category: Mapped[str] = mapped_column(String(50), nullable=False)
    landslide_trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    landslide_setting: Mapped[str] = mapped_column(String(50), nullable=False)
    location_accuracy: Mapped[str] = mapped_column(String(50), nullable=False)
    nama_wilayah: Mapped[str | None] = mapped_column(String(255), nullable=True)
    geocoding_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="error"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    user: Mapped["User"] = relationship(back_populates="input_data")
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="input_data",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return (
            f"<InputData input_id={self.input_id} user_id={self.user_id} "
            f"event_date={self.event_date}>"
        )
