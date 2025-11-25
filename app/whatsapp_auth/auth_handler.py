"""
WhatsApp Authentication Handler
Manages Firebase Phone Auth integration for WhatsApp users
"""

import os
import logging
import random
from typing import Dict, Any, Optional
from firebase_admin import auth
from app.whatsapp_auth.session_store import session_store, AuthStage

logger = logging.getLogger(__name__)

class WhatsAppAuthHandler:
    """Handles WhatsApp authentication using Firebase Phone Auth"""
    
    def __init__(self):
        """Initialize auth handler"""
        self.otp_store = {}  # Temporary OTP storage (use Redis in production)
    
    async def initiate_verification(self, phone_number: str) -> Dict[str, Any]:
        """
        Initiate phone number verification
        
        Args:
            phone_number: WhatsApp phone number
            
        Returns:
            Dict with success status and message
        """
        try:
            # Get or create session
            session = session_store.get_or_create_session(phone_number)
            
            # Check if locked
            if session.get("is_locked"):
                return {
                    "success": False,
                    "message": "Account locked due to too many failed attempts. Please try again after 24 hours.",
                    "locked": True
                }
            
            # Check if already verified
            if session_store.is_session_verified(phone_number):
                return {
                    "success": True,
                    "message": "You're already verified! You can now upload documents.",
                    "already_verified": True
                }
            
            # Record OTP sent (with cooldown check)
            if not session_store.record_otp_sent(phone_number):
                return {
                    "success": False,
                    "message": "Please wait 60 seconds before requesting a new OTP.",
                    "cooldown": True
                }
            
            # Generate 6-digit OTP
            otp_code = self._generate_otp()
            
            # Store OTP temporarily (in production, use Redis with TTL)
            self.otp_store[phone_number] = otp_code
            
            logger.info(f"Generated OTP for {phone_number}: {otp_code}")
            
            return {
                "success": True,
                "otp_code": otp_code,  # In production, send via SMS
                "message": f"Verification code sent! Your OTP is: {otp_code}\n\nReply with this code to verify your account.",
                "expires_in_minutes": 5
            }
            
        except Exception as e:
            logger.error(f"Failed to initiate verification: {e}")
            return {
                "success": False,
                "message": "Failed to send verification code. Please try again."
            }
    
    async def verify_otp(self, phone_number: str, otp_code: str) -> Dict[str, Any]:
        """
        Verify OTP code
        
        Args:
            phone_number: WhatsApp phone number
            otp_code: OTP code from user
            
        Returns:
            Dict with success status and Firebase UID
        """
        try:
            session = session_store.get_session(phone_number)
            
            if not session:
                return {
                    "success": False,
                    "message": "Session not found. Please request a new verification code."
                }
            
            # Check if locked
            if session.get("is_locked"):
                return {
                    "success": False,
                    "message": "Account locked due to too many failed attempts. Please try again after 24 hours.",
                    "locked": True
                }
            
            # Get stored OTP
            stored_otp = self.otp_store.get(phone_number)
            
            if not stored_otp:
                return {
                    "success": False,
                    "message": "OTP expired or not found. Please request a new code."
                }
            
            # Verify OTP
            if otp_code.strip() != stored_otp:
                # Increment failed attempts
                attempt_data = session_store.increment_otp_attempts(phone_number)
                
                attempts_left = 5 - attempt_data["attempts"]
                
                if attempt_data["locked"]:
                    return {
                        "success": False,
                        "message": "❌ Too many failed attempts. Your account has been locked for 24 hours.",
                        "locked": True
                    }
                
                return {
                    "success": False,
                    "message": f"❌ Incorrect OTP. {attempts_left} attempts remaining.",
                    "attempts_left": attempts_left
                }
            
            # OTP is correct - create/get Firebase user
            firebase_user = await self._get_or_create_firebase_user(phone_number)
            
            if not firebase_user:
                return {
                    "success": False,
                    "message": "Failed to create user account. Please try again."
                }
            
            # Update session to verified
            session_store.update_session_stage(
                phone_number,
                AuthStage.VERIFIED,
                firebase_uid=firebase_user["uid"]
            )
            
            # Reset OTP attempts
            session_store.reset_otp_attempts(phone_number)
            
            # Clear OTP from store
            if phone_number in self.otp_store:
                del self.otp_store[phone_number]
            
            logger.info(f"✅ User verified: {firebase_user['uid']}")
            
            return {
                "success": True,
                "message": "✅ Verification successful! You can now upload your medical documents.",
                "firebase_uid": firebase_user["uid"],
                "user_info": firebase_user
            }
            
        except Exception as e:
            logger.error(f"Failed to verify OTP: {e}")
            return {
                "success": False,
                "message": "Verification failed. Please try again."
            }
    
    async def _get_or_create_firebase_user(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Get existing Firebase user or create new one
        
        Args:
            phone_number: Phone number
            
        Returns:
            User data dict or None
        """
        try:
            # Normalize phone number to E.164 format
            normalized_phone = phone_number
            if not phone_number.startswith("+"):
                normalized_phone = f"+{phone_number}"
            
            try:
                # Try to get existing user
                user = auth.get_user_by_phone_number(normalized_phone)
                logger.info(f"Found existing Firebase user: {user.uid}")
                
                return {
                    "uid": user.uid,
                    "phone_number": user.phone_number,
                    "email": user.email,
                    "display_name": user.display_name,
                    "created": False
                }
                
            except auth.UserNotFoundError:
                # Create new user
                user = auth.create_user(
                    phone_number=normalized_phone,
                    display_name=f"Patient {normalized_phone[-4:]}"  # Use last 4 digits
                )
                
                # Set custom claims for patient role
                auth.set_custom_user_claims(user.uid, {
                    "role": "patient",
                    "verified_via": "whatsapp"
                })
                
                logger.info(f"Created new Firebase user: {user.uid}")
                
                return {
                    "uid": user.uid,
                    "phone_number": user.phone_number,
                    "email": user.email,
                    "display_name": user.display_name,
                    "created": True
                }
                
        except Exception as e:
            logger.error(f"Failed to get/create Firebase user: {e}")
            return None
    
    def _generate_otp(self, length: int = 6) -> str:
        """Generate random OTP code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])
    
    def get_user_verification_status(self, phone_number: str) -> Dict[str, Any]:
        """Get user's current verification status"""
        session = session_store.get_session(phone_number)
        
        if not session:
            return {
                "verified": False,
                "stage": "unverified",
                "message": "Not verified. Reply with VERIFY to start."
            }
        
        is_verified = session_store.is_session_verified(phone_number)
        
        return {
            "verified": is_verified,
            "stage": session.get("auth_stage"),
            "firebase_uid": session.get("firebase_uid"),
            "is_locked": session.get("is_locked"),
            "message": "Verified ✅" if is_verified else "Not verified. Reply with VERIFY to start."
        }

# Global instance
auth_handler = WhatsAppAuthHandler()
