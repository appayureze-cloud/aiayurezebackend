"""
RAG-Based Conversation System
Uses all chat history from Supabase to provide intelligent, context-aware responses

Features:
- Saves ALL conversations (app + WhatsApp) to Supabase
- Retrieves relevant past conversations for context
- Builds conversation history for AI model
- Semantic search through chat history
- Conversation summarization for long contexts
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from .database import db_manager

logger = logging.getLogger(__name__)

class RAGConversationSystem:
    """
    Retrieval Augmented Generation system for conversations
    Uses Supabase to store and retrieve conversation history
    """
    
    def __init__(self):
        self.max_context_messages = 50  # Maximum messages to include in context
        self.relevance_threshold = 0.5  # Minimum relevance score
        
    async def save_conversation(
        self,
        user_id: str,
        journey_id: str,
        user_message: str,
        ai_response: str,
        platform: str = "app",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save conversation to Supabase for RAG retrieval
        
        Args:
            user_id: Patient/user ID
            journey_id: Journey ID (used as session_id)
            user_message: User's message
            ai_response: AI's response
            platform: 'app' or 'whatsapp'
            metadata: Additional metadata
        
        Returns:
            Save result with message IDs
        """
        try:
            # Prepare metadata
            full_metadata = {
                "platform": platform,
                "user_id": user_id,
                "journey_id": journey_id,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Save to Supabase chat_messages table
            # This is used by RAG for retrieval
            result = await db_manager.save_chat_message(
                session_id=journey_id,  # Using journey_id as session
                user_message=user_message,
                assistant_response=ai_response,
                language=metadata.get("language", "en") if metadata else "en",
                metadata=full_metadata
            )
            
            logger.info(
                f"💾 Saved conversation to RAG: user={user_id}, "
                f"platform={platform}, journey={journey_id[:8]}..."
            )
            
            return {
                "success": True,
                "message": "Conversation saved to RAG system",
                "platform": platform,
                "journey_id": journey_id
            }
            
        except Exception as e:
            logger.error(f"❌ Error saving conversation to RAG: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_conversation_context(
        self,
        user_id: str,
        journey_id: Optional[str] = None,
        current_query: Optional[str] = None,
        max_messages: int = 20
    ) -> str:
        """
        Build conversation context from chat history for AI model
        
        This retrieves relevant past conversations and formats them
        as context for the AI model to generate better responses
        
        Args:
            user_id: Patient/user ID
            journey_id: Filter by specific journey
            current_query: Current user query (for relevance filtering)
            max_messages: Maximum messages to include
        
        Returns:
            Formatted conversation context string
        """
        try:
            # Get recent conversation history
            history = await self._get_recent_history(
                user_id=user_id,
                journey_id=journey_id,
                limit=max_messages
            )
            
            if not history:
                return "No previous conversation history."
            
            # Filter for relevance if query provided
            if current_query:
                history = await self._filter_relevant_conversations(
                    conversations=history,
                    query=current_query
                )
            
            # Build context string
            context = self._build_context_string(history)
            
            logger.info(
                f"📚 Built RAG context: {len(history)} messages, "
                f"{len(context)} chars for user={user_id}"
            )
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Error building conversation context: {e}")
            return "Error retrieving conversation history."
    
    async def get_similar_conversations(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar past conversations using semantic search
        
        Args:
            query: Search query
            user_id: Filter by user (optional)
            limit: Number of results
        
        Returns:
            List of similar conversations
        """
        try:
            # Get all conversations (or by user)
            if user_id:
                sessions = await db_manager.get_user_sessions(user_id, limit=10)
                all_conversations = []
                
                for session in sessions:
                    history = await db_manager.get_chat_history(
                        session["id"],
                        limit=100
                    )
                    all_conversations.extend(history)
            else:
                # Get recent conversations across all users
                # TODO: Implement global search
                all_conversations = []
            
            # Simple keyword matching (can be enhanced with embeddings)
            similar = self._simple_similarity_search(
                query=query,
                conversations=all_conversations,
                limit=limit
            )
            
            return similar
            
        except Exception as e:
            logger.error(f"❌ Error finding similar conversations: {e}")
            return []
    
    async def summarize_conversation_history(
        self,
        user_id: str,
        journey_id: str
    ) -> str:
        """
        Create a summary of conversation history for long contexts
        
        When conversation history is too long, this creates a summary
        to fit within AI model's context window
        
        Args:
            user_id: Patient/user ID
            journey_id: Journey ID
        
        Returns:
            Conversation summary
        """
        try:
            # Get full history
            sessions = await db_manager.get_user_sessions(user_id, limit=1)
            if not sessions:
                return "No conversation history."
            
            history = await db_manager.get_chat_history(
                sessions[0]["id"],
                limit=1000  # Get all messages
            )
            
            # Build summary
            summary = self._create_summary(history)
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error summarizing conversation: {e}")
            return "Error creating summary."
    
    # Helper Methods
    
    async def _get_recent_history(
        self,
        user_id: str,
        journey_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        try:
            # Get user sessions
            sessions = await db_manager.get_user_sessions(user_id, limit=5)
            
            if not sessions:
                return []
            
            # If journey_id provided, filter sessions
            if journey_id:
                sessions = [s for s in sessions if s["id"] == journey_id]
            
            # Get chat history from latest session
            if sessions:
                history = await db_manager.get_chat_history(
                    sessions[0]["id"],
                    limit=limit
                )
                return history
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting recent history: {e}")
            return []
    
    def _build_context_string(
        self,
        conversations: List[Dict[str, Any]]
    ) -> str:
        """
        Build formatted context string from conversations
        
        Format:
        [Previous Conversation]
        User: How are you?
        Assistant: I'm well, thank you! How can I help?
        User: What should I eat?
        Assistant: For breakfast, I recommend...
        
        [Current Context]
        Based on the above conversation...
        """
        if not conversations:
            return "No previous conversation."
        
        context_parts = ["[Previous Conversation History]\n"]
        
        for conv in conversations[-20:]:  # Last 20 messages
            # Add user message
            user_msg = conv.get("user_message", "")
            if user_msg:
                context_parts.append(f"User: {user_msg}")
            
            # Add assistant response
            ai_msg = conv.get("assistant_response", "")
            if ai_msg:
                context_parts.append(f"Assistant: {ai_msg}")
            
            context_parts.append("")  # Empty line
        
        context_parts.append("\n[Current Context]")
        context_parts.append(
            "Based on the above conversation history, "
            "provide a personalized response to the user's current query."
        )
        
        return "\n".join(context_parts)
    
    async def _filter_relevant_conversations(
        self,
        conversations: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """Filter conversations by relevance to current query"""
        # Simple keyword matching
        # Can be enhanced with embeddings and cosine similarity
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_conversations = []
        
        for conv in conversations:
            # Calculate relevance score
            user_msg = conv.get("user_message", "").lower()
            ai_msg = conv.get("assistant_response", "").lower()
            
            combined = user_msg + " " + ai_msg
            conv_words = set(combined.split())
            
            # Jaccard similarity
            intersection = query_words & conv_words
            union = query_words | conv_words
            
            if union:
                score = len(intersection) / len(union)
            else:
                score = 0
            
            if score > 0:
                scored_conversations.append((score, conv))
        
        # Sort by score descending
        scored_conversations.sort(reverse=True, key=lambda x: x[0])
        
        # Return top conversations
        return [conv for score, conv in scored_conversations if score > self.relevance_threshold]
    
    def _simple_similarity_search(
        self,
        query: str,
        conversations: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Simple keyword-based similarity search"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored = []
        
        for conv in conversations:
            user_msg = conv.get("user_message", "").lower()
            ai_msg = conv.get("assistant_response", "").lower()
            
            # Count matching words
            score = 0
            for word in query_words:
                if word in user_msg or word in ai_msg:
                    score += 1
            
            if score > 0:
                scored.append((score, conv))
        
        # Sort by score
        scored.sort(reverse=True, key=lambda x: x[0])
        
        return [conv for score, conv in scored[:limit]]
    
    def _create_summary(
        self,
        conversations: List[Dict[str, Any]]
    ) -> str:
        """Create summary of conversation history"""
        if not conversations:
            return "No conversation history."
        
        # Count stats
        total_messages = len(conversations)
        
        # Extract key topics (simple version)
        all_text = " ".join([
            conv.get("user_message", "") + " " + 
            conv.get("assistant_response", "")
            for conv in conversations
        ]).lower()
        
        # Common health topics
        topics = {
            "diet": ["eat", "food", "diet", "breakfast", "lunch", "dinner"],
            "medicine": ["medicine", "tablet", "dose", "medication"],
            "symptoms": ["pain", "symptom", "feeling", "sick", "hurt"],
            "sleep": ["sleep", "rest", "tired", "fatigue"],
            "exercise": ["exercise", "walk", "yoga", "activity"]
        }
        
        mentioned_topics = []
        for topic, keywords in topics.items():
            if any(keyword in all_text for keyword in keywords):
                mentioned_topics.append(topic)
        
        summary = f"""
Conversation Summary:
- Total messages: {total_messages}
- Topics discussed: {', '.join(mentioned_topics) if mentioned_topics else 'general health'}
- Recent conversations available for context

The AI has access to full conversation history for personalized responses.
"""
        
        return summary.strip()


# Global RAG system instance
rag_system = RAGConversationSystem()
