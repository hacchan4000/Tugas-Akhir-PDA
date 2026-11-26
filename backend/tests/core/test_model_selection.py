"""Tes split stratified, K-Fold, dan Grid Search CV."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from app.core import (
    KNNClassifier,
    Preprocessor,
    RandomForest,
    encode_target,
    grid_search_cv,
    holdout_grid_search,
    stratified_holdout,
    stratified_kfold,
)


# ---------------------------------------------------------------------------
# Split
# ---------------------------------------------------------------------------
def test_stratified_holdout_preserves_proportions() -> None:
    y = np.array([0] * 150 + [1] * 100 + [2] * 50)
    X = np.arange(y.size).reshape(-1, 1)

    X_train, X_test, y_train, y_test = stratified_holdout(
        X, y, test_size=0.15, seed=42
    )

    assert len(X_train) + len(X_test) == len(X)
    assert len(y_train) + len(y_test) == len(y)
    assert set(y_test.tolist()) == {0, 1, 2}

    overall = np.bincount(y, minlength=3) / len(y)
    observed = np.bincount(y_test, minlength=3) / len(y_test)
    assert np.allclose(observed, overall, atol=0.02)

    # Tidak ada indeks yang bocor antara train dan test.
    train_ids = set(X_train[:, 0].tolist())
    test_ids = set(X_test[:, 0].tolist())
    assert train_ids.isdisjoint(test_ids)

    # Determinisme seed.
    again = stratified_holdout(X, y, test_size=0.15, seed=42)
    assert np.array_equal(again[2], y_train)
    assert np.array_equal(again[3], y_test)


def test_stratified_kfold_partitions_and_coverage() -> None:
    y = np.array([0] * 60 + [1] * 40 + [2] * 20)
    folds = stratified_kfold(y, n_splits=5, seed=42)

    assert len(folds) == 5
    seen = np.concatenate([test_idx for _, test_idx in folds])
    assert sorted(seen.tolist()) == list(range(y.size))

    for train_idx, test_idx in folds:
        assert len(test_idx) == 24
        assert set(y[test_idx].tolist()) == {0, 1, 2}
        assert len(np.intersect1d(train_idx, test_idx)) == 0
        assert len(train_idx) + len(test_idx) == y.size


def test_encode_target_roundtrip() -> None:
    encoded = encode_target(["small", "large", "medium", "small"])
    assert encoded.tolist() == [0, 2, 1, 0]
    with pytest.raises(ValueError, match="tidak dikenal"):
        encode_target(["small", "raksasa"])


# ---------------------------------------------------------------------------
# Grid Search
# ---------------------------------------------------------------------------
def test_grid_search_cv_fits_preprocessor_per_fold_only(make_engineered) -> None:
    class RecordingPreprocessor(Preprocessor):
        instances: list["RecordingPreprocessor"] = []

        def __init__(self) -> None:
            super().__init__()
            self.fit_rows: int | None = None
            RecordingPreprocessor.instances.append(self)

        def fit(self, df: pd.DataFrame) -> "RecordingPreprocessor":
            self.fit_rows = len(df)
            return super().fit(df)

    RecordingPreprocessor.instances = []
    df = make_engineered(n=120, seed=4)
    n_splits = 4

    results, best = grid_search_cv(
        lambda **params: KNNClassifier(**params),
        {"k": [3, 5], "weights": ["uniform"]},
        df,
        n_splits=n_splits,
        seed=42,
        preprocessor_factory=RecordingPreprocessor,
    )

    assert len(results) == 2
    assert best["k"] in (3, 5)
    assert {"k", "weights", "mean_macro_f1", "std_macro_f1"}.issubset(results.columns)
    assert results["mean_macro_f1"].is_monotonic_decreasing

    instances = RecordingPreprocessor.instances
    assert len(instances) == n_splits
    # Total baris yang di-fit = n * (n_splits - 1), dan tidak pernah full data.
    assert sum(instance.fit_rows for instance in instances) == len(df) * (n_splits - 1)
    assert all(instance.fit_rows < len(df) for instance in instances)


def test_grid_search_cv_rf_prefix_optimization(make_engineered) -> None:
    df = make_engineered(n=120, seed=6)
    results, best = grid_search_cv(
        lambda **params: RandomForest(**params),
        {"n_estimators": [2, 4], "max_depth": [2, 3]},
        df,
        n_splits=3,
        seed=42,
    )

    assert len(results) == 4
    assert best["n_estimators"] in (2, 4)
    assert best["max_depth"] in (2, 3)
    assert results["mean_macro_f1"].is_monotonic_decreasing


def test_holdout_grid_search_runs_each_ratio(make_engineered) -> None:
    df = make_engineered(n=150, seed=8)
    reports = holdout_grid_search(
        lambda **params: KNNClassifier(**params),
        {"k": [3], "weights": ["uniform"], "metric": ["euclidean"]},
        df,
        test_sizes=(0.10, 0.20),
        n_splits=3,
        seed=42,
    )

    assert [report["test_size"] for report in reports] == [0.10, 0.20]
    for report in reports:
        assert report["n_train"] + report["n_test"] == len(df)
        assert set(report["test_metrics"]) >= {
            "macro_f1",
            "balanced_accuracy",
            "accuracy",
            "precision_macro",
            "recall_macro",
            "confusion_matrix",
        }