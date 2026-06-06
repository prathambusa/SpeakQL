from __future__ import annotations

from typing import Any
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.models import ColumnMeta, TableMeta


async def introspect_schema(engine: AsyncEngine, sample_rows: int = 3) -> list[TableMeta]:
    """Introspect every table in the connected DB and return rich metadata."""

    def _sync_introspect(sync_conn) -> list[TableMeta]:
        insp = inspect(sync_conn)
        tables: list[TableMeta] = []

        for table_name in insp.get_table_names():
            columns: list[ColumnMeta] = []
            pk_cols = set(insp.get_pk_constraint(table_name).get("constrained_columns", []))
            fk_map: dict[str, str] = {}
            for fk in insp.get_foreign_keys(table_name):
                for local_col, ref_col in zip(
                    fk["constrained_columns"], fk["referred_columns"]
                ):
                    fk_map[local_col] = f"{fk['referred_table']}.{ref_col}"

            for col in insp.get_columns(table_name):
                columns.append(
                    ColumnMeta(
                        name=col["name"],
                        type=str(col["type"]),
                        nullable=col.get("nullable", True),
                        primary_key=col["name"] in pk_cols,
                        foreign_key=fk_map.get(col["name"]),
                    )
                )

            # Row count
            row_count: int | None = None
            try:
                result = sync_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                row_count = result.scalar()
            except Exception:
                pass

            # Sample values
            sample_values: dict[str, list[Any]] = {}
            try:
                result = sync_conn.execute(
                    text(f'SELECT * FROM "{table_name}" LIMIT {sample_rows}')
                )
                col_names = list(result.keys())
                rows_data = result.fetchall()
                for i, col_name in enumerate(col_names):
                    sample_values[col_name] = [row[i] for row in rows_data]
            except Exception:
                pass

            tables.append(
                TableMeta(
                    name=table_name,
                    columns=columns,
                    row_count=row_count,
                    sample_values=sample_values if sample_values else None,
                )
            )

        return tables

    async with engine.connect() as conn:
        tables = await conn.run_sync(_sync_introspect)

    return tables


def table_to_document(table: TableMeta) -> str:
    """Render a TableMeta as a plain-text document for embedding."""
    lines = [f"Table: {table.name}"]
    if table.row_count is not None:
        lines.append(f"Row count: {table.row_count}")

    lines.append("Columns:")
    for col in table.columns:
        flags = []
        if col.primary_key:
            flags.append("PRIMARY KEY")
        if col.foreign_key:
            flags.append(f"FK → {col.foreign_key}")
        if not col.nullable:
            flags.append("NOT NULL")
        flag_str = f"  [{', '.join(flags)}]" if flags else ""
        lines.append(f"  - {col.name}: {col.type}{flag_str}")

    if table.sample_values:
        lines.append("Sample values:")
        for col_name, vals in table.sample_values.items():
            lines.append(f"  {col_name}: {vals}")

    return "\n".join(lines)
