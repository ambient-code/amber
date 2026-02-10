"""LLM factory for Amber.

Provides a centralized factory function for creating LLM instances
using Anthropic models via Google Cloud Vertex AI Model Garden.
"""

from langchain_anthropic import ChatAnthropicVertex

from amber.config import get_settings


def get_llm(
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> ChatAnthropicVertex:
    """Create an LLM instance using Anthropic via Vertex AI.

    Args:
        max_tokens: Maximum tokens for the response. Defaults to settings.llm_max_tokens.
        temperature: Sampling temperature. Defaults to settings.llm_temperature.

    Returns:
        ChatAnthropicVertex instance configured for the Vertex AI Model Garden.
    """
    settings = get_settings()

    return ChatAnthropicVertex(
        project_id=settings.gcp_project_id,
        region=settings.gcp_region,
        model_name=settings.llm_model,
        temperature=temperature if temperature is not None else settings.llm_temperature,
        max_tokens=max_tokens if max_tokens is not None else settings.llm_max_tokens,
    )
