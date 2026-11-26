"""Tes jarak dan KNN manual dibandingkan dengan scikit-learn."""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pytest
from sklearn.neighbors import KNeighborsClassifier
from app.core import KNNClassifier, compute_distances


# ---------------------------------------------------------------------------
# Jarak
# ---------------------------------------------------------------------------
def _brute_force_distances(
    X_train: np.ndarray, X_query: np.ndarray, metric: str
) -> np.ndarray:
    out = np.zeros((X_query.shape[0], X_train.shape[0]), dtype=np.float64)
    for i, query in enumerate(X_query):
        diff = np.abs(X_train - query[None, :])
        if metric == "euclidean":
            out[i] = np.sqrt(np.sum(diff**2, axis=1))
        elif metric == "manhattan":
            out[i] = diff.sum(axis=1)
        else:
            out[i] = diff.max(axis=1)
    return out


@pytest.mark.parametrize("metric", ["euclidean", "manhattan", "chebyshev"])
def test_compute_distances_matches_bruteforce(metric: str) -> None:
    rng = np.random.default_rng(3)
    X_train = rng.normal(size=(40, 6))
    X_query = rng.normal(size=(300, 6))  # > CHUNK_SIZE untuk menguji chunking

    distances = compute_distances(X_train, X_query, metric=metric)
    expected = _brute_force_distances(X_train, X_query, metric)

    assert distances.shape == (300, 40)
    assert np.allclose(distances, expected, atol=1e-10)


def test_compute_distances_rejects_bad_input() -> None:
    with pytest.raises(ValueError, match="metric"):
        compute_distances(np.zeros((3, 2)), np.zeros((2, 2)), metric="cosine")
    with pytest.raises(ValueError, match="Jumlah fitur"):
        compute_distances(np.zeros((3, 2)), np.zeros((2, 3)))


# ---------------------------------------------------------------------------
# Klasifikasi
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("metric", ["euclidean", "manhattan", "chebyshev"])
@pytest.mark.parametrize("weights", ["uniform", "distance"])
def test_knn_matches_sklearn(three_class_data, metric: str, weights: str) -> None:
    X, y = three_class_data
    ours = KNNClassifier(k=5, metric=metric, weights=weights).fit(X, y)
    ref = KNeighborsClassifier(
        n_neighbors=5, metric=metric, weights=weights, algorithm="brute"
    ).fit(X, y)

    ours_proba = ours.predict_proba(X)
    ref_proba = ref.predict_proba(X)

    assert ours_proba.shape == (len(X), 3)
    assert np.allclose(ours_proba.sum(axis=1), 1.0, atol=1e-12)
    assert np.allclose(ours_proba, ref_proba, atol=1e-6)
    assert np.array_equal(ours.predict(X), ref.predict(X))


def test_knn_distance_weights_zero_distance() -> None:
    X = np.array([[0.0, 0.0], [0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [2.0, 2.0]])
    y = np.array([0, 0, 1, 2, 1])
    query = np.array([[0.0, 0.0]])

    ours = KNNClassifier(k=3, weights="distance").fit(X, y)
    ref = KNeighborsClassifier(
        n_neighbors=3, weights="distance", algorithm="brute"
    ).fit(X, y)

    assert np.allclose(ours.predict_proba(query), ref.predict_proba(query))
    assert ours.predict(query)[0] == 0
    assert np.allclose(ours.predict_proba(query)[0], [1.0, 0.0, 0.0])


def test_knn_tie_break_uses_nearest_neighbor() -> None:
    # Ketiga kelas berjarak sama-sama menjadi tetangga (proba seri 1/3),
    # tetapi kelas 2 punya tetangga terdekat (jarak 1 vs 2).
    X = np.array([[2.0, 0.0], [0.0, 2.0], [1.0, 0.0]])
    y = np.array([0, 1, 2])
    query = np.array([[0.0, 0.0]])

    model = KNNClassifier(k=3, weights="uniform").fit(X, y)
    proba = model.predict_proba(query)
    assert np.allclose(proba[0], [1 / 3, 1 / 3, 1 / 3])
    assert model.predict(query)[0] == 2


def test_knn_serialization_roundtrip(tmp_path: Path, three_class_data) -> None:
    X, y = three_class_data
    model = KNNClassifier(k=7, metric="manhattan", weights="distance").fit(X, y)

    path = tmp_path / "knn_store.npz"
    np.savez(path, **model.to_arrays())
    with np.load(path) as arrays:
        restored = KNNClassifier.from_arrays(arrays)

    assert restored.k == 7
    assert restored.metric == "manhattan"
    assert restored.weights == "distance"
    assert np.allclose(model.predict_proba(X), restored.predict_proba(X))
    assert np.array_equal(model.predict(X), restored.predict(X))


def test_knn_precomputed_distances_match_normal_path(three_class_data) -> None:
    X, y = three_class_data
    model = KNNClassifier(k=5, metric="euclidean", weights="distance").fit(X, y)
    query = X[:25]

    distances = compute_distances(
        model.X_train.astype(np.float64), query, metric="euclidean"
    )
    assert np.allclose(
        model.predict_proba_from_distances(distances), model.predict_proba(query)
    )
    assert np.array_equal(
        model.predict_from_distances(distances), model.predict(query)
    )