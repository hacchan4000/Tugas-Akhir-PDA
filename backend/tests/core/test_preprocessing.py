"""Tes cleaning, feature engineering, scaler, one-hot, dan Preprocessor."""

from __future__ import annotations
import json
import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from app.core import (
    CATEGORICAL,
    FEATURE_COLUMNS,
    NUMERIC,
    TARGET,
    ManualOneHotEncoder,
    ManualStandardScaler,
    Preprocessor,
    clean_raw,
    engineer_features,
    payload_to_frame,
)


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------
def test_clean_raw_applies_all_rules(raw_frame: pd.DataFrame) -> None:
    cleaned = clean_raw(raw_frame)

    assert len(cleaned) == 5
    assert set(cleaned[TARGET]) == {"medium", "large"}
    assert cleaned[TARGET].value_counts().to_dict() == {"large": 3, "medium": 2}
    assert pd.api.types.is_datetime64_any_dtype(cleaned["event_date"])
    assert cleaned["latitude"].dtype == np.float64
    assert cleaned["longitude"].dtype == np.float64

    # Tidak ada nilai kosong/whitespace pada fitur kategorikal.
    for column in CATEGORICAL:
        assert cleaned[column].notna().all()
        assert (cleaned[column].str.strip() != "").all()

    # Duplikat (event_date, latitude, longitude) benar-benar hilang.
    assert not cleaned.duplicated(
        subset=["event_date", "latitude", "longitude"]
    ).any()

    # Baris dengan kategorikal whitespace menjadi "unknown".
    assert "unknown" in set(cleaned["landslide_category"])


def test_clean_raw_requires_columns() -> None:
    with pytest.raises(ValueError, match="Kolom wajib"):
        clean_raw(pd.DataFrame({"event_date": ["2020-01-01"]}))


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------
def test_engineer_features_has_nine_features(engineered_frame: pd.DataFrame) -> None:
    assert list(engineered_frame.columns) == FEATURE_COLUMNS + [TARGET]
    assert "year" not in engineered_frame.columns
    assert engineered_frame.shape[1] == 10  # 9 fitur + target

    numeric = engineered_frame[NUMERIC].to_numpy(dtype=np.float64)
    assert np.isfinite(numeric).all()

    # event_date tidak boleh ikut sebagai fitur (hanya bulan yang dipakai).
    assert "event_date" not in engineered_frame.columns

    # geo_* berada pada bola satuan.
    radius = (
        engineered_frame["geo_x"] ** 2
        + engineered_frame["geo_y"] ** 2
        + engineered_frame["geo_z"] ** 2
    )
    assert np.allclose(radius.to_numpy(), 1.0, atol=1e-12)


def test_engineer_features_exact_formulas() -> None:
    frame = pd.DataFrame(
        {
            "event_date": ["2020-07-15", "2020-12-15"],
            "latitude": [-8.0, 45.0],
            "longitude": [115.0, -90.0],
            "landslide_category": ["landslide", "mudslide"],
            "landslide_trigger": ["rain", "rain"],
            "landslide_setting": ["urban", "urban"],
            "location_accuracy": ["exact", "exact"],
        }
    )
    out = engineer_features(frame)

    month = np.array([7.0, 12.0])
    assert np.allclose(out["month_sin"], np.sin(2 * np.pi * month / 12))
    assert np.allclose(out["month_cos"], np.cos(2 * np.pi * month / 12))
    assert np.isclose(out.loc[0, "month_sin"], -0.5)
    assert np.isclose(out.loc[1, "month_cos"], 1.0)

    lat = np.deg2rad(np.array([-8.0, 45.0]))
    lon = np.deg2rad(np.array([115.0, -90.0]))
    assert np.allclose(out["geo_x"], np.cos(lat) * np.cos(lon))
    assert np.allclose(out["geo_y"], np.cos(lat) * np.sin(lon))
    assert np.allclose(out["geo_z"], np.sin(lat))
    assert TARGET not in out.columns


# ---------------------------------------------------------------------------
# payload_to_frame (jalur inference dari form)
# ---------------------------------------------------------------------------
def test_payload_to_frame_matches_engineer_features(
    raw_frame: pd.DataFrame, engineered_frame: pd.DataFrame
) -> None:
    cleaned = clean_raw(raw_frame)
    row = cleaned.iloc[0]

    payload = {
        "event_date": pd.Timestamp(row["event_date"]).strftime("%Y-%m-%d"),
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"]),
        **{column: str(row[column]) for column in CATEGORICAL},
    }
    from_payload = payload_to_frame(payload)
    from_frame = engineer_features(cleaned.iloc[[0]])[FEATURE_COLUMNS]

    assert list(from_payload.columns) == FEATURE_COLUMNS

    preprocessor = Preprocessor().fit(engineered_frame)
    assert np.allclose(
        preprocessor.transform(from_payload),
        preprocessor.transform(from_frame),
        atol=1e-12,
    )


