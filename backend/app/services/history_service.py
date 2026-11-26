"""Riwayat prediksi: query terpaginasi + pemetaan ke schema response."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.db.models import InputData, Model, Prediction
from app.db.repositories import prediction_repo
from app.db.repositories.prediction_repo import HistoryFilters
from app.schemas.prediction import PredictionRead
from app.utils.sar import FALLBACK_SAR_PRIORITIES

Row = tuple[Prediction, InputData, Model]


@dataclass(frozen=True, slots=True)
class HistoryQuery:
    page: int = 1
    page_size: int = 10
    date_from: date | None = None
    date_to: date | None = None
    region: str | None = None
    q: str | None = None

    def to_filters(self) -> HistoryFilters:
        return HistoryFilters(
            date_from=self.date_from,
            date_to=self.date_to,
            region=self.region,
            q=self.q,
        )


def row_to_read(row: Row) -> PredictionRead:
    prediction, input_data, model = row
    sar = prediction.sar_priority
    if sar is not None:
        level = sar.sar_priority_level
        recommendation = sar.sar_recommendation
    else:
        level, recommendation = FALLBACK_SAR_PRIORITIES.get(
            prediction.predicted_class, ("", "")
        )
    return PredictionRead.from_row(
        prediction,
        input_data,
        model,
        sar_level=level,
        sar_recommendation=recommendation,
    )


class HistoryService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(self, user_id: int, query: HistoryQuery) -> tuple[list[PredictionRead], int]:
        filters = query.to_filters()
        rows = prediction_repo.list_for_user(
            self._db,
            user_id,
            filters,
            page=query.page,
            page_size=query.page_size,
        )
        total = prediction_repo.count_for_user(self._db, user_id, filters)
        return [row_to_read(row) for row in rows], total

    def get(self, user_id: int, prediction_id: int) -> PredictionRead | None:
        row = prediction_repo.get_for_user(self._db, prediction_id, user_id)
        return row_to_read(row) if row is not None else None

    def iter_for_export(
        self, user_id: int, query: HistoryQuery
    ) -> Iterator[PredictionRead]:
        """Alirkan riwayat satu per satu (bukan list) supaya memori tetap datar."""
        for row in prediction_repo.iter_for_user(self._db, user_id, query.to_filters()):
            yield row_to_read(row)


__all__ = ["HistoryQuery", "HistoryService", "row_to_read"]
