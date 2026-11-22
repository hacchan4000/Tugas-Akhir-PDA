"""Tabel `sar_priorities`: master pemetaan kelas -> level & rekomendasi SAR."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.prediction import Prediction


class SarPriority(Base):
    __tablename__ = "sar_priorities"

    sar_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    predicted_class: Mapped[str] = mapped_column(
        String(10), nullable=False, unique=True
    )
    sar_priority_level: Mapped[str] = mapped_column(String(20), nullable=False)
    sar_recommendation: Mapped[str] = mapped_column(Text, nullable=False)

    predictions: Mapped[list["Prediction"]] = relationship(back_populates="sar_priority")

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return (
            f"<SarPriority predicted_class={self.predicted_class!r} "
            f"level={self.sar_priority_level!r}>"
        )
