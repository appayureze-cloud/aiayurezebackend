"""
Custom WhatsApp API Webhook Handler
Receives incoming messages from your custom WhatsApp server
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/custom-whatsapp")
async def handle_custom_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle incoming WhatsApp messages from custom API
    
    This webhook receives messages when patients reply to:
    - Medicine reminders (TAKEN, SKIP, LATER)
    - AI agent queries
    - General messages
    """
    try:
        webhook_data = await request.json()
        logger.info(f"📥 Received custom WhatsApp webhook: {webhook_data}")
        
        # Process the webhook in background to respond quickly
        background_tasks.add_task(process_incoming_message, webhook_data)
        
        return {
            "success": True,
            "message": "Webhook received"
        }
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_incoming_message(webhook_data: Dict[str, Any]):
    """
    Process incoming WhatsApp message based on type and content
    
    Webhook format from whatsapp.ayureze.in:
    {
        "contact": {
            "phone_number": "...",
            "first_name": "...",
            ...
        },
        "message": {
            "is_new_message": true,
            "body": "message text",
            "media": {...},
            "interactive": {  # Button click
                "type": "button_reply",
                "button_reply": {
                    "id": "button_id",
                    "title": "Button Title"
                }
            }
        }
    }
    """
    try:
        # Extract message details from ayureze webhook format
        contact = webhook_data.get("contact", {})
        message = webhook_data.get("message", {})
        
        phone_number = contact.get("phone_number")
        message_body = message.get("body", "")
        is_new_message = message.get("is_new_message", False)
        timestamp = datetime.now().isoformat()
        
        # Check for interactive button click
        interactive = message.get("interactive")
        if interactive and interactive.get("type") == "button_reply":
            button_reply = interactive.get("button_reply", {})
            button_id = button_reply.get("id")
            
            if button_id:
                logger.info(f"🔘 Button clicked: {button_id} from {phone_number}")
                await handle_button_click(phone_number, button_id, contact.get("first_name", "there"))
                return
        
        # Check for interactive list selection
        if interactive and interactive.get("type") == "list_reply":
            list_reply = interactive.get("list_reply", {})
            row_id = list_reply.get("id")
            
            if row_id:
                logger.info(f"📋 List item selected: {row_id} from {phone_number}")
                await handle_list_selection(phone_number, row_id)
                return
        
        # Only process new messages with text body
        if not is_new_message or not message_body:
            logger.info(f"Skipping webhook - is_new: {is_new_message}, has_body: {bool(message_body)}")
            return
        
        if not phone_number:
            logger.warning("Missing phone number in webhook")
            return
        
        message_lower = message_body.lower().strip()
        
        logger.info(f"📨 Message from {phone_number}: {message_body}")
        
        # Check for media/document upload
        media_data = message.get("media")
        if media_data:
            await handle_media_upload(phone_number, media_data, message_body)
            return
        
        # PRIORITY 1: Handle greetings first (automatic welcome message)
        greeting_keywords = ['hi', 'hello', 'hey', 'namaste', 'hii', 'hlo', 'start', 'help']
        if any(keyword == message_lower or message_lower.startswith(keyword + ' ') for keyword in greeting_keywords):
            await handle_welcome_message(phone_number, contact.get("first_name", "there"))
            return
        
        # PRIORITY 2: Handle WhatsApp email-based authentication
        # Check if message is an email address (for login)
        from app.medicine_reminders.email_auth_handlers import is_valid_email, handle_email_login, handle_otp_verification_email, handle_logout
        
        if is_valid_email(message_body):
            await handle_email_login(phone_number, message_body)
            return
        
        # Check if message is an OTP code (6 digits)
        if message_body.strip().isdigit() and len(message_body.strip()) == 6:
            await handle_otp_verification_email(phone_number, message_body.strip())
            return
        
        # Handle logout command
        if message_lower in ['logout', 'signout', 'sign out', 'log out']:
            await handle_logout(phone_number)
            return
        
        # Document management commands
        if message_lower in ['view docs', 'my docs', 'documents', 'view documents', 'list docs']:
            await handle_view_documents(phone_number)
            return
        
        if message_lower.startswith('get doc'):
            # Extract document number
            parts = message_body.strip().split()
            if len(parts) >= 3 and parts[2].isdigit():
                doc_num = int(parts[2])
                await handle_get_document(phone_number, doc_num)
            else:
                await handle_unknown_message(phone_number)
            return
        
        # Order tracking commands
        if message_lower in ['track order', 'track my order', 'order status', 'where is my order', 'track']:
            await handle_track_order_command(phone_number, contact.get("first_name", "there"))
            return
        
        # PRIORITY 3: Handle medicine reminder responses
        if message_lower in ['taken', '✅ taken', 'yes', 'done']:
            await handle_medicine_response(phone_number, 'taken', timestamp)
            
        elif message_lower in ['skip', '❌ skip', 'skipped', 'no']:
            await handle_medicine_response(phone_number, 'skipped', timestamp)
            
        elif message_lower in ['later', '⏰ later', 'remind later', 'snooze']:
            await handle_medicine_response(phone_number, 'later', timestamp)
            
        elif message_lower in ['stop', 'cancel', 'unsubscribe']:
            await handle_stop_request(phone_number)
            
        # PRIORITY 4: Handle AI agent queries
        elif len(message_body) > 10:  # Likely a question/query
            await handle_ai_query(phone_number, message_body)
            
        else:
            # Unknown message type - send helpful response
            await handle_unknown_message(phone_number)
        
    except Exception as e:
        logger.error(f"Error processing incoming message: {str(e)}")

