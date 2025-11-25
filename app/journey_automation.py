"""
Journey Automation Service
Automatically creates cases and manages complete patient journey from prescription to resolution
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .companion_system import companion_manager, CompanionStatus, CaseStatus
from .database_models import SessionLocal, PrescriptionRecord, PrescribedMedicine
from .medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient

logger = logging.getLogger(__name__)

class JourneyAutomation:
    """Automates complete patient journey from prescription to resolution"""
    
    def __init__(self):
        self.whatsapp_client = CustomWhatsAppClient()
    
    async def auto_create_case_from_prescription(
        self,
        prescription_id: str,
        patient_id: str,
        doctor_id: str,
        diagnosis: str
    ) -> Optional[Dict[str, Any]]:
        """
        🚀 AUTO-TRIGGER: Create health case automatically after prescription is saved
        
        This function is called immediately after prescription PDF is generated
        and creates a complete AI companion journey for the patient.
        """
        try:
            logger.info(f"🤖 AUTO-CREATING case for prescription: {prescription_id}")
            
            # Step 1: Check if patient already has an active journey
            journey_id = await self._get_or_create_journey(
                user_id=patient_id,
                health_concern=diagnosis
            )
            
            if not journey_id:
                logger.error("Failed to create/get journey")
                return None
            
            # Step 2: Get prescription details for treatment planning
            db = SessionLocal()
            try:
                prescription = db.query(PrescriptionRecord).filter(
                    PrescriptionRecord.prescription_id == prescription_id
                ).first()
                
                if not prescription:
                    logger.error(f"Prescription not found: {prescription_id}")
                    return None
                
                # Get medicines for duration calculation
                medicines = db.query(PrescribedMedicine).filter(
                    PrescribedMedicine.prescription_id == prescription_id
                ).all()
                
                # Calculate treatment duration (longest medicine duration)
                treatment_duration_days = 30  # Default
                if medicines:
                    max_duration = 0
                    for med in medicines:
                        # Extract duration from various formats
                        duration_str = med.duration or "30 days"
                        try:
                            # Parse "30 days", "2 weeks", "1 month" etc.
                            if "day" in duration_str.lower():
                                days = int(''.join(filter(str.isdigit, duration_str)))
                                max_duration = max(max_duration, days)
                            elif "week" in duration_str.lower():
                                weeks = int(''.join(filter(str.isdigit, duration_str)))
                                max_duration = max(max_duration, weeks * 7)
                            elif "month" in duration_str.lower():
                                months = int(''.join(filter(str.isdigit, duration_str)))
                                max_duration = max(max_duration, months * 30)
                        except:
                            pass
                    
                    if max_duration > 0:
                        treatment_duration_days = max_duration
                
            finally:
                db.close()
            
            # Step 3: Create health case
            case_id = await companion_manager.create_case(
                journey_id=journey_id,
                user_id=patient_id,
                doctor_id=doctor_id,
                diagnosis=diagnosis,
                prescription_id=prescription_id,
                treatment_duration_days=treatment_duration_days,
                follow_up_schedule=[
                    f"Day {int(treatment_duration_days * 0.25)}",  # 25% mark
                    f"Day {int(treatment_duration_days * 0.50)}",  # 50% mark
                    f"Day {int(treatment_duration_days * 0.75)}",  # 75% mark
                    f"Day {treatment_duration_days}"               # Completion
                ]
            )
            
            if not case_id:
                logger.error("Failed to create case")
                return None
            
            logger.info(f"✅ Case created successfully: {case_id}")
            
            # Step 4: Send WhatsApp notification to patient
            await self._send_case_creation_notification(
                patient_id=patient_id,
                case_id=case_id,
                diagnosis=diagnosis,
                treatment_duration=treatment_duration_days
            )
            
            return {
                "success": True,
                "journey_id": journey_id,
                "case_id": case_id,
                "treatment_duration_days": treatment_duration_days,
                "message": "AI Companion journey started successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in auto case creation: {e}", exc_info=True)
            return None
    
    async def _get_or_create_journey(
        self,
        user_id: str,
        health_concern: str
    ) -> Optional[str]:
        """Get existing active journey or create new one"""
        try:
            # Check for existing active journey
            # (In production, query database for user's active journeys)
            
            # For now, create new journey
            journey_id = await companion_manager.start_companion_journey(
                user_id=user_id,
                health_concern=health_concern,
                language="en"
            )
            
            return journey_id
            
        except Exception as e:
            logger.error(f"Error getting/creating journey: {e}")
            return None
    
    async def _send_case_creation_notification(
        self,
        patient_id: str,
        case_id: str,
        diagnosis: str,
        treatment_duration: int
    ):
        """Send WhatsApp notification about case creation"""
        try:
            # Get patient phone number from database
            db = SessionLocal()
            try:
                from .database_models import PatientProfile
                patient = db.query(PatientProfile).filter(
                    PatientProfile.patient_id == patient_id
                ).first()
                
                if not patient or not patient.phone_number:
                    logger.warning(f"No phone number found for patient {patient_id}")
                    return
                
                phone_number = patient.phone_number
            finally:
                db.close()
            
            # Create welcome message
            message = f"""🌿 *Welcome to Your AI Wellness Journey!*

🙏 Namaste! I'm Astra, your AI Ayurvedic Wellness Companion.

✅ *Your Health Case Created Successfully*

📋 *Case ID:* {case_id[:8]}...
🏥 *Diagnosis:* {diagnosis}
⏱️ *Treatment Duration:* {treatment_duration} days
📅 *Follow-ups:* Day {int(treatment_duration * 0.25)}, Day {int(treatment_duration * 0.50)}, Day {treatment_duration}

*I'll Be With You Throughout Your Journey:*
✅ Daily medicine reminders
✅ Diet and lifestyle guidance
✅ Progress tracking
✅ Symptom assessment
✅ 24/7 support

*Quick Commands:*
📊 Type *PROGRESS* - View your progress
📋 Type *HELP* - Get assistance
⏸️ Type *END JOURNEY* - Complete journey (when healed)

Let's start your healing journey together! 💚

_Powered by AyurEze Healthcare 🌿_"""
            
            # Send WhatsApp message
            if self.whatsapp_client:
                await self.whatsapp_client.send_message(
                    phone_number=phone_number,
                    message=message
                )
                logger.info(f"✅ Case creation notification sent to {phone_number}")
            
        except Exception as e:
            logger.error(f"Error sending case creation notification: {e}")

# Global instance
journey_automation = JourneyAutomation()
