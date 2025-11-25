"""
Unified Conversation API
Merges conversations from App (Supabase) and WhatsApp into single timeline
Enables seamless chat experience across both platforms
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from .companion_system import companion_manager
from .database import db_manager
from .auth_middleware import rate_limit_check
from .rag_conversation_system import rag_system

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/unified-chat",
    tags=["Unified Conversation"],
    dependencies=[Depends(rate_limit_check)]
)

class Message(BaseModel):
    """Unified message model for both app and WhatsApp"""
    id: str
    journey_id: str
    user_id: str
    content: str
    sender: str  # "user" or "assistant"
    platform: str  # "app" or "whatsapp"
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class SendMessageRequest(BaseModel):
    journey_id: str
    user_id: str
    message: str
    platform: str = "app"

class ConversationResponse(BaseModel):
    journey_id: str
    user_id: str
    messages: List[Message]
    total_count: int
    unread_count: int

@router.get("/conversations/{user_id}", response_model=ConversationResponse)
async def get_unified_conversation(
    user_id: str,
    journey_id: Optional[str] = Query(None, description="Filter by journey ID"),
    limit: int = Query(50, description="Number of messages to return"),
    platform: Optional[str] = Query(None, description="Filter by platform: app/whatsapp")
):
    """
    Get unified conversation merging messages from:
    - App (Supabase chat_messages)
    - WhatsApp (companion_interactions)
    
    Returns chronologically sorted messages from both platforms
    """
    try:
        all_messages: List[Message] = []
        
        # Get journey ID if not provided
        if not journey_id:
            # Find user's latest active journey
            # TODO: Query companion_journeys for user's active journey
            journey_id = "auto_detected_journey"
        
        # 1. Get APP messages from Supabase
        if platform != "whatsapp":
            try:
                app_messages = await _get_app_messages(user_id, journey_id, limit)
                all_messages.extend(app_messages)
            except Exception as e:
                logger.warning(f"Could not fetch app messages: {e}")
        
        # 2. Get WHATSAPP messages from companion_interactions
        if platform != "app":
            try:
                whatsapp_messages = await _get_whatsapp_messages(user_id, journey_id, limit)
                all_messages.extend(whatsapp_messages)
            except Exception as e:
                logger.warning(f"Could not fetch WhatsApp messages: {e}")
        
        # 3. Sort all messages chronologically
        all_messages.sort(key=lambda m: m.timestamp)
        
        # 4. Limit to requested count
        all_messages = all_messages[-limit:]
        
        # 5. Calculate unread count (messages from assistant not yet seen)
        unread_count = sum(1 for m in all_messages if m.sender == "assistant" and not m.metadata.get("read", False))
        
        return ConversationResponse(
            journey_id=journey_id,
            user_id=user_id,
            messages=all_messages,
            total_count=len(all_messages),
            unread_count=unread_count
        )
        
    except Exception as e:
        logger.error(f"Error fetching unified conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send")
async def send_unified_message(data: SendMessageRequest):
    """
    Send message from app frontend
    - Saves to Supabase (app messages)
    - Generates AI response
    - Optionally sends to WhatsApp if user is on WhatsApp
    
    Returns AI response immediately for app display
    """
    try:
        logger.info(f"📤 Sending message from {data.platform}: {data.message[:50]}...")
        
        # Get journey details
        journey = await companion_manager.get_journey(data.journey_id)
        if not journey:
            raise HTTPException(status_code=404, detail="Journey not found")
        
        # Save user message
        await db_manager.save_chat_message(
            session_id=data.journey_id,  # Using journey_id as session
            user_message=data.message,
            assistant_response="",  # Will update after AI response
            language=journey.get('language', 'en'),
            metadata={
                "platform": data.platform,
                "user_id": data.user_id
            }
        )
        
        # 🚀 RAG: Get conversation context from history
        conversation_context = await rag_system.get_conversation_context(
            user_id=data.user_id,
            journey_id=data.journey_id,
            current_query=data.message,
            max_messages=20
        )
        
        # Generate AI response with RAG context
        from .model_service import model_service
        
        # Build enhanced context with conversation history
        enhanced_context = f"""
{conversation_context}

[Current Journey Information]
Health Concern: {journey.get('health_concern', 'General wellness')}
Platform: {data.platform}
Language: {journey.get('language', 'en')}

[Current User Query]
{data.message}

Please provide a personalized response based on the conversation history and current context.
"""
        
        ai_response = await model_service.generate_response(
            prompt=data.message,
            language=journey.get('language', 'en'),
            context=enhanced_context,
            max_length=500
        )
        
        # 💾 RAG: Save conversation to RAG system (Supabase)
        await rag_system.save_conversation(
            user_id=data.user_id,
            journey_id=data.journey_id,
            user_message=data.message,
            ai_response=ai_response,
            platform=data.platform,
            metadata={
                "language": journey.get('language', 'en'),
                "health_concern": journey.get('health_concern', ''),
                "context_used": True  # RAG context was used
            }
        )
        
        # Log interaction in companion system
        await companion_manager.log_interaction(
            journey_id=data.journey_id,
            interaction_type="check_in",
            content=ai_response,
            language=journey.get('language', 'en'),
            metadata={
                "platform": data.platform,
                "user_message": data.message
            }
        )
        
        # TODO: Optionally send to WhatsApp if user prefers WhatsApp notifications
        # await _send_to_whatsapp_if_needed(data.user_id, ai_response)
        
        return {
            "success": True,
            "message_id": str(datetime.utcnow().timestamp()),
            "ai_response": ai_response,
            "platform": data.platform,
            "synced_to_whatsapp": False  # TODO: Implement WhatsApp sync
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending unified message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-whatsapp")
async def sync_whatsapp_message(
    journey_id: str,
    user_id: str,
    message: str,
    is_from_user: bool = True
):
    """
    Called by WhatsApp webhook to sync WhatsApp messages to app
    
    When user sends message on WhatsApp:
    1. This endpoint is called
    2. Message saved to companion_interactions
    3. App can fetch via /conversations endpoint
    """
    try:
        logger.info(f"🔄 Syncing WhatsApp message to app: {message[:50]}...")
        
        # Log to companion system (WhatsApp messages)
        await companion_manager.log_interaction(
            journey_id=journey_id,
            interaction_type="check_in",
            content=message,
            metadata={
                "platform": "whatsapp",
                "user_id": user_id,
                "is_from_user": is_from_user
            }
        )
        
        return {
            "success": True,
            "message": "WhatsApp message synced to app",
            "journey_id": journey_id
        }
        
    except Exception as e:
        logger.error(f"Error syncing WhatsApp message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count/{user_id}")
async def get_unread_count(user_id: str):
    """Get count of unread messages for user across all platforms"""
    try:
        # Get user's active journeys
        # Count unread messages
        # TODO: Implement unread counting logic
        
        return {
            "user_id": user_id,
            "unread_count": 0,
            "app_unread": 0,
            "whatsapp_unread": 0
        }
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rag/context/{user_id}")
async def get_rag_context(
    user_id: str,
    journey_id: Optional[str] = Query(None),
    query: Optional[str] = Query(None, description="Current query for relevance filtering"),
    max_messages: int = Query(20, description="Maximum messages to include")
):
    """
    Get RAG conversation context for AI model
    
    Returns formatted conversation history that can be used as context
    for generating AI responses
    """
    try:
        context = await rag_system.get_conversation_context(
            user_id=user_id,
            journey_id=journey_id,
            current_query=query,
            max_messages=max_messages
        )
        
        return {
            "user_id": user_id,
            "journey_id": journey_id,
            "context": context,
            "max_messages": max_messages
        }
        
    except Exception as e:
        logger.error(f"Error getting RAG context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rag/similar")
async def get_similar_conversations(
    query: str = Query(..., description="Search query"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    limit: int = Query(5, description="Number of results")
):
    """
    Find similar past conversations using RAG semantic search
    
    Useful for finding how AI responded to similar queries in the past
    """
    try:
        similar = await rag_system.get_similar_conversations(
            query=query,
            user_id=user_id,
            limit=limit
        )
        
        return {
            "query": query,
            "results": similar,
            "count": len(similar)
        }
        
    except Exception as e:
        logger.error(f"Error finding similar conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rag/summary/{user_id}/{journey_id}")
async def get_conversation_summary(user_id: str, journey_id: str):
    """
    Get summarized conversation history for long contexts
    
    When full conversation history is too long, this provides a summary
    """
    try:
        summary = await rag_system.summarize_conversation_history(
            user_id=user_id,
            journey_id=journey_id
        )
        
        return {
            "user_id": user_id,
            "journey_id": journey_id,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

async def _get_app_messages(user_id: str, journey_id: str, limit: int) -> List[Message]:
    """Fetch messages from app (Supabase chat_messages)"""
    messages: List[Message] = []
    
    try:
        # Get chat history from Supabase
        sessions = await db_manager.get_user_sessions(user_id, limit=1)
        if sessions:
            history = await db_manager.get_chat_history(sessions[0]["id"], limit=limit)
            
            for msg in history:
                # Add user message
                messages.append(Message(
                    id=f"app_user_{msg['created_at']}",
                    journey_id=journey_id,
                    user_id=user_id,
                    content=msg["user_message"],
                    sender="user",
                    platform="app",
                    timestamp=msg["created_at"],
                    metadata={"session_id": sessions[0]["id"]}
                ))
                
                # Add assistant response
                messages.append(Message(
                    id=f"app_assistant_{msg['created_at']}",
                    journey_id=journey_id,
                    user_id=user_id,
                    content=msg["assistant_response"],
                    sender="assistant",
                    platform="app",
                    timestamp=msg["created_at"],
                    metadata={"session_id": sessions[0]["id"]}
                ))
    except Exception as e:
        logger.error(f"Error fetching app messages: {e}")
    
    return messages

async def _get_whatsapp_messages(user_id: str, journey_id: str, limit: int) -> List[Message]:
    """Fetch messages from WhatsApp (companion_interactions)"""
    messages: List[Message] = []
    
    try:
        # Get interactions from companion system
        # These are logged when WhatsApp messages are sent
        
        # TODO: Query companion_interactions table
        # For now, return empty list
        pass
        
    except Exception as e:
        logger.error(f"Error fetching WhatsApp messages: {e}")
    
    return messages
