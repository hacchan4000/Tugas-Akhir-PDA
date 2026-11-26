"""Endpoint health check (public)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies.deps import AppSettings, DbSession, ModelServiceDep

router = APIRouter(tags=["Health"])

# Pesan pengganti di production: pesan asli bisa memuat path absolut server.
_GENERIC_MODEL_ERROR = "Artefak model gagal dimuat; periksa log server"


class HealthResponse(BaseModel):
    status: str
    database: str
    model_ready: bool
    model_version: str | None = None
    model_error: str | None = None


@router.get("/health", response_model=HealthResponse, summary="Status API & artefak")
def health(
    db: DbSession, model: ModelServiceDep, settings: AppSettings
) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError:
        database = "error"

    # Endpoint ini publik. Di production jangan bocorkan detail filesystem
    # (mis. "model_meta.json tidak ditemukan di /app/artifacts/v1") — cukup
    # sinyal bahwa model belum siap, detailnya ada di log.
    model_error = model.error
    if model_error and settings.ENV == "production":
        model_error = _GENERIC_MODEL_ERROR

    return HealthResponse(
        status="ok" if database == "ok" else "degraded",
        database=database,
        model_ready=model.is_ready,
        model_version=model.version if model.is_ready else None,
        model_error=model_error,
    )


__all__ = ["router"]
