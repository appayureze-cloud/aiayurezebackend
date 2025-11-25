"""
AI Content Filter
Prevents inappropriate or off-topic responses from AI model
Ensures all responses are focused on Ayurvedic wellness
"""

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

class AIContentFilter:
    """
    Content filter for AI responses
    Validates that responses are appropriate and on-topic
    """
    
    def __init__(self):
        # Inappropriate keywords that should not appear in responses
        self.inappropriate_keywords = [
            'porn', 'sex', 'nude', 'explicit', 'adult content',
            'violence', 'weapon', 'kill', 'murder', 'death',
            'drug', 'cocaine', 'heroin', 'meth',
            'racist', 'hate speech', 'slur',
            'suicide', 'self-harm'
        ]
        
        # Off-topic keywords (not related to health/wellness)
        self.offtopic_keywords = [
            'movie', 'film', 'celebrity', 'politics',
            'sports', 'game', 'gaming', 'video game',
            'cryptocurrency', 'bitcoin', 'stock market'
        ]
        
        # Ayurvedic/health-related keywords (good indicators)
        self.health_keywords = [
            'ayurveda', 'ayurvedic', 'dosha', 'vata', 'pitta', 'kapha',
            'health', 'wellness', 'medicine', 'herb', 'treatment',
            'digestion', 'sleep', 'stress', 'immunity', 'diet',
            'yoga', 'meditation', 'balance', 'natural', 'holistic'
        ]
    
    def is_appropriate(self, text: str) -> Tuple[bool, str]:
        """
        Check if AI response is appropriate
        Returns: (is_appropriate, reason)
        """
        text_lower = text.lower()
        
        # Check for inappropriate content
        for keyword in self.inappropriate_keywords:
            if keyword in text_lower:
                logger.warning(f"⚠️ Inappropriate content detected: {keyword}")
                return False, f"inappropriate_content:{keyword}"
        
        return True, "appropriate"
    
    def is_on_topic(self, text: str) -> Tuple[bool, str]:
        """
        Check if AI response is on-topic (health/wellness related)
        Returns: (is_on_topic, reason)
        """
        text_lower = text.lower()
        
        # Check for off-topic content
        offtopic_count = 0
        for keyword in self.offtopic_keywords:
            if keyword in text_lower:
                offtopic_count += 1
        
        # If multiple off-topic keywords, likely off-topic
        if offtopic_count >= 2:
            logger.warning(f"⚠️ Off-topic content detected: {offtopic_count} keywords")
            return False, "off_topic"
        
        # Check for health-related keywords
        health_count = 0
        for keyword in self.health_keywords:
            if keyword in text_lower:
                health_count += 1
        
        # If no health keywords, might be off-topic
        if health_count == 0 and len(text) > 100:
            logger.warning("⚠️ No health keywords detected in long response")
            return False, "no_health_context"
        
        return True, "on_topic"
    
    def filter_response(self, ai_response: str, user_query: str) -> Tuple[str, bool]:
        """
        Filter AI response and return safe version
        Returns: (filtered_response, was_modified)
        """
        # Check if response is appropriate
        is_appropriate, reason = self.is_appropriate(ai_response)
        
        if not is_appropriate:
            logger.error(f"❌ Blocked inappropriate AI response: {reason}")
            return self._get_safe_fallback_response(user_query), True
        
        # Check if response is on-topic
        is_on_topic, reason = self.is_on_topic(ai_response)
        
        if not is_on_topic:
            logger.warning(f"⚠️ Off-topic AI response: {reason}")
            return self._get_safe_fallback_response(user_query), True
        
        # Response is safe and on-topic
        return ai_response, False
    
    def _get_safe_fallback_response(self, user_query: str) -> str:
        """
        Get a safe, appropriate fallback response
        """
        fallback_responses = [
            """🌿 *Ayurvedic Wellness Focus*

I'm Astra, your Ayurvedic health assistant. I specialize in:

💊 *Medicine & Herbs* - Natural remedies and treatments
🧘 *Wellness Practices* - Yoga, meditation, lifestyle
🍃 *Dosha Balance* - Vata, Pitta, Kapha harmony
🥗 *Nutrition* - Ayurvedic diet and recipes
😴 *Sleep & Stress* - Natural management techniques

*How can I help with your health and wellness today?*

_Please ask questions related to Ayurveda and holistic health._""",

            """🙏 *Namaste!*

I'm designed to help with Ayurvedic health and wellness questions.

*I can assist with:*
• Ayurvedic principles and doshas
• Natural remedies and herbs
• Digestive health and nutrition
• Sleep, stress, and immunity
• Seasonal wellness practices

*Ask me anything about your health journey!* 🌿

_For other topics, please visit our website or contact support._""",

            """✨ *Your Ayurvedic Wellness Partner*

I'm here to guide you on Ayurvedic health topics:

🌿 **Traditional Wisdom**
Learn about ancient Ayurvedic practices

💚 **Natural Healing**
Discover herbs and holistic treatments

🧘 **Balanced Living**
Tips for mind-body wellness

*What health question can I answer for you?*

_I focus on Ayurveda and wellness - please ask related questions!_"""
        ]
        
        # Choose fallback based on query length
        if len(user_query) > 50:
            return fallback_responses[0]  # Detailed response
        else:
            return fallback_responses[1]  # Medium response
    
    def validate_query(self, user_query: str) -> Tuple[bool, str]:
        """
        Validate if user query is appropriate
        Returns: (is_valid, reason)
        """
        query_lower = user_query.lower()
        
        # Check for inappropriate queries
        for keyword in self.inappropriate_keywords:
            if keyword in query_lower:
                logger.warning(f"⚠️ Inappropriate query: {keyword}")
                return False, f"inappropriate:{keyword}"
        
        return True, "valid"

# Global instance
_content_filter = None

def get_content_filter() -> AIContentFilter:
    """Get or create content filter instance"""
    global _content_filter
    if _content_filter is None:
        _content_filter = AIContentFilter()
    return _content_filter
