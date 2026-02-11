"""
Centralized LLM Configuration - Google Gemini 3 Flash via LangChain.

This module provides the ONLY LLM configuration for the entire system.
All agents MUST use the LLM instances provided by this module.

LLM: Google Gemini 3 Flash
Access: LangChain's Google Generative AI integration
"""

from functools import lru_cache
from typing import Any, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from app.config import get_settings

T = TypeVar("T", bound=BaseModel)


@lru_cache
def get_llm(
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> ChatGoogleGenerativeAI:
    """
    Get the centralized Gemini 3 Flash LLM instance.

    This is the ONLY function that should be used to obtain an LLM instance.
    All agents in the system use this same LLM configuration.

    Args:
        temperature: Override default temperature (0.0-1.0)
        max_tokens: Override default max output tokens

    Returns:
        ChatGoogleGenerativeAI: Configured Gemini 3 Flash instance

    Example:
        >>> llm = get_llm()
        >>> response = llm.invoke("Hello, world!")
    """
    settings = get_settings()

    resolved_temp = temperature if temperature is not None else settings.llm_temperature
    resolved_max = max_tokens if max_tokens is not None else settings.llm_max_tokens

    kwargs: dict = {
        "model": settings.llm_model,
        "google_api_key": settings.google_api_key,
        "timeout": settings.llm_timeout,
        "convert_system_message_to_human": True,
    }

    if resolved_temp is not None:
        kwargs["temperature"] = resolved_temp
    if resolved_max is not None:
        kwargs["max_output_tokens"] = resolved_max

    return ChatGoogleGenerativeAI(**kwargs)


def get_llm_with_structured_output(
    output_schema: type[T],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> BaseChatModel:
    """
    Get Gemini 3 Flash configured for structured JSON output.

    This wraps the base LLM with structured output parsing capabilities,
    ensuring agents produce valid, typed responses.

    Args:
        output_schema: Pydantic model defining expected output structure
        temperature: Override default temperature
        max_tokens: Override default max tokens

    Returns:
        LLM configured to output structured data matching the schema

    Example:
        >>> class TaskOutput(BaseModel):
        ...     task_name: str
        ...     steps: list[str]
        >>> llm = get_llm_with_structured_output(TaskOutput)
        >>> result = llm.invoke("Create a task for building a login page")
    """
    base_llm = get_llm(temperature=temperature, max_tokens=max_tokens)
    return base_llm.with_structured_output(output_schema)


def get_llm_config() -> dict[str, Any]:
    """
    Get current LLM configuration for debugging/logging.

    Returns:
        Dictionary containing current LLM settings
    """
    settings = get_settings()
    return {
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "timeout": settings.llm_timeout,
        "provider": "Google Generative AI (Gemini)",
    }
