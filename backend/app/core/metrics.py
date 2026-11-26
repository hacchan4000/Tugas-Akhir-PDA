"""Metrik evaluasi manual (tanpa scikit-learn).

Semua fungsi dibuat konsisten dengan konvensi scikit-learn: ``zero_division=0``
dan macro average dihitung tanpa bobot per kelas.
"""

from __future__ import annotations
from typing import Any, Sequence
import numpy as np
from .constants import CLASS_LABELS


def _as_arrays(y_true: Any, y_pred: Any) -> tuple[np.ndarray, np.ndarray]:
    yt = np.asarray(y_true).ravel()
    yp = np.asarray(y_pred).ravel()
    if yt.shape[0] != yp.shape[0]:
        raise ValueError(
            f"Panjang y_true dan y_pred berbeda: {yt.shape[0]} vs {yp.shape[0]}"
        )
    return yt, yp


def _resolve_labels(
    y_true: np.ndarray, y_pred: np.ndarray, labels: Sequence[Any] | None
) -> np.ndarray:
    if labels is not None:
        return np.asarray(labels)
    if y_true.size == 0 and y_pred.size == 0:
        return np.array([])
    return np.unique(np.concatenate([y_true, y_pred]))


def _label_indices(y: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Petakan label asli ke indeks baris/kolom confusion matrix (-1 bila asing)."""
    n_labels = labels.size
    if n_labels == 0:
        return np.full(y.size, -1, dtype=np.int64)

    if (
        np.issubdtype(labels.dtype, np.integer)
        and np.issubdtype(y.dtype, np.integer)
        and np.array_equal(labels, np.arange(n_labels))
    ):
        idx = y.astype(np.int64)
        return np.where((idx >= 0) & (idx < n_labels), idx, -1)

    mapping = {label: index for index, label in enumerate(labels.tolist())}
    return np.fromiter(
        (mapping.get(value, -1) for value in y.tolist()),
        dtype=np.int64,
        count=y.size,
    )


def confusion_matrix(
    y_true: Any, y_pred: Any, labels: Sequence[Any] | None = None
) -> np.ndarray:
    """Confusion matrix berukuran ``(len(labels), len(labels))``."""
    yt, yp = _as_arrays(y_true, y_pred)
    resolved = _resolve_labels(yt, yp, labels)
    n_labels = resolved.size

    matrix = np.zeros((n_labels, n_labels), dtype=np.int64)
    true_idx = _label_indices(yt, resolved)
    pred_idx = _label_indices(yp, resolved)
    valid = (true_idx >= 0) & (pred_idx >= 0)
    np.add.at(matrix, (true_idx[valid], pred_idx[valid]), 1)
    return matrix


def _per_class_stats(matrix: np.ndarray) -> dict[str, np.ndarray]:
    true_positive = np.diag(matrix).astype(np.float64)
    support = matrix.sum(axis=1).astype(np.float64)
    predicted = matrix.sum(axis=0).astype(np.float64)
    false_positive = predicted - true_positive
    false_negative = support - true_positive

    with np.errstate(divide="ignore", invalid="ignore"):
        precision = np.where(
            (true_positive + false_positive) > 0,
            true_positive / (true_positive + false_positive),
            0.0,
        )
        recall = np.where(
            (true_positive + false_negative) > 0,
            true_positive / (true_positive + false_negative),
            0.0,
        )
        f1 = np.where(
            (precision + recall) > 0,
            2.0 * precision * recall / (precision + recall),
            0.0,
        )
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "support": support,
    }


def accuracy(y_true: Any, y_pred: Any) -> float:
    yt, yp = _as_arrays(y_true, y_pred)
    if yt.size == 0:
        return 0.0
    return float(np.mean(yt == yp))


def balanced_accuracy(y_true: Any, y_pred: Any) -> float:
    """Rata-rata recall per kelas yang benar-benar muncul di ``y_true``."""
    yt, yp = _as_arrays(y_true, y_pred)
    labels = _resolve_labels(yt, yp, None)
    matrix = confusion_matrix(yt, yp, labels)
    stats = _per_class_stats(matrix)
    support = stats["support"]
    present = support > 0
    if not present.any():
        return 0.0
    return float(np.mean(stats["recall"][present]))


def _average_scores(
    scores: np.ndarray, support: np.ndarray, average: str
) -> float | np.ndarray:
    if average is None:
        return scores
    if average == "macro":
        return float(np.mean(scores)) if scores.size else 0.0
    if average == "weighted":
        total = support.sum()
        if total <= 0:
            return 0.0
        return float(np.sum(scores * support) / total)
    raise ValueError(f"average tidak dikenal: {average!r}")


def precision(
    y_true: Any,
    y_pred: Any,
    labels: Sequence[Any] | None = None,
    average: str | None = "macro",
) -> float | np.ndarray:
    yt, yp = _as_arrays(y_true, y_pred)
    if average == "micro":
        # Untuk klasifikasi single-label, micro precision = micro recall = accuracy.
        return accuracy(yt, yp)
    resolved = _resolve_labels(yt, yp, labels)
    stats = _per_class_stats(confusion_matrix(yt, yp, resolved))
    return _average_scores(stats["precision"], stats["support"], average)


def recall(
    y_true: Any,
    y_pred: Any,
    labels: Sequence[Any] | None = None,
    average: str | None = "macro",
) -> float | np.ndarray:
    yt, yp = _as_arrays(y_true, y_pred)
    if average == "micro":
        return accuracy(yt, yp)
    resolved = _resolve_labels(yt, yp, labels)
    stats = _per_class_stats(confusion_matrix(yt, yp, resolved))
    return _average_scores(stats["recall"], stats["support"], average)


def macro_f1(
    y_true: Any, y_pred: Any, labels: Sequence[Any] | None = None
) -> float:
    yt, yp = _as_arrays(y_true, y_pred)
    resolved = _resolve_labels(yt, yp, labels)
    stats = _per_class_stats(confusion_matrix(yt, yp, resolved))
    if stats["f1"].size == 0:
        return 0.0
    return float(np.mean(stats["f1"]))


def evaluate(
    y_true: Any, y_pred: Any, labels: Sequence[Any] | None = None
) -> dict[str, Any]:
    """Hitung seluruh metrik evaluasi dalam satu kamus siap-JSON."""
    yt, yp = _as_arrays(y_true, y_pred)

    if labels is None:
        if np.issubdtype(yt.dtype, np.integer) and np.issubdtype(yp.dtype, np.integer):
            max_label = max(int(yt.max(initial=-1)), int(yp.max(initial=-1)))
            n_labels = max(max_label + 1, len(CLASS_LABELS))
            resolved = np.arange(n_labels, dtype=np.int64)
        else:
            resolved = _resolve_labels(yt, yp, None)
    else:
        resolved = np.asarray(labels)

    matrix = confusion_matrix(yt, yp, resolved)
    stats = _per_class_stats(matrix)

    display_labels: list[str] = []
    for index, label in enumerate(resolved.tolist()):
        if (
            isinstance(label, (int, np.integer))
            and 0 <= int(label) < len(CLASS_LABELS)
        ):
            display_labels.append(CLASS_LABELS[int(label)])
        else:
            display_labels.append(str(label))

    per_class: dict[str, dict[str, float]] = {}
    for index, name in enumerate(display_labels):
        per_class[name] = {
            "precision": float(stats["precision"][index]),
            "recall": float(stats["recall"][index]),
            "f1": float(stats["f1"][index]),
            "support": int(stats["support"][index]),
        }

    present = stats["support"] > 0
    balanced = (
        float(np.mean(stats["recall"][present])) if present.any() else 0.0
    )

    return {
        "macro_f1": float(np.mean(stats["f1"])) if stats["f1"].size else 0.0,
        "balanced_accuracy": balanced,
        "accuracy": accuracy(yt, yp),
        "precision_macro": float(np.mean(stats["precision"]))
        if stats["precision"].size
        else 0.0,
        "recall_macro": float(np.mean(stats["recall"]))
        if stats["recall"].size
        else 0.0,
        "confusion_matrix": matrix.tolist(),
        "labels": display_labels,
        "per_class": per_class,
    }


__all__ = [
    "confusion_matrix",
    "accuracy",
    "balanced_accuracy",
    "precision",
    "recall",
    "macro_f1",
    "evaluate",
]
