"""
WhatsApp Authentication Module
Handles Firebase authentication and document uploads via WhatsApp
"""

from app.whatsapp_auth.session_store import session_store, AuthStage
from app.whatsapp_auth.auth_handler import auth_handler
from app.whatsapp_auth.document_handler import document_handler

__all__ = [
    'session_store',
    'AuthStage',
    'auth_handler',
    'document_handler'
]
