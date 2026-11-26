"""Tahap 2 preprocessing: Feature Engineering (fitur turunan).

Dari ``event_date`` dan koordinat dibuat 5 fitur numerik; tahun sengaja dibuang.
Bersama 4 fitur kategorikal, totalnya 9 fitur model.
"""

from __future__ import annotations
from typing import Any, Mapping
import numpy as np
import pandas as pd
from ..constants import (
    CATEGORICAL,
    FEATURE_COLUMNS,
    NUMERIC,
    TARGET,
    TARGET_ALIASES,
)
from .helpers import clean_categorical, parse_dates, require_columns

_FEATURE_REQUIRED = ["event_date", "latitude", "longitude", *CATEGORICAL]


def engineer_features(df_clean: pd.DataFrame) -> pd.DataFrame:
    """Hasilkan tepat 9 fitur model (tanpa kolom ``year``).

    Kolom keluaran selalu ``NUMERIC + CATEGORICAL`` (lalu ``TARGET`` bila ada).

    Rumus:
        month_sin = sin(2*pi*bulan/12) | month_cos = cos(2*pi*bulan/12)
        geo_x = cos(lat)*cos(lon) | geo_y = cos(lat)*sin(lon) | geo_z = sin(lat)
    """
    if not isinstance(df_clean, pd.DataFrame):
        raise TypeError("df_clean harus berupa pandas.DataFrame")
    require_columns(df_clean, _FEATURE_REQUIRED)

    has_target = TARGET in df_clean.columns
    out_cols = FEATURE_COLUMNS + ([TARGET] if has_target else [])

    if len(df_clean) == 0:
        empty = pd.DataFrame(index=df_clean.index)
        for col in NUMERIC:
            empty[col] = pd.Series(dtype=np.float64)
        for col in CATEGORICAL:
            empty[col] = pd.Series(dtype=object)
        if has_target:
            empty[TARGET] = pd.Series(dtype=object)
        return empty[out_cols]

    dates = parse_dates(df_clean["event_date"])
    if dates.isna().any():
        bad = int(dates.isna().sum())
        raise ValueError(f"event_date tidak valid pada {bad} baris data bersih")

    lat = pd.to_numeric(df_clean["latitude"], errors="coerce").to_numpy(
        dtype=np.float64
    )
    lon = pd.to_numeric(df_clean["longitude"], errors="coerce").to_numpy(
        dtype=np.float64
    )
    if not np.isfinite(lat).all() or not np.isfinite(lon).all():
        raise ValueError("latitude/longitude mengandung nilai tidak valid")

    month = dates.dt.month.to_numpy(dtype=np.float64)
    lat_rad = np.deg2rad(lat)
    lon_rad = np.deg2rad(lon)

    out = pd.DataFrame(index=df_clean.index)
    out["month_sin"] = np.sin(2.0 * np.pi * month / 12.0)
    out["month_cos"] = np.cos(2.0 * np.pi * month / 12.0)
    out["geo_x"] = np.cos(lat_rad) * np.cos(lon_rad)
    out["geo_y"] = np.cos(lat_rad) * np.sin(lon_rad)
    out["geo_z"] = np.sin(lat_rad)

    for col in CATEGORICAL:
        out[col] = clean_categorical(df_clean[col])

    if has_target:
        target = df_clean[TARGET].astype("string").str.strip().str.lower()
        out[TARGET] = target.replace(TARGET_ALIASES).astype(str)

    return out[out_cols]


def payload_to_frame(payload: Mapping[str, Any]) -> pd.DataFrame:
    """Ubah satu payload API (form operator) menjadi DataFrame 1 baris, 9 fitur."""
    if not isinstance(payload, Mapping):
        raise TypeError("payload harus berupa mapping/dict")

    required = ["event_date", "latitude", "longitude", *CATEGORICAL]
    missing = [key for key in required if key not in payload or payload[key] is None]
    if missing:
        raise ValueError(f"Field wajib tidak lengkap: {missing}")

    row = {key: payload[key] for key in required}
    df = pd.DataFrame([row])

    parsed = parse_dates(df["event_date"])
    if bool(parsed.isna().iloc[0]):
        raise ValueError("event_date tidak valid; gunakan format YYYY-MM-DD")
    df["event_date"] = parsed

    if isinstance(payload["latitude"], bool) or isinstance(payload["longitude"], bool):
        raise ValueError("latitude dan longitude harus berupa angka, bukan boolean")

    lat = pd.to_numeric(df["latitude"], errors="coerce")
    lon = pd.to_numeric(df["longitude"], errors="coerce")
    if bool(lat.isna().iloc[0]) or not (-90.0 <= float(lat.iloc[0]) <= 90.0):
        raise ValueError("latitude harus berupa angka antara -90 dan 90")
    if bool(lon.isna().iloc[0]) or not (-180.0 <= float(lon.iloc[0]) <= 180.0):
        raise ValueError("longitude harus berupa angka antara -180 dan 180")
    
    df["latitude"] = lat.astype(np.float64)
    df["longitude"] = lon.astype(np.float64)

    return engineer_features(df)