"""
Email Authentication Handlers for WhatsApp
Handles email-based login flow instead of phone verification
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_regex, email.strip()))

async def handle_email_login(phone_number: str, email: str):
    """
    Handle email-based login request
    User sends their email address to login
    """
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.medicine_reminders.email_auth_service import get_email_auth_service
        
        whatsapp_client = CustomWhatsAppClient()
        auth_service = get_email_auth_service()
        
        # Validate email format
        if not is_valid_email(email):
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body="""❌ *Invalid Email Format*

Please provide a valid email address.

📧 *Example:*
`your.email@example.com`

_Send your registered email to login._"""
            )
            logger.warning(f"⚠️ Invalid email format from {phone_number}: {email}")
            return
        
        # Initiate email login
        result = await auth_service.initiate_email_login(phone_number, email)
        
        if result['success']:
            # Send OTP via WhatsApp
            otp_message = f"""✅ *Login Started!*

📧 Email: `{email}`
🔐 Your verification code is: `{result['otp']}`

⏱️ Valid for {result['expires_in_minutes']} minutes

*Reply with the 6-digit code to complete login.*

_This code is secure and encrypted._"""
            
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=otp_message
            )
            
            logger.info(f"✅ Email login OTP sent to {phone_number} for email {email}")
        
        elif result['error'] == 'cooldown':
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=f"""⏳ *Please Wait*

{result['message']}

_Try again in {result['cooldown_seconds']} seconds._"""
            )
        
        elif result['error'] == 'account_locked':
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=f"""🔒 *Account Locked*

{result['message']}

_Too many failed login attempts. Please try again later._"""
            )
        
        else:
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body="""❌ *Login Failed*

Unable to start login process. Please try again or contact support.

Type your email again to retry."""
            )
        
    except Exception as e:
        logger.error(f"❌ Error handling email login: {str(e)}")

async def handle_otp_verification_email(phone_number: str, otp: str):
    """
    Handle OTP verification for email-based login
    User sends 6-digit OTP received via WhatsApp
    """
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.medicine_reminders.email_auth_service import get_email_auth_service
        
        whatsapp_client = CustomWhatsAppClient()
        auth_service = get_email_auth_service()
        
        # Verify OTP
        result = await auth_service.verify_otp(phone_number, otp)
        
        if result['success']:
            # Successfully authenticated!
            welcome_message = f"""🎉 *Login Successful!*

✅ Authenticated as: `{result['email']}`

You now have full access to:
📁 *Your Medical Documents*
💊 *Medicine Schedules*
🤖 *Personalized AI Assistant*

*What would you like to do?*

📄 *Commands:*
• `VIEW DOCS` - See your documents
• `Upload photo/PDF` - Add new document
• Ask any health question

_Your data is secure and encrypted._"""
            
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=welcome_message
            )
            
            logger.info(f"✅ Email login successful for {phone_number} - {result['email']}")
        
        elif result.get('already_verified'):
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=f"""✅ *Already Logged In*

You're authenticated as: `{result['email']}`

Ready to help! Ask me any health question or type `VIEW DOCS` to see your documents."""
            )
        
        elif result['error'] == 'no_session':
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body="""❌ *No Active Login Session*

Please start login by sending your registered email address.

📧 *Example:*
`your.email@example.com`"""
            )
        
        elif result['error'] == 'otp_expired':
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body="""⏱️ *OTP Expired*

Your verification code has expired.

*To get a new code:*
Send your email address again to restart login."""
            )
        
        elif result['error'] == 'account_locked':
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=f"""🔒 *Account Locked*

{result['message']}

_Too many failed OTP attempts. Please try again later._"""
            )
        
        elif result['error'] == 'invalid_otp':
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=f"""❌ *Invalid OTP Code*

{result['message']}

*Attempts remaining:* {result.get('remaining_attempts', 0)}

_Please check your code and try again._"""
            )
        
        else:
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body="""❌ *Verification Failed*

Unable to verify OTP. Please try again or restart login by sending your email."""
            )
        
    except Exception as e:
        logger.error(f"❌ Error handling OTP verification: {str(e)}")

async def handle_logout(phone_number: str):
    """Handle logout request"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.medicine_reminders.email_auth_service import get_email_auth_service
        
        whatsapp_client = CustomWhatsAppClient()
        auth_service = get_email_auth_service()
        
        result = await auth_service.logout(phone_number)
        
        await whatsapp_client.send_text_message(
            phone_number=phone_number,
            message_body="""👋 *Logged Out Successfully*

Your session has been cleared.

To login again:
📧 Send your registered email address

_Thank you for using AyurEze Healthcare!_"""
        )
        
        logger.info(f"✅ User {phone_number} logged out")
        
    except Exception as e:
        logger.error(f"❌ Error handling logout: {str(e)}")

async def get_authenticated_patient_data(phone_number: str):
    """
    Get patient data for authenticated user using email from session
    Returns patient data from Firebase/Backend using the authenticated email
    """
    try:
        from app.medicine_reminders.email_auth_service import get_email_auth_service
        from app.firebase_patient_service import get_firebase_service
        from app.ayureze_backend_client import get_backend_client
        
        auth_service = get_email_auth_service()
        
        # Check if user is authenticated
        if not auth_service.is_authenticated(phone_number):
            return None, "Guest"
        
        # Get authenticated email
        email = auth_service.get_user_email(phone_number)
        if not email:
            return None, "Guest"
        
        # Try Firebase first
        try:
            firebase_service = get_firebase_service()
            patient_data = await firebase_service.get_patient_by_email(email)
            
            if patient_data:
                patient_name = patient_data.get('name') or patient_data.get('display_name', 'there')
                logger.info(f"✅ Using Firebase patient data for {email}: {patient_name}")
                return patient_data, patient_name
        except Exception as firebase_error:
            logger.warning(f"Firebase lookup failed for email {email}: {str(firebase_error)}")
        
        # If not found in Firebase, try Ayureze backend
        try:
            backend_client = await get_backend_client()
            patient_data = await backend_client.get_patient_by_email(email)
            
            if patient_data:
                patient_name = patient_data.get('name') or patient_data.get('patient_name', 'there')
                logger.info(f"✅ Using backend patient data for {email}: {patient_name}")
                return patient_data, patient_name
        except Exception as backend_error:
            logger.warning(f"Backend lookup failed for email {email}: {str(backend_error)}")
        
        # User is authenticated but no patient record found
        logger.warning(f"⚠️ Authenticated user {email} not found in patient database")
        return None, email.split('@')[0].title()  # Use part of email as name
        
    except Exception as e:
        logger.error(f"❌ Error getting authenticated patient data: {str(e)}")
        return None, "Guest"
