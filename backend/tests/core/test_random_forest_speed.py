"""Tes kesetaraan: versi cepat harus menghasilkan hasil yang sama dengan acuan."""

from __future__ import annotations
import numpy as np
import pytest
from app.core import DecisionTree, RandomForest, find_best_split
from app.core.random_forest.splitting import find_best_split_reference


def _random_node(seed: int, n: int = 200):
    rng = np.random.default_rng(seed)
    X = np.column_stack(
        [
            rng.normal(size=n),                              # kontinu
            rng.integers(0, 2, size=n).astype(float),        # biner (mirip one-hot)
            np.round(rng.normal(size=n), 1),                 # banyak nilai kembar
            rng.integers(0, 2, size=n).astype(float),
            rng.uniform(size=n),
        ]
    )
    y = rng.integers(0, 3, size=n)
    return X, y


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("max_thresholds", [128, 16])
def test_vectorized_split_matches_reference(seed: int, max_thresholds: int) -> None:
    X, y = _random_node(seed)
    features = np.arange(X.shape[1])

    fast = find_best_split(X, y, features, max_thresholds=max_thresholds)
    ref = find_best_split_reference(X, y, features, max_thresholds=max_thresholds)

    if ref[0] is None:
        assert fast == ref
        return
    assert fast[0] == ref[0]
    assert fast[1] == pytest.approx(ref[1])
    assert fast[2] == pytest.approx(ref[2])


def test_vectorized_split_respects_feature_subset_and_order() -> None:
    X, y = _random_node(3)
    subset = np.array([4, 2, 0])
    assert find_best_split(X, y, subset)[0] == find_best_split_reference(X, y, subset)[0]


def _predict_loop(tree: DecisionTree, X: np.ndarray) -> np.ndarray:
    """Penelusuran satu baris per iterasi (versi lama) sebagai acuan."""
    out = np.empty((X.shape[0], tree.n_classes_))
    for row in range(X.shape[0]):
        node = 0
        while tree.feature_idx_[node] != -1:
            f = int(tree.feature_idx_[node])
            go_left = X[row, f] <= tree.threshold_[node]
            node = int(tree.left_child_[node] if go_left else tree.right_child_[node])
        out[row] = tree.leaf_probs_[node]
    return out


def test_vectorized_tree_prediction_matches_loop(three_class_data) -> None:
    X, y = three_class_data
    tree = DecisionTree().fit(X, y, max_depth=None, max_features="sqrt", rng=7)
    assert np.allclose(tree.predict_proba(X), _predict_loop(tree, X))


def test_predict_proba_per_tree_matches_prefix(three_class_data) -> None:
    X, y = three_class_data
    forest = RandomForest(n_estimators=6, max_depth=5, random_state=2).fit(X, y)
    per_tree = forest.predict_proba_per_tree(X)

    assert per_tree.shape == (6, len(X), 3)
    for n_trees in (1, 3, 6):
        assert np.allclose(
            per_tree[:n_trees].mean(axis=0),
            forest.predict_proba_prefix(X, n_trees),
        )


def test_n_jobs_gives_identical_forest(three_class_data) -> None:
    X, y = three_class_data
    serial = RandomForest(n_estimators=4, max_depth=5, random_state=1, n_jobs=1).fit(X, y)
    parallel = RandomForest(n_estimators=4, max_depth=5, random_state=1, n_jobs=2).fit(X, y)
    assert np.allclose(serial.predict_proba(X), parallel.predict_proba(X))