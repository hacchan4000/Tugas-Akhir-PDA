"""Tes Gini, pencarian split, DecisionTree, dan RandomForest manual."""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pytest
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from app.core import (
    DecisionTree,
    RandomForest,
    find_best_split,
    gini_gain,
    gini_impurity,
    macro_f1,
)
from app.core.metrics import accuracy


# ---------------------------------------------------------------------------
# Gini (bisa dihitung tangan)
# ---------------------------------------------------------------------------
def test_gini_impurity_hand_computed() -> None:
    assert gini_impurity(np.array([3, 3])) == pytest.approx(0.5)
    assert gini_impurity(np.array([6, 0])) == pytest.approx(0.0)
    assert gini_impurity(np.array([1, 1, 1])) == pytest.approx(2 / 3)
    assert gini_impurity(np.array([0, 0, 0])) == pytest.approx(0.0)


def test_gini_gain_hand_computed() -> None:
    # Parent 50/50, anak kiri murni, anak kanan murni -> gain 0.5.
    gain = gini_gain(np.array([4, 4]), np.array([4, 0]), np.array([0, 4]))
    assert gain == pytest.approx(0.5)

    # Tidak ada pemisahan informasi -> gain 0.
    gain_none = gini_gain(np.array([4, 4]), np.array([2, 2]), np.array([2, 2]))
    assert gain_none == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Pencarian split
# ---------------------------------------------------------------------------
def test_find_best_split_finds_known_threshold() -> None:
    X = np.array([[0.0], [1.0], [2.0], [3.0]])
    y = np.array([0, 0, 1, 1])

    feature, threshold, gain = find_best_split(X, y, np.array([0]))
    assert feature == 0
    assert threshold == pytest.approx(1.5)
    assert gain == pytest.approx(0.5)


def test_find_best_split_returns_none_when_no_gain() -> None:
    X = np.array([[0.0], [1.0], [2.0]])
    y = np.array([1, 1, 1])
    assert find_best_split(X, y, np.array([0])) == (None, None, 0.0)

    constant = np.ones((4, 2))
    mixed = np.array([0, 0, 1, 1])
    assert find_best_split(constant, mixed, np.array([0, 1])) == (None, None, 0.0)


def test_find_best_split_respects_threshold_cap() -> None:
    rng = np.random.default_rng(5)
    X = np.sort(rng.normal(size=(200, 1)), axis=0)
    y = (X[:, 0] > 0.0).astype(np.int64)

    feature, threshold, gain = find_best_split(X, y, np.array([0]), max_thresholds=4)
    assert feature == 0
    assert gain > 0.0
    assert X[:, 0].min() < threshold < X[:, 0].max()


# ---------------------------------------------------------------------------
# DecisionTree
# ---------------------------------------------------------------------------
def test_decision_tree_learns_and_roundtrips(tmp_path: Path) -> None:
    X, y = make_classification(
        n_samples=120,
        n_features=5,
        n_informative=4,
        n_redundant=0,
        n_classes=3,
        n_clusters_per_class=1,
        class_sep=2.0,
        random_state=11,
    )
    tree = DecisionTree().fit(X, y, max_depth=6, max_features="sqrt", rng=42)
    proba = tree.predict_proba(X)

    assert proba.shape == (len(X), 3)
    assert np.allclose(proba.sum(axis=1), 1.0)
    assert accuracy(y, tree.predict(X)) >= 0.9

    path = tmp_path / "tree.npz"
    np.savez(path, **tree.to_arrays())
    with np.load(path) as arrays:
        restored = DecisionTree.from_arrays(arrays)
    assert np.allclose(proba, restored.predict_proba(X))
    assert np.array_equal(tree.predict(X), restored.predict(X))


# ---------------------------------------------------------------------------
# RandomForest
# ---------------------------------------------------------------------------
def test_random_forest_proba_and_roundtrip(tmp_path: Path, three_class_data) -> None:
    X, y = three_class_data
    forest = RandomForest(
        n_estimators=8, max_depth=6, max_features="sqrt", random_state=3
    ).fit(X, y)

    proba = forest.predict_proba(X)
    assert proba.shape == (len(X), 3)
    assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-12)
    assert np.array_equal(forest.predict(X), np.argmax(proba, axis=1))

    path = tmp_path / "rf_trees.npz"
    np.savez(path, **forest.to_arrays())
    with np.load(path) as arrays:
        restored = RandomForest.from_arrays(arrays)

    assert restored.n_estimators == 8
    assert restored.n_classes_ == 3
    assert np.allclose(proba, restored.predict_proba(X), atol=1e-12)
    assert np.array_equal(forest.predict(X), restored.predict(X))


def test_random_forest_prefix_equals_separate_fit(three_class_data) -> None:
    X, y = three_class_data
    full = RandomForest(n_estimators=6, max_depth=5, random_state=17).fit(X, y)
    shorter = RandomForest(n_estimators=3, max_depth=5, random_state=17).fit(X, y)

    assert np.allclose(
        full.predict_proba_prefix(X, 3), shorter.predict_proba(X), atol=1e-12
    )


def test_random_forest_max_features_none_roundtrip(three_class_data) -> None:
    X, y = three_class_data
    forest = RandomForest(
        n_estimators=3, max_depth=4, max_features=None, random_state=9
    ).fit(X, y)
    restored = RandomForest.from_arrays(forest.to_arrays())

    assert restored.max_features is None
    assert restored.max_features_ == X.shape[1]
    assert np.allclose(forest.predict_proba(X), restored.predict_proba(X))


def test_random_forest_macro_f1_close_to_sklearn() -> None:
    X, y = make_classification(
        n_samples=300,
        n_features=8,
        n_informative=6,
        n_redundant=0,
        n_classes=3,
        n_clusters_per_class=1,
        class_sep=1.5,
        flip_y=0.02,
        random_state=42,
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    ours = RandomForest(
        n_estimators=20, max_depth=8, max_features="sqrt", random_state=42
    ).fit(X_train, y_train)
    ref = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        max_features="sqrt",
        random_state=42,
        n_jobs=1,
    ).fit(X_train, y_train)

    ours_f1 = macro_f1(y_test, ours.predict(X_test))
    ref_f1 = macro_f1(y_test, ref.predict(X_test))

    assert ours_f1 >= 0.85
    assert abs(ours_f1 - ref_f1) <= 0.10