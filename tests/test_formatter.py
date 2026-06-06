"""Tests for SQL validation and row-cap injection."""
import pytest
from backend.pipeline.formatter import (
    SQLValidationError,
    inject_limit,
    validate_sql,
)


# ── Safe queries ───────────────────────────────────────────────────────────────

def test_valid_simple_select():
    validate_sql("SELECT * FROM products")


def test_valid_select_with_where():
    validate_sql("SELECT product_id, product_name FROM products WHERE unit_price > 10")


def test_valid_select_with_join():
    sql = """
    SELECT o.order_id, p.product_name, oi.quantity
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    """
    validate_sql(sql)


def test_valid_aggregate():
    validate_sql("SELECT category, COUNT(*) AS cnt, AVG(unit_price) FROM products GROUP BY category")


# ── Unsafe queries blocked by regex ───────────────────────────────────────────

@pytest.mark.parametrize("bad_sql", [
    "DROP TABLE products",
    "DELETE FROM orders WHERE order_id = 1",
    "UPDATE products SET unit_price = 0",
    "INSERT INTO products VALUES (99, 'Hack', 'X', 0, 0)",
    "TRUNCATE TABLE orders",
    "ALTER TABLE products ADD COLUMN foo TEXT",
    "CREATE TABLE evil (id INT)",
    "EXEC sp_executesql 'DROP TABLE products'",
])
def test_blocked_write_statements(bad_sql):
    with pytest.raises(SQLValidationError):
        validate_sql(bad_sql)


# ── Non-SELECT AST ─────────────────────────────────────────────────────────────

def test_empty_sql_raises():
    with pytest.raises(SQLValidationError):
        validate_sql("")


# ── Row-cap injection ─────────────────────────────────────────────────────────

def test_inject_limit_adds_limit():
    result = inject_limit("SELECT * FROM products", max_rows=100)
    assert "100" in result.upper() or "limit" in result.lower()


def test_inject_limit_preserves_existing():
    sql = "SELECT * FROM products LIMIT 5"
    result = inject_limit(sql, max_rows=1000)
    # Should keep 5, not replace with 1000
    lower = result.lower()
    # LIMIT 5 still present, 1000 should NOT appear
    assert "5" in result
    assert "1000" not in result


def test_inject_limit_default_1000():
    result = inject_limit("SELECT * FROM orders")
    lower = result.lower()
    assert "limit" in lower
    assert "1000" in result
