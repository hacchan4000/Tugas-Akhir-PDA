"""Schema prediksi: payload form operator dan representasi hasil."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models import InputData, Model, Prediction

PredictedClass = Literal["small", "medium", "large"]

_CATEGORY_FIELDS = (
    "landslide_category",
    "landslide_trigger",
    "landslide_setting",
    "location_accuracy",
)


class PredictionCreate(BaseModel):
    """Payload POST /api/v1/predictions.

    Validasi di sini hanya bentuk & rentang. Kesesuaian nilai kategorikal
    dengan `valid_categories` artefak dicek di `PredictionService` (butuh
    metadata model yang dimuat saat startup).
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_date: date
    latitude: float = Field(ge=-90.0, le=90.0, allow_inf_nan=False)
    longitude: float = Field(ge=-180.0, le=180.0, allow_inf_nan=False)
    landslide_category: str = Field(min_length=1, max_length=50)
    landslide_trigger: str = Field(min_length=1, max_length=50)
    landslide_setting: str = Field(min_length=1, max_length=50)
    location_accuracy: str = Field(min_length=1, max_length=50)

    @field_validator("event_date")
    @classmethod
    def _not_beyond_today_wib(cls, value: date) -> date:
        limit = (datetime.now(timezone.utc) + timedelta(hours=14)).date()
        if value > limit:
            raise ValueError(
                f"event_date tidak boleh melebihi {limit.isoformat()} (hari ini WIB)"
            )
        return value

    @field_validator(*_CATEGORY_FIELDS)
    @classmethod
    def _normalize_category(cls, value: str) -> str:
        return value.strip().lower()


class PredictionRead(BaseModel):
    prediction_id: int
    input_id: int
    event_date: date
    latitude: float
    longitude: float
    nama_wilayah: str | None
    geocoding_status: str
    landslide_category: str
    landslide_trigger: str
    landslide_setting: str
    location_accuracy: str
    predicted_class: PredictedClass
    confidence_score: float
    probabilities: dict[str, float]
    sar_priority_level: str
    sar_recommendation: str
    status: str
    prediction_date: datetime
    model_name: str
    model_version: str

    @classmethod
    def from_row(
        cls,
        prediction: Prediction,
        input_data: InputData,
        model: Model,
        *,
        sar_level: str,
        sar_recommendation: str,
    ) -> "PredictionRead":
        probabilities: dict[str, Any] = prediction.probabilities or {}
        return cls(
            prediction_id=prediction.prediction_id,
            input_id=input_data.input_id,
            event_date=input_data.event_date,
            latitude=float(input_data.latitude),
            longitude=float(input_data.longitude),
            nama_wilayah=input_data.nama_wilayah,
            geocoding_status=input_data.geocoding_status,
            landslide_category=input_data.landslide_category,
            landslide_trigger=input_data.landslide_trigger,
            landslide_setting=input_data.landslide_setting,
            location_accuracy=input_data.location_accuracy,
            predicted_class=prediction.predicted_class,  # type: ignore[arg-type]
            confidence_score=float(prediction.confidence_score),
            probabilities={str(k): float(v) for k, v in probabilities.items()},
            sar_priority_level=sar_level,
            sar_recommendation=sar_recommendation,
            status=prediction.status,
            prediction_date=prediction.prediction_date,
            model_name=model.model_name,
            model_version=model.model_version,
        )


__all__ = ["PredictionCreate", "PredictionRead", "PredictedClass"]
