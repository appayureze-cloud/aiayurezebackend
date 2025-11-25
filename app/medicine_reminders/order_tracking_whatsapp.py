"""
WhatsApp Order Tracking Handler
Sends Shopify order tracking information via WhatsApp
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

async def send_order_tracking_whatsapp(
    phone_number: str,
    patient_name: str,
    order_id: int
) -> bool:
    """
    Get order tracking from Shopify and send via WhatsApp
    """
    try:
        from app.shopify_client import shopify_client
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        
        whatsapp_client = CustomWhatsAppClient()
        
        # Get tracking information from Shopify
        tracking_info = shopify_client.get_order_tracking(order_id)
        
        if not tracking_info:
            # Order not found
            message = f"""❌ *Order Not Found*

Hello {patient_name},

We couldn't find order #{order_id} in our system.

*Please check:*
• Order ID is correct
• Order has been placed and paid
• Draft order has been converted to real order

*Need Help?*
Reply with your prescription ID or contact our support team.

_AyurEze Healthcare Team_ 🌿"""
            
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=message
            )
            return False
        
        # Format tracking message
        message = format_tracking_message(patient_name, tracking_info)
        
        # Send via WhatsApp
        await whatsapp_client.send_text_message(
            phone_number=phone_number,
            message_body=message
        )
        
        logger.info(f"✅ Tracking info sent to {phone_number} for order {order_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send tracking info: {e}")
        return False

def format_tracking_message(patient_name: str, tracking_info: dict) -> str:
    """
    Format tracking information into WhatsApp message
    """
    order_name = tracking_info.get('order_name', 'N/A')
    fulfillment_status = tracking_info.get('fulfillment_status', 'pending')
    total_price = tracking_info.get('total_price', '0.00')
    
    # Status emoji mapping
    status_emoji = {
        'fulfilled': '✅',
        'partial': '🔄',
        'unfulfilled': '📦',
        'pending': '⏳',
        'in_transit': '🚚',
        'out_for_delivery': '📬',
        'delivered': '🎉'
    }
    
    emoji = status_emoji.get(fulfillment_status, '📦')
    
    # Build message
    message = f"""{emoji} *Order Tracking - {order_name}*

Hello {patient_name},

*Order Summary:*
💰 Total Amount: ₹{total_price}
📊 Status: {fulfillment_status.replace('_', ' ').title()}

"""
    
    # Add items
    items = tracking_info.get('items', [])
    if items:
        message += "*Items Ordered:*\n"
        for idx, item in enumerate(items, 1):
            message += f"{idx}. {item.get('name')} (Qty: {item.get('quantity')}) - ₹{item.get('price')}\n"
        message += "\n"
    
    # Add tracking details
    tracking_details = tracking_info.get('tracking_details', [])
    
    if tracking_details:
        message += "*📦 Shipment Tracking:*\n\n"
        
        for idx, tracking in enumerate(tracking_details, 1):
            tracking_company = tracking.get('tracking_company', 'Courier')
            tracking_number = tracking.get('tracking_number', 'N/A')
            tracking_url = tracking.get('tracking_url', '')
            status = tracking.get('status', 'unknown')
            shipped_at = tracking.get('shipped_at', '')
            
            message += f"*Shipment #{idx}:*\n"
            message += f"🚚 Courier: {tracking_company}\n"
            message += f"📋 Tracking #: {tracking_number}\n"
            message += f"📍 Status: {status.replace('_', ' ').title()}\n"
            
            if shipped_at:
                try:
                    shipped_date = datetime.fromisoformat(shipped_at.replace('Z', '+00:00'))
                    message += f"📅 Shipped: {shipped_date.strftime('%b %d, %Y at %I:%M %p')}\n"
                except:
                    message += f"📅 Shipped: {shipped_at}\n"
            
            if tracking_url:
                message += f"\n🔗 *Track Live:*\n{tracking_url}\n\n"
            else:
                message += "\n"
        
        # Add shipping address
        shipping = tracking_info.get('shipping_address', {})
        if shipping.get('city'):
            message += f"*📍 Delivery Address:*\n"
            message += f"{shipping.get('city')}, {shipping.get('state')} - {shipping.get('zip')}\n\n"
        
        message += "*Estimated Delivery:*\n"
        message += "⏱️ 3-5 business days from shipment date\n\n"
        
    else:
        # No tracking yet
        message += "*📦 Shipment Status:*\n"
        
        if fulfillment_status == 'unfulfilled' or fulfillment_status == 'pending':
            message += """⏳ Your order is being prepared for shipment.

*Next Steps:*
• Order is being packed at our warehouse
• You'll receive tracking details once shipped
• Typically ships within 24-48 hours

We'll send you an update as soon as it's dispatched! 🚀\n\n"""
        elif fulfillment_status == 'fulfilled':
            message += "✅ Order has been fulfilled and delivered!\n\n"
    
    # Footer
    message += """*Need Help?*
Reply to this message or contact our support team.

*Track Anytime:*
Send "TRACK ORDER" to get latest updates

_AyurEze Healthcare Team_ 🌿"""
    
    return message

async def handle_track_order_command(phone_number: str, patient_name: str):
    """
    Handle "TRACK ORDER" command - finds latest order for authenticated user
    """
    try:
        from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
        from app.medicine_reminders.email_auth_handlers import get_authenticated_patient_data
        from app.database_models import PrescriptionRecord, SessionLocal
        
        whatsapp_client = CustomWhatsAppClient()
        
        # Check if user is authenticated
        patient_data, patient_name = await get_authenticated_patient_data(phone_number)
        
        if not patient_data:
            # User not logged in
            message = """🔐 *Login Required*

To track your orders, please login first:

*How to Login:*
1. Send your registered email address
2. Enter the OTP you receive
3. Access your order history

📧 Send your email to start!

_AyurEze Healthcare Team_ 🌿"""
            
            await whatsapp_client.send_text_message(
                phone_number=phone_number,
                message_body=message
            )
            return
        
        # Get patient's latest order from database
        if SessionLocal:
            db = SessionLocal()
            try:
                # Find latest prescription for this patient
                patient_uid = patient_data.get('uid') if isinstance(patient_data, dict) else None
                
                if patient_uid:
                    # Try to find by Firebase UID first
                    latest_prescription = db.query(PrescriptionRecord).filter(
                        PrescriptionRecord.patient_id == patient_uid
                    ).order_by(PrescriptionRecord.created_at.desc()).first()
                else:
                    # Fallback to phone number search
                    latest_prescription = db.query(PrescriptionRecord).join(
                        # Note: This requires PatientProfile table join
                        # Simplified for now
                    ).order_by(PrescriptionRecord.created_at.desc()).first()
                
                if latest_prescription and latest_prescription.draft_order_id:
                    # Convert draft_order_id to real Shopify order_id
                    # Note: This assumes draft order has been converted to real order
                    order_id = int(latest_prescription.draft_order_id)
                    
                    # Send tracking info
                    await send_order_tracking_whatsapp(
                        phone_number=phone_number,
                        patient_name=patient_name,
                        order_id=order_id
                    )
                else:
                    # No orders found
                    message = f"""📦 *No Orders Found*

Hello {patient_name},

We couldn't find any orders in your account yet.

*How to Place an Order:*
1. Consult with our doctor
2. Receive prescription via WhatsApp
3. Complete payment
4. Track your order here!

*Need Help?*
Contact our support team.

_AyurEze Healthcare Team_ 🌿"""
                    
                    await whatsapp_client.send_text_message(
                        phone_number=phone_number,
                        message_body=message
                    )
                
            finally:
                db.close()
        else:
            logger.warning("Database not available for order lookup")
            
    except Exception as e:
        logger.error(f"❌ Error handling track order command: {e}")
        import traceback
        logger.error(traceback.format_exc())
