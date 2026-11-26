"""Memuat artefak notebook (`artifacts/<version>/`) dan menjalankan inferensi.

Artefak yang dibaca:
    preprocessor.json, model_meta.json, rf_trees.npz / knn_store.npz

Tidak ada `joblib`/pickle: model direkonstruksi lewat `from_arrays()` milik
`app/core`, jadi artefak aman dan portabel.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from app.core import (
    CATEGORICAL,
    CLASS_LABELS,
    KNNClassifier,
    Preprocessor,
    RandomForest,
    payload_to_frame,
)
from app.utils.errors import ModelUnavailableError

logger = logging.getLogger(__name__)

MODEL_TYPE_RF = "random_forest"
MODEL_TYPE_KNN = "knn"

COORDINATE_BOUNDS: dict[str, tuple[float, float]] = {
    "latitude": (-90.0, 90.0),
    "longitude": (-180.0, 180.0),
}


@dataclass(frozen=True, slots=True)
class PredictionResult:
    predicted_class: str
    confidence: float
    probabilities: dict[str, float]


def max_event_date() -> date:
    """Batas tanggal form: hari ini WIB (UTC+7) + toleransi UTC+14."""
    return (datetime.now(timezone.utc) + timedelta(hours=14)).date()


class ModelService:
    def __init__(self, artifact_dir: Path) -> None:
        self._dir = Path(artifact_dir)
        self._meta: dict[str, Any] = {}
        self._preprocessor: Preprocessor | None = None
        self._estimator: RandomForest | KNNClassifier | None = None
        self._class_labels: list[str] = list(CLASS_LABELS)
        self._valid_categories: dict[str, list[str]] = {}
        self._d_enc: int = 0
        self._ready = False
        self._error: str | None = None

    # -- status ------------------------------------------------------------
    @property
    def artifact_dir(self) -> Path:
        return self._dir

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def version(self) -> str:
        return str(self._meta.get("version") or self._dir.name)

    @property
    def model_type(self) -> str:
        return str(self._meta.get("model_type") or "")

    @property
    def model_name(self) -> str:
        return str(self._meta.get("model_name") or "")

    @property
    def best_params(self) -> dict[str, Any]:
        params = self._meta.get("best_params")
        return dict(params) if isinstance(params, dict) else {}

    @property
    def class_labels(self) -> list[str]:
        return list(self._class_labels)

    @property
    def valid_categories(self) -> dict[str, list[str]]:
        return {key: list(values) for key, values in self._valid_categories.items()}

    @property
    def d_enc(self) -> int:
        return self._d_enc

    # -- pemuatan ----------------------------------------------------------
    def load(self) -> bool:
        """Muat artefak. Kembalikan False (tanpa crash) bila belum tersedia.

        Sengaja menangkap ``Exception``, bukan daftar tipe tertentu. Artefak
        adalah berkas di disk yang bisa terpotong (notebook dihentikan saat
        menulis, disk penuh, salinan gagal), dan ``np.load`` melempar
        ``zipfile.BadZipFile`` / ``EOFError`` untuk kasus itu — keduanya di luar
        ``OSError``/``ValueError``. Daftar tipe yang sempit membuat satu berkas
        rusak menjatuhkan seluruh proses saat startup, padahal kontraknya
        (README + SPEC §2.4) adalah API tetap hidup dengan ``model_ready=false``.
        ``KeyboardInterrupt``/``SystemExit`` tetap lolos karena bukan ``Exception``.
        """
        try:
            self._load()
        except Exception as exc:  # noqa: BLE001 - lihat docstring di atas
            self._ready = False
            # Pesan terkurasi (ModelUnavailableError) dipakai apa adanya; error
            # tak terduga diberi nama tipenya supaya /health bisa didiagnosis.
            self._error = (
                str(exc)
                if isinstance(exc, ModelUnavailableError)
                else f"{type(exc).__name__}: {exc}"
            )
            logger.error("Artefak model gagal dimuat dari %s: %s", self._dir, exc)
            logger.debug("Detail kegagalan muat artefak", exc_info=True)
            return False

        self._ready = True
        self._error = None
        logger.info(
            "Model aktif dimuat: %s v%s (%d fitur, %s)",
            self.model_name or self.model_type,
            self.version,
            self._d_enc,
            self._dir,
        )
        return True

    def _load(self) -> None:
        meta_path = self._dir / "model_meta.json"
        prep_path = self._dir / "preprocessor.json"
        if not meta_path.is_file():
            raise ModelUnavailableError(f"model_meta.json tidak ditemukan di {self._dir}")
        if not prep_path.is_file():
            raise ModelUnavailableError(f"preprocessor.json tidak ditemukan di {self._dir}")

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if not isinstance(meta, dict):
            raise ModelUnavailableError("model_meta.json harus berupa objek JSON")

        preprocessor = Preprocessor.from_dict(
            json.loads(prep_path.read_text(encoding="utf-8"))
        )

        model_type = str(meta.get("model_type", "")).strip().lower()
        if model_type not in {MODEL_TYPE_RF, MODEL_TYPE_KNN}:
            raise ModelUnavailableError(
                f"model_type {model_type!r} tidak dikenal; "
                f"harus {MODEL_TYPE_RF!r} atau {MODEL_TYPE_KNN!r}"
            )

        class_labels = [str(label) for label in meta.get("class_labels", [])]
        if class_labels != CLASS_LABELS:
            raise ModelUnavailableError(
                f"class_labels artefak {class_labels} != {CLASS_LABELS} "
                "(urutan probabilitas akan salah)"
            )

        model_path = self._resolve_model_path(meta, model_type)
        with np.load(model_path, allow_pickle=False) as arrays:
            estimator: RandomForest | KNNClassifier
            if model_type == MODEL_TYPE_RF:
                estimator = RandomForest.from_arrays(arrays)
            else:
                estimator = KNNClassifier.from_arrays(arrays)

        d_enc = int(meta.get("d_enc", preprocessor.n_features_out_))
        if int(preprocessor.n_features_out_) != d_enc:
            raise ModelUnavailableError(
                f"d_enc artefak ({d_enc}) != n_features_out preprocessor "
                f"({preprocessor.n_features_out_})"
            )
        estimator_features = int(getattr(estimator, "n_features_in_", d_enc))
        if estimator_features != d_enc:
            raise ModelUnavailableError(
                f"model mengharapkan {estimator_features} fitur, preprocessor "
                f"menghasilkan {d_enc}"
            )

        self._meta = meta
        self._preprocessor = preprocessor
        self._estimator = estimator
        self._class_labels = class_labels
        self._d_enc = d_enc
        self._valid_categories = self._resolve_valid_categories(meta, preprocessor)

    def _resolve_model_path(self, meta: Mapping[str, Any], model_type: str) -> Path:
        files = meta.get("artifact_files")
        model_file = files.get("model") if isinstance(files, Mapping) else None
        if not model_file:
            model_file = (
                "rf_trees.npz" if model_type == MODEL_TYPE_RF else "knn_store.npz"
            )

        root = self._dir.resolve()
        path = (root / str(model_file)).resolve()
        if path.parent != root:
            raise ModelUnavailableError(
                f"path artefak model {model_file!r} keluar dari folder versi"
            )
        if not path.is_file():
            raise ModelUnavailableError(f"file artefak model tidak ditemukan: {path}")
        return path

    @staticmethod
    def _resolve_valid_categories(
        meta: Mapping[str, Any], preprocessor: Preprocessor
    ) -> dict[str, list[str]]:
        raw = meta.get("valid_categories") or meta.get("categorical_options")
        resolved: dict[str, list[str]] = {}

        if isinstance(raw, Mapping):
            for column in CATEGORICAL:
                values = raw.get(column)
                if isinstance(values, (list, tuple)) and values:
                    cleaned = sorted(
                        {str(v).strip().lower() for v in values if str(v).strip()}
                    )
                    if cleaned:
                        resolved[column] = cleaned

        if len(resolved) != len(CATEGORICAL):
            # Fallback: kategori yang benar-benar dipelajari one-hot encoder.
            encoder = getattr(preprocessor, "encoder_", None)
            categories = getattr(encoder, "categories_", None) or []
            columns = list(getattr(preprocessor, "categorical_columns", CATEGORICAL))
            for column, values in zip(columns, categories):
                resolved.setdefault(
                    column, sorted({str(v).strip().lower() for v in values if str(v).strip()})
                )

        missing = [c for c in CATEGORICAL if not resolved.get(c)]
        if missing:
            raise ModelUnavailableError(
                f"valid_categories tidak lengkap untuk kolom: {missing}"
            )
        return {column: sorted(resolved[column]) for column in CATEGORICAL}

    # -- inferensi ---------------------------------------------------------
    def predict_one(self, payload: Mapping[str, Any]) -> PredictionResult:
        if not self._ready or self._preprocessor is None or self._estimator is None:
            raise ModelUnavailableError(
                self._error or "Artefak model belum dimuat"
            )

        frame = payload_to_frame(dict(payload))
        vector = self._preprocessor.transform_one(frame).reshape(1, -1)
        if vector.shape[1] != self._d_enc:
            raise ModelUnavailableError(
                f"vektor fitur {vector.shape[1]} != d_enc {self._d_enc}"
            )

        raw = np.asarray(self._estimator.predict_proba(vector), dtype=np.float64)
        expected = (1, len(self._class_labels))
        if raw.shape != expected:
            raise ModelUnavailableError(
                f"predict_proba menghasilkan {raw.shape}, seharusnya {expected}"
            )

        row = np.clip(raw[0], 0.0, None)
        total = float(row.sum())
        row = row / total if total > 0 else np.full(row.shape, 1.0 / row.size)

        index = int(self._estimator.predict(vector)[0])
        # Indeks negatif akan lolos diam-diam di Python (`labels[-1]` = kelas
        # terakhir), jadi batas bawah ikut diperiksa — bukan hanya atas.
        if not 0 <= index < len(self._class_labels):
            raise ModelUnavailableError(
                f"estimator memprediksi indeks kelas {index}, di luar rentang "
                f"0..{len(self._class_labels) - 1}"
            )
        label = self._class_labels[index]
        probabilities = {
            label_name: float(prob)
            for label_name, prob in zip(self._class_labels, row)
        }
        return PredictionResult(
            predicted_class=label,
            confidence=float(row[index]),
            probabilities=probabilities,
        )

    # -- metadata untuk API ------------------------------------------------
    def options(self) -> dict[str, Any]:
        return {
            "valid_categories": self.valid_categories,
            "coordinate_bounds": {
                "latitude": list(COORDINATE_BOUNDS["latitude"]),
                "longitude": list(COORDINATE_BOUNDS["longitude"]),
            },
            "class_labels": self.class_labels,
            "max_event_date": max_event_date(),
        }

    def info(self) -> dict[str, Any]:
        if not self._ready:
            raise ModelUnavailableError(self._error or "Artefak model belum dimuat")
        return {
            "model_name": self.model_name,
            "model_version": self.version,
            "trained_date": self._trained_at(),
            "best_params": self.best_params,
            "d_enc": self._d_enc,
            "class_labels": self.class_labels,
            "evaluation_metrics": self._meta.get("evaluation_metrics")
            or self._meta.get("test_metrics"),
            "comparator_info": self._meta.get("comparator_info")
            or self._meta.get("comparator"),
        }

    def _trained_at(self) -> datetime | None:
        raw = self._meta.get("trained_at")
        if not isinstance(raw, str):
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None


__all__ = ["ModelService", "PredictionResult", "COORDINATE_BOUNDS", "max_event_date"]
