"""K-Nearest Neighbors manual berbasis NumPy (tanpa scikit-learn)."""

from __future__ import annotations
from typing import Any
import numpy as np
from .constants import CLASS_LABELS

_METRICS = ("euclidean", "manhattan", "chebyshev")
_WEIGHTS = ("uniform", "distance")

# Ukuran potongan baris query. # TUNE: naikkan bila RAM longgar, turunkan bila
# terjadi lonjakan memori saat inference data besar.
CHUNK_SIZE = 256
_TRAIN_CHUNK = 512


def compute_distances(
    X_train: np.ndarray,
    X_query: np.ndarray,
    metric: str = "euclidean",
    chunk_size: int = CHUNK_SIZE,
) -> np.ndarray:
    """Hitung matriks jarak ``(n_query, n_train)`` per potongan.

    Mendukung ``euclidean``, ``manhattan``, dan ``chebyshev``.
    """
    if metric not in _METRICS:
        raise ValueError(f"metric tidak dikenal: {metric!r}; pilih {_METRICS}")

    Xt = np.asarray(X_train, dtype=np.float64)
    Xq = np.asarray(X_query, dtype=np.float64)
    if Xt.ndim != 2 or Xq.ndim != 2:
        raise ValueError("X_train dan X_query harus berupa matriks 2 dimensi")
    if Xt.shape[1] != Xq.shape[1]:
        raise ValueError(
            f"Jumlah fitur tidak cocok: train {Xt.shape[1]}, query {Xq.shape[1]}"
        )
    if not np.isfinite(Xt).all() or not np.isfinite(Xq).all():
        raise ValueError("X_train/X_query mengandung NaN atau nilai tak hingga")

    n_train, n_query = Xt.shape[0], Xq.shape[0]
    out = np.empty((n_query, n_train), dtype=np.float64)
    if n_train == 0 or n_query == 0:
        return out

    step = max(1, int(chunk_size))

    if metric == "euclidean":
        # ||a-b||^2 = ||a||^2 + ||b||^2 - 2 a.b ; jauh lebih hemat memori.
        train_sq = np.einsum("ij,ij->i", Xt, Xt)
        for start in range(0, n_query, step):
            query = Xq[start : start + step]
            query_sq = np.einsum("ij,ij->i", query, query)
            dist_sq = query_sq[:, None] + train_sq[None, :] - 2.0 * (query @ Xt.T)
            np.maximum(dist_sq, 0.0, out=dist_sq)  # noise floating point
            out[start : start + step] = np.sqrt(dist_sq)
        return out

    for start in range(0, n_query, step):
        query = Xq[start : start + step]
        for t_start in range(0, n_train, _TRAIN_CHUNK):
            block = Xt[t_start : t_start + _TRAIN_CHUNK]
            diff = np.abs(query[:, None, :] - block[None, :, :])
            if metric == "manhattan":
                out[start : start + step, t_start : t_start + _TRAIN_CHUNK] = diff.sum(
                    axis=2
                )
            else:  # chebyshev
                out[start : start + step, t_start : t_start + _TRAIN_CHUNK] = diff.max(
                    axis=2
                )
    return out


