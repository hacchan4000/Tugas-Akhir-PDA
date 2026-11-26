"""Grid Search dengan Stratified K-Fold CV (PPT slide 29-37, direvisi).

Alur untuk SATU rasio holdout:
    1. data dibagi train/test (stratified);
    2. pada data train, tiap kombinasi hyperparameter dinilai dengan 5-fold CV
       (macro-F1 rata-rata antar fold);
    3. kombinasi terbaik di-refit pada 100% data train, lalu diuji sekali di test.

Preprocessor di-fit ulang di setiap fold HANYA pada data latih fold (anti leakage).

Dua optimasi (hasilnya identik dengan cara biasa, hanya lebih cepat):
    - KNN : matriks jarak per metric dihitung sekali per fold, dipakai ulang
            oleh semua kombinasi k dan weights.
    - RF  : hutan terbesar dilatih sekali per fold, lalu n pohon pertama dipakai
            untuk n_estimators yang lebih kecil.
"""

from __future__ import annotations

import itertools
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd

from ..constants import CLASS_LABELS, TARGET
from ..knn import compute_distances
from ..metrics import evaluate, macro_f1
from ..preprocessing import Preprocessor
from .splits import encode_target, stratified_holdout, stratified_kfold

FoldData = tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]


# ---------------------------------------------------------------------------
# Helper parameter grid
# ---------------------------------------------------------------------------
def _python_scalar(value: Any) -> Any:
    return value.item() if isinstance(value, np.generic) else value


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple, np.ndarray)):
        return list(value)
    return [value]