async def handle_welcome_message(phone_number: str, customer_name: str):
    """Send automatic welcome message when user says hi with email login option"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.medicine_reminders.email_auth_service import get_email_auth_service
        
        whatsapp_client = CustomWhatsAppClient()
        auth_service = get_email_auth_service()
        
        # Check if user is already logged in
        is_logged_in = auth_service.is_authenticated(phone_number)
        user_email = auth_service.get_user_email(phone_number) if is_logged_in else None
        
        if is_logged_in and user_email:
            welcome_message = f"""🙏 *Namaste, {customer_name}!*

Welcome back to *AyurEze Healthcare*! 🌿

✅ Logged in as: `{user_email}`

I'm *Astra*, your personalized AI health assistant. I can help you with:

💊 *Medicine Reminders* - Get timely notifications
🤖 *Health Questions* - Ask me anything about Ayurveda
📁 *Medical Documents* - Upload & access your records
📦 *Order Updates* - Track your medicine orders

*Quick Commands:*
• `VIEW DOCS` - See your uploaded documents
• `Upload photo/PDF` - Add medical records
• `LOGOUT` - Sign out
• Ask any health question!

_Your data is secure and encrypted._ 🔐"""
        else:
            welcome_message = f"""🙏 *Namaste, {customer_name}!*

Welcome to *AyurEze Healthcare* - Your Ayurvedic Wellness Partner! 🌿

I'm *Astra*, your AI health assistant. I'm here to help you with:

💊 *Medicine Reminders* - Get timely notifications
🤖 *Health Questions* - Ask anything about Ayurveda
📁 *Secure Documents* - Upload & access medical records
📦 *Order Updates* - Track your medicine orders

*🔐 Login to Access Your Profile:*
Send your registered email address to login and access personalized features!

📧 *Example:*
`your.email@example.com`

Or ask me any health question! 🌿"""
        
        await whatsapp_client.send_text_message(
            phone_number=phone_number,
            message_body=welcome_message
        )
        
        logger.info(f"👋 Welcome message sent to {phone_number} (Logged in: {is_logged_in})")
        
    except Exception as e:
        logger.error(f"Error sending welcome message: {str(e)}")

async def handle_track_order_command(phone_number: str, customer_name: str):
    """Handle order tracking command"""
    try:
        from app.medicine_reminders.order_tracking_whatsapp import handle_track_order_command as track_order
        await track_order(phone_number, customer_name)
    except ImportError:
        # Order tracking module not yet deployed
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        whatsapp_client = CustomWhatsAppClient()
        await whatsapp_client.send_text_message(
            phone_number=phone_number,
            message_body="📦 Order tracking feature is being deployed. Please try again in a few minutes!"
        )
        logger.warning("Order tracking module not found - feature not yet deployed")

async def handle_unknown_message(phone_number: str):
    """Send helpful response for unknown messages"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        
        whatsapp_client = CustomWhatsAppClient()
        
        help_message = """🌿 *AyurEze Healthcare*

I didn't quite understand that. Here's what I can help with:

🔐 *Email-Based Login:*
• Send your email address (e.g., `user@example.com`)
• Enter the 6-digit OTP to verify
• `LOGOUT` - Sign out from your account

📁 *Documents (After Login):*
• `VIEW DOCS` - See your uploaded documents
• Send photos/PDFs - Upload medical records
• `GET DOC [number]` - Download a document

📦 *Order Tracking:*
• `TRACK ORDER` - Get your latest order status
• `WHERE IS MY ORDER` - Check delivery status

💊 *Medicine Reminders:*
• `TAKEN` - Mark medicine as taken
• `SKIP` - Mark as skipped
• `LATER` - Remind me later

🤖 *Health Questions:*
Ask me anything about Ayurveda!

🆘 *More Commands:*
Type "HI" for welcome message

_Login to access personalized features!_ 🌿"""
        
        await whatsapp_client.send_text_message(
            phone_number=phone_number,
            message_body=help_message
        )
        
        logger.info(f"❓ Help message sent to {phone_number}")
        
    except Exception as e:
        logger.error(f"Error sending help message: {str(e)}")

async def handle_medicine_response(phone_number: str, response: str, timestamp: str):
    """Handle patient response to medicine reminder"""
    try:
        from app.medicine_reminders.reminder_engine import ReminderEngine
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        
        reminder_engine = ReminderEngine()
        whatsapp_client = CustomWhatsAppClient()
        
        # Update adherence tracking
        success = reminder_engine.handle_patient_response(
            patient_phone=phone_number,
            response=response,
            message_timestamp=timestamp
        )
        
        if success:
            # Send confirmation
            confirmation_messages = {
                'taken': "✅ Great! Medicine recorded as taken. Keep up the good work! 🌿",
                'skipped': "⚠️ Noted. Please don't miss your next dose for better health outcomes.",
                'later': "⏰ Okay, I'll remind you in 30 minutes. Don't forget!"
            }
            
            confirmation = confirmation_messages.get(response, "Message received")
            
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=confirmation
            )
            
            logger.info(f"✅ Medicine response '{response}' processed for {phone_number}")
        else:
            logger.warning(f"Failed to process medicine response for {phone_number}")
            
    except Exception as e:
        logger.error(f"Error handling medicine response: {str(e)}")

async def handle_ai_query(phone_number: str, query: str):
    """Handle patient query using AI agent with authenticated patient data"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.medicine_reminders.email_auth_handlers import get_authenticated_patient_data
        from app.ai_content_filter import get_content_filter
        import main_enhanced
        
        whatsapp_client = CustomWhatsAppClient()
        content_filter = get_content_filter()
        
        # Validate user query first
        is_valid_query, reason = content_filter.validate_query(query)
        if not is_valid_query:
            logger.warning(f"⚠️ Blocked inappropriate query from {phone_number}: {reason}")
            ai_response = """⚠️ *Content Guidelines*

Please ask questions related to Ayurvedic health and wellness.

I can help with:
🌿 Ayurvedic principles and doshas
💊 Natural remedies and herbs
🍃 Health, nutrition, and lifestyle
🧘 Wellness practices and balance

_Please keep questions appropriate and health-related._ 🙏"""
            
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=ai_response
            )
            return
        
        # Get authenticated patient data using email from session
        patient_data, patient_name = await get_authenticated_patient_data(phone_number)
        
        if patient_data:
            logger.info(f"✅ Using authenticated patient data: {patient_name}")
        else:
            # User not authenticated or no patient data found
            logger.info(f"⚠️ Using guest mode for {phone_number} - patient name: {patient_name}")
        
        # Get AI response using the global model inference
        if main_enhanced.model_inference and hasattr(main_enhanced.model_inference, 'generate_response'):
            try:
                raw_ai_response = await main_enhanced.model_inference.generate_response(
                    prompt=query,
                    language="en",
                    max_length=512,
                    temperature=0.7
                )
                
                # Filter AI response for inappropriate content
                ai_response, was_filtered = content_filter.filter_response(raw_ai_response, query)
                
                if was_filtered:
                    logger.warning(f"⚠️ AI response filtered for {phone_number}")
                
            except Exception as ai_error:
                logger.error(f"AI generation error: {str(ai_error)}")
                ai_response = "Thank you for your message! Our AI assistant is currently loading. Please try again in a moment. 🌿"
        else:
            ai_response = "Thank you for your message! Our AI assistant is currently loading. Please try again in a moment. 🌿"
        
        # Send AI response via WhatsApp
        await whatsapp_client.send_ai_response(
            patient_phone=phone_number,
            patient_name=patient_name,
            ai_message=ai_response
        )
        
        logger.info(f"🤖 AI query handled for {phone_number} (patient: {patient_name})")
        
    except Exception as e:
        logger.error(f"Error handling AI query: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

async def handle_stop_request(phone_number: str):
    """Handle patient request to stop reminders"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.database_models import PatientProfile, MedicineSchedule, SessionLocal
        
        whatsapp_client = CustomWhatsAppClient()
        db = SessionLocal()
        
        try:
            # Find patient
            patient = db.query(PatientProfile).filter(
                PatientProfile.phone.like(f"%{phone_number.replace('+', '').replace('91', '')}%")
            ).first()
            
            if patient:
                # Disable all active schedules
                active_schedules = db.query(MedicineSchedule).filter(
                    MedicineSchedule.patient_id == patient.patient_id,
                    MedicineSchedule.is_active == True
                ).all()
                
                for schedule in active_schedules:
                    schedule.reminders_enabled = False
                
                db.commit()
                
                # Send confirmation
                message = f"""🛑 *Reminders Paused*

Hello {patient.name},

Your medicine reminders have been paused as requested.

To resume reminders, please contact your doctor or reply with "START".

_AyurEze Healthcare Team_ 🌿"""
                
                await whatsapp_client.send_text_message(
                    phone_number=phone_number,
                    message_body=message
                )
                
                logger.info(f"🛑 Reminders stopped for {phone_number}")
            else:
                logger.warning(f"Patient not found for stop request: {phone_number}")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error handling stop request: {str(e)}")

async def handle_verify_request(phone_number: str):
    """Handle user request to verify their account"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.whatsapp_auth import auth_handler
        
        whatsapp_client = CustomWhatsAppClient()
        
        # Initiate verification
        result = await auth_handler.initiate_verification(phone_number)
        
        # Send response
        await whatsapp_client.send_text_message(
            phone_number=phone_number,
            message_body=result["message"]
        )
        
        logger.info(f"🔐 Verification initiated for {phone_number}")
        
    except Exception as e:
        logger.error(f"Error handling verify request: {str(e)}")

async def handle_otp_verification(phone_number: str, otp_code: str):
    """Handle OTP verification"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.whatsapp_auth import auth_handler
        
        whatsapp_client = CustomWhatsAppClient()
        
        # Verify OTP
        result = await auth_handler.verify_otp(phone_number, otp_code)
        
        # Send response
        await whatsapp_client.send_text_message(
            phone_number=phone_number,
            message_body=result["message"]
        )
        
        logger.info(f"🔐 OTP verification for {phone_number}: {result['success']}")
        
    except Exception as e:
        logger.error(f"Error handling OTP verification: {str(e)}")

async def handle_media_upload(phone_number: str, media_data: Dict[str, Any], caption: str):
    """Handle document/media upload"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.whatsapp_auth import document_handler
        
        whatsapp_client = CustomWhatsAppClient()
        
        # Extract media details
        media_url = media_data.get("url")
        media_type = media_data.get("mime_type")
        filename = media_data.get("filename")
        
        if not media_url:
            logger.warning("Media URL not found in webhook data")
            return
        
        # Handle upload
        result = await document_handler.handle_document_upload(
            phone_number=phone_number,
            media_url=media_url,
            media_type=media_type,
            filename=filename,
            caption=caption
        )
        
        # Send response
        await whatsapp_client.send_text_message(
            phone_number=phone_number,
            message_body=result["message"]
        )
        
        logger.info(f"📤 Document upload for {phone_number}: {result['success']}")
        
    except Exception as e:
        logger.error(f"Error handling media upload: {str(e)}")

async def handle_view_documents(phone_number: str):
    """Handle request to view documents with interactive list"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.whatsapp_auth import document_handler
        
        whatsapp_client = CustomWhatsAppClient()
        
        # List documents
        result = await document_handler.list_user_documents(phone_number)
        
        # If there are documents, send interactive list
        if result.get("success") and result.get("documents"):
            documents = result["documents"][:10]  # Max 10 items
            
            # Build interactive list sections
            rows = []
            for i, doc in enumerate(documents, 1):
                rows.append({
                    "id": f"doc_{i}",
                    "title": f"{i}. {doc.get('filename', 'Unknown')[:20]}",
                    "description": f"{doc.get('doc_type', 'N/A').title()} - {doc.get('uploaded_at', 'N/A')[:10]}"
                })
            
            sections = [{
                "title": "Your Documents",
                "rows": rows
            }]
            
            body_text = f"📁 *Your Medical Documents*\n\nYou have {len(documents)} document(s).\nTap a document to download it."
            
            await whatsapp_client.send_interactive_list(
                phone_number=phone_number,
                body_text=body_text,
                button_text="View Documents",
                sections=sections,
                header_text="🔐 Secure Documents",
                footer_text="AyurEze Healthcare"
            )
        else:
            # No documents or error - send text message
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=result["message"]
            )
        
        logger.info(f"📁 Document list for {phone_number}: {result['success']}")
        
    except Exception as e:
        logger.error(f"Error handling view documents: {str(e)}")

async def handle_get_document(phone_number: str, doc_index: int):
    """Handle request to get a specific document"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.whatsapp_auth import document_handler
        
        whatsapp_client = CustomWhatsAppClient()
        
        # Get document link
        result = await document_handler.get_document_link(phone_number, doc_index)
        
        # Send response
        await whatsapp_client.send_text_message(
            phone_number=phone_number,
            message_body=result["message"]
        )
        
        logger.info(f"📥 Document download for {phone_number}: {result['success']}")
        
    except Exception as e:
        logger.error(f"Error handling get document: {str(e)}")

async def handle_button_click(phone_number: str, button_id: str, customer_name: str):
    """Handle interactive button clicks"""
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        
        whatsapp_client = CustomWhatsAppClient()
        timestamp = datetime.now().isoformat()
        
        # Map button IDs to actions
        if button_id in ["taken", "taken_medicine"]:
            # Medicine taken button
            await handle_medicine_response(phone_number, 'taken', timestamp)
            
        elif button_id in ["later", "remind_later"]:
            # Remind later button
            await handle_medicine_response(phone_number, 'later', timestamp)
            
        elif button_id in ["skip", "skip_medicine"]:
            # Skip medicine button
            await handle_medicine_response(phone_number, 'skipped', timestamp)
            
        elif button_id == "verify_account":
            # Verify account button
            await handle_verify_request(phone_number)
            
        elif button_id == "view_documents":
            # View documents button
            await handle_view_documents(phone_number)
            
        elif button_id == "ask_ai":
            # Ask AI button - send helpful message
            help_text = f"""Hi {customer_name}! 🌿

I'm Astra, your AI Ayurvedic wellness assistant.

You can ask me questions like:
• "How to improve digestion?"
• "Best herbs for sleep?"
• "Tips for managing stress?"
• "Ayurvedic remedies for acidity?"

Just type your question and I'll help! 😊"""
            
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=help_text
            )
            
        else:
            logger.warning(f"Unknown button ID: {button_id}")
            
    except Exception as e:
        logger.error(f"Error handling button click: {str(e)}")

async def handle_list_selection(phone_number: str, row_id: str):
    """Handle interactive list selections"""
    try:
        # Check if it's a document selection
        if row_id.startswith("doc_"):
            # Extract document number (e.g., "doc_1" -> 1)
            doc_num = int(row_id.split("_")[1])
            await handle_get_document(phone_number, doc_num)
            
        else:
            logger.warning(f"Unknown list selection: {row_id}")
            
    except Exception as e:
        logger.error(f"Error handling list selection: {str(e)}")
