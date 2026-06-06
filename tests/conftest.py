"""
Shared fixtures.

Uses a small in-memory SQLite database so no external services are needed.
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock
import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text

# Stub heavy optional dependencies that are only available inside Docker.
# Tests that exercise these code paths mock them out; the stubs just prevent
# ImportError when the module under test does a local `from langchain_core…`
# or `from chromadb…` import.
for _mod in (
    "langchain_core",
    "langchain_core.messages",
    "langchain_anthropic",
    "langchain_openai",
    "chromadb",
    "chromadb.utils",
    "chromadb.utils.embedding_functions",
):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()


SEED_SQL = """
CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT    NOT NULL,
    category     TEXT,
    unit_price   REAL    NOT NULL,
    in_stock     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer    TEXT NOT NULL,
    order_date  TEXT NOT NULL,
    total       REAL NOT NULL
);

CREATE TABLE order_items (
    item_id    INTEGER PRIMARY KEY,
    order_id   INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity   INTEGER NOT NULL,
    price      REAL    NOT NULL
);

INSERT INTO products VALUES
  (1, 'Chai',              'Beverages',  18.00, 39),
  (2, 'Chang',             'Beverages',  19.00, 17),
  (3, 'Aniseed Syrup',     'Condiments', 10.00, 13),
  (4, 'Pavlova',           'Confections',17.45, 29),
  (5, 'Carnarvon Tigers',  'Seafood',    62.50, 42);

INSERT INTO orders VALUES
  (1001, 'Alice',   '2024-07-01', 55.00),
  (1002, 'Bob',     '2024-07-03', 37.45),
  (1003, 'Charlie', '2024-07-05', 125.00),
  (1004, 'Alice',   '2024-08-01', 62.50),
  (1005, 'Diana',   '2024-08-15', 19.00);

INSERT INTO order_items VALUES
  (1, 1001, 1, 2, 18.00),
  (2, 1001, 3, 1, 10.00),
  (3, 1001, 4, 1, 17.45),
  (4, 1002, 3, 2, 10.00),
  (5, 1002, 1, 1, 18.00),
  (6, 1003, 5, 2, 62.50),
  (7, 1004, 5, 1, 62.50),
  (8, 1005, 2, 1, 19.00);
"""


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncEngine:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        for statement in SEED_SQL.split(";"):
            stmt = statement.strip()
            if stmt:
                await conn.execute(text(stmt))
    yield engine
    await engine.dispose()
