"""Pembagian data: holdout stratified dan K-Fold stratified.

Stratified = proporsi tiap kelas dijaga sama di setiap bagian.
"""

from __future__ import annotations
from typing import Any, Iterable
import numpy as np
import pandas as pd
from ..constants import CLASS_LABELS, CLASS_TO_INDEX


def _take(X: Any, indices: np.ndarray) -> Any:
    if isinstance(X, pd.DataFrame):
        return X.iloc[indices]
    if isinstance(X, pd.Series):
        return X.iloc[indices]
    return np.asarray(X)[indices]


def _check_lengths(X: Any, y: np.ndarray) -> None:
    n_x = len(X)
    if n_x != y.shape[0]:
        raise ValueError(f"Panjang X dan y berbeda: {n_x} vs {y.shape[0]}")


def encode_target(values: Iterable[Any]) -> np.ndarray:
    """Ubah label target (string atau indeks) menjadi indeks kelas int64."""
    array = np.asarray(values)
    if np.issubdtype(array.dtype, np.integer):
        encoded = array.astype(np.int64)
        if (encoded < 0).any() or (encoded >= len(CLASS_LABELS)).any():
            raise ValueError("Label target di luar rentang CLASS_LABELS")
        return encoded

    encoded = np.empty(array.shape[0], dtype=np.int64)
    for index, value in enumerate(array.tolist()):
        key = str(value).strip().lower()
        if key not in CLASS_TO_INDEX:
            raise ValueError(f"Label target tidak dikenal: {value!r}")
        encoded[index] = CLASS_TO_INDEX[key]
    return encoded


def stratified_holdout(
    X: Any,
    y: Any,
    test_size: float = 0.2,
    seed: int = 42,
) -> tuple[Any, Any, np.ndarray, np.ndarray]:
    """Split train/test yang mempertahankan proporsi tiap kelas.

    Mengembalikan ``(X_train, X_test, y_train, y_test)``.
    """
    if not 0.0 < float(test_size) < 1.0:
        raise ValueError("test_size harus berada di antara 0 dan 1 (eksklusif)")

    labels = np.asarray(y)
    if labels.ndim != 1:
        raise ValueError("y harus vektor 1D")
    _check_lengths(X, labels)
    if labels.size == 0:
        raise ValueError("Tidak dapat melakukan split pada data kosong")

    rng = np.random.default_rng(seed)
    train_parts: list[np.ndarray] = []
    test_parts: list[np.ndarray] = []

    for label in np.unique(labels):
        class_indices = np.flatnonzero(labels == label)
        rng.shuffle(class_indices)
        n_class = class_indices.size

        n_test = int(np.floor(n_class * float(test_size)))
        if n_class >= 2 and n_test == 0:
            n_test = 1
        n_test = min(n_test, max(0, n_class - 1))

        test_parts.append(class_indices[:n_test])
        train_parts.append(class_indices[n_test:])

    train_idx = (
        np.concatenate(train_parts) if train_parts else np.array([], dtype=np.int64)
    )
    test_idx = (
        np.concatenate(test_parts) if test_parts else np.array([], dtype=np.int64)
    )
    rng.shuffle(train_idx)
    rng.shuffle(test_idx)

    return (
        _take(X, train_idx),
        _take(X, test_idx),
        labels[train_idx],
        labels[test_idx],
    )


def stratified_kfold(
    y: Any,
    n_splits: int = 5,
    seed: int = 42,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Bagi indeks menjadi ``n_splits`` fold dengan proporsi kelas terjaga.

    Mengembalikan daftar ``(train_idx, valid_idx)`` untuk tiap fold; setiap
    sampel menjadi data validasi tepat satu kali.
    """
    labels = np.asarray(y)
    if labels.ndim != 1:
        raise ValueError("y harus vektor 1D")
    n_samples = labels.size
    if int(n_splits) < 2:
        raise ValueError("n_splits harus >= 2")
    if int(n_splits) > n_samples:
        raise ValueError("n_splits tidak boleh melebihi jumlah sampel")

    n_splits = int(n_splits)
    rng = np.random.default_rng(seed)
    fold_parts: list[list[np.ndarray]] = [[] for _ in range(n_splits)]

    for class_offset, label in enumerate(np.unique(labels)):
        class_indices = np.flatnonzero(labels == label)
        rng.shuffle(class_indices)
        # Sebar sisa pembagian secara round-robin agar ukuran tiap fold seimbang.
        fold_assignments = (np.arange(class_indices.size) + class_offset) % n_splits
        for fold_index in range(n_splits):
            fold_parts[fold_index].append(class_indices[fold_assignments == fold_index])

    all_indices = np.arange(n_samples, dtype=np.int64)
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    for parts in fold_parts:
        test_idx = (
            np.sort(np.concatenate(parts)) if parts else np.array([], dtype=np.int64)
        )
        train_idx = np.setdiff1d(all_indices, test_idx, assume_unique=True)
        folds.append((train_idx, test_idx))
    return folds