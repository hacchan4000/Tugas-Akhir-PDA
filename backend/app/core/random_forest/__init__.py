"""Paket Random Forest manual (CART/Gini), NumPy murni.

Urutan konsep:
    impurity  -> ukuran ketidakmurnian node (Gini)
    splitting -> mencari (fitur, threshold) terbaik
    tree      -> membangun satu pohon keputusan
    forest    -> bootstrap + banyak pohon + voting
"""

from .forest import RandomForest
from .impurity import gini_gain, gini_impurity
from .splitting import MAX_THRESHOLDS, find_best_split
from .tree import DecisionTree

__all__ = [
    "gini_impurity",
    "gini_gain",
    "find_best_split",
    "DecisionTree",
    "RandomForest",
    "MAX_THRESHOLDS",
]