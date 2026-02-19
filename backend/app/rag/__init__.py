"""
RAG (Retrieval Augmented Generation) module for codebase-aware agents.

Provides code indexing, embedding, and retrieval so that chat and agents
can understand the existing codebase before making changes.
"""

from app.rag.indexer import CodebaseIndexer
from app.rag.retriever import CodebaseRetriever
from app.rag.vector_store import get_vector_store, delete_vector_store

__all__ = [
    "CodebaseIndexer",
    "CodebaseRetriever",
    "get_vector_store",
    "delete_vector_store",
]