class KNNClassifier:
    """KNN dengan bobot uniform/distance dan tie-break tetangga terdekat."""

    def __init__(
        self,
        k: int = 5,
        metric: str = "euclidean",
        weights: str = "uniform",
        n_classes: int | None = None,
    ) -> None:
        if int(k) < 1:
            raise ValueError("k harus >= 1")
        if metric not in _METRICS:
            raise ValueError(f"metric tidak dikenal: {metric!r}; pilih {_METRICS}")
        if weights not in _WEIGHTS:
            raise ValueError(f"weights tidak dikenal: {weights!r}; pilih {_WEIGHTS}")
        if n_classes is not None and int(n_classes) < 1:
            raise ValueError("n_classes harus >= 1")

        self.k = int(k)
        self.metric = metric
        self.weights = weights
        self.n_classes = int(n_classes) if n_classes is not None else len(CLASS_LABELS)

        self.X_train: np.ndarray | None = None
        self.y_train: np.ndarray | None = None
        self.n_features_in_: int | None = None

    # -- fit --------------------------------------------------------------
    def fit(self, X: np.ndarray, y: np.ndarray) -> "KNNClassifier":
        X_arr = np.asarray(X, dtype=np.float32)
        y_arr = np.asarray(y)
        if X_arr.ndim != 2:
            raise ValueError("X harus berupa matriks 2 dimensi")
        if y_arr.ndim != 1 or y_arr.shape[0] != X_arr.shape[0]:
            raise ValueError("y harus vektor 1D dengan panjang sama dengan X")
        if X_arr.shape[0] == 0:
            raise ValueError("Tidak dapat melakukan fit pada data kosong")
        if not np.isfinite(X_arr).all():
            raise ValueError("X mengandung NaN atau nilai tak hingga")

        y_int = y_arr.astype(np.int64)
        if (y_int < 0).any() or (y_int >= self.n_classes).any():
            raise ValueError(
                f"Label kelas harus berada pada rentang [0, {self.n_classes - 1}]"
            )

        # Data latih disimpan float32 sesuai spesifikasi (hemat memori);
        # perhitungan jarak tetap dilakukan dalam float64.
        self.X_train = np.ascontiguousarray(X_arr, dtype=np.float32)
        self.y_train = y_int
        self.n_features_in_ = int(X_arr.shape[1])
        return self

    # -- internal ---------------------------------------------------------
    def _neighbors_from_distances(
        self, distances: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        if self.X_train is None or self.y_train is None:
            raise RuntimeError("KNNClassifier belum di-fit")

        dist = np.asarray(distances, dtype=np.float64)
        if dist.ndim != 2:
            raise ValueError("distances harus berupa matriks 2 dimensi")
        if dist.shape[1] != self.y_train.shape[0]:
            raise ValueError(
                f"Jumlah kolom distances tidak cocok: {dist.shape[1]} vs "
                f"{self.y_train.shape[0]} data latih"
            )
        if not np.isfinite(dist).all() or (dist < 0).any():
            raise ValueError("distances mengandung NaN, tak hingga, atau nilai negatif")

        k_eff = min(self.k, self.y_train.shape[0])
        nearest = np.argpartition(dist, k_eff - 1, axis=1)[:, :k_eff]
        nearest_dist = np.take_along_axis(dist, nearest, axis=1)
        order = np.argsort(nearest_dist, axis=1, kind="stable")
        nearest = np.take_along_axis(nearest, order, axis=1)
        nearest_dist = np.take_along_axis(nearest_dist, order, axis=1)
        return nearest_dist, self.y_train[nearest]

    def _neighbors(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if self.X_train is None:
            raise RuntimeError("KNNClassifier belum di-fit")

        Xq = np.asarray(X, dtype=np.float32).astype(np.float64)
        if Xq.ndim == 1:
            Xq = Xq.reshape(1, -1)
        if Xq.ndim != 2:
            raise ValueError("X harus berupa matriks 2 dimensi")
        if Xq.shape[1] != self.X_train.shape[1]:
            raise ValueError(
                f"Jumlah fitur tidak cocok: {Xq.shape[1]} vs {self.X_train.shape[1]}"
            )

        distances = compute_distances(
            self.X_train.astype(np.float64), Xq, metric=self.metric
        )
        return self._neighbors_from_distances(distances)

    def _neighbor_weights(self, distances: np.ndarray) -> np.ndarray:
        if self.weights == "uniform":
            return np.ones_like(distances, dtype=np.float64)

        # Toleransi 1e-7 untuk meredam noise float32/float64 pada titik identik.
        zero_mask = distances <= 1e-7
        has_zero = zero_mask.any(axis=1)
        with np.errstate(divide="ignore"):
            inverse = np.where(zero_mask, 0.0, 1.0 / np.maximum(distances, 1e-15))
        return np.where(has_zero[:, None], zero_mask.astype(np.float64), inverse)

    def _weighted_proba(
        self, distances: np.ndarray, labels: np.ndarray
    ) -> np.ndarray:
        weights = self._neighbor_weights(distances)
        probs = np.zeros((labels.shape[0], self.n_classes), dtype=np.float64)
        rows = np.repeat(np.arange(labels.shape[0]), labels.shape[1])
        np.add.at(probs, (rows, labels.ravel()), weights.ravel())
        totals = probs.sum(axis=1, keepdims=True)
        np.divide(probs, totals, out=probs, where=totals > 0)
        return probs

    # -- API --------------------------------------------------------------
    def _predict_from_neighbors(
        self, distances: np.ndarray, labels: np.ndarray
    ) -> np.ndarray:
        probs = self._weighted_proba(distances, labels)
        predictions = np.argmax(probs, axis=1)

        if probs.shape[1] < 2:
            return predictions

        # Tie-break: bila probabilitas tertinggi seri, pilih kelas yang punya
        # tetangga terdekat (jarak minimum) di antara kandidat seri.
        sorted_probs = np.sort(probs, axis=1)
        tied_rows = np.flatnonzero(
            np.isclose(sorted_probs[:, -1], sorted_probs[:, -2], rtol=0.0, atol=1e-12)
        )
        for row in tied_rows:
            top = probs[row].max()
            candidates = np.flatnonzero(probs[row] >= top - 1e-12)
            best_distance = np.inf
            best_class = int(candidates[0])
            for cls in candidates:
                mask = labels[row] == cls
                if not mask.any():
                    continue
                min_distance = float(distances[row][mask].min())
                if min_distance < best_distance - 1e-15:
                    best_distance = min_distance
                    best_class = int(cls)
            predictions[row] = best_class
        return predictions

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        distances, labels = self._neighbors(X)
        return self._weighted_proba(distances, labels)

    def predict(self, X: np.ndarray) -> np.ndarray:
        distances, labels = self._neighbors(X)
        return self._predict_from_neighbors(distances, labels)

    def predict_proba_from_distances(self, distances: np.ndarray) -> np.ndarray:
        """Probabilitas dari matriks jarak yang sudah dihitung (optimasi tuning)."""
        nearest_dist, labels = self._neighbors_from_distances(distances)
        return self._weighted_proba(nearest_dist, labels)

    def predict_from_distances(self, distances: np.ndarray) -> np.ndarray:
        """Prediksi dari matriks jarak yang sudah dihitung (optimasi tuning)."""
        nearest_dist, labels = self._neighbors_from_distances(distances)
        return self._predict_from_neighbors(nearest_dist, labels)

    def predict_one(self, x: np.ndarray) -> int:
        vector = np.asarray(x, dtype=np.float64).reshape(1, -1)
        return int(self.predict(vector)[0])

    # -- serialisasi ------------------------------------------------------
    def to_arrays(self) -> dict[str, np.ndarray]:
        if self.X_train is None or self.y_train is None:
            raise RuntimeError("KNNClassifier belum di-fit")
        return {
            "X_train": np.ascontiguousarray(self.X_train, dtype=np.float32),
            "y_train": np.ascontiguousarray(self.y_train, dtype=np.int64),
            "k": np.array(self.k, dtype=np.int64),
            "metric": np.array(self.metric, dtype="<U16"),
            "weights": np.array(self.weights, dtype="<U16"),
            "n_classes": np.array(self.n_classes, dtype=np.int64),
        }

    @classmethod
    def from_arrays(cls, arrays: Any) -> "KNNClassifier":
        def scalar(key: str) -> Any:
            value = arrays[key]
            return value.item() if getattr(value, "ndim", 0) == 0 else value

        obj = cls(
            k=int(scalar("k")),
            metric=str(scalar("metric")),
            weights=str(scalar("weights")),
            n_classes=int(scalar("n_classes")),
        )
        X_train = np.ascontiguousarray(arrays["X_train"], dtype=np.float32)
        y_train = np.asarray(arrays["y_train"], dtype=np.int64)
        if X_train.ndim != 2 or y_train.shape[0] != X_train.shape[0]:
            raise ValueError("Array KNN tidak konsisten")
        obj.X_train = X_train
        obj.y_train = y_train
        obj.n_features_in_ = int(X_train.shape[1])
        return obj


pairwise_distance = compute_distances

__all__ = ["compute_distances", "pairwise_distance", "KNNClassifier", "CHUNK_SIZE"]