"""
Journey Rating & Feedback System
Collects patient feedback at journey completion
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class JourneyRating(BaseModel):
    """Patient rating and feedback"""
    journey_id: str
    case_id: str
    patient_id: str
    rating: int  # 1-5 stars
    feedback_text: Optional[str] = None
    symptom_improvement: int  # 0-100%
    companion_helpfulness: int  # 1-5
    reminder_effectiveness: int  # 1-5
    would_recommend: bool
    rated_at: str

class RatingSystem:
    """Manages journey ratings and feedback"""
    
    def __init__(self):
        self.ratings_cache: Dict[str, JourneyRating] = {}
    
    async def collect_rating(
        self,
        journey_id: str,
        case_id: str,
        patient_id: str,
        rating: int,
        feedback_text: Optional[str] = None,
        symptom_improvement: int = 100,
        companion_helpfulness: int = 5,
        reminder_effectiveness: int = 5,
        would_recommend: bool = True
    ) -> Dict[str, Any]:
        """
        Collect patient rating after journey completion
        
        Args:
            rating: 1-5 stars
            symptom_improvement: 0-100%
            companion_helpfulness: 1-5
            reminder_effectiveness: 1-5
            would_recommend: True/False
        """
        try:
            rating_data = JourneyRating(
                journey_id=journey_id,
                case_id=case_id,
                patient_id=patient_id,
                rating=rating,
                feedback_text=feedback_text,
                symptom_improvement=symptom_improvement,
                companion_helpfulness=companion_helpfulness,
                reminder_effectiveness=reminder_effectiveness,
                would_recommend=would_recommend,
                rated_at=datetime.utcnow().isoformat()
            )
            
            # Cache rating
            self.ratings_cache[journey_id] = rating_data
            
            # TODO: Save to database
            # db.save_rating(rating_data.dict())
            
            logger.info(f"✅ Rating collected for journey {journey_id}: {rating} stars")
            
            return {
                "success": True,
                "message": "Thank you for your feedback!",
                "rating_data": rating_data.dict()
            }
            
        except Exception as e:
            logger.error(f"Error collecting rating: {e}")
            return {
                "success": False,
                "message": "Failed to save rating",
                "error": str(e)
            }
    
    def get_rating(self, journey_id: str) -> Optional[JourneyRating]:
        """Get rating for a journey"""
        return self.ratings_cache.get(journey_id)
    
    def get_average_rating(self) -> float:
        """Calculate average rating across all journeys"""
        if not self.ratings_cache:
            return 0.0
        
        total = sum(r.rating for r in self.ratings_cache.values())
        return total / len(self.ratings_cache)
    
    def get_nps_score(self) -> float:
        """Calculate Net Promoter Score"""
        if not self.ratings_cache:
            return 0.0
        
        promoters = sum(1 for r in self.ratings_cache.values() if r.would_recommend)
        detractors = sum(1 for r in self.ratings_cache.values() if not r.would_recommend)
        total = len(self.ratings_cache)
        
        return ((promoters - detractors) / total) * 100

# Global instance
rating_system = RatingSystem()
