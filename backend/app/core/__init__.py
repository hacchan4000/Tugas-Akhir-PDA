"""Modul ML manual (NumPy murni) yang dipakai notebook training dan backend."""

from .constants import (
    CATEGORICAL,
    CLASS_LABELS,
    CLASS_TO_INDEX,
    FEATURE_COLUMNS,
    INDEX_TO_CLASS,
    NUMERIC,
    TARGET,
)
from .knn import CHUNK_SIZE, KNNClassifier, compute_distances
from .metrics import (
    accuracy,
    balanced_accuracy,
    confusion_matrix,
    evaluate,
    macro_f1,
    precision,
    recall,
)
from .model_selection import (
    encode_target,
    grid_search_cv,
    holdout_grid_search,
    stratified_holdout,
    stratified_kfold,
)
from .preprocessing import (
    ManualOneHotEncoder,
    ManualStandardScaler,
    Preprocessor,
    clean_raw,
    engineer_features,
    payload_to_frame,
)
from .random_forest import (
    MAX_THRESHOLDS,
    DecisionTree,
    RandomForest,
    find_best_split,
    gini_gain,
    gini_impurity,
)

__all__ = [
    "CLASS_LABELS",
    "CATEGORICAL",
    "NUMERIC",
    "TARGET",
    "FEATURE_COLUMNS",
    "CLASS_TO_INDEX",
    "INDEX_TO_CLASS",
    "clean_raw",
    "engineer_features",
    "payload_to_frame",
    "ManualStandardScaler",
    "ManualOneHotEncoder",
    "Preprocessor",
    "compute_distances",
    "KNNClassifier",
    "CHUNK_SIZE",
    "gini_impurity",
    "gini_gain",
    "find_best_split",
    "DecisionTree",
    "RandomForest",
    "MAX_THRESHOLDS",
    "stratified_holdout",
    "stratified_kfold",
    "grid_search_cv",
    "holdout_grid_search",
    "encode_target",
    "macro_f1",
    "balanced_accuracy",
    "accuracy",
    "precision",
    "recall",
    "confusion_matrix",
    "evaluate",
]
