"""Langkah 4: Random Forest = bootstrap + banyak pohon + voting (PPT slide 8).

Tiap pohon dilatih pada sampel bootstrap (dengan pengembalian) dan memakai
subset fitur acak di setiap node. Seed pohon ke-t selalu (random_state, t),
sehingga memakai ``n`` pohon pertama sama dengan melatih hutan berukuran ``n``.
Sifat ini dimanfaatkan grid search agar 100/200/300 pohon cukup satu kali fit.
"""

from __future__ import annotations
from typing import Any
import numpy as np
from .tree import DecisionTree
from concurrent.futures import ProcessPoolExecutor

def _fit_tree_range(args):
    """Latih sekumpulan pohon; seed tiap pohon hanya bergantung pada indeksnya."""
    X_arr, y_arr, tree_indices, max_depth, max_features, random_state, n_classes = args
    n_samples = X_arr.shape[0]
    trees = []
    for tree_index in tree_indices:
        rng = np.random.default_rng(np.random.SeedSequence([random_state, tree_index]))
        bootstrap_indices = rng.integers(0, n_samples, size=n_samples)
        tree = DecisionTree()
        tree.fit(
            X_arr[bootstrap_indices],
            y_arr[bootstrap_indices],
            max_depth=max_depth,
            max_features=max_features,
            rng=rng,
            n_classes=n_classes,
        )
        trees.append(tree)
    return trees

