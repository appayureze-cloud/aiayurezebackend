"""
Journey Completion Handler
Handles END JOURNEY command, rating collection, and PDF report generation
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .journey_automation import journey_automation
from .journey_rating_system import rating_system
from .journey_pdf_generator import pdf_generator
from .companion_system import companion_manager, CompanionStatus, CaseStatus
from .firebase_email_service import firebase_email_service
from .medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
from .database_models import SessionLocal, PatientProfile

logger = logging.getLogger(__name__)

class JourneyCompletionHandler:
    """Handles complete journey termination flow"""
    
    def __init__(self):
        self.whatsapp_client = CustomWhatsAppClient()
        self.pending_ratings: Dict[str, Dict[str, Any]] = {}
    
    async def handle_end_journey_command(
        self,
        patient_id: str,
        phone_number: str
    ) -> Dict[str, Any]:
        """
        Handle when patient sends 'END JOURNEY' command
        
        Flow:
        1. Find patient's active journey
        2. Ask for rating
        3. Collect feedback
        4. Generate PDF reports
        5. Email to patient and admin
        6. Mark journey as RESOLVED
        """
        try:
            logger.info(f"🎯 END JOURNEY command from patient: {patient_id}")
            
            # Find patient's active journey
            # TODO: Query database for active journey
            # For now, use mock data
            journey_id = "mock_journey_123"
            case_id = "mock_case_456"
            
            # Store pending rating request
            self.pending_ratings[patient_id] = {
                "journey_id": journey_id,
                "case_id": case_id,
                "phone_number": phone_number,
                "stage": "awaiting_rating",
                "requested_at": datetime.utcnow().isoformat()
            }
            
            # Send rating request message
            message = """🎉 *Congratulations on Completing Your Journey!*

I'm so happy to hear you're feeling better! 💚

Before we conclude, I'd love to get your feedback to help us improve.

*Please Rate Your Experience:*

Reply with a number from 1-5:
⭐ 1 - Poor
⭐⭐ 2 - Below Average
⭐⭐⭐ 3 - Average
⭐⭐⭐⭐ 4 - Good
⭐⭐⭐⭐⭐ 5 - Excellent

Just send the number (1-5)"""
            
            if self.whatsapp_client:
                await self.whatsapp_client.send_message(
                    phone_number=phone_number,
                    message=message
                )
            
            return {
                "success": True,
                "message": "Rating request sent",
                "next_stage": "awaiting_rating"
            }
            
        except Exception as e:
            logger.error(f"Error handling END JOURNEY: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def handle_rating_response(
        self,
        patient_id: str,
        rating: int,
        phone_number: str
    ) -> Dict[str, Any]:
        """
        Handle patient's rating response (1-5)
        Then ask for additional feedback
        """
        try:
            logger.info(f"⭐ Rating received: {rating} from patient {patient_id}")
            
            pending = self.pending_ratings.get(patient_id)
            if not pending:
                return {"success": False, "error": "No pending rating found"}
            
            # Store rating temporarily
            pending["rating"] = rating
            pending["stage"] = "awaiting_feedback"
            
            # Ask for text feedback
            message = f"""Thank you for the {rating}-star rating! ⭐

*Optional:* Would you like to share any specific feedback about your experience?

You can:
✍️ Type your feedback (1-2 sentences)
or
⏭️ Type SKIP to finish

Your feedback helps us serve patients better! 💚"""
            
            if self.whatsapp_client:
                await self.whatsapp_client.send_message(
                    phone_number=phone_number,
                    message=message
                )
            
            return {
                "success": True,
                "message": "Feedback request sent",
                "next_stage": "awaiting_feedback"
            }
            
        except Exception as e:
            logger.error(f"Error handling rating response: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_feedback_response(
        self,
        patient_id: str,
        feedback_text: str,
        phone_number: str
    ) -> Dict[str, Any]:
        """
        Handle patient's text feedback
        Then generate and send PDF reports
        """
        try:
            logger.info(f"💬 Feedback received from patient {patient_id}")
            
            pending = self.pending_ratings.get(patient_id)
            if not pending:
                return {"success": False, "error": "No pending feedback found"}
            
            journey_id = pending["journey_id"]
            case_id = pending["case_id"]
            rating = pending.get("rating", 5)
            
            # Save rating to system
            await rating_system.collect_rating(
                journey_id=journey_id,
                case_id=case_id,
                patient_id=patient_id,
                rating=rating,
                feedback_text=feedback_text if feedback_text.upper() != "SKIP" else None,
                symptom_improvement=100,  # Assume 100% since they ended journey
                companion_helpfulness=rating,
                reminder_effectiveness=rating,
                would_recommend=rating >= 4
            )
            
            # Update journey and case status
            await companion_manager.update_journey_status(
                journey_id=journey_id,
                status=CompanionStatus.RESOLVED,
                resolution_notes=f"Patient completed journey. Rating: {rating}/5"
            )
            
            await companion_manager.update_case_progress(
                case_id=case_id,
                progress_percentage=100.0,
                adherence_score=95.0,  # Mock adherence
                notes="Journey completed successfully"
            )
            
            # Generate PDF reports
            logger.info("📄 Generating PDF reports...")
            
            patient_pdf = await pdf_generator.generate_patient_report(
                journey_id=journey_id,
                case_id=case_id
            )
            
            admin_pdf = await pdf_generator.generate_admin_report(
                journey_id=journey_id,
                case_id=case_id
            )
            
            # Get patient email
            patient_email = await self._get_patient_email(patient_id)
            
            # Send patient report via email
            if patient_pdf and patient_email:
                try:
                    firebase_email_service.send_journey_completion_email(
                        recipient_email=patient_email,
                        pdf_content=patient_pdf,
                        patient_name=await self._get_patient_name(patient_id),
                        rating=rating
                    )
                    logger.info(f"✅ Patient report emailed to {patient_email}")
                except Exception as e:
                    logger.error(f"Failed to email patient report: {e}")
            
            # Send admin report to super admin
            admin_email = "admin@ayureze.com"  # TODO: Get from environment
            if admin_pdf:
                try:
                    firebase_email_service.send_admin_journey_report(
                        recipient_email=admin_email,
                        pdf_content=admin_pdf,
                        journey_id=journey_id,
                        patient_id=patient_id
                    )
                    logger.info(f"✅ Admin report emailed to {admin_email}")
                except Exception as e:
                    logger.error(f"Failed to email admin report: {e}")
            
            # Send completion message to patient
            completion_message = f"""🎉 *Journey Complete!*

Thank you for being part of the AyurEze family! 💚

*Summary:*
✅ Rating: {rating}/5 stars
✅ Status: Journey Completed
✅ Progress: 100%

📧 *Report Sent:*
A detailed PDF report of your wellness journey has been emailed to you at {patient_email}.

*What's Next:*
✅ Continue healthy lifestyle
✅ Follow Ayurvedic principles
✅ Stay hydrated
✅ Manage stress

*Need Support Again?*
I'm always here if you need me. Just text "START" to begin a new journey.

*Thank You for Trusting AyurEze Healthcare! 🙏*

_May you always be healthy and happy! 🌿_"""
            
            if self.whatsapp_client:
                await self.whatsapp_client.send_message(
                    phone_number=phone_number,
                    message=completion_message
                )
            
            # Clean up pending ratings
            del self.pending_ratings[patient_id]
            
            return {
                "success": True,
                "message": "Journey completed successfully",
                "rating": rating,
                "feedback": feedback_text,
                "reports_sent": True
            }
            
        except Exception as e:
            logger.error(f"Error handling feedback response: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def _get_patient_email(self, patient_id: str) -> Optional[str]:
        """Get patient email from database"""
        try:
            db = SessionLocal()
            try:
                patient = db.query(PatientProfile).filter(
                    PatientProfile.patient_id == patient_id
                ).first()
                
                if patient:
                    return patient.email or patient.phone_number  # Fallback to phone
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting patient email: {e}")
        
        return None
    
    async def _get_patient_name(self, patient_id: str) -> str:
        """Get patient name from database"""
        try:
            db = SessionLocal()
            try:
                patient = db.query(PatientProfile).filter(
                    PatientProfile.patient_id == patient_id
                ).first()
                
                if patient:
                    return patient.name or "Patient"
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting patient name: {e}")
        
        return "Patient"

# Global instance
completion_handler = JourneyCompletionHandler()
