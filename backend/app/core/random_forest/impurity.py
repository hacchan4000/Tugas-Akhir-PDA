"""Langkah 1: Gini Impurity dan Gini Gain (PPT slide 8).

    G(t)  = 1 - sum_k p_k^2
    dG    = G(t) - ( n_L/n * G(t_L) + n_R/n * G(t_R) )

G bernilai 0 bila node murni (satu kelas) dan membesar bila kelas bercampur.
Split terbaik adalah yang memberi penurunan impuritas (dG) terbesar.
"""

from __future__ import annotations
import numpy as np


def gini_impurity(class_counts: np.ndarray) -> float:
    """G(t) = 1 - sum(p_k^2). Node kosong dianggap impuritas 0."""
    counts = np.asarray(class_counts, dtype=np.float64)
    if counts.ndim != 1:
        raise ValueError("class_counts harus vektor 1 dimensi")
    total = float(counts.sum())
    if total <= 0.0:
        return 0.0
    probs = counts / total
    return float(1.0 - np.sum(probs * probs))


def gini_gain(
    parent_counts: np.ndarray,
    left_counts: np.ndarray,
    right_counts: np.ndarray,
) -> float:
    """Delta G = G(t) - (n_L/n * G(t_L) + n_R/n * G(t_R))."""
    parent = np.asarray(parent_counts, dtype=np.float64)
    left = np.asarray(left_counts, dtype=np.float64)
    right = np.asarray(right_counts, dtype=np.float64)
    if parent.ndim != 1 or left.shape != parent.shape or right.shape != parent.shape:
        raise ValueError("Distribusi kelas parent/left/right harus 1D dan sama panjang")

    total = float(parent.sum())
    if total <= 0.0:
        return 0.0
    n_left = float(left.sum())
    n_right = float(right.sum())
    weighted = (n_left / total) * gini_impurity(left) + (
        n_right / total
    ) * gini_impurity(right)
    return float(gini_impurity(parent) - weighted)


def gini_impurity_rows(counts: np.ndarray, totals: np.ndarray) -> np.ndarray:
    """Versi vektorisasi G(t): satu impuritas per baris ``counts`` (n_split, n_kelas).

    Dipakai ``find_best_split`` untuk menilai banyak threshold sekaligus.
    """
    counts = np.asarray(counts, dtype=np.float64)
    totals = np.asarray(totals, dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        probs = counts / totals[:, None]
    gini = 1.0 - np.sum(probs * probs, axis=1)
    return np.where(totals > 0.0, gini, 0.0)