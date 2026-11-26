"""Fungsi bantu internal untuk paket preprocessing.

Dipakai bersama oleh cleaning, features, transformers, dan preprocessor.
Tidak ditujukan untuk diimpor dari luar paket ini.
"""

from __future__ import annotations
from typing import Any, Sequence
import numpy as np
import pandas as pd


def parse_dates(values: pd.Series | Sequence[Any]) -> pd.Series:
    """Parse tanggal menjadi datetime64 tz-naive tanpa melempar error (NaT bila gagal)."""
    if isinstance(values, pd.Series) and pd.api.types.is_datetime64_any_dtype(values):
        if getattr(values.dt, "tz", None) is not None:
            return values.dt.tz_convert("UTC").dt.tz_localize(None)
        return values
    try:
        parsed = pd.to_datetime(values, errors="coerce", format="mixed", utc=True)
    except (TypeError, ValueError):
        parsed = pd.to_datetime(values, errors="coerce", utc=True)
    if isinstance(parsed, pd.Series):
        return parsed.dt.tz_localize(None)
    return pd.Series(parsed.tz_localize(None))


def clean_categorical(values: pd.Series) -> pd.Series:
    """Strip whitespace, lowercase, dan ganti kosong/whitespace dengan ``unknown``."""
    s = values.astype("string").str.strip().str.lower()
    s = s.mask(s.isna() | (s == ""), "unknown")
    return s.astype(str)


def as_2d_float(X: Any, name: str = "X") -> np.ndarray:
    """Pastikan X matriks 2D float64 tanpa NaN/inf."""
    arr = np.asarray(X, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError(f"{name} harus berupa matriks 2 dimensi, diterima {arr.shape}")
    if not np.isfinite(arr).all():
        raise ValueError(f"{name} mengandung NaN atau nilai tak hingga")
    return arr


def as_2d_object(X: Any, name: str = "X") -> np.ndarray:
    """Pastikan X matriks 2D bertipe object (untuk kolom kategorikal)."""
    arr = np.asarray(X, dtype=object)
    if arr.ndim != 2:
        raise ValueError(f"{name} harus berupa matriks 2 dimensi, diterima {arr.shape}")
    return arr


def require_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    """Lempar ValueError bila ada kolom wajib yang tidak ada di ``df``."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom wajib tidak ditemukan: {missing}")