def test_payload_to_frame_rejects_invalid_input() -> None:
    base = {
        "event_date": "2026-07-15",
        "latitude": -8.1,
        "longitude": 115.1,
        "landslide_category": "landslide",
        "landslide_trigger": "rain",
        "landslide_setting": "urban",
        "location_accuracy": "exact",
    }
    with pytest.raises(ValueError, match="event_date"):
        payload_to_frame({**base, "event_date": "31-02-2026"})
    with pytest.raises(ValueError, match="latitude"):
        payload_to_frame({**base, "latitude": 91})
    with pytest.raises(ValueError, match="longitude"):
        payload_to_frame({**base, "longitude": -180.5})
    with pytest.raises(ValueError, match="Field wajib"):
        payload_to_frame({k: v for k, v in base.items() if k != "landslide_trigger"})


# ---------------------------------------------------------------------------
# Scaler dan encoder manual vs scikit-learn
# ---------------------------------------------------------------------------
def test_manual_scaler_matches_sklearn() -> None:
    rng = np.random.default_rng(1)
    X = rng.normal(loc=3.0, scale=2.0, size=(80, 5))
    X[:, 3] = 7.0  # kolom konstan: scale harus 1.0

    ours = ManualStandardScaler().fit(X)
    ref = StandardScaler().fit(X)

    assert np.allclose(ours.mean_, ref.mean_, atol=1e-12)
    assert np.allclose(ours.scale_, ref.scale_, atol=1e-12)
    assert ours.scale_[3] == 1.0
    assert np.allclose(ours.transform(X), ref.transform(X), atol=1e-12)


def test_manual_ohe_matches_sklearn_and_ignores_unknown() -> None:
    X_train = np.array(
        [["a", "x"], ["b", "y"], ["a", "y"], ["c", "x"]], dtype=object
    )
    X_test = np.array([["a", "x"], ["zzz", "y"], ["c", "qqq"]], dtype=object)

    ours = ManualOneHotEncoder().fit(X_train)
    ref = OneHotEncoder(handle_unknown="ignore", sparse_output=False).fit(X_train)

    assert ours.categories_ == [list(map(str, c)) for c in ref.categories_]
    encoded = ours.transform(X_test)
    assert encoded.dtype == np.float64
    assert np.allclose(encoded, ref.transform(X_test))
    # Kategori asing menghasilkan vektor 0 pada kolom terkait.
    assert np.all(encoded[1, : len(ours.categories_[0])] == 0.0)
    assert np.all(encoded[2, len(ours.categories_[0]) :] == 0.0)


# ---------------------------------------------------------------------------
# Preprocessor gabungan
# ---------------------------------------------------------------------------
def test_preprocessor_matches_sklearn_column_transformer(make_engineered) -> None:
    df = make_engineered(n=160, seed=2)

    ours = Preprocessor().fit(df)
    ref = ColumnTransformer(
        [
            ("num", StandardScaler(), NUMERIC),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL,
            ),
        ]
    ).fit(df)

    X_ours = ours.transform(df)
    X_ref = np.asarray(ref.transform(df), dtype=np.float64)

    assert X_ours.shape == X_ref.shape
    assert X_ours.shape[1] == ours.n_features_out_
    assert np.allclose(X_ours, X_ref, atol=1e-12)

    # Kategori baru saat inference harus diabaikan (bukan error).
    new_row = df.iloc[[0]].copy()
    new_row["landslide_category"] = "kategori_tidak_dikenal"
    new_encoded = ours.transform(new_row)
    new_ref = np.asarray(ref.transform(new_row), dtype=np.float64)
    assert np.allclose(new_encoded, new_ref, atol=1e-12)

    # transform_one == baris matriks transform.
    for index in (0, 7, 42):
        single = ours.transform_one(df.iloc[[index]])
        assert single.ndim == 1
        assert np.allclose(single, X_ours[index], atol=1e-12)

    # Serialisasi JSON -> from_dict menghasilkan output identik.
    payload = json.loads(json.dumps(ours.to_dict()))
    restored = Preprocessor.from_dict(payload)
    assert restored.n_features_out_ == ours.n_features_out_
    assert np.allclose(restored.transform(df), X_ours, atol=1e-12)