"""seed master sar_priorities

Revision ID: 002_seed_sar_priorities
Revises: 001_initial_schema
Create Date: 2026-11-22
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import context, op

revision: str = "002_seed_sar_priorities"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SAR_PRIORITIES = (
    {
        "predicted_class": "small",
        "sar_priority_level": "Rendah",
        "sar_recommendation": (
            "Perkiraan skala kecil; dapat ditangani setelah kejadian berskala lebih besar"
        ),
    },
    {
        "predicted_class": "medium",
        "sar_priority_level": "Sedang",
        "sar_recommendation": (
            "Perkiraan skala menengah; siapkan sumber daya dan pantau perkembangan"
        ),
    },
    {
        "predicted_class": "large",
        "sar_priority_level": "Tinggi",
        "sar_recommendation": (
            "Perkiraan skala besar; prioritaskan penanganan dan verifikasi lapangan"
        ),
    },
)

sar_priorities_table = sa.table(
    "sar_priorities",
    sa.column("predicted_class", sa.String(length=10)),
    sa.column("sar_priority_level", sa.String(length=20)),
    sa.column("sar_recommendation", sa.Text()),
)


def upgrade() -> None:
    if context.is_offline_mode():
        # `--sql` tidak punya koneksi untuk SELECT; tulis seed apa adanya.
        op.bulk_insert(sar_priorities_table, list(SAR_PRIORITIES))
        return

    bind = op.get_bind()
    existing = {
        str(row[0])
        for row in bind.execute(sa.text("SELECT predicted_class FROM sar_priorities"))
    }
    rows = [row for row in SAR_PRIORITIES if row["predicted_class"] not in existing]
    if rows:
        op.bulk_insert(sar_priorities_table, rows)


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM sar_priorities "
            "WHERE predicted_class IN ('small', 'medium', 'large')"
        )
    )