def _param_combinations(param_grid: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Semua kombinasi (hasil kali kartesius) dari ``param_grid``."""
    if not param_grid:
        return [{}]
    keys = list(param_grid.keys())
    values = [_as_list(value) for value in param_grid.values()]
    return [
        {key: _python_scalar(value) for key, value in zip(keys, combination)}
        for combination in itertools.product(*values)
    ]


# ---------------------------------------------------------------------------
# Prediksi per kombinasi (termasuk dua optimasi)
# ---------------------------------------------------------------------------
def _predict_knn_with_cached_distances(
    estimator_factory: Callable[..., Any],
    params: Mapping[str, Any],
    fold: FoldData,
    distance_cache: dict[str, np.ndarray],
) -> np.ndarray | None:
    """Optimasi KNN. Mengembalikan None bila estimator bukan KNN."""
    estimator = estimator_factory(**params)
    metric_attr = getattr(estimator, "metric", None)
    if metric_attr is None or not hasattr(estimator, "predict_from_distances"):
        return None

    X_train, y_train, X_valid, _ = fold
    metric = str(metric_attr)
    distances = distance_cache.get(metric)
    if distances is None:
        # Samakan dengan KNN.fit yang menyimpan data latih float32.
        train_for_distance = np.asarray(X_train, dtype=np.float32).astype(np.float64)
        distances = compute_distances(train_for_distance, X_valid, metric=metric)
        distance_cache[metric] = distances
    estimator.fit(X_train, y_train)
    return estimator.predict_from_distances(distances)


def _predict_rf_with_prefix_cache(
    estimator_factory: Callable[..., Any],
    params: Mapping[str, Any],
    max_n_estimators: int | None,
    fold: FoldData,
    prefix_cache: dict[Any, Any],
) -> np.ndarray | None:
    """Optimasi RF. Mengembalikan None bila tidak berlaku."""
    if max_n_estimators is None or "n_estimators" not in params:
        return None

    X_train, y_train, X_valid, _ = fold
    other_params = {k: v for k, v in params.items() if k != "n_estimators"}
    cache_key = tuple(sorted((key, repr(value)) for key, value in other_params.items()))

    cached = prefix_cache.get(cache_key)
    if cached is None:
        probe = estimator_factory(**params)
        if hasattr(probe, "predict_proba_per_tree"):
            forest = estimator_factory(
                **{**other_params, "n_estimators": max_n_estimators}
            )
            forest.fit(X_train, y_train)
            # (n_pohon, n_validasi, n_kelas); dihitung sekali per fold dan max_depth.
            cached = forest.predict_proba_per_tree(X_valid)
        else:
            cached = False
        prefix_cache[cache_key] = cached

    if cached is False:
        return None
    n_trees = int(params["n_estimators"])
    return np.argmax(cached[:n_trees].mean(axis=0), axis=1)


def _predict_for_params(
    estimator_factory: Callable[..., Any],
    params: Mapping[str, Any],
    max_n_estimators: int | None,
    fold: FoldData,
    prefix_cache: dict[Any, Any],
    distance_cache: dict[str, np.ndarray],
) -> np.ndarray:
    """Prediksi data validasi satu fold untuk satu kombinasi parameter."""
    predictions = _predict_knn_with_cached_distances(
        estimator_factory, params, fold, distance_cache
    )
    if predictions is not None:
        return predictions

    predictions = _predict_rf_with_prefix_cache(
        estimator_factory, params, max_n_estimators, fold, prefix_cache
    )
    if predictions is not None:
        return predictions

    # Jalur umum: latih estimator biasa lalu prediksi.
    X_train, y_train, X_valid, _ = fold
    estimator = estimator_factory(**params)
    estimator.fit(X_train, y_train)
    return np.asarray(estimator.predict(X_valid))


# ---------------------------------------------------------------------------
# Grid Search CV
# ---------------------------------------------------------------------------
def grid_search_cv(
    estimator_factory: Callable[..., Any],
    param_grid: Mapping[str, Any],
    df_train: pd.DataFrame,
    n_splits: int = 5,
    seed: int = 42,
    preprocessor_factory: Callable[[], Preprocessor] | None = None,
    on_step: Callable[[], None] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Tuning hyperparameter dengan Stratified K-Fold.

    Mengembalikan ``(tabel_hasil, best_params)``. Tabel diurutkan dari
    ``mean_macro_f1`` tertinggi (seri dipecah oleh ``std_macro_f1`` terkecil).
    """
    if not isinstance(df_train, pd.DataFrame):
        raise TypeError("df_train harus berupa pandas.DataFrame")
    if TARGET not in df_train.columns:
        raise ValueError(f"Kolom target {TARGET!r} tidak ditemukan pada df_train")
    if preprocessor_factory is None:
        preprocessor_factory = Preprocessor

    y = encode_target(df_train[TARGET].to_numpy())
    folds = stratified_kfold(y, n_splits=n_splits, seed=seed)

    # Anti-leakage: preprocessing hanya melihat data latih fold.
    fold_data: list[FoldData] = []
    for train_idx, valid_idx in folds:
        preprocessor = preprocessor_factory()
        X_train = preprocessor.fit_transform(df_train.iloc[train_idx])
        X_valid = preprocessor.transform(df_train.iloc[valid_idx])
        fold_data.append((X_train, y[train_idx], X_valid, y[valid_idx]))

    n_estimators_values = _as_list(param_grid.get("n_estimators", []))
    max_n_estimators = (
        max(int(v) for v in n_estimators_values) if n_estimators_values else None
    )

    combinations = _param_combinations(param_grid)
    scores_by_combo: list[list[float]] = [[] for _ in combinations]
    all_labels = np.arange(len(CLASS_LABELS), dtype=np.int64)

    # Fold di loop luar agar cache jarak/pohon hanya hidup selama satu fold (hemat RAM).
    for fold in fold_data:
        y_valid = fold[3]
        prefix_cache: dict[Any, Any] = {}
        distance_cache: dict[str, np.ndarray] = {}
        for combo_index, params in enumerate(combinations):
            predictions = _predict_for_params(
                estimator_factory,
                params,
                max_n_estimators,
                fold,
                prefix_cache,
                distance_cache,
            )
            # Selalu evaluasi ketiga kelas agar skor antar fold sebanding.
            scores_by_combo[combo_index].append(
                macro_f1(y_valid, predictions, labels=all_labels)
            )
            if on_step is not None:
                on_step()

    records: list[dict[str, Any]] = []
    for params, fold_scores in zip(combinations, scores_by_combo):
        scores = np.asarray(fold_scores, dtype=np.float64)
        records.append(
            {
                "params": dict(params),
                "mean_macro_f1": float(scores.mean()),
                "std_macro_f1": float(scores.std(ddof=0)),
                "fold_scores": fold_scores,
                "n_splits": int(n_splits),
            }
        )

    best_record = max(records, key=lambda r: (r["mean_macro_f1"], -r["std_macro_f1"]))

    param_columns = pd.DataFrame([record["params"] for record in records])
    metrics_columns = pd.DataFrame(
        [
            {
                "mean_macro_f1": record["mean_macro_f1"],
                "std_macro_f1": record["std_macro_f1"],
                "fold_scores": record["fold_scores"],
                "n_splits": record["n_splits"],
            }
            for record in records
        ]
    )
    results = pd.concat([param_columns, metrics_columns], axis=1)
    results = results.sort_values(
        ["mean_macro_f1", "std_macro_f1"], ascending=[False, True]
    ).reset_index(drop=True)

    return results, dict(best_record["params"])


def holdout_grid_search(
    estimator_factory: Callable[..., Any],
    param_grid: Mapping[str, Any],
    df: pd.DataFrame,
    test_sizes: Sequence[float] = (0.10, 0.15, 0.20),
    n_splits: int = 5,
    seed: int = 42,
    preprocessor_factory: Callable[[], Preprocessor] | None = None,
    on_step: Callable[[], None] | None = None,
) -> list[dict[str, Any]]:
    """Jalankan Grid Search CV untuk setiap rasio holdout (3 rasio x 5 fold).

    Tiap elemen hasil memuat parameter terbaik, skor CV, dan metrik data uji.
    """
    if preprocessor_factory is None:
        preprocessor_factory = Preprocessor
    if TARGET not in df.columns:
        raise ValueError(f"Kolom target {TARGET!r} tidak ditemukan pada df")

    y = encode_target(df[TARGET].to_numpy())
    reports: list[dict[str, Any]] = []

    for test_size in test_sizes:
        train_df, test_df, y_train, y_test = stratified_holdout(
            df, y, test_size=float(test_size), seed=seed
        )
        results, best_params = grid_search_cv(
            estimator_factory,
            param_grid,
            train_df,
            n_splits=n_splits,
            seed=seed,
            preprocessor_factory=preprocessor_factory,
            on_step=on_step,
        )

        # Refit parameter terbaik pada 100% data latih, uji sekali di data uji.
        preprocessor = preprocessor_factory()
        X_train = preprocessor.fit_transform(train_df)
        X_test = preprocessor.transform(test_df)
        estimator = estimator_factory(**best_params)
        estimator.fit(X_train, y_train)
        predictions = np.asarray(estimator.predict(X_test))
        if on_step is not None:
            on_step()

        reports.append(
            {
                "test_size": float(test_size),
                "n_train": int(len(train_df)),
                "n_test": int(len(test_df)),
                "best_params": best_params,
                "cv_mean_macro_f1": float(results.iloc[0]["mean_macro_f1"]),
                "cv_std_macro_f1": float(results.iloc[0]["std_macro_f1"]),
                "cv_results": results,
                "test_metrics": evaluate(y_test, predictions),
            }
        )

    return reports