"""Tes kontrak konstanta dan aturan 'core tanpa scikit-learn'."""

from __future__ import annotations
import re
from pathlib import Path
from app.core import CATEGORICAL, CLASS_LABELS, FEATURE_COLUMNS, NUMERIC

CORE_DIR = Path(__file__).resolve().parents[2] / "app" / "core"


def test_constants_contract() -> None:
    assert CLASS_LABELS == ["small", "medium", "large"]
    assert len(NUMERIC) == 5
    assert len(CATEGORICAL) == 4
    assert FEATURE_COLUMNS == NUMERIC + CATEGORICAL
    assert len(FEATURE_COLUMNS) == 9
    assert "year" not in FEATURE_COLUMNS


def test_core_never_imports_sklearn() -> None:
    pattern = re.compile(r"^\s*(?:from|import)\s+sklearn", re.MULTILINE)
    offenders = [
        str(path.relative_to(CORE_DIR))
        for path in CORE_DIR.rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []