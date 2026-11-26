"""Konstanta bersama untuk pipeline ML manual.

Modul ini sengaja tidak mengimpor scikit-learn. Seluruh modul di ``app/core``
hanya boleh bergantung pada NumPy, pandas, dan pustaka standar Python.
"""

from __future__ import annotations

# Urutan label menentukan urutan kolom pada ``predict_proba``.
CLASS_LABELS: list[str] = ["small", "medium", "large"]

# Empat fitur kategorikal (di-one-hot-encode).
CATEGORICAL: list[str] = [
    "landslide_category",
    "landslide_trigger",
    "landslide_setting",
    "location_accuracy",
]

# Lima fitur numerik hasil feature engineering. Fitur ``year`` sengaja TIDAK
# disertakan sesuai keputusan desain pada SPEC.md bagian 2.1.
NUMERIC: list[str] = ["month_sin", "month_cos", "geo_x", "geo_y", "geo_z"]

# Kolom target pada data mentah/bersih.
TARGET: str = "landslide_size"

# Sembilan fitur model, dalam urutan tetap (numerik dulu, lalu kategorikal).
FEATURE_COLUMNS: list[str] = NUMERIC + CATEGORICAL

# Pemetaan label <-> indeks kelas. Indeks dipakai oleh model manual supaya
# probabilitas selalu konsisten dengan urutan CLASS_LABELS.
CLASS_TO_INDEX: dict[str, int] = {label: i for i, label in enumerate(CLASS_LABELS)}
INDEX_TO_CLASS: dict[int, str] = {i: label for i, label in enumerate(CLASS_LABELS)}

# Nilai target mentah yang digabung menjadi "large" (SPEC.md 2.1).
TARGET_ALIASES: dict[str, str] = {
    "very_large": "large",
    "catastrophic": "large",
}

__all__ = [
    "CLASS_LABELS",
    "CATEGORICAL",
    "NUMERIC",
    "TARGET",
    "FEATURE_COLUMNS",
    "CLASS_TO_INDEX",
    "INDEX_TO_CLASS",
    "TARGET_ALIASES",
]
