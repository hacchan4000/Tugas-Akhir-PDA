import math
import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Model as ModelRecord


FALLBACK_REGION = "Wilayah tidak teridentifikasi / Koordinat terpencil"
BACKEND_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSOR_PATH = Path(
    os.getenv("PREPROCESSOR_PATH", str(BACKEND_ROOT / "models" / "preprocessor.pkl"))
)
NOMINATIM_TIMEOUT = float(os.getenv("NOMINATIM_TIMEOUT", "5"))

CATEGORICAL_FEATURES = [
    "landslide_category",
    "landslide_trigger",
    "landslide_setting",
    "location_accuracy",
]

SAR_PRIORITY_MAP: dict[str, str] = {
    "small": "Prioritas Rendah - pengawasan rutin dan evakuasi preventif terbatas",
    "medium": "Prioritas Menengah - siagakan tim SAR dan penutupan jalur terdampak",
    "large": "Prioritas Tinggi - mobilisasi tim SAR, evakuasi segera, dan koordinasi darurat",
}

VALID_CLASSES = set(SAR_PRIORITY_MAP)


def reverse_geocode(latitude: float, longitude: float) -> str:
    geolocator = Nominatim(
        user_agent=os.getenv("NOMINATIM_USER_AGENT", "basarnas-landslide-classifier"),
        timeout=NOMINATIM_TIMEOUT,
    )

    try:
        location = geolocator.reverse(
            (latitude, longitude),
            language="id",
            exactly_one=True,
        )
        if location is None:
            return FALLBACK_REGION

        raw = getattr(location, "raw", {})
        address = raw.get("address", {}) if isinstance(raw, dict) else {}
        if not address:
            return FALLBACK_REGION

        parts = (
            address.get("province"),
            address.get("city"),
            address.get("municipality"),
            address.get("county"),
            address.get("district"),
            address.get("village"),
        )
        region_parts = list(dict.fromkeys(part for part in parts if part))
        if not region_parts:
            return FALLBACK_REGION
        return ", ".join(region_parts)
    except (GeocoderTimedOut, GeocoderServiceError, TimeoutError):
        return FALLBACK_REGION


def _enum_value(value: Any) -> str:
    return str(value.value if hasattr(value, "value") else value)


def _resolve_artifact_path(model_file: str) -> Path:
    path = Path(model_file).expanduser()
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    if not path.exists():
        raise FileNotFoundError(f"File model tidak ditemukan: {path}")
    if path.suffix.lower() != ".pkl":
        raise ValueError("File model aktif harus berformat .pkl")
    return path


def load_active_model(db: Session) -> ModelRecord:
    model_record = db.scalar(
        select(ModelRecord)
        .where(ModelRecord.model_status == "active")
        .limit(1)
    )
    if model_record is None:
        raise LookupError("Tidak ada model aktif yang terdaftar")
    return model_record


def encode_categorical_features(input_data: dict[str, Any]) -> np.ndarray:
    if not PREPROCESSOR_PATH.exists():
        raise FileNotFoundError(
            f"Artefak preprocessor tidak ditemukan: {PREPROCESSOR_PATH}"
        )

    preprocessor = joblib.load(PREPROCESSOR_PATH)
    if isinstance(preprocessor, dict):
        preprocessor = preprocessor.get("encoder") or preprocessor.get("preprocessor")
    if preprocessor is None:
        raise ValueError("Artefak preprocessor tidak memiliki encoder/preprocessor")

    dataframe = pd.DataFrame(
        [[_enum_value(input_data[name]) for name in CATEGORICAL_FEATURES]],
        columns=CATEGORICAL_FEATURES,
    )
    transformed = preprocessor.transform(dataframe)
    encoded = np.asarray(transformed)
    if encoded.ndim == 1:
        encoded = encoded.reshape(1, -1)
    encoded = encoded.astype(float)

    if encoded.shape[1] != 4:
        raise ValueError(
            "Preprocessor harus menghasilkan tepat 4 fitur kategorikal "
            "(bukan one-hot encoding dengan dimensi tambahan)"
        )
    return encoded.reshape(-1)


def build_exact_features(input_data: dict[str, Any]) -> np.ndarray:
    event_date = input_data["event_date"]
    if isinstance(event_date, str):
        from datetime import date

        event_date = date.fromisoformat(event_date)

    latitude = float(input_data["latitude"])
    longitude = float(input_data["longitude"])
    lat_radians = math.radians(latitude)
    lon_radians = math.radians(longitude)

    numeric_features = np.array(
        [
            int(event_date.year),
            math.sin(2 * math.pi * event_date.month / 12),
            math.cos(2 * math.pi * event_date.month / 12),
            math.cos(lat_radians) * math.cos(lon_radians),
            math.cos(lat_radians) * math.sin(lon_radians),
            math.sin(lat_radians),
        ],
        dtype=float,
    )
    categorical_features = encode_categorical_features(input_data)
    features = np.concatenate([numeric_features, categorical_features])

    if features.shape[0] != 10:
        raise RuntimeError(
            f"Preprocessing menghasilkan {features.shape[0]} fitur, harus tepat 10"
        )
    return features.reshape(1, -1)


def get_sar_priority(predicted_class: str) -> str:
    normalized = str(predicted_class).strip().lower()
    if normalized not in VALID_CLASSES:
        raise ValueError(
            f"Kelas prediksi '{predicted_class}' tidak valid; "
            "harus small, medium, atau large"
        )
    return SAR_PRIORITY_MAP[normalized]


def predict_with_active_model(
    db: Session,
    input_data: dict[str, Any],
) -> tuple[str, str, ModelRecord]:
    model_record = load_active_model(db)
    model_path = _resolve_artifact_path(model_record.model_file)
    classifier = joblib.load(model_path)
    features = build_exact_features(input_data)

    prediction = classifier.predict(features)
    predicted_values = np.asarray(prediction).reshape(-1)
    if predicted_values.size != 1:
        raise RuntimeError("Model aktif harus menghasilkan tepat satu kelas prediksi")

    predicted_class = str(predicted_values[0]).strip().lower()
    sar_priority = get_sar_priority(predicted_class)
    return predicted_class, sar_priority, model_record