class RandomForest:
    """Hutan pohon keputusan dengan bootstrap sampling dan voting probabilitas."""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int | None = None,
        max_features: Any = "sqrt",
        random_state: int = 42,
        n_classes: int | None = None,
        n_jobs: int = 1,
    ) -> None:
        if int(n_estimators) < 1:
            raise ValueError("n_estimators harus >= 1")
        if max_depth is not None and int(max_depth) < 0:
            raise ValueError("max_depth harus >= 0 atau None")

        self.n_estimators = int(n_estimators)
        self.max_depth = None if max_depth is None else int(max_depth)
        self.max_features = max_features
        self.random_state = int(random_state)
        self.n_jobs = int(n_jobs)
        self.n_classes = int(n_classes) if n_classes is not None else None

        self.trees_: list[DecisionTree] = []
        self.n_classes_: int | None = None
        self.n_features_in_: int | None = None
        self.max_features_: int | None = None

    # -- fit --------------------------------------------------------------
    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomForest":
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

        self.n_features_in_ = int(X_arr.shape[1])
        self.n_classes_ = (
            int(self.n_classes) if self.n_classes is not None else int(y_arr.max()) + 1
        )
        if (y_arr < 0).any() or (y_arr >= self.n_classes_).any():
            raise ValueError("Label kelas di luar rentang n_classes")
        self.max_features_ = DecisionTree.resolve_max_features(
            self.max_features, self.n_features_in_
        )

        indices = list(range(self.n_estimators))
        chunks = (
            [indices]
            if self.n_jobs == 1 or self.n_estimators < 2
            else [indices[i :: self.n_jobs] for i in range(self.n_jobs)]
        )
        payloads = [
            (X_arr, y_arr, chunk, self.max_depth, self.max_features_,
             self.random_state, self.n_classes_)
            for chunk in chunks
            if chunk
        ]
        if len(payloads) == 1:
            results = [_fit_tree_range(payloads[0])]
        else:
            with ProcessPoolExecutor(max_workers=len(payloads)) as pool:
                results = list(pool.map(_fit_tree_range, payloads))

        # Kembalikan urutan pohon sesuai indeks (hasil sama persis dengan n_jobs=1).
        trees: list[DecisionTree | None] = [None] * self.n_estimators
        for payload, chunk_trees in zip(payloads, results):
            for tree_index, tree in zip(payload[2], chunk_trees):
                trees[tree_index] = tree
        self.trees_ = trees  # type: ignore[assignment]
        return self

    # -- prediksi ---------------------------------------------------------
    def _validate_X(self, X: np.ndarray) -> np.ndarray:
        if not self.trees_:
            raise RuntimeError("RandomForest belum di-fit")
        X_arr = np.asarray(X, dtype=np.float64)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)
        if X_arr.ndim != 2:
            raise ValueError("X harus berupa matriks 2 dimensi")
        if X_arr.shape[1] != self.n_features_in_:
            raise ValueError(
                f"Jumlah fitur tidak cocok: {X_arr.shape[1]} vs {self.n_features_in_}"
            )
        return X_arr

    def _average_proba(self, X: np.ndarray, n_trees: int) -> np.ndarray:
        X_arr = self._validate_X(X)
        if not 1 <= n_trees <= len(self.trees_):
            raise ValueError(
                f"n_trees harus antara 1 dan {len(self.trees_)} (diterima {n_trees})"
            )
        total = np.zeros((X_arr.shape[0], self.n_classes_), dtype=np.float64)
        for tree in self.trees_[:n_trees]:
            total += tree.predict_proba(X_arr)
        return total / float(n_trees)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Rata-rata distribusi kelas daun dari seluruh pohon."""
        return self._average_proba(X, len(self.trees_))

    def predict_proba_prefix(self, X: np.ndarray, n_trees: int) -> np.ndarray:
        """Probabilitas memakai ``n_trees`` pohon pertama (optimasi tuning)."""
        return self._average_proba(X, int(n_trees))
    
    def predict_proba_per_tree(self, X: np.ndarray) -> np.ndarray:
        """Probabilitas tiap pohon, bentuk ``(n_pohon, n_baris, n_kelas)``.

        Dipakai grid search: rata-rata ``n`` pohon pertama = probabilitas hutan
        berukuran ``n``, jadi 100/200/300 pohon cukup satu kali prediksi.
        """
        X_arr = self._validate_X(X)
        out = np.empty(
            (len(self.trees_), X_arr.shape[0], self.n_classes_), dtype=np.float64
        )
        for index, tree in enumerate(self.trees_):
            out[index] = tree.predict_proba(X_arr)
        return out

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(X), axis=1)

    def predict_one(self, x: np.ndarray) -> int:
        vector = np.asarray(x, dtype=np.float64).reshape(1, -1)
        return int(self.predict(vector)[0])

    # -- serialisasi ------------------------------------------------------
    def to_arrays(self) -> dict[str, np.ndarray]:
        """Gabungkan semua pohon menjadi array datar (untuk ``rf_trees.npz``)."""
        if not self.trees_:
            raise RuntimeError("RandomForest belum di-fit")

        offsets = [0]
        features: list[np.ndarray] = []
        thresholds: list[np.ndarray] = []
        left_children: list[np.ndarray] = []
        right_children: list[np.ndarray] = []
        leaf_probs: list[np.ndarray] = []

        for tree in self.trees_:
            arrays = tree.to_arrays()
            offset = offsets[-1]
            left = np.asarray(arrays["left_child"], dtype=np.int32).copy()
            right = np.asarray(arrays["right_child"], dtype=np.int32).copy()
            left[left >= 0] += offset
            right[right >= 0] += offset
            features.append(np.asarray(arrays["feature_idx"], dtype=np.int32))
            thresholds.append(np.asarray(arrays["threshold"], dtype=np.float64))
            left_children.append(left)
            right_children.append(right)
            leaf_probs.append(np.asarray(arrays["leaf_probs"], dtype=np.float64))
            offsets.append(offset + int(left.shape[0]))

        if self.max_features is None:
            max_features = "none"
        elif isinstance(self.max_features, str):
            max_features = self.max_features
        else:
            max_features = str(self.max_features)
        return {
            "n_estimators": np.array(len(self.trees_), dtype=np.int64),
            "max_depth": np.array(
                -1 if self.max_depth is None else self.max_depth, dtype=np.int64
            ),
            "max_features": np.array(max_features, dtype="<U32"),
            "random_state": np.array(self.random_state, dtype=np.int64),
            "n_classes": np.array(self.n_classes_, dtype=np.int64),
            "n_features_in": np.array(self.n_features_in_, dtype=np.int64),
            "tree_offsets": np.asarray(offsets, dtype=np.int64),
            "feature_idx": np.concatenate(features),
            "threshold": np.concatenate(thresholds),
            "left_child": np.concatenate(left_children),
            "right_child": np.concatenate(right_children),
            "leaf_probs": np.vstack(leaf_probs),
        }

    @classmethod
    def from_arrays(cls, arrays: Any) -> "RandomForest":
        def scalar(key: str) -> Any:
            value = arrays[key]
            return value.item() if getattr(value, "ndim", 0) == 0 else value

        n_estimators = int(scalar("n_estimators"))
        max_depth_raw = int(scalar("max_depth"))
        max_depth = None if max_depth_raw < 0 else max_depth_raw
        max_features_raw = str(scalar("max_features"))
        if max_features_raw.lower() == "none":
            max_features: Any = None
        else:
            try:
                max_features = int(max_features_raw)
            except ValueError:
                try:
                    max_features = float(max_features_raw)
                except ValueError:
                    max_features = max_features_raw
        random_state = int(scalar("random_state"))
        n_classes = int(scalar("n_classes"))
        n_features_in = int(scalar("n_features_in"))

        obj = cls(
            n_estimators=n_estimators,
            max_depth=max_depth,
            max_features=max_features,
            random_state=random_state,
            n_classes=n_classes,
        )
        obj.n_classes_ = n_classes
        obj.n_features_in_ = n_features_in
        obj.max_features_ = DecisionTree.resolve_max_features(
            max_features, n_features_in
        )

        offsets = np.asarray(arrays["tree_offsets"], dtype=np.int64)
        features = np.asarray(arrays["feature_idx"], dtype=np.int64)
        thresholds = np.asarray(arrays["threshold"], dtype=np.float64)
        left_all = np.asarray(arrays["left_child"], dtype=np.int64)
        right_all = np.asarray(arrays["right_child"], dtype=np.int64)
        leaf_all = np.asarray(arrays["leaf_probs"], dtype=np.float64)

        if offsets.shape[0] != n_estimators + 1:
            raise ValueError("tree_offsets tidak konsisten dengan n_estimators")
        if offsets[0] != 0 or offsets[-1] != features.shape[0]:
            raise ValueError("tree_offsets tidak menutupi seluruh node")
        if np.any(np.diff(offsets) <= 0):
            raise ValueError("Setiap pohon harus memiliki minimal satu node")
        n_nodes = features.shape[0]
        if not (
            thresholds.shape[0]
            == left_all.shape[0]
            == right_all.shape[0]
            == n_nodes
        ):
            raise ValueError("Array hutan tidak konsisten")
        if leaf_all.shape != (n_nodes, n_classes):
            raise ValueError("leaf_probs tidak konsisten dengan n_classes")
        if n_features_in < 1 or n_classes < 1:
            raise ValueError("n_features_in/n_classes tidak valid")

        obj.trees_ = []
        for index in range(n_estimators):
            start, end = int(offsets[index]), int(offsets[index + 1])
            for child in (left_all[start:end], right_all[start:end]):
                mask = child >= 0
                if ((child[mask] < start) | (child[mask] >= end)).any():
                    raise ValueError(
                        "Indeks anak pohon tidak menunjuk node dalam pohon yang sama"
                    )

            tree = DecisionTree()
            tree.n_classes_ = n_classes
            tree.n_features_in_ = n_features_in
            tree.max_depth_ = max_depth
            tree.max_features_ = obj.max_features_
            tree.feature_idx_ = features[start:end].copy()
            tree.threshold_ = thresholds[start:end].copy()

            left = left_all[start:end].copy()
            right = right_all[start:end].copy()
            left[left >= 0] -= start
            right[right >= 0] -= start
            tree.left_child_ = left
            tree.right_child_ = right
            tree.leaf_probs_ = leaf_all[start:end].copy()
            obj.trees_.append(tree)
        return obj