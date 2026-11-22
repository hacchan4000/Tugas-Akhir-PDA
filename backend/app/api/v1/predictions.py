"""Endpoint prediksi: buat, riwayat terpaginasi, detail, dan ekspor CSV.

Urutan route penting: `/export` didaftarkan SEBELUM `/{prediction_id}` supaya
"export" tidak diparse sebagai integer ID.
"""

from __future__ import annotations

import math
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.dependencies.deps import (
    CurrentUser,
    DbSession,
    GeocodingServiceDep,
    ModelServiceDep,
)
from app.schemas.history import HistoryPage
from app.schemas.prediction import PredictionCreate, PredictionRead
from app.services.export_service import EXPORT_FILENAME, stream_csv
from app.services.history_service import HistoryQuery, HistoryService
from app.services.prediction_service import PredictionService
from app.utils.errors import ApiValidationError

router = APIRouter(prefix="/predictions", tags=["Predictions"])

DateFromQuery = Query(default=None, description="Filter awal tanggal kejadian (YYYY-MM-DD)")
DateToQuery = Query(default=None, description="Filter akhir tanggal kejadian (YYYY-MM-DD)")
RegionQuery = Query(default=None, max_length=255, description="Cari nama wilayah")
SearchQuery = Query(default=None, max_length=100, description="Cari teks bebas")


def _history_query(
    *,
    page: int = 1,
    page_size: int = 10,
    date_from: date | None,
    date_to: date | None,
    region: str | None,
    q: str | None,
) -> HistoryQuery:
    if date_from and date_to and date_from > date_to:
        raise ApiValidationError.single(
            "date_to", "date_to tidak boleh lebih awal dari date_from"
        )
    return HistoryQuery(
        page=page,
        page_size=page_size,
        date_from=date_from,
        date_to=date_to,
        region=region.strip() if region else None,
        q=q.strip() if q else None,
    )


@router.get("/export", summary="Ekspor CSV seluruh riwayat terfilter")
def export_predictions(
    current_user: CurrentUser,
    db: DbSession,
    date_from: date | None = DateFromQuery,
    date_to: date | None = DateToQuery,
    region: str | None = RegionQuery,
    q: str | None = SearchQuery,
) -> StreamingResponse:
    query = _history_query(
        page=1,
        page_size=1,
        date_from=date_from,
        date_to=date_to,
        region=region,
        q=q,
    )
    items = HistoryService(db).all_for_export(current_user.user_id, query)
    return StreamingResponse(
        stream_csv(items),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{EXPORT_FILENAME}"',
            "Cache-Control": "no-store",
        },
    )


@router.post(
    "",
    response_model=PredictionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Jalankan prediksi dan simpan riwayat",
)
def create_prediction(
    payload: PredictionCreate,
    current_user: CurrentUser,
    db: DbSession,
    model: ModelServiceDep,
    geocoding: GeocodingServiceDep,
) -> PredictionRead:
    created = PredictionService(db, model, geocoding).create(
        user=current_user, payload=payload
    )
    return PredictionRead.from_row(
        created.prediction,
        created.input_data,
        created.model,
        sar_level=created.sar.level,
        sar_recommendation=created.sar.recommendation,
    )


@router.get("", response_model=HistoryPage, summary="Riwayat prediksi milik operator")
def list_predictions(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    date_from: date | None = DateFromQuery,
    date_to: date | None = DateToQuery,
    region: str | None = RegionQuery,
    q: str | None = SearchQuery,
) -> HistoryPage:
    query = _history_query(
        page=page,
        page_size=page_size,
        date_from=date_from,
        date_to=date_to,
        region=region,
        q=q,
    )
    items, total = HistoryService(db).list(current_user.user_id, query)
    pages = math.ceil(total / page_size) if total else 0
    return HistoryPage(
        items=items, total=total, page=page, page_size=page_size, pages=pages
    )


@router.get("/{prediction_id}", response_model=PredictionRead, summary="Detail 1 prediksi")
def get_prediction(
    prediction_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> PredictionRead:
    item = HistoryService(db).get(current_user.user_id, prediction_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Riwayat prediksi tidak ditemukan",
        )
    return item


__all__ = ["router"]
