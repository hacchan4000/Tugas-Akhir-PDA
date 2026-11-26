"""Langkah 3: satu pohon keputusan (CART) dengan feature subsampling.

Berhenti membelah bila: node murni, kedalaman = max_depth, data < 2, atau tidak
ada split yang menurunkan impuritas. Pohon disimpan sebagai array (bukan objek
bersarang) supaya mudah diserialisasi ke ``.npz``.
"""

from __future__ import annotations
from typing import Any
import numpy as np
from .impurity import gini_impurity
from .splitting import find_best_split


class DecisionTree:
    """CART klasifikasi dengan criterion Gini dan feature subsampling."""

    def __init__(self) -> None:
        self.feature_idx_: np.ndarray | None = None   # -1 = daun
        self.threshold_: np.ndarray | None = None
        self.left_child_: np.ndarray | None = None
        self.right_child_: np.ndarray | None = None
        self.leaf_probs_: np.ndarray | None = None    # distribusi kelas tiap node
        self.n_classes_: int | None = None
        self.n_features_in_: int | None = None
        self.max_depth_: int | None = None
        self.max_features_: int | None = None

    @staticmethod
    def resolve_max_features(max_features: Any, n_features: int) -> int:
        """Ubah ``"sqrt"``, ``None``, int, atau float menjadi jumlah fitur per node."""
        if max_features is None:
            return n_features
        if isinstance(max_features, str):
            key = max_features.lower()
            if key == "sqrt":
                return max(1, int(np.floor(np.sqrt(n_features))))
            if key == "log2":
                return max(1, int(np.floor(np.log2(n_features)))) if n_features > 0 else 1
            if key == "all":
                return n_features
            try:
                max_features = int(key)
            except ValueError as exc:
                raise ValueError(f"max_features tidak dikenal: {key!r}") from exc
        if isinstance(max_features, bool):
            raise ValueError(f"max_features tidak valid: {max_features!r}")
        if isinstance(max_features, (int, np.integer)):
            if int(max_features) < 1:
                raise ValueError("max_features integer harus >= 1")
            return min(int(max_features), n_features)
        if isinstance(max_features, float):
            if not np.isfinite(max_features) or max_features <= 0.0:
                raise ValueError("max_features float harus > 0.0")
            if max_features <= 1.0:
                return max(1, int(np.floor(max_features * n_features)))
            return min(int(max_features), n_features)
        raise ValueError(f"max_features tidak valid: {max_features!r}")

    # -- fit --------------------------------------------------------------
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        max_depth: int | None = None,
        max_features: Any = None,
        rng: np.random.Generator | int | None = None,
        n_classes: int | None = None,
    ) -> "DecisionTree":
        X_arr = np.asarray(X, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.int64)
        if X_arr.ndim != 2:
            raise ValueError("X harus berupa matriks 2 dimensi")
        if y_arr.ndim != 1 or y_arr.shape[0] != X_arr.shape[0]:
            raise ValueError("y harus vektor 1D dengan panjang sama dengan X")
        if X_arr.shape[0] == 0:
            raise ValueError("Tidak dapat melakukan fit pada data kosong")
        if not np.isfinite(X_arr).all():
            raise ValueError("X mengandung NaN atau nilai tak hingga")
        if max_depth is not None and int(max_depth) < 0:
            raise ValueError("max_depth harus >= 0 atau None")

        if rng is None:
            generator = np.random.default_rng(0)
        elif isinstance(rng, (int, np.integer)):
            generator = np.random.default_rng(int(rng))
        else:
            generator = rng

        self.n_classes_ = (
            int(n_classes) if n_classes is not None else int(y_arr.max()) + 1
        )
        if (y_arr < 0).any() or (y_arr >= self.n_classes_).any():
            raise ValueError("Label kelas di luar rentang n_classes")
        self.n_features_in_ = int(X_arr.shape[1])
        self.max_depth_ = None if max_depth is None else int(max_depth)
        self.max_features_ = self.resolve_max_features(
            max_features, self.n_features_in_
        )

        feature_idx: list[int] = []
        threshold: list[float] = []
        left_child: list[int] = []
        right_child: list[int] = []
        node_probs: list[np.ndarray] = []

        def new_node() -> int:
            node_id = len(feature_idx)
            feature_idx.append(-1)
            threshold.append(np.nan)
            left_child.append(-1)
            right_child.append(-1)
            node_probs.append(np.zeros(self.n_classes_, dtype=np.float64))
            return node_id

        root = new_node()
        stack: list[tuple[int, np.ndarray, int]] = [(root, np.arange(X_arr.shape[0]), 0)]

        while stack:
            node_id, indices, depth = stack.pop()
            node_labels = y_arr[indices]
            counts = np.bincount(node_labels, minlength=self.n_classes_).astype(
                np.float64
            )
            node_probs[node_id] = counts / counts.sum()

            # Syarat berhenti.
            pure = gini_impurity(counts) == 0.0
            too_deep = self.max_depth_ is not None and depth >= self.max_depth_
            too_small = indices.size < 2
            if pure or too_deep or too_small:
                continue

            # Pilih subset fitur acak (max_features) untuk node ini.
            if self.max_features_ < self.n_features_in_:
                candidates = generator.choice(
                    self.n_features_in_, size=self.max_features_, replace=False
                )
            else:
                candidates = np.arange(self.n_features_in_)

            node_X = X_arr[np.ix_(indices, candidates)]
            local_feature, split_threshold, gain = find_best_split(
                node_X, node_labels, np.arange(candidates.size)
            )
            if local_feature is None or split_threshold is None or gain <= 0.0:
                continue
            feature = int(candidates[local_feature])

            mask = node_X[:, local_feature] <= split_threshold
            if not mask.any() or mask.all():
                continue

            left_indices = indices[mask]
            right_indices = indices[~mask]
            left_node = new_node()
            right_node = new_node()
            feature_idx[node_id] = feature
            threshold[node_id] = split_threshold
            left_child[node_id] = left_node
            right_child[node_id] = right_node

            stack.append((left_node, left_indices, depth + 1))
            stack.append((right_node, right_indices, depth + 1))

        self.feature_idx_ = np.asarray(feature_idx, dtype=np.int64)
        self.threshold_ = np.asarray(threshold, dtype=np.float64)
        self.left_child_ = np.asarray(left_child, dtype=np.int64)
        self.right_child_ = np.asarray(right_child, dtype=np.int64)
        self.leaf_probs_ = np.vstack(node_probs).astype(np.float64)
        return self

    # -- prediksi ---------------------------------------------------------
    def _validate_X(self, X: np.ndarray) -> np.ndarray:
        if self.feature_idx_ is None or self.leaf_probs_ is None:
            raise RuntimeError("DecisionTree belum di-fit")
        X_arr = np.asarray(X, dtype=np.float64)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)
        if X_arr.ndim != 2:
            raise ValueError("X harus berupa matriks 2 dimensi")
        if X_arr.shape[1] != self.n_features_in_:
            raise ValueError(
                f"Jumlah fitur tidak cocok: {X_arr.shape[1]} vs {self.n_features_in_}"
            )
        if not np.isfinite(X_arr).all():
            raise ValueError("X mengandung NaN atau nilai tak hingga")
        return X_arr

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Telusuri pohon dari akar ke daun; semua baris maju satu level bersamaan."""
        X_arr = self._validate_X(X)
        node = np.zeros(X_arr.shape[0], dtype=np.int64)
        while True:
            active = np.flatnonzero(self.feature_idx_[node] != -1)
            if active.size == 0:
                break
            current = node[active]
            go_left = X_arr[active, self.feature_idx_[current]] <= self.threshold_[current]
            node[active] = np.where(
                go_left, self.left_child_[current], self.right_child_[current]
            )
        return self.leaf_probs_[node]

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(X), axis=1)

    # -- serialisasi ------------------------------------------------------
    def to_arrays(self) -> dict[str, np.ndarray]:
        if self.feature_idx_ is None:
            raise RuntimeError("DecisionTree belum di-fit")
        return {
            "feature_idx": np.asarray(self.feature_idx_, dtype=np.int32),
            "threshold": np.asarray(self.threshold_, dtype=np.float64),
            "left_child": np.asarray(self.left_child_, dtype=np.int32),
            "right_child": np.asarray(self.right_child_, dtype=np.int32),
            "leaf_probs": np.asarray(self.leaf_probs_, dtype=np.float64),
            "n_classes": np.array(self.n_classes_, dtype=np.int64),
            "n_features_in": np.array(self.n_features_in_, dtype=np.int64),
        }

    @classmethod
    def from_arrays(cls, arrays: Any) -> "DecisionTree":
        def scalar(key: str, default: Any = None) -> Any:
            if key not in arrays:
                return default
            value = arrays[key]
            return value.item() if getattr(value, "ndim", 0) == 0 else value

        obj = cls()
        obj.feature_idx_ = np.asarray(arrays["feature_idx"], dtype=np.int64)
        obj.threshold_ = np.asarray(arrays["threshold"], dtype=np.float64)
        obj.left_child_ = np.asarray(arrays["left_child"], dtype=np.int64)
        obj.right_child_ = np.asarray(arrays["right_child"], dtype=np.int64)
        obj.leaf_probs_ = np.asarray(arrays["leaf_probs"], dtype=np.float64)
        obj.n_classes_ = int(scalar("n_classes", obj.leaf_probs_.shape[1]))
        obj.n_features_in_ = int(scalar("n_features_in", 0)) or None
        obj.max_depth_ = None
        obj.max_features_ = None

        n_nodes = obj.feature_idx_.shape[0]
        if not (
            obj.threshold_.shape[0]
            == obj.left_child_.shape[0]
            == obj.right_child_.shape[0]
            == obj.leaf_probs_.shape[0]
            == n_nodes
        ):
            raise ValueError("Array DecisionTree tidak konsisten")
        return obj