"""
In-Memory Cache for Companion System
Provides graceful degradation when Supabase is unavailable
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)


class CompanionCache:
    """
    Thread-safe in-memory cache for companion journeys
    Used as fallback when database is unavailable
    """
    
    def __init__(self):
        self._journeys: Dict[str, Dict[str, Any]] = {}
        self._interactions: Dict[str, List[Dict[str, Any]]] = {}  # journey_id -> list of interactions
        self._cases: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        logger.info("✅ CompanionCache initialized for graceful degradation")
    
    # ============ JOURNEY OPERATIONS ============
    
    def set_journey(self, journey_id: str, journey_data: Dict[str, Any]) -> None:
        """Store journey in cache"""
        with self._lock:
            self._journeys[journey_id] = journey_data
            logger.info(f"📦 Cached journey {journey_id}")
    
    def get_journey(self, journey_id: str) -> Optional[Dict[str, Any]]:
        """Get journey from cache"""
        with self._lock:
            return self._journeys.get(journey_id)
    
    def get_user_journeys(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all journeys for a user"""
        with self._lock:
            return [
                journey for journey in self._journeys.values()
                if journey.get("user_id") == user_id
            ]
    
    def update_journey(self, journey_id: str, updates: Dict[str, Any]) -> bool:
        """Update journey in cache"""
        with self._lock:
            if journey_id in self._journeys:
                self._journeys[journey_id].update(updates)
                self._journeys[journey_id]["updated_at"] = datetime.utcnow().isoformat()
                return True
            return False
    
    # ============ INTERACTION OPERATIONS ============
    
    def add_interaction(self, journey_id: str, interaction: Dict[str, Any]) -> None:
        """Add interaction to cache"""
        with self._lock:
            if journey_id not in self._interactions:
                self._interactions[journey_id] = []
            self._interactions[journey_id].append(interaction)
            
            # Update journey interaction count
            if journey_id in self._journeys:
                self._journeys[journey_id]["interaction_count"] = len(self._interactions[journey_id])
                self._journeys[journey_id]["last_interaction"] = datetime.utcnow().isoformat()
    
    def get_interactions(self, journey_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get interactions for a journey"""
        with self._lock:
            interactions = self._interactions.get(journey_id, [])
            return interactions[-limit:] if len(interactions) > limit else interactions
    
    # ============ CASE OPERATIONS ============
    
    def set_case(self, case_id: str, case_data: Dict[str, Any]) -> None:
        """Store case in cache"""
        with self._lock:
            self._cases[case_id] = case_data
            logger.info(f"📦 Cached case {case_id}")
    
    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get case from cache"""
        with self._lock:
            return self._cases.get(case_id)
    
    def update_case(self, case_id: str, updates: Dict[str, Any]) -> bool:
        """Update case in cache"""
        with self._lock:
            if case_id in self._cases:
                self._cases[case_id].update(updates)
                self._cases[case_id]["updated_at"] = datetime.utcnow().isoformat()
                return True
            return False
    
    # ============ CACHE STATS ============
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        with self._lock:
            return {
                "journeys_count": len(self._journeys),
                "interactions_count": sum(len(i) for i in self._interactions.values()),
                "cases_count": len(self._cases)
            }
    
    def clear(self) -> None:
        """Clear all cache (use with caution)"""
        with self._lock:
            self._journeys.clear()
            self._interactions.clear()
            self._cases.clear()
            logger.warning("🗑️ CompanionCache cleared")


# Global cache instance
companion_cache = CompanionCache()
