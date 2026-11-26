"""Tahap 3 preprocessing: Data Transformation (scaler dan one-hot manual).

Keduanya meniru perilaku scikit-learn (ddof=0 dan handle_unknown="ignore")
dan wajib di-fit HANYA pada data latih agar tidak terjadi data leakage.
"""

from __future__ import annotations
from typing import Any
import numpy as np
from .helpers import as_2d_float, as_2d_object


class ManualStandardScaler:
    """StandardScaler manual: ``(X - mean_) / scale_`` dengan ``ddof=0``."""

    def __init__(self) -> None:
        self.mean_: np.ndarray | None = None
        self.scale_: np.ndarray | None = None

    def fit(self, X_num: Any) -> "ManualStandardScaler":
        X = as_2d_float(X_num, "X_num")
        if X.shape[0] == 0:
            raise ValueError("Tidak dapat melakukan fit pada data kosong")
        self.mean_ = X.mean(axis=0)
        scale = X.std(axis=0, ddof=0)
        # Kolom konstan: skala 0 diganti 1.0 agar tidak terjadi pembagian nol.
        self.scale_ = np.where(np.isclose(scale, 0.0, rtol=0.0, atol=1e-15), 1.0, scale)
        return self

    def transform(self, X_num: Any) -> np.ndarray:
        if self.mean_ is None or self.scale_ is None:
            raise RuntimeError("ManualStandardScaler belum di-fit")
        X = as_2d_float(X_num, "X_num")
        if X.shape[1] != self.mean_.shape[0]:
            raise ValueError(
                f"Jumlah fitur tidak cocok: {X.shape[1]} vs {self.mean_.shape[0]}"
            )
        return (X - self.mean_) / self.scale_

    def fit_transform(self, X_num: Any) -> np.ndarray:
        return self.fit(X_num).transform(X_num)


class ManualOneHotEncoder:
    """OneHotEncoder manual dengan perilaku ``handle_unknown="ignore"``.

    Kategori yang tidak dikenal saat transform menghasilkan nol di seluruh kolom
    fitur tersebut (tidak error), penting untuk kategori langka saat CV.
    """

    def __init__(self) -> None:
        self.categories_: list[list[str]] | None = None

    def fit(self, X_cat: Any) -> "ManualOneHotEncoder":
        X = as_2d_object(X_cat, "X_cat")
        if X.shape[0] == 0:
            raise ValueError("Tidak dapat melakukan fit pada data kosong")
        self.categories_ = [
            sorted({str(value) for value in X[:, col]}) for col in range(X.shape[1])
        ]
        return self

    def transform(self, X_cat: Any) -> np.ndarray:
        if self.categories_ is None:
            raise RuntimeError("ManualOneHotEncoder belum di-fit")
        X = as_2d_object(X_cat, "X_cat")
        if X.shape[1] != len(self.categories_):
            raise ValueError(
                f"Jumlah fitur tidak cocok: {X.shape[1]} vs {len(self.categories_)}"
            )

        widths = [len(cats) for cats in self.categories_]
        out = np.zeros((X.shape[0], int(sum(widths))), dtype=np.float64)
        offset = 0
        for col, cats in enumerate(self.categories_):
            values = np.asarray([str(v) for v in X[:, col]], dtype=object)
            for idx, category in enumerate(cats):
                out[:, offset + idx] = values == category
            offset += len(cats)
        return out

    def fit_transform(self, X_cat: Any) -> np.ndarray:
        return self.fit(X_cat).transform(X_cat)