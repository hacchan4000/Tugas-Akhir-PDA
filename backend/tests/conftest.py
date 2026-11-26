"""Konfigurasi pytest dan fixture bersama untuk seluruh tes.

scikit-learn HANYA dipakai di folder tests sebagai pembanding kebenaran;
modul app/core tidak boleh mengimpornya.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import make_classification
from sklearn.preprocessing import StandardScaler

from app.core import CLASS_LABELS, clean_raw, engineer_features


@pytest.fixture(scope="session")
def raw_frame() -> pd.DataFrame:
    """Data mentah kecil yang sengaja memuat semua kasus cleaning."""
    rows = [
        # valid
        dict(event_date="2020-01-15", latitude=-8.1, longitude=115.1,
             landslide_size="medium", category="landslide"),
        # target kosong / unknown -> dibuang
        dict(event_date="2020-01-16", latitude=-8.2, longitude=115.2,
             landslide_size="unknown", category="mudslide"),
        dict(event_date="2020-01-17", latitude=-8.3, longitude=115.3,
             landslide_size=None, category="mudslide"),
        # tanggal gagal parse -> dibuang
        dict(event_date="not-a-date", latitude=-8.4, longitude=115.4,
             landslide_size="small", category="rock_fall"),
        # koordinat di luar rentang -> dibuang
        dict(event_date="2020-01-18", latitude=91.0, longitude=115.5,
             landslide_size="small", category="rock_fall"),
        dict(event_date="2020-01-19", latitude=-8.6, longitude=-181.0,
             landslide_size="small", category="rock_fall"),
        # duplikat (event_date, latitude, longitude) -> dibuang
        dict(event_date="2020-01-15", latitude=-8.1, longitude=115.1,
             landslide_size="large", category="complex"),
        # alias target -> large
        dict(event_date="2020-02-20", latitude=-8.7, longitude=115.7,
             landslide_size="very_large", category="complex"),
        dict(event_date="2020-03-21", latitude=-8.8, longitude=115.8,
             landslide_size="catastrophic", category="debris_flow"),
        # huruf besar + spasi -> large
        dict(event_date="2020-04-22", latitude=-8.9, longitude=115.9,
             landslide_size=" LARGE ", category="landslide"),
        # kategorikal kosong/whitespace -> unknown
        dict(event_date="2020-05-23", latitude=-9.0, longitude=116.0,
             landslide_size="medium", category="   "),
    ]
    frame = pd.DataFrame(rows)
    frame["landslide_trigger"] = ["rain"] * len(rows)
    frame["landslide_setting"] = ["urban"] * len(rows)
    frame["location_accuracy"] = ["exact"] * len(rows)
    frame = frame.rename(columns={"category": "landslide_category"})
    frame.loc[10, "landslide_setting"] = None
    return frame


@pytest.fixture(scope="session")
def engineered_frame(raw_frame: pd.DataFrame) -> pd.DataFrame:
    """Hasil clean_raw + engineer_features dari ``raw_frame``."""
    return engineer_features(clean_raw(raw_frame))


@pytest.fixture(scope="session")
def make_engineered():
    """Pabrik data engineered sintetis: ``make_engineered(n=150, seed=0)``."""

    def _make(n: int = 150, seed: int = 0) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        raw = pd.DataFrame(
            {
                "event_date": pd.Timestamp("2020-01-01")
                + pd.to_timedelta(rng.integers(0, 365 * 3, size=n), unit="D"),
                "latitude": rng.uniform(-60.0, 60.0, size=n),
                "longitude": rng.uniform(-170.0, 170.0, size=n),
                "landslide_category": rng.choice(
                    ["landslide", "mudslide", "rock_fall", "complex"], size=n
                ),
                "landslide_trigger": rng.choice(
                    ["rain", "downpour", "unknown"], size=n
                ),
                "landslide_setting": rng.choice(
                    ["urban", "natural_slope", "unknown"], size=n
                ),
                "location_accuracy": rng.choice(["exact", "1km", "5km"], size=n),
                "landslide_size": rng.choice(
                    CLASS_LABELS, size=n, p=[0.3, 0.5, 0.2]
                ),
            }
        )
        return engineer_features(clean_raw(raw))

    return _make


@pytest.fixture(scope="session")
def three_class_data() -> tuple[np.ndarray, np.ndarray]:
    """Dataset numerik 3 kelas yang terstandarisasi (dipakai tes KNN dan RF)."""
    X, y = make_classification(
        n_samples=240,
        n_features=6,
        n_informative=5,
        n_redundant=0,
        n_classes=3,
        n_clusters_per_class=1,
        class_sep=1.5,
        random_state=0,
    )
    X = StandardScaler().fit_transform(X)
    return X, y