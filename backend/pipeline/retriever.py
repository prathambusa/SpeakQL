from __future__ import annotations

import logging

import chromadb
from chromadb.utils.embedding_functions import (
    OpenAIEmbeddingFunction,
    DefaultEmbeddingFunction,
)

from backend.config import settings
from backend.models import TableMeta
from backend.db.introspect import table_to_document

logger = logging.getLogger(__name__)

_COLLECTION_PREFIX = "speakql_schema"


def _make_embedding_function():
    if settings.embedding_provider == "local":
        # Uses chromadb's built-in ONNX MiniLM-L6-v2 — no API key needed.
        return DefaultEmbeddingFunction()
    if settings.embedding_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        return OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.openai_embedding_model,
        )
    raise RuntimeError(
        f"Unsupported EMBEDDING_PROVIDER: {settings.embedding_provider}. "
        "Set EMBEDDING_PROVIDER=local (no key) or openai."
    )


def _get_chroma_client() -> chromadb.ClientAPI:
    if settings.chroma_mode == "http":
        return chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def _collection_name(db_alias: str) -> str:
    return f"{_COLLECTION_PREFIX}_{db_alias}"


def index_tables(tables: list[TableMeta], db_alias: str) -> None:
    """Embed and store table schemas in Chroma (replaces existing collection)."""
    client = _get_chroma_client()
    ef = _make_embedding_function()
    col_name = _collection_name(db_alias)

    # Drop and recreate for a clean refresh
    try:
        client.delete_collection(col_name)
    except Exception:
        pass

    collection = client.create_collection(col_name, embedding_function=ef)

    documents = [table_to_document(t) for t in tables]
    ids = [t.name for t in tables]
    metadatas = [{"table_name": t.name, "db_alias": db_alias} for t in tables]

    if documents:
        collection.add(documents=documents, ids=ids, metadatas=metadatas)
        logger.info("Indexed %d tables for alias '%s'", len(documents), db_alias)


def is_collection_empty(db_alias: str) -> bool:
    try:
        client = _get_chroma_client()
        ef = _make_embedding_function()
        col = client.get_collection(_collection_name(db_alias), embedding_function=ef)
        return col.count() == 0
    except Exception:
        return True


def delete_index(db_alias: str) -> None:
    """Remove the Chroma collection for a database alias."""
    try:
        client = _get_chroma_client()
        client.delete_collection(_collection_name(db_alias))
    except Exception as exc:
        logger.warning("Could not delete Chroma collection for '%s': %s", db_alias, exc)


def retrieve_tables(question: str, db_alias: str, top_k: int | None = None) -> list[str]:
    """
    Embed the question and return the top-K most relevant table names.
    Returns an empty list if the collection doesn't exist or is empty.
    """
    k = top_k or settings.top_k_tables
    try:
        client = _get_chroma_client()
        ef = _make_embedding_function()
        collection = client.get_collection(_collection_name(db_alias), embedding_function=ef)
        if collection.count() == 0:
            return []
        results = collection.query(query_texts=[question], n_results=min(k, collection.count()))
        return results["ids"][0]  # list of table names
    except Exception as exc:
        logger.warning("Chroma retrieval failed: %s", exc)
        return []
