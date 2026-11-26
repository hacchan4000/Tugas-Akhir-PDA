"""Tes metrik evaluasi manual dibandingkan dengan scikit-learn."""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix as sk_confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from app.core import CLASS_LABELS, evaluate, macro_f1, precision, recall
from app.core.metrics import accuracy, balanced_accuracy, confusion_matrix


def test_metrics_match_sklearn() -> None:
    rng = np.random.default_rng(13)
    y_true = rng.integers(0, 3, size=300)
    y_pred = rng.integers(0, 3, size=300)
    labels = [0, 1, 2]

    assert accuracy(y_true, y_pred) == pytest.approx(accuracy_score(y_true, y_pred))
    assert balanced_accuracy(y_true, y_pred) == pytest.approx(
        balanced_accuracy_score(y_true, y_pred)
    )
    assert np.array_equal(
        confusion_matrix(y_true, y_pred, labels=labels),
        sk_confusion_matrix(y_true, y_pred, labels=labels),
    )
    assert macro_f1(y_true, y_pred, labels=labels) == pytest.approx(
        f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    )
    assert precision(y_true, y_pred, labels=labels) == pytest.approx(
        precision_score(
            y_true, y_pred, labels=labels, average="macro", zero_division=0
        )
    )
    assert recall(y_true, y_pred, labels=labels) == pytest.approx(
        recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    )


def test_metrics_handle_missing_predictions_and_string_labels() -> None:
    y_true = np.array(["small", "small", "large", "medium"])
    y_pred = np.array(["small", "small", "small", "small"])

    assert macro_f1(y_true, y_pred) == pytest.approx(
        f1_score(y_true, y_pred, average="macro", zero_division=0)
    )
    assert precision(y_true, y_pred) == pytest.approx(
        precision_score(y_true, y_pred, average="macro", zero_division=0)
    )
    assert recall(y_true, y_pred) == pytest.approx(
        recall_score(y_true, y_pred, average="macro", zero_division=0)
    )


def test_evaluate_returns_three_by_three_matrix() -> None:
    # Hanya kelas 0 dan 1 muncul, tetapi matriks tetap 3x3 sesuai CLASS_LABELS.
    metrics = evaluate(np.array([0, 0, 1, 1]), np.array([0, 1, 0, 1]))

    assert len(metrics["confusion_matrix"]) == 3
    assert all(len(row) == 3 for row in metrics["confusion_matrix"])
    assert metrics["labels"] == CLASS_LABELS
    assert set(metrics["per_class"]) == set(CLASS_LABELS)
    assert 0.0 <= metrics["macro_f1"] <= 1.0
    assert metrics["accuracy"] == pytest.approx(0.5)