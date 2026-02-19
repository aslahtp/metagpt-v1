"""
Embeddings configuration for RAG.

Uses Google Gemini's text-embedding-004 model via LangChain.
Reuses the existing GOOGLE_API_KEY from app config.
"""

from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import get_settings


@lru_cache
def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """
    Get the configured embeddings instance.

    Uses Google's text-embedding-004 model which produces
    768-dimensional embeddings optimized for retrieval.

    Returns:
        GoogleGenerativeAIEmbeddings instance
    """
    settings = get_settings()
    return GoogleGenerativeAIEmbeddings(
        model=settings.rag_embedding_model,
        google_api_key=settings.google_api_key,
    )
