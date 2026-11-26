"""Langkah 2: mencari split terbaik pada satu node.

Tidak ada binning. Untuk setiap fitur numerik, kandidat threshold adalah titik
tengah antar nilai unik berurutan; jumlah kelas kumulatif (cumsum) pada data
terurut membuat SEMUA kandidat satu fitur dinilai sekali jalan.
Kolom one-hot (0/1) otomatis hanya punya satu threshold, yaitu 0.5.

Dua implementasi dengan hasil identik:
  - find_best_split           : tervektorisasi lintas fitur (dipakai pohon, cepat)
  - find_best_split_reference : satu fitur per iterasi (acuan dan dipakai tes)
Fitur dengan nilai unik > max_thresholds memakai jalur acuan (kandidat dibatasi
ke posisi kuantil).
"""

from __future__ import annotations
import numpy as np
from .impurity import gini_impurity, gini_impurity_rows

# Batas kandidat threshold per fitur (optimasi komputasi, bukan binning data).
# TUNE: naikkan untuk akurasi lebih teliti, turunkan untuk training lebih cepat.
MAX_THRESHOLDS = 128


def _validate(X, y, feature_indices, max_thresholds):
    X_arr = np.asarray(X, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.int64)
    if X_arr.ndim != 2:
        raise ValueError("X harus berupa matriks 2 dimensi")
    if y_arr.ndim != 1 or y_arr.shape[0] != X_arr.shape[0]:
        raise ValueError("y harus vektor 1D dengan panjang sama dengan X")
    if max_thresholds < 1:
        raise ValueError("max_thresholds harus >= 1")
    features = np.asarray(feature_indices, dtype=np.int64).ravel()
    if features.size and ((features < 0).any() or (features >= X_arr.shape[1]).any()):
        raise ValueError("feature_indices keluar dari rentang kolom X")
    return X_arr, y_arr, features


# ---------------------------------------------------------------------------
# Jalur acuan: satu fitur
# ---------------------------------------------------------------------------
def _best_for_feature_reference(
    values: np.ndarray,
    y: np.ndarray,
    n_classes: int,
    total_counts: np.ndarray,
    parent_gini: float,
    max_thresholds: int,
) -> tuple[float, float] | None:
    """Return ``(gain, threshold)`` terbaik untuk satu fitur, atau None."""
    n_samples = values.shape[0]
    unique_values = np.unique(values)
    if unique_values.size < 2:
        return None

    # Batasi jumlah kandidat bila terlalu banyak nilai unik.
    if unique_values.size - 1 > max_thresholds:
        positions = np.linspace(0, unique_values.size - 1, max_thresholds + 1)
        positions = np.unique(np.round(positions).astype(np.int64))
        selected = unique_values[positions]
    else:
        selected = unique_values
    if selected.size < 2:
        return None

    thresholds = selected[:-1] + (selected[1:] - selected[:-1]) / 2.0

    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    sorted_labels = y[order]

    one_hot = np.zeros((n_samples, n_classes), dtype=np.float64)
    one_hot[np.arange(n_samples), sorted_labels] = 1.0
    cumulative = np.vstack(
        [np.zeros((1, n_classes), dtype=np.float64), np.cumsum(one_hot, axis=0)]
    )

    split_positions = np.searchsorted(sorted_values, thresholds, side="right")
    left_counts = cumulative[split_positions]
    right_counts = total_counts[None, :] - left_counts
    n_left = split_positions.astype(np.float64)
    n_right = n_samples - n_left

    left_gini = gini_impurity_rows(left_counts, n_left)
    right_gini = gini_impurity_rows(right_counts, n_right)
    gains = parent_gini - (
        (n_left / n_samples) * left_gini + (n_right / n_samples) * right_gini
    )

    local_idx = int(np.argmax(gains))
    return float(gains[local_idx]), float(thresholds[local_idx])


def find_best_split_reference(
    X: np.ndarray,
    y: np.ndarray,
    feature_indices: np.ndarray,
    max_thresholds: int = MAX_THRESHOLDS,
) -> tuple[int | None, float | None, float]:
    """Versi acuan (satu fitur per iterasi). Dipakai tes untuk membandingkan."""
    X_arr, y_arr, features = _validate(X, y, feature_indices, max_thresholds)
    if features.size == 0 or X_arr.shape[0] < 2:
        return None, None, 0.0

    n_classes = int(y_arr.max()) + 1
    total_counts = np.bincount(y_arr, minlength=n_classes).astype(np.float64)
    parent_gini = gini_impurity(total_counts)
    if parent_gini == 0.0:
        return None, None, 0.0

    best_feature: int | None = None
    best_threshold: float | None = None
    best_gain = 0.0
    for feature in features:
        result = _best_for_feature_reference(
            X_arr[:, feature], y_arr, n_classes, total_counts, parent_gini,
            max_thresholds,
        )
        if result is None:
            continue
        gain, threshold = result
        if gain > best_gain + 1e-15:
            best_gain, best_feature, best_threshold = gain, int(feature), threshold

    if best_feature is None:
        return None, None, 0.0
    return best_feature, best_threshold, best_gain


