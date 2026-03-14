"""
GigBridge AI Chat Module
Database-powered Chat Service
"""

from .db_chat_service import DatabaseChatService
from .chat_routes import register_chat_routes

__all__ = ['DatabaseChatService', 'register_chat_routes']
