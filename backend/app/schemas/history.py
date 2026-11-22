"""Schema riwayat prediksi (list terpaginasi)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.prediction import PredictionRead


class HistoryPage(BaseModel):
    items: list[PredictionRead]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    pages: int = Field(ge=0)


__all__ = ["HistoryPage"]