# ---------------------------------------------------------------------------
# Jalur cepat: semua fitur sekaligus
# ---------------------------------------------------------------------------
def _best_for_features_vectorized(
    sub: np.ndarray,
    y: np.ndarray,
    n_classes: int,
    total_counts: np.ndarray,
    parent_gini: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Split terbaik tiap kolom ``sub`` (n, f), tanpa batas kandidat.

    Mengembalikan ``(gain, threshold, n_valid)`` masing-masing berukuran f;
    ``n_valid`` = jumlah posisi split yang sah (nilai unik - 1).
    """
    n, f = sub.shape
    order = np.argsort(sub, axis=0, kind="stable")
    sorted_values = np.take_along_axis(sub, order, axis=0)
    labels = y[order]                                   # (n, f)

    # Posisi i sah bila nilai ke-i berbeda dari nilai ke-(i+1).
    valid = sorted_values[1:] > sorted_values[:-1]      # (n-1, f)
    n_left = np.arange(1, n, dtype=np.float64)[:, None]
    n_right = n - n_left

    gini_left = np.ones((n - 1, f), dtype=np.float64)
    gini_right = np.ones((n - 1, f), dtype=np.float64)
    for c in range(n_classes):
        left_c = np.cumsum(labels == c, axis=0)[:-1].astype(np.float64)
        right_c = total_counts[c] - left_c
        gini_left -= (left_c / n_left) ** 2
        gini_right -= (right_c / n_right) ** 2

    gains = parent_gini - ((n_left / n) * gini_left + (n_right / n) * gini_right)
    gains = np.where(valid, gains, -np.inf)

    best_idx = np.argmax(gains, axis=0)                 # posisi pertama yang maksimum
    cols = np.arange(f)
    best_gain = gains[best_idx, cols]
    low = sorted_values[best_idx, cols]
    high = sorted_values[best_idx + 1, cols]
    thresholds = low + (high - low) / 2.0
    return best_gain, thresholds, valid.sum(axis=0)


def find_best_split(
    X: np.ndarray,
    y: np.ndarray,
    feature_indices: np.ndarray,
    max_thresholds: int = MAX_THRESHOLDS,
) -> tuple[int | None, float | None, float]:
    """Cari ``(fitur, threshold, delta_gini)`` terbaik pada kandidat fitur.

    Hasilnya identik dengan ``find_best_split_reference``. Mengembalikan
    ``(None, None, 0.0)`` bila tidak ada split yang menurunkan impuritas.
    """
    X_arr, y_arr, features = _validate(X, y, feature_indices, max_thresholds)
    if features.size == 0 or X_arr.shape[0] < 2:
        return None, None, 0.0

    n_classes = int(y_arr.max()) + 1
    total_counts = np.bincount(y_arr, minlength=n_classes).astype(np.float64)
    parent_gini = gini_impurity(total_counts)
    if parent_gini == 0.0:
        return None, None, 0.0

    sub = X_arr[:, features]
    # Pisahkan kolom ber-kardinalitas rendah (vektorisasi penuh) vs tinggi (kuantil).
    low_card_positions: list[int] = []
    high_card_positions: list[int] = []
    for pos in range(features.size):
        n_unique = np.unique(sub[:, pos]).size
        if n_unique < 2:
            continue
        if n_unique - 1 > max_thresholds:
            high_card_positions.append(pos)
        else:
            low_card_positions.append(pos)

    vec_results: dict[int, tuple[float, float]] = {}
    if low_card_positions:
        gains, thresholds, _ = _best_for_features_vectorized(
            sub[:, low_card_positions], y_arr, n_classes, total_counts, parent_gini
        )
        for idx, pos in enumerate(low_card_positions):
            vec_results[pos] = (float(gains[idx]), float(thresholds[idx]))
            
    # Kumpulkan hasil per fitur DALAM URUTAN ASLI agar tie-break sama dengan acuan.
    best_feature: int | None = None
    best_threshold: float | None = None
    best_gain = 0.0
    for pos in range(features.size):
        if pos in vec_results:
            gain, threshold = vec_results[pos]
        elif pos in high_card_positions:
            result = _best_for_feature_reference(
                sub[:, pos], y_arr, n_classes, total_counts, parent_gini,
                max_thresholds,
            )
            if result is None:
                continue
            gain, threshold = result
        else:
            continue
        if gain > best_gain + 1e-15:
            best_gain, best_feature, best_threshold = gain, int(features[pos]), threshold

    if best_feature is None:
        return None, None, 0.0
    return best_feature, best_threshold, best_gain