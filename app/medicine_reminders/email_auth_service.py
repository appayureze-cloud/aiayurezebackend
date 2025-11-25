"""
Email-Based Authentication Service for WhatsApp
Allows users to login via email instead of phone verification
"""

import os
import logging
import secrets
import string
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class EmailAuthService:
    """
    Email-based authentication service for WhatsApp users
    Stores user sessions and authentication state
    """
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.sessions = {}  # phone_number -> {email, verified, otp, otp_expires, attempts, locked_until}
        self.otp_cooldown = {}  # phone_number -> last_otp_time
        self.MAX_OTP_ATTEMPTS = 5
        self.OTP_COOLDOWN_SECONDS = 60
        self.OTP_EXPIRY_MINUTES = 10
        self.LOCKOUT_HOURS = 24
        
    def generate_otp(self, length: int = 6) -> str:
        """Generate a random OTP code"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    async def initiate_email_login(self, phone_number: str, email: str) -> Dict[str, Any]:
        """
        Initiate email-based login process
        Returns OTP code to be sent via WhatsApp
        """
        try:
            # Check if account is locked
            if phone_number in self.sessions:
                session = self.sessions[phone_number]
                if 'locked_until' in session and session['locked_until']:
                    if datetime.now() < session['locked_until']:
                        remaining = (session['locked_until'] - datetime.now()).seconds // 60
                        return {
                            'success': False,
                            'error': 'account_locked',
                            'message': f'Account locked for {remaining} minutes. Too many failed attempts.',
                            'locked_until': session['locked_until'].isoformat()
                        }
                    else:
                        # Unlock account
                        session['locked_until'] = None
                        session['attempts'] = 0
            
            # Check OTP cooldown
            if phone_number in self.otp_cooldown:
                last_otp_time = self.otp_cooldown[phone_number]
                cooldown_remaining = self.OTP_COOLDOWN_SECONDS - (datetime.now() - last_otp_time).seconds
                if cooldown_remaining > 0:
                    return {
                        'success': False,
                        'error': 'cooldown',
                        'message': f'Please wait {cooldown_remaining} seconds before requesting a new OTP.',
                        'cooldown_seconds': cooldown_remaining
                    }
            
            # Generate OTP
            otp = self.generate_otp()
            otp_expires = datetime.now() + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
            
            # Store session
            self.sessions[phone_number] = {
                'email': email.lower().strip(),
                'verified': False,
                'otp': otp,
                'otp_expires': otp_expires,
                'attempts': 0,
                'locked_until': None,
                'created_at': datetime.now()
            }
            
            # Set cooldown
            self.otp_cooldown[phone_number] = datetime.now()
            
            logger.info(f"✅ Email login initiated for {phone_number} with email {email}")
            # Security: Never log OTP in plaintext
            logger.info(f"🔐 OTP generated (6 digits, expires in {self.OTP_EXPIRY_MINUTES} minutes)")
            
            return {
                'success': True,
                'otp': otp,
                'expires_in_minutes': self.OTP_EXPIRY_MINUTES,
                'message': f'OTP sent! Please reply with the 6-digit code within {self.OTP_EXPIRY_MINUTES} minutes.'
            }
            
        except Exception as e:
            logger.error(f"❌ Error initiating email login: {str(e)}")
            return {
                'success': False,
                'error': 'server_error',
                'message': 'Failed to initiate login. Please try again.'
            }
    
    async def verify_otp(self, phone_number: str, otp: str) -> Dict[str, Any]:
        """
        Verify OTP code submitted by user
        Returns success status and email if verified
        """
        try:
            # Check if session exists
            if phone_number not in self.sessions:
                return {
                    'success': False,
                    'error': 'no_session',
                    'message': 'No active login session. Please start by providing your email address.'
                }
            
            session = self.sessions[phone_number]
            
            # Check if account is locked
            if session.get('locked_until') and datetime.now() < session['locked_until']:
                remaining = (session['locked_until'] - datetime.now()).seconds // 60
                return {
                    'success': False,
                    'error': 'account_locked',
                    'message': f'Account locked for {remaining} minutes. Too many failed attempts.'
                }
            
            # Check if already verified
            if session.get('verified'):
                return {
                    'success': True,
                    'already_verified': True,
                    'email': session['email'],
                    'message': 'You are already logged in!'
                }
            
            # Check if OTP expired
            if datetime.now() > session['otp_expires']:
                return {
                    'success': False,
                    'error': 'otp_expired',
                    'message': 'OTP code has expired. Please request a new one by sending your email again.'
                }
            
            # Verify OTP
            if otp.strip() == session['otp']:
                # Success!
                session['verified'] = True
                session['verified_at'] = datetime.now()
                session['attempts'] = 0
                
                logger.info(f"✅ Email login verified for {phone_number} with email {session['email']}")
                
                return {
                    'success': True,
                    'email': session['email'],
                    'message': 'Login successful! You now have access to your patient profile and documents.'
                }
            else:
                # Failed attempt
                session['attempts'] += 1
                remaining_attempts = self.MAX_OTP_ATTEMPTS - session['attempts']
                
                if remaining_attempts <= 0:
                    # Lock account
                    session['locked_until'] = datetime.now() + timedelta(hours=self.LOCKOUT_HOURS)
                    logger.warning(f"🔒 Account locked for {phone_number} - too many failed OTP attempts")
                    
                    return {
                        'success': False,
                        'error': 'account_locked',
                        'message': f'Account locked for {self.LOCKOUT_HOURS} hours due to too many failed attempts.'
                    }
                
                logger.warning(f"⚠️ Failed OTP attempt for {phone_number} - {remaining_attempts} attempts remaining")
                
                return {
                    'success': False,
                    'error': 'invalid_otp',
                    'message': f'Invalid OTP code. {remaining_attempts} attempts remaining.',
                    'remaining_attempts': remaining_attempts
                }
                
        except Exception as e:
            logger.error(f"❌ Error verifying OTP: {str(e)}")
            return {
                'success': False,
                'error': 'server_error',
                'message': 'Failed to verify OTP. Please try again.'
            }
    
    def is_authenticated(self, phone_number: str) -> bool:
        """Check if user is authenticated"""
        if phone_number not in self.sessions:
            return False
        session = self.sessions[phone_number]
        return session.get('verified', False)
    
    def get_user_email(self, phone_number: str) -> Optional[str]:
        """Get authenticated user's email"""
        if not self.is_authenticated(phone_number):
            return None
        return self.sessions[phone_number].get('email')
    
    def get_session_info(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get full session information"""
        if phone_number not in self.sessions:
            return None
        session = self.sessions[phone_number].copy()
        # Remove sensitive data
        if 'otp' in session:
            session['otp'] = '***REDACTED***'
        return session
    
    async def logout(self, phone_number: str) -> Dict[str, Any]:
        """Logout user and clear session"""
        if phone_number in self.sessions:
            del self.sessions[phone_number]
            logger.info(f"✅ User {phone_number} logged out")
            return {
                'success': True,
                'message': 'Logged out successfully.'
            }
        return {
            'success': False,
            'message': 'No active session found.'
        }

# Global instance
_email_auth_service = None

def get_email_auth_service() -> EmailAuthService:
    """Get or create email auth service instance"""
    global _email_auth_service
    if _email_auth_service is None:
        _email_auth_service = EmailAuthService()
    return _email_auth_service
