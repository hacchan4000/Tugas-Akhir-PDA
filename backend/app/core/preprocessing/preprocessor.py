"""Preprocessor gabungan: scaler untuk numerik + one-hot untuk kategorikal.

Satu objek ini dipakai di notebook (training) dan backend (inference),
sehingga transformasinya identik. Disimpan sebagai JSON lewat ``to_dict``.
"""

from __future__ import annotations
from typing import Any, Mapping, Sequence
import numpy as np
import pandas as pd
from ..constants import CATEGORICAL, NUMERIC
from .helpers import clean_categorical, require_columns
from .transformers import ManualOneHotEncoder, ManualStandardScaler


class Preprocessor:
    """Gabungan scaler numerik + one-hot encoder kategorikal."""

    def __init__(
        self,
        numeric_columns: Sequence[str] | None = None,
        categorical_columns: Sequence[str] | None = None,
    ) -> None:
        self.numeric_columns = list(numeric_columns or NUMERIC)
        self.categorical_columns = list(
            CATEGORICAL if categorical_columns is None else categorical_columns
        )
        self.scaler_ = ManualStandardScaler()
        self.encoder_ = ManualOneHotEncoder()
        self.is_fitted_ = False

    # -- internal ---------------------------------------------------------
    def _numeric_matrix(self, df: pd.DataFrame) -> np.ndarray:
        require_columns(df, self.numeric_columns)
        try:
            X = df[self.numeric_columns].to_numpy(dtype=np.float64)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Kolom numerik tidak dapat dikonversi ke float: {exc}"
            ) from exc
        if not np.isfinite(X).all():
            raise ValueError("Fitur numerik mengandung NaN atau nilai tak hingga")
        return X

    def _categorical_matrix(self, df: pd.DataFrame) -> np.ndarray:
        require_columns(df, self.categorical_columns)
        columns = [
            clean_categorical(df[col]).to_numpy(dtype=str)
            for col in self.categorical_columns
        ]
        if not columns:
            return np.empty((len(df), 0), dtype=object)
        return np.column_stack(columns)

    # -- API --------------------------------------------------------------
    @property
    def n_features_out_(self) -> int:
        """Jumlah kolom setelah one-hot (disebut ``d_enc`` di PRD)."""
        if not self.is_fitted_:
            raise RuntimeError("Preprocessor belum di-fit")
        return len(self.numeric_columns) + sum(
            len(cats) for cats in self.encoder_.categories_
        )

    def fit(self, df: pd.DataFrame) -> "Preprocessor":
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Preprocessor.fit membutuhkan pandas.DataFrame")
        X_num = self._numeric_matrix(df)
        X_cat = self._categorical_matrix(df)
        self.scaler_.fit(X_num)
        self.encoder_.fit(X_cat)
        self.is_fitted_ = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted_:
            raise RuntimeError("Preprocessor belum di-fit")
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Preprocessor.transform membutuhkan pandas.DataFrame")
        X_num = self.scaler_.transform(self._numeric_matrix(df))
        X_cat = self.encoder_.transform(self._categorical_matrix(df))
        return np.hstack([X_num, X_cat]).astype(np.float64, copy=False)

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.fit(df).transform(df)

    def transform_one(self, df_row: Any) -> np.ndarray:
        """Transform satu baris (dict, Series, atau DataFrame 1 baris) -> vektor 1D."""
        if isinstance(df_row, pd.DataFrame):
            frame = df_row
        elif isinstance(df_row, pd.Series):
            frame = df_row.to_frame().T
        elif isinstance(df_row, Mapping):
            frame = pd.DataFrame([dict(df_row)])
        else:
            raise TypeError(
                "df_row harus berupa dict, pandas.Series, atau DataFrame 1 baris"
            )
        if len(frame) != 1:
            raise ValueError(
                f"transform_one membutuhkan tepat 1 baris, diterima {len(frame)}"
            )
        return self.transform(frame)[0]

    # -- serialisasi ------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        if not self.is_fitted_:
            raise RuntimeError("Preprocessor belum di-fit")
        return {
            "numeric_columns": list(self.numeric_columns),
            "categorical_columns": list(self.categorical_columns),
            "mean": self.scaler_.mean_.tolist(),
            "scale": self.scaler_.scale_.tolist(),
            "categories": [list(cats) for cats in self.encoder_.categories_],
            "n_features_out": int(self.n_features_out_),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Preprocessor":
        required = {
            "numeric_columns",
            "categorical_columns",
            "mean",
            "scale",
            "categories",
        }
        missing = sorted(required - set(payload.keys()))
        if missing:
            raise ValueError(f"Payload preprocessor tidak lengkap: {missing}")

        obj = cls(
            numeric_columns=payload["numeric_columns"],
            categorical_columns=payload["categorical_columns"],
        )
        mean = np.asarray(payload["mean"], dtype=np.float64)
        scale = np.asarray(payload["scale"], dtype=np.float64)
        categories = [[str(v) for v in cats] for cats in payload["categories"]]

        if mean.shape != scale.shape:
            raise ValueError("mean dan scale harus memiliki panjang yang sama")
        if len(categories) != len(obj.categorical_columns):
            raise ValueError("Jumlah kategori tidak cocok dengan kolom kategorikal")
        if mean.shape[0] != len(obj.numeric_columns):
            raise ValueError("Jumlah mean tidak cocok dengan kolom numerik")

        obj.scaler_.mean_ = mean
        obj.scaler_.scale_ = scale
        obj.encoder_.categories_ = categories
        obj.is_fitted_ = True
        return obj