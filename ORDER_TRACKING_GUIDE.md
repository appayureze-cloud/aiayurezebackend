# 📦 ORDER TRACKING SYSTEM - Complete Guide

## 🎯 **How to Get Order Information**

Your system has **3 ways** to get order information:

1. **Shopify Orders** - E-commerce platform
2. **Shiprocket Tracking** - Shipping & delivery
3. **Local Database** - Your prescription records

---

## 📊 **1. GET ORDER FROM SHOPIFY**

### **A. Get Order by Order ID:**

```python
from app.shopify_client import shopify_client

# Get draft order details
draft_order = shopify_client.get_draft_order(draft_order_id=7891234)

# Returns:
{
    "id": 7891234,
    "order_id": 5001234567,  # Real order ID after payment
    "status": "open" | "invoice_sent" | "completed",
    "invoice_url": "https://ayureze-healthcare.myshopify.com/...",
    "line_items": [...],  # Products ordered
    "customer": {...},  # Customer details
    "total_price": "1247.00",
    "currency": "INR",
    "created_at": "2025-11-07T10:30:00Z",
    "updated_at": "2025-11-07T12:00:00Z"
}
```

### **B. Get Orders via API Endpoint:**

**API:** `GET /orders/prescription/{prescription_id}`

```bash
curl https://your-hf-space.hf.space/orders/prescription/RX-20251107-ABC123
```

**Response:**
```json
{
  "prescription_id": "RX-20251107-ABC123",
  "patient_id": "patient_123",
  "diagnosis": "Digestive issues",
  "status": "shipped",
  "payment_status": "paid",
  "draft_order_id": "7891234",
  "invoice_url": "https://...",
  "total_amount": "₹1,247.00",
  "prescribed_at": "2025-11-07T10:00:00",
  "paid_at": "2025-11-07T11:30:00",
  "medicines": [
    {
      "medicine_name": "Abhayarishtam",
      "dose": "10ml",
      "schedule": "After Meals",
      "duration": "30 days",
      "quantity": 1,
      "unit_price": "₹95.00",
      "total_price": "₹95.00"
    }
  ],
  "status_history": [
    {
      "previous_status": "pending",
      "new_status": "paid",
      "changed_at": "2025-11-07T11:30:00",
      "tracking_number": null
    },
    {
      "previous_status": "paid",
      "new_status": "shipped",
      "changed_at": "2025-11-07T14:00:00",
      "tracking_number": "AWB123456789",
      "tracking_url": "https://shiprocket.co/tracking/..."
    }
  ]
}
```

---

## 🚚 **2. GET SHIPPING TRACKING (SHIPROCKET)**

### **A. Track by Shipment ID:**

```python
from app.shiprocket_client import shiprocket_client

# Track shipment
tracking = await shiprocket_client.track_shipment(shipment_id="123456789")

# Returns:
{
    "success": True,
    "shipment_id": "123456789",
    "awb_code": "AWB123456789",  # Air Waybill Number
    "courier_name": "Delhivery",
    "current_status": "In Transit",
    "delivery_date": null,  # or "2025-11-10 18:00:00"
    "tracking_url": "https://shiprocket.co/tracking/123456789",
    "tracking_data": [
        {
            "date": "2025-11-07 10:00:00",
            "status": "Picked Up",
            "location": "Mumbai Warehouse"
        },
        {
            "date": "2025-11-07 14:30:00",
            "status": "In Transit",
            "location": "Pune Hub"
        },
        {
            "date": "2025-11-08 09:00:00",
            "status": "Out for Delivery",
            "location": "Bangalore"
        }
    ]
}
```

### **B. Track by AWB Code:**

```python
# Track using Air Waybill number
tracking = await shiprocket_client.track_by_awb(awb_code="AWB123456789")
```

### **C. Get Tracking Link:**

```python
tracking_url = f"https://shiprocket.co/tracking/{shipment_id}"
```

---

## 💾 **3. GET ORDER FROM LOCAL DATABASE**

### **A. Get Patient's All Orders:**

**API:** `GET /orders/patient/{patient_id}`

```bash
curl https://your-hf-space.hf.space/orders/patient/patient_123
```

**Response:**
```json
{
  "patient_id": "patient_123",
  "total_prescriptions": 5,
  "prescriptions": [
    {
      "prescription_id": "RX-20251107-ABC123",
      "diagnosis": "Digestive issues",
      "status": "shipped",
      "total_amount": "₹1,247.00",
      "prescribed_at": "2025-11-07T10:00:00",
      "medicines": [...]
    },
    {
      "prescription_id": "RX-20251101-XYZ456",
      "diagnosis": "Sleep issues",
      "status": "delivered",
      "total_amount": "₹850.00",
      "prescribed_at": "2025-11-01T15:00:00",
      "medicines": [...]
    }
  ]
}
```

### **B. Get Orders by Status:**

**API:** `GET /orders/status/{status}`

```bash
# Get all shipped orders
curl https://your-hf-space.hf.space/orders/status/shipped

# Get all pending orders
curl https://your-hf-space.hf.space/orders/status/pending
```

**Available Statuses:**
- `pending` - Prescription created, awaiting payment
- `paid` - Payment completed
- `shipped` - Order shipped
- `delivered` - Delivered to customer
- `cancelled` - Order cancelled

---

## 📱 **4. SEND TRACKING INFO VIA WHATSAPP**

### **Complete WhatsApp Integration:**

```python
from app.medicine_reminders.custom_whatsapp_client import CustomWhatsAppClient
from app.shiprocket_client import shiprocket_client

async def send_order_tracking_to_patient(
    patient_phone: str,
    patient_name: str,
    prescription_id: str,
    shipment_id: str
):
    """Send order tracking information via WhatsApp"""
    
    whatsapp_client = CustomWhatsAppClient()
    
    # Get tracking information
    tracking = await shiprocket_client.track_shipment(shipment_id)
    
    if not tracking.get('success'):
        logger.error("Failed to get tracking info")
        return
    
    # Format WhatsApp message
    message = f"""📦 *Order Shipped!*

Hello {patient_name},

Your order *{prescription_id}* has been shipped! 🎉

*Tracking Details:*
🚚 Courier: {tracking['courier_name']}
📋 AWB: {tracking['awb_code']}
📍 Status: {tracking['current_status']}

*Track Your Order:*
{tracking['tracking_url']}

*Delivery Timeline:*
Expected within 3-5 business days

*Recent Updates:*
"""
    
    # Add recent tracking updates
    for update in tracking['tracking_data'][-3:]:  # Last 3 updates
        message += f"\n• {update['date']} - {update['status']} ({update['location']})"
    
    message += """

*Need Help?*
Reply to this message or contact our support team.

_AyurEze Healthcare Team_ 🌿"""
    
    # Send WhatsApp message
    await whatsapp_client.send_text_message(
        phone_number=patient_phone,
        message_body=message
    )
    
    logger.info(f"✅ Tracking info sent to {patient_phone}")
```

---

## 🔄 **5. AUTOMATED ORDER TRACKING FLOW**

### **Complete Order Journey:**

```
1. Doctor Creates Prescription
   ↓
2. System Creates Shopify Draft Order
   ↓
3. Patient Receives Payment Link (WhatsApp)
   ↓
4. Patient Pays → Shopify Webhook "orders/paid"
   ↓
5. System Creates Shiprocket Order
   ↓
6. Shiprocket Assigns Courier & AWB
   ↓
7. System Sends Tracking Info (WhatsApp)
   ↓
8. Courier Picks Up → WhatsApp Update
   ↓
9. In Transit → WhatsApp Update
   ↓
10. Out for Delivery → WhatsApp Update
    ↓
11. Delivered → WhatsApp Confirmation
```

---

## 🛠️ **6. API ENDPOINTS AVAILABLE**

### **Order Management:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/orders/prescription/{id}` | GET | Get prescription details |
| `/orders/patient/{patient_id}` | GET | Get patient's all orders |
| `/orders/status/{status}` | GET | Get orders by status |
| `/orders/prescription/save` | POST | Save new prescription |
| `/orders/prescription/status` | PATCH | Update order status |
| `/orders/shopify/webhook` | POST | Shopify webhook receiver |

### **Shiprocket Integration:**

| Action | Method | Description |
|--------|--------|-------------|
| `shiprocket_client.create_order()` | POST | Create shipping order |
| `shiprocket_client.track_shipment()` | GET | Track by shipment ID |
| `shiprocket_client.track_by_awb()` | GET | Track by AWB code |
| `shiprocket_client.generate_label()` | POST | Generate shipping label |
| `shiprocket_client.cancel_shipment()` | POST | Cancel shipment |

---

## 💡 **7. EXAMPLE USE CASES**

### **Use Case 1: Customer Asks "Where is my order?"**

```python
# Via WhatsApp AI
user_query = "where is my order?"

# System:
# 1. Get patient ID from authenticated session
# 2. Fetch latest order from database
# 3. Get tracking info from Shiprocket
# 4. Format & send tracking details via WhatsApp

latest_order = get_patient_latest_order(patient_id)
tracking = await shiprocket_client.track_shipment(latest_order.shipment_id)

response = format_tracking_message(tracking)
await whatsapp_client.send_text_message(phone_number, response)
```

### **Use Case 2: Admin Wants to See All Pending Orders**

```bash
GET /orders/status/pending
```

### **Use Case 3: Update Order Status When Shipped**

```bash
PATCH /orders/prescription/status

{
  "prescription_id": "RX-20251107-ABC123",
  "new_status": "shipped",
  "change_reason": "Order shipped via Delhivery",
  "additional_data": {
    "shipment_id": "123456789",
    "awb_code": "AWB123456789",
    "tracking_url": "https://shiprocket.co/tracking/123456789"
  }
}
```

---

## 🔐 **8. ENVIRONMENT VARIABLES NEEDED**

Make sure these are set in your HuggingFace Space:

```bash
# Shiprocket Credentials
SHIPROCKET_EMAIL=your.email@example.com
SHIPROCKET_PASSWORD=your_password
SHIPROCKET_API_KEY=your_api_key

# Shopify Credentials (already set)
SHOPIFY_ACCESS_TOKEN=your_token
SHOPIFY_SHOP_URL=ayureze-healthcare.myshopify.com

# WhatsApp API (already set)
CUSTOM_WA_API_BASE_URL=https://whatsapp.ayureze.in
CUSTOM_WA_BEARER_TOKEN=your_token
```

---

## 📊 **9. ORDER STATUS TRACKING**

### **Status Lifecycle:**

```
pending → paid → processing → shipped → in_transit → out_for_delivery → delivered
                    ↓
                cancelled (at any stage)
```

### **Status Definitions:**

- **pending**: Prescription created, awaiting payment
- **paid**: Payment completed in Shopify
- **processing**: Being prepared for shipping
- **shipped**: Shipped from warehouse
- **in_transit**: En route to destination
- **out_for_delivery**: Out for final delivery
- **delivered**: Successfully delivered
- **cancelled**: Order cancelled

---

## 🎯 **10. QUICK START**

### **Step 1: Install Shiprocket Client**

File already created: `app/shiprocket_client.py` ✅

### **Step 2: Set Environment Variables**

Add to HuggingFace Space Secrets:
- `SHIPROCKET_EMAIL`
- `SHIPROCKET_PASSWORD`
- `SHIPROCKET_API_KEY`

### **Step 3: Create Shipping Order (Example)**

```python
from app.shiprocket_client import ShiprocketOrderRequest, shiprocket_client

order_request = ShiprocketOrderRequest(
    order_id="RX-20251107-ABC123",
    order_date="2025-11-07",
    pickup_location="Primary Warehouse",
    billing_customer_name="Rajesh Kumar",
    billing_address="123 MG Road",
    billing_city="Bangalore",
    billing_pincode="560001",
    billing_state="Karnataka",
    billing_email="rajesh@example.com",
    billing_phone="916380176373",
    order_items=[
        {
            "name": "Abhayarishtam",
            "sku": "AEAA1001",
            "units": 1,
            "selling_price": 95,
            "discount": 0
        }
    ],
    payment_method="Prepaid",
    sub_total=95.0,
    weight=0.5
)

# Create order
result = await shiprocket_client.create_order(order_request)

# Returns shipment_id for tracking
print(result['shipment_id'])  # Use this to track
```

### **Step 4: Track Order**

```python
tracking = await shiprocket_client.track_shipment(shipment_id="123456789")
print(tracking['current_status'])
print(tracking['tracking_url'])
```

### **Step 5: Send Tracking via WhatsApp**

```python
await send_order_tracking_to_patient(
    patient_phone="916380176373",
    patient_name="Rajesh Kumar",
    prescription_id="RX-20251107-ABC123",
    shipment_id="123456789"
)
```

---

## ✅ **Summary**

**You Can Now:**
- ✅ Get Shopify order information
- ✅ Track Shiprocket shipments
- ✅ Access order history from database
- ✅ Send tracking updates via WhatsApp
- ✅ Handle order status webhooks
- ✅ Generate shipping labels
- ✅ Check available couriers

**APIs Available:**
- `/orders/prescription/{id}` - Get order details
- `/orders/patient/{patient_id}` - Get patient orders
- `/orders/status/{status}` - Filter by status
- Shiprocket tracking methods
- WhatsApp notification system

**Next Steps:**
1. Set Shiprocket credentials in environment
2. Test order creation
3. Test tracking
4. Integrate WhatsApp notifications

---

**Need help with specific integration?** Let me know! 🚀📦
