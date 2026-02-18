"""
Services package initialization
"""

from .cosmos_db_service import CosmosDBService
from .openai_service import chat_completion, is_available as openai_available

__all__ = ["CosmosDBService"]
