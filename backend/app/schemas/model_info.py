"""Schema info model aktif + opsi dropdown form (meta)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class CoordinateBounds(BaseModel):
    latitude: tuple[float, float]
    longitude: tuple[float, float]


class MetaOptions(BaseModel):
    """Isi GET /api/v1/meta/options (dibaca dari `model_meta.json`)."""

    valid_categories: dict[str, list[str]]
    coordinate_bounds: CoordinateBounds
    class_labels: list[str]
    max_event_date: date


class ModelInfo(BaseModel):
    """Isi GET /api/v1/model/info (gabungan DB + artefak)."""

    model_id: int | None = None
    model_name: str
    model_version: str
    trained_date: datetime | None = None
    best_params: dict[str, Any] = Field(default_factory=dict)
    d_enc: int
    class_labels: list[str]
    evaluation_metrics: dict[str, Any] | None = None
    comparator_info: dict[str, Any] | None = None


__all__ = ["CoordinateBounds", "MetaOptions", "ModelInfo"]
