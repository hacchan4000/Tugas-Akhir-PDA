"""Query helper untuk `input_data` + `predictions` (riwayat prediksi)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import InputData, Model, Prediction

# Jumlah baris per batch saat mengekspor riwayat. 500 baris cukup untuk
# menyembunyikan latensi per-query tanpa menahan memori.
EXPORT_BATCH_SIZE = 500


@dataclass(frozen=True, slots=True)
class HistoryFilters:
    """Filter yang sama dipakai untuk list, count, dan export (anti-drift)."""

    date_from: date | None = None
    date_to: date | None = None
    region: str | None = None
    q: str | None = None


def _like_pattern(text: str) -> str:
    """Bungkus teks pencarian jadi pola ``%...%`` dengan wildcard di-escape.

    Tanpa ini ``?q=%`` mencocokkan seluruh riwayat (dan ``?q=_`` mencocokkan
    satu karakter apa pun) — bukan SQL injection, tapi wildcard injection yang
    membuat filter terasa rusak. ``ESCAPE '\\'`` dipakai di sisi query supaya
    perilakunya sama di SQLite dan PostgreSQL.
    """
    escaped = (
        text.strip()
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"


def _apply_filters(stmt: Select[Any], filters: HistoryFilters) -> Select[Any]:
    if filters.date_from is not None:
        stmt = stmt.where(InputData.event_date >= filters.date_from)
    if filters.date_to is not None:
        stmt = stmt.where(InputData.event_date <= filters.date_to)
    if filters.region:
        stmt = stmt.where(
            InputData.nama_wilayah.ilike(_like_pattern(filters.region), escape="\\")
        )
    if filters.q:
        pattern = _like_pattern(filters.q)
        stmt = stmt.where(
            or_(
                InputData.nama_wilayah.ilike(pattern, escape="\\"),
                InputData.landslide_category.ilike(pattern, escape="\\"),
                InputData.landslide_trigger.ilike(pattern, escape="\\"),
                InputData.landslide_setting.ilike(pattern, escape="\\"),
                Prediction.predicted_class.ilike(pattern, escape="\\"),
            )
        )
    return stmt


def _base_query(user_id: int, filters: HistoryFilters) -> Select[Any]:
    stmt = (
        select(Prediction, InputData, Model)
        .join(InputData, Prediction.input_id == InputData.input_id)
        .join(Model, Prediction.model_id == Model.model_id)
        .where(InputData.user_id == user_id)
        # Hindari N+1 saat HistoryService memetakan sar_priority per baris.
        .options(selectinload(Prediction.sar_priority))
    )
    return _apply_filters(stmt, filters)


def list_for_user(
    db: Session,
    user_id: int,
    filters: HistoryFilters,
    *,
    page: int,
    page_size: int,
) -> list[tuple[Prediction, InputData, Model]]:
    stmt = (
        _base_query(user_id, filters)
        .order_by(Prediction.prediction_date.desc(), Prediction.prediction_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return [tuple(row) for row in db.execute(stmt).all()]  # type: ignore[misc]


def count_for_user(db: Session, user_id: int, filters: HistoryFilters) -> int:
    stmt = (
        select(func.count())
        .select_from(Prediction)
        .join(InputData, Prediction.input_id == InputData.input_id)
        .where(InputData.user_id == user_id)
    )
    stmt = _apply_filters(stmt, filters)
    return int(db.scalar(stmt) or 0)


def iter_for_user(
    db: Session,
    user_id: int,
    filters: HistoryFilters,
    *,
    batch_size: int | None = None,
) -> Iterator[tuple[Prediction, InputData, Model]]:
    """Iterator *keyset*, bukan list: memori dibatasi ``batch_size`` baris.

    Sebelumnya fungsi ini mengembalikan seluruh riwayat sebagai list, jadi satu
    operator dengan riwayat besar bisa menghabiskan memori proses saat menekan
    "Ekspor CSV". Sekarang baris diambil per batch dan langsung dialirkan.

    ``OFFSET`` sengaja tidak dipakai: pada tabel besar, offset membuat database
    memindai ulang dari awal untuk setiap batch. Cursor memakai pasangan
    ``(prediction_date, prediction_id)`` yang unik dan sudah terindeks
    (``ix_predictions_user_created``).

    Batch dibaca berurutan, tidak pernah bersamaan, sehingga satu ``Session``
    tetap aman dipakai.
    """
    limit = batch_size if batch_size and batch_size > 0 else EXPORT_BATCH_SIZE
    cursor: tuple[datetime, int] | None = None

    while True:
        stmt = (
            _base_query(user_id, filters)
            .order_by(Prediction.prediction_date.asc(), Prediction.prediction_id.asc())
            .limit(limit)
        )
        if cursor is not None:
            tanggal, prediction_id = cursor
            stmt = stmt.where(
                or_(
                    Prediction.prediction_date > tanggal,
                    and_(
                        Prediction.prediction_date == tanggal,
                        Prediction.prediction_id > prediction_id,
                    ),
                )
            )

        rows: list[tuple[Prediction, InputData, Model]] = [
            tuple(row) for row in db.execute(stmt).all()  # type: ignore[misc]
        ]
        if not rows:
            return
        yield from rows

        last_prediction = rows[-1][0]
        cursor = (last_prediction.prediction_date, last_prediction.prediction_id)
        if len(rows) < limit:
            return


def get_for_user(
    db: Session, prediction_id: int, user_id: int
) -> tuple[Prediction, InputData, Model] | None:
    stmt = _base_query(user_id, HistoryFilters()).where(
        Prediction.prediction_id == prediction_id
    )
    row = db.execute(stmt).first()
    return tuple(row) if row is not None else None  # type: ignore[return-value]


def create_input(db: Session, **values: Any) -> InputData:
    record = InputData(**values)
    db.add(record)
    db.flush()
    return record


def create_prediction(db: Session, **values: Any) -> Prediction:
    record = Prediction(**values)
    db.add(record)
    db.flush()
    return record


__all__ = [
    "EXPORT_BATCH_SIZE",
    "HistoryFilters",
    "list_for_user",
    "count_for_user",
    "iter_for_user",
    "get_for_user",
    "create_input",
    "create_prediction",
]
