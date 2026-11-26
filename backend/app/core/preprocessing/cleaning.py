"""Tahap 1 preprocessing: Data Cleaning (data reduction pada baris).

Mengubah data mentah GLC menjadi data bersih.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from ..constants import CATEGORICAL, CLASS_LABELS, TARGET, TARGET_ALIASES
from .helpers import clean_categorical, parse_dates, require_columns

_RAW_REQUIRED = [TARGET, "event_date", "latitude", "longitude", *CATEGORICAL]


def clean_raw(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Bersihkan data mentah GLC.

    Urutan: buang target kosong/``unknown`` -> parse ``event_date`` -> validasi
    koordinat -> buang duplikat -> imputasi kategorikal -> gabungkan target
    ``very_large``/``catastrophic`` menjadi ``large``.
    """
    if not isinstance(df_raw, pd.DataFrame):
        raise TypeError("df_raw harus berupa pandas.DataFrame")
    require_columns(df_raw, _RAW_REQUIRED)

    df = df_raw.copy()

    # 1. Normalisasi target, buang kosong/"unknown", lalu gabungkan alias.
    target = df[TARGET].astype("string").str.strip().str.lower()
    keep = target.notna() & (target != "") & (target != "unknown")
    df = df.loc[keep].copy()
    target = target.loc[keep].replace(TARGET_ALIASES)
    df[TARGET] = target
    df = df.loc[df[TARGET].isin(CLASS_LABELS)].copy()

    # 2. Parse event_date; baris yang gagal di-parse dibuang.
    parsed = parse_dates(df["event_date"])
    df = df.loc[parsed.notna()].copy()
    df["event_date"] = parsed.loc[parsed.notna()]

    # 3. Validasi rentang koordinat.
    lat = pd.to_numeric(df["latitude"], errors="coerce")
    lon = pd.to_numeric(df["longitude"], errors="coerce")
    valid_coord = (
        lat.notna()
        & lon.notna()
        & lat.between(-90.0, 90.0)
        & lon.between(-180.0, 180.0)
    )
    df = df.loc[valid_coord].copy()
    df["latitude"] = lat.loc[valid_coord].astype(np.float64)
    df["longitude"] = lon.loc[valid_coord].astype(np.float64)

    # 4. Buang duplikat identik berdasarkan (event_date, latitude, longitude).
    df = df.drop_duplicates(
        subset=["event_date", "latitude", "longitude"], keep="first"
    )

    # 5. Imputasi nilai kosong/whitespace pada 4 fitur kategorikal.
    for col in CATEGORICAL:
        df[col] = clean_categorical(df[col])

    return df.reset_index(drop=True)