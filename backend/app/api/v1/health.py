"""Endpoint health check (public)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies.deps import DbSession, ModelServiceDep

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    database: str
    model_ready: bool
    model_version: str | None = None
    model_error: str | None = None


@router.get("/health", response_model=HealthResponse, summary="Status API & artefak")
def health(db: DbSession, model: ModelServiceDep) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError:
        database = "error"

    return HealthResponse(
        status="ok" if database == "ok" else "degraded",
        database=database,
        model_ready=model.is_ready,
        model_version=model.version if model.is_ready else None,
        model_error=model.error,
    )


__all__ = ["router", "HealthResponse"]
