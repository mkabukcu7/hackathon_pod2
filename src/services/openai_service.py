"""
Azure OpenAI Service - Reusable client wrapper for GPT-4o-mini
Uses Microsoft Entra ID (Azure AD) token authentication via service principal,
since key-based auth is disabled by subscription policy.
"""
import os
import logging
from typing import List, Dict, Any, Optional

from openai import AzureOpenAI
from azure.identity import ClientSecretCredential, get_bearer_token_provider
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Singleton client instance
_client: Optional[AzureOpenAI] = None
_deployment: Optional[str] = None


def _get_client() -> Optional[AzureOpenAI]:
    """Get or create the singleton Azure OpenAI client using Entra ID auth."""
    global _client, _deployment

    if _client is not None:
        return _client

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    _deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")

    if not endpoint:
        logger.warning("AZURE_OPENAI_ENDPOINT not set — AI features disabled")
        return None

    if not all([tenant_id, client_id, client_secret]):
        logger.warning("Azure service principal credentials not configured — AI features disabled")
        return None

    try:
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )
        _client = AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
            api_version=api_version,
        )
        logger.info(f"Azure OpenAI client initialized with Entra ID auth (deployment: {_deployment})")
        return _client
    except Exception as e:
        logger.error(f"Failed to initialize Azure OpenAI client: {e}")
        return None


def chat_completion(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1024,
    response_format: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Send a chat completion request to Azure OpenAI.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        temperature: Sampling temperature (0.0 - 1.0).
        max_tokens: Maximum tokens in the response.
        response_format: Optional response format (e.g. {"type": "json_object"}).

    Returns:
        The assistant's reply text, or None if the call fails.
    """
    client = _get_client()
    if client is None:
        return None

    try:
        kwargs: Dict[str, Any] = {
            "model": _deployment,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Azure OpenAI chat completion failed: {e}")
        return None


def is_available() -> bool:
    """Check whether the Azure OpenAI service is configured and reachable."""
    return _get_client() is not None
