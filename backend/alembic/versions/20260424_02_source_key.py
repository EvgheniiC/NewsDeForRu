"""Add stable source_key to sources.

Revision ID: 20260424_02
Revises: 20260424_01
Create Date: 2026-04-24
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision: str = "20260424_02"
down_revision: str | None = "20260424_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _slug_base(name: str) -> str:
    base: str = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return (base[:64] if base else "source")[:64]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("sources"):
        return

    columns: set[str] = {column["name"] for column in inspector.get_columns("sources")}
    if "source_key" not in columns:
        op.add_column("sources", sa.Column("source_key", sa.String(length=64), nullable=True))

    rows = bind.execute(text("SELECT id, name, source_key FROM sources")).mappings().all()
    used_keys: set[str] = {str(r["source_key"]) for r in rows if r.get("source_key") not in (None, "")}

    for row in rows:
        if row.get("source_key"):
            continue
        rid: int = int(row["id"])
        name: str = str(row["name"])
        base: str = _slug_base(name)
        candidate: str = base
        suffix: int = 0
        while candidate in used_keys:
            suffix += 1
            candidate = f"{base}_{suffix}"[:64]
        used_keys.add(candidate)
        bind.execute(text("UPDATE sources SET source_key = :sk WHERE id = :id"), {"sk": candidate, "id": rid})

    inspector = inspect(bind)
    sk_col: dict[str, object] | None = next(
        (c for c in inspector.get_columns("sources") if c["name"] == "source_key"),
        None,
    )
    cons_names: set[str] = {
        str(c["name"]) for c in inspector.get_unique_constraints("sources") if c.get("name")
    }

    with op.batch_alter_table("sources") as batch_op:
        if sk_col is not None and bool(sk_col.get("nullable")):
            batch_op.alter_column(
                "source_key",
                existing_type=sa.String(length=64),
                nullable=False,
            )
        if "uq_sources_source_key" not in cons_names:
            batch_op.create_unique_constraint("uq_sources_source_key", ["source_key"])


def downgrade() -> None:
    with op.batch_alter_table("sources") as batch_op:
        batch_op.drop_constraint("uq_sources_source_key", type_="unique")
        batch_op.drop_column("source_key")
