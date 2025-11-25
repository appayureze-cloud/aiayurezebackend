"""
WhatsApp Authentication Session Store
Manages authentication states and OTP verification for WhatsApp users
"""

import os
import logging
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from app.database_models import SessionLocal
from sqlalchemy import Column, String, Integer, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

Base = declarative_base()

class AuthStage(str, Enum):
    """Authentication stages for WhatsApp users"""
    UNVERIFIED = "unverified"
    OTP_SENT = "otp_sent"
    VERIFIED = "verified"
    AWAITING_UPLOAD = "awaiting_upload"
    UPLOAD_PROCESSING = "upload_processing"
    READY = "ready"

class WhatsAppSession(Base):
    """Database model for WhatsApp authentication sessions"""
    __tablename__ = "whatsapp_auth_sessions"
    
    phone_hash = Column(String, primary_key=True)
    phone_number = Column(String, nullable=False, unique=True)
    auth_stage = Column(String, default=AuthStage.UNVERIFIED, nullable=False)
    firebase_uid = Column(String, nullable=True)
    otp_attempts = Column(Integer, default=0)
    last_otp_sent_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    session_expires_at = Column(DateTime, nullable=False)
    is_locked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WhatsAppSessionStore:
    """Manages WhatsApp authentication sessions with TTL and security"""
    
    MAX_OTP_ATTEMPTS = 5
    OTP_RESEND_COOLDOWN_SECONDS = 60
    SESSION_TTL_HOURS = 24
    
    def __init__(self):
        """Initialize session store"""
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create table if it doesn't exist"""
        try:
            from app.database_models import engine
            Base.metadata.create_all(bind=engine)
            logger.info("WhatsApp session store table ready")
        except Exception as e:
            logger.error(f"Failed to create session table: {e}")
    
    def _normalize_phone(self, phone_number: str) -> str:
        """Normalize phone number (remove +, spaces, etc.)"""
        return phone_number.replace("+", "").replace(" ", "").replace("-", "").strip()
    
    def _hash_phone(self, phone_number: str) -> str:
        """Generate SHA-256 hash of phone number for privacy"""
        normalized = self._normalize_phone(phone_number)
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]
    
    def get_or_create_session(self, phone_number: str) -> Dict[str, Any]:
        """
        Get existing session or create new one
        
        Args:
            phone_number: WhatsApp phone number
            
        Returns:
            Session data dict
        """
        db = SessionLocal()
        try:
            phone_hash = self._hash_phone(phone_number)
            normalized_phone = self._normalize_phone(phone_number)
            
            session = db.query(WhatsAppSession).filter(
                WhatsAppSession.phone_hash == phone_hash
            ).first()
            
            if session:
                # Check if session expired
                if datetime.utcnow() > session.session_expires_at:
                    logger.info(f"Session expired for {phone_hash}, resetting")
                    session.auth_stage = AuthStage.UNVERIFIED
                    session.otp_attempts = 0
                    session.is_locked = False
                    session.session_expires_at = datetime.utcnow() + timedelta(hours=self.SESSION_TTL_HOURS)
                    db.commit()
            else:
                # Create new session
                session = WhatsAppSession(
                    phone_hash=phone_hash,
                    phone_number=normalized_phone,
                    auth_stage=AuthStage.UNVERIFIED,
                    session_expires_at=datetime.utcnow() + timedelta(hours=self.SESSION_TTL_HOURS)
                )
                db.add(session)
                db.commit()
                logger.info(f"Created new session for {phone_hash}")
            
            return self._session_to_dict(session)
            
        finally:
            db.close()
    
    def update_session_stage(
        self, 
        phone_number: str, 
        new_stage: AuthStage,
        firebase_uid: Optional[str] = None
    ) -> bool:
        """
        Update session authentication stage
        
        Args:
            phone_number: WhatsApp phone number
            new_stage: New authentication stage
            firebase_uid: Firebase UID (if verified)
            
        Returns:
            Success boolean
        """
        db = SessionLocal()
        try:
            phone_hash = self._hash_phone(phone_number)
            
            session = db.query(WhatsAppSession).filter(
                WhatsAppSession.phone_hash == phone_hash
            ).first()
            
            if not session:
                logger.warning(f"Session not found for {phone_hash}")
                return False
            
            session.auth_stage = new_stage
            
            if firebase_uid:
                session.firebase_uid = firebase_uid
            
            if new_stage == AuthStage.VERIFIED:
                session.verified_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"Updated session {phone_hash} to stage: {new_stage}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def record_otp_sent(self, phone_number: str) -> bool:
        """
        Record that OTP was sent
        
        Args:
            phone_number: WhatsApp phone number
            
        Returns:
            Success boolean
        """
        db = SessionLocal()
        try:
            phone_hash = self._hash_phone(phone_number)
            
            session = db.query(WhatsAppSession).filter(
                WhatsAppSession.phone_hash == phone_hash
            ).first()
            
            if not session:
                return False
            
            # Check if OTP was sent recently (cooldown)
            if session.last_otp_sent_at:
                time_since_last = (datetime.utcnow() - session.last_otp_sent_at).total_seconds()
                if time_since_last < self.OTP_RESEND_COOLDOWN_SECONDS:
                    logger.warning(f"OTP cooldown active for {phone_hash}")
                    return False
            
            session.last_otp_sent_at = datetime.utcnow()
            session.auth_stage = AuthStage.OTP_SENT
            db.commit()
            
            logger.info(f"Recorded OTP sent for {phone_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record OTP: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def increment_otp_attempts(self, phone_number: str) -> Dict[str, Any]:
        """
        Increment OTP verification attempts
        
        Args:
            phone_number: WhatsApp phone number
            
        Returns:
            Dict with attempt count and locked status
        """
        db = SessionLocal()
        try:
            phone_hash = self._hash_phone(phone_number)
            
            session = db.query(WhatsAppSession).filter(
                WhatsAppSession.phone_hash == phone_hash
            ).first()
            
            if not session:
                return {"attempts": 0, "locked": False}
            
            session.otp_attempts += 1
            
            # Lock account after max attempts
            if session.otp_attempts >= self.MAX_OTP_ATTEMPTS:
                session.is_locked = True
                session.auth_stage = AuthStage.UNVERIFIED
                logger.warning(f"Session locked for {phone_hash} after {self.MAX_OTP_ATTEMPTS} attempts")
            
            db.commit()
            
            return {
                "attempts": session.otp_attempts,
                "locked": session.is_locked
            }
            
        except Exception as e:
            logger.error(f"Failed to increment attempts: {e}")
            db.rollback()
            return {"attempts": 0, "locked": False}
        finally:
            db.close()
    
    def reset_otp_attempts(self, phone_number: str) -> bool:
        """Reset OTP attempts after successful verification"""
        db = SessionLocal()
        try:
            phone_hash = self._hash_phone(phone_number)
            
            session = db.query(WhatsAppSession).filter(
                WhatsAppSession.phone_hash == phone_hash
            ).first()
            
            if not session:
                return False
            
            session.otp_attempts = 0
            session.is_locked = False
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset attempts: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def is_session_verified(self, phone_number: str) -> bool:
        """Check if session is verified and not expired"""
        db = SessionLocal()
        try:
            phone_hash = self._hash_phone(phone_number)
            
            session = db.query(WhatsAppSession).filter(
                WhatsAppSession.phone_hash == phone_hash
            ).first()
            
            if not session:
                return False
            
            return (
                session.auth_stage == AuthStage.VERIFIED and
                datetime.utcnow() < session.session_expires_at and
                not session.is_locked
            )
            
        finally:
            db.close()
    
    def get_session(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get current session data"""
        db = SessionLocal()
        try:
            phone_hash = self._hash_phone(phone_number)
            
            session = db.query(WhatsAppSession).filter(
                WhatsAppSession.phone_hash == phone_hash
            ).first()
            
            if not session:
                return None
            
            return self._session_to_dict(session)
            
        finally:
            db.close()
    
    def _session_to_dict(self, session: WhatsAppSession) -> Dict[str, Any]:
        """Convert session object to dict"""
        return {
            "phone_hash": session.phone_hash,
            "phone_number": session.phone_number,
            "auth_stage": session.auth_stage,
            "firebase_uid": session.firebase_uid,
            "otp_attempts": session.otp_attempts,
            "is_locked": session.is_locked,
            "verified_at": session.verified_at.isoformat() if session.verified_at else None,
            "session_expires_at": session.session_expires_at.isoformat(),
            "created_at": session.created_at.isoformat()
        }

# Global instance
session_store = WhatsAppSessionStore()
