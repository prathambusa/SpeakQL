from __future__ import annotations

import re
import sqlglot
from sqlglot import exp

# Secondary regex guard — belt-and-suspenders before AST check
_WRITE_PATTERN = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|TRUNCATE|ALTER|CREATE|EXEC|EXECUTE|REPLACE|MERGE|CALL|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


class SQLValidationError(ValueError):
    pass


def validate_sql(sql: str) -> None:
    """
    Raise SQLValidationError if sql is not a safe SELECT statement.
    Two layers:
      1. Regex keyword blocklist
      2. sqlglot AST: top-level statement must be a Select
    """
    if _WRITE_PATTERN.search(sql):
        raise SQLValidationError(
            "The generated query contained a write keyword and was blocked."
        )

    try:
        statements = sqlglot.parse(sql)
    except sqlglot.errors.ParseError as exc:
        raise SQLValidationError(f"SQL parse error: {exc}") from exc

    if not statements:
        raise SQLValidationError("Empty SQL statement.")

    for stmt in statements:
        # CTEs (WITH … SELECT …) parse as exp.With whose .this is the SELECT
        inner = stmt.this if isinstance(stmt, exp.With) else stmt
        if not isinstance(inner, exp.Select):
            raise SQLValidationError(
                f"Only SELECT statements are allowed; got {type(inner).__name__}."
            )


# Matches GROUP_CONCAT(DISTINCT col, 'sep') — invalid in SQLite
_GROUP_CONCAT_DISTINCT = re.compile(
    r"GROUP_CONCAT\(\s*DISTINCT\s+([^,)]+?)\s*,\s*(?:'[^']*'|\"[^\"]*\")\s*\)",
    re.IGNORECASE,
)


def fix_sqlite_quirks(sql: str) -> str:
    """Rewrite common SQLite-incompatible patterns produced by the LLM."""
    # GROUP_CONCAT(DISTINCT col, sep) → GROUP_CONCAT(DISTINCT col)
    sql = _GROUP_CONCAT_DISTINCT.sub(r"GROUP_CONCAT(DISTINCT \1)", sql)
    return sql


def inject_limit(sql: str, max_rows: int = 1000) -> str:
    """Add LIMIT max_rows if the query has no LIMIT clause."""
    try:
        tree = sqlglot.parse_one(sql)
        if tree.find(exp.Limit) is None:
            tree = tree.limit(max_rows)
        return tree.sql(pretty=False)
    except Exception:
        # Fallback: append LIMIT textually
        stripped = sql.rstrip().rstrip(";")
        return f"{stripped} LIMIT {max_rows}"


def format_sql(sql: str, dialect: str | None = None) -> str:
    """Pretty-print SQL using sqlglot."""
    try:
        return sqlglot.transpile(sql, read=dialect or "sqlite", pretty=True)[0]
    except Exception:
        return sql


def detect_dialect(db_url: str) -> str:
    if "postgresql" in db_url or "postgres" in db_url:
        return "postgres"
    if "mysql" in db_url or "mariadb" in db_url:
        return "mysql"
    return "sqlite"
