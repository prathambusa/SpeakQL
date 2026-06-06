"""Tests for schema introspection."""
import pytest
from backend.db.introspect import introspect_schema, table_to_document


@pytest.mark.asyncio
async def test_introspect_returns_all_tables(db_engine):
    tables = await introspect_schema(db_engine)
    names = {t.name for t in tables}
    assert {"products", "orders", "order_items"}.issubset(names)


@pytest.mark.asyncio
async def test_introspect_column_names(db_engine):
    tables = await introspect_schema(db_engine)
    products = next(t for t in tables if t.name == "products")
    col_names = {c.name for c in products.columns}
    assert {"product_id", "product_name", "unit_price", "in_stock"}.issubset(col_names)


@pytest.mark.asyncio
async def test_introspect_primary_key_detected(db_engine):
    tables = await introspect_schema(db_engine)
    products = next(t for t in tables if t.name == "products")
    pk_cols = [c for c in products.columns if c.primary_key]
    assert len(pk_cols) >= 1
    assert pk_cols[0].name == "product_id"


@pytest.mark.asyncio
async def test_introspect_row_count(db_engine):
    tables = await introspect_schema(db_engine)
    products = next(t for t in tables if t.name == "products")
    assert products.row_count == 5


@pytest.mark.asyncio
async def test_introspect_sample_values(db_engine):
    tables = await introspect_schema(db_engine)
    products = next(t for t in tables if t.name == "products")
    assert products.sample_values is not None
    assert "product_name" in products.sample_values
    assert len(products.sample_values["product_name"]) > 0


def test_table_to_document_format(db_engine):
    from backend.models import TableMeta, ColumnMeta
    table = TableMeta(
        name="products",
        columns=[
            ColumnMeta(name="product_id", type="INTEGER", primary_key=True),
            ColumnMeta(name="product_name", type="TEXT"),
        ],
        row_count=5,
        sample_values={"product_name": ["Chai", "Chang"]},
    )
    doc = table_to_document(table)
    assert "Table: products" in doc
    assert "product_id" in doc
    assert "PRIMARY KEY" in doc
    assert "Chai" in doc
