"""Orkestrator prediksi: validasi -> inferensi -> geocoding -> simpan DB."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core import CATEGORICAL
from app.db.models import InputData, Model, Prediction, User
from app.db.repositories import model_repo, prediction_repo
from app.schemas.prediction import PredictionCreate
from app.services.geocoding_service import GeocodingService
from app.services.model_service import ModelService
from app.utils.errors import (
    ApiValidationError,
    FieldError,
    ModelUnavailableError,
    PersistenceError,
)
from app.utils.sar import SarPriorityInfo, resolve_sar

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CreatedPrediction:
    prediction: Prediction
    input_data: InputData
    model: Model
    sar: SarPriorityInfo


class PredictionService:
    def __init__(
        self,
        db: Session,
        model_service: ModelService,
        geocoding_service: GeocodingService,
    ) -> None:
        self._db = db
        self._model = model_service
        self._geocoding = geocoding_service

    def create(self, *, user: User, payload: PredictionCreate) -> CreatedPrediction:
        self._validate_categories(payload)

        if not self._model.is_ready:
            raise ModelUnavailableError(
                self._model.error or "Artefak model belum dimuat"
            )

        # Urutan sengaja: kerja CPU (inferensi) dan jaringan (geocoding)
        # diselesaikan SEBELUM query DB, supaya koneksi pool tidak tertahan
        # selama panggilan Nominatim yang bisa sampai 2 detik.
        try:
            result = self._model.predict_one(payload.model_dump())
        except ValueError as exc:
            # Payload lolos Pydantic tapi ditolak pipeline fitur (mis. NaN).
            raise ApiValidationError.single("payload", str(exc)) from exc

        model_record = model_repo.get_active(self._db)
        if model_record is None:
            raise ModelUnavailableError(
                "Belum ada model aktif di tabel models; jalankan aplikasi sekali "
                "agar registri model disinkronkan dari artefak"
            )
        if model_record.model_version != self._model.version:
            raise ModelUnavailableError(
                f"model aktif di DB (v{model_record.model_version}) berbeda dengan "
                f"artefak yang dimuat (v{self._model.version}); restart aplikasi"
            )

        sar = resolve_sar(self._db, result.predicted_class)
        nama_wilayah, geocoding_status = self._geocoding.reverse(
            payload.latitude, payload.longitude
        )

        try:
            input_row = prediction_repo.create_input(
                self._db,
                user_id=user.user_id,
                event_date=payload.event_date,
                latitude=payload.latitude,
                longitude=payload.longitude,
                landslide_category=payload.landslide_category,
                landslide_trigger=payload.landslide_trigger,
                landslide_setting=payload.landslide_setting,
                location_accuracy=payload.location_accuracy,
                nama_wilayah=nama_wilayah,
                geocoding_status=geocoding_status,
            )
            prediction = prediction_repo.create_prediction(
                self._db,
                input_id=input_row.input_id,
                model_id=model_record.model_id,
                predicted_class=result.predicted_class,
                confidence_score=result.confidence,
                probabilities=result.probabilities,
                status="success",
            )
            # Satu transaksi: input_data + predictions commit bersama.
            self._db.commit()
        except SQLAlchemyError as exc:
            self._db.rollback()
            logger.exception("Gagal menyimpan prediksi ke database")
            raise PersistenceError(
                "Gagal menyimpan hasil prediksi ke database"
            ) from exc

        return CreatedPrediction(
            prediction=prediction,
            input_data=input_row,
            model=model_record,
            sar=sar,
        )

    def _validate_categories(self, payload: PredictionCreate) -> None:
        valid = self._model.valid_categories
        if not valid:
            # Artefak belum siap -> biarkan pengecekan status model yang bicara.
            return

        errors: list[FieldError] = []
        for field in CATEGORICAL:
            allowed = valid.get(field, [])
            value = getattr(payload, field)
            if allowed and value not in allowed:
                errors.append(
                    FieldError(
                        field=field,
                        message=(
                            f"nilai {value!r} tidak valid; "
                            f"pilihan: {', '.join(allowed)}"
                        ),
                    )
                )
        if errors:
            raise ApiValidationError(errors)


__all__ = ["PredictionService", "CreatedPrediction"]
