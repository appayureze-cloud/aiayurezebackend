"""
Shiprocket API Client
Handles order creation, tracking, and label generation
"""

import logging
import requests
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ShiprocketOrderRequest(BaseModel):
    """Request model for creating Shiprocket order"""
    order_id: str
    order_date: str  # YYYY-MM-DD format
    pickup_location: str
    channel_id: str = "Custom"
    billing_customer_name: str
    billing_last_name: str = ""
    billing_address: str
    billing_city: str
    billing_pincode: str
    billing_state: str
    billing_country: str = "India"
    billing_email: str
    billing_phone: str
    shipping_is_billing: bool = True
    order_items: List[Dict[str, Any]]
    payment_method: str = "Prepaid"
    sub_total: float
    length: int = 10  # cm
    breadth: int = 10  # cm
    height: int = 10  # cm
    weight: float = 0.5  # kg

class ShiprocketClient:
    """
    Client for Shiprocket API
    Handles authentication, order creation, and tracking
    """
    
    def __init__(self):
        self.email = os.getenv('SHIPROCKET_EMAIL')
        self.password = os.getenv('SHIPROCKET_PASSWORD')
        self.api_key = os.getenv('SHIPROCKET_API_KEY')
        self.base_url = "https://apiv2.shiprocket.in/v1/external"
        
        self.token = None
        self.token_expiry = None
        
        if not self.email or not self.password:
            logger.warning("⚠️ Shiprocket credentials not configured")
            self.mock_mode = True
        else:
            self.mock_mode = False
            logger.info("✅ Shiprocket client initialized")
    
    async def get_auth_token(self) -> Optional[str]:
        """
        Get authentication token from Shiprocket
        Tokens are valid for 10 days
        """
        # Check if we have a valid token
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token
        
        if self.mock_mode:
            return "mock_token_12345"
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={
                    "email": self.email,
                    "password": self.password
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            self.token = data.get('token')
            # Token expires in 10 days
            self.token_expiry = datetime.now() + timedelta(days=10)
            
            logger.info("✅ Shiprocket authentication successful")
            return self.token
            
        except Exception as e:
            logger.error(f"❌ Shiprocket authentication failed: {e}")
            return None
    
    async def create_order(self, order_data: ShiprocketOrderRequest) -> Dict[str, Any]:
        """
        Create order in Shiprocket for shipping
        Returns order_id and shipment_id
        """
        if self.mock_mode:
            return {
                "success": True,
                "order_id": order_data.order_id,
                "shipment_id": "123456789",
                "status": "NEW",
                "awb_code": None,
                "courier_name": None,
                "message": "Mock order created successfully"
            }
        
        try:
            token = await self.get_auth_token()
            if not token:
                raise Exception("Failed to authenticate with Shiprocket")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            # Prepare order payload
            payload = order_data.dict()
            
            response = requests.post(
                f"{self.base_url}/orders/create/adhoc",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"✅ Shiprocket order created: {order_data.order_id}")
            
            return {
                "success": True,
                "order_id": data.get('order_id'),
                "shipment_id": data.get('shipment_id'),
                "status": data.get('status'),
                "awb_code": data.get('awb_code'),
                "courier_name": data.get('courier_name'),
                "message": "Order created successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create Shiprocket order: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create shipping order"
            }
    
    async def track_shipment(self, shipment_id: str) -> Dict[str, Any]:
        """
        Track shipment status using shipment ID
        Returns tracking information and current status
        """
        if self.mock_mode:
            return {
                "success": True,
                "shipment_id": shipment_id,
                "awb_code": "AWB123456789",
                "courier_name": "Delhivery",
                "current_status": "In Transit",
                "delivery_date": None,
                "tracking_url": f"https://shiprocket.co/tracking/{shipment_id}",
                "tracking_data": [
                    {
                        "date": "2025-11-07 10:00:00",
                        "status": "Picked Up",
                        "location": "Mumbai"
                    },
                    {
                        "date": "2025-11-07 14:30:00",
                        "status": "In Transit",
                        "location": "Pune Hub"
                    }
                ]
            }
        
        try:
            token = await self.get_auth_token()
            if not token:
                raise Exception("Failed to authenticate with Shiprocket")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.get(
                f"{self.base_url}/courier/track/shipment/{shipment_id}",
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            tracking_data = data.get('tracking_data', {})
            shipment_track = tracking_data.get('shipment_track', [])
            
            return {
                "success": True,
                "shipment_id": shipment_id,
                "awb_code": tracking_data.get('awb_code'),
                "courier_name": tracking_data.get('courier_name'),
                "current_status": tracking_data.get('shipment_status'),
                "delivery_date": tracking_data.get('delivered_date'),
                "tracking_url": f"https://shiprocket.co/tracking/{shipment_id}",
                "tracking_data": shipment_track
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to track shipment: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to track shipment"
            }
    
    async def track_by_awb(self, awb_code: str) -> Dict[str, Any]:
        """
        Track shipment using AWB (Air Waybill) code
        """
        if self.mock_mode:
            return await self.track_shipment("mock_shipment_123")
        
        try:
            token = await self.get_auth_token()
            if not token:
                raise Exception("Failed to authenticate with Shiprocket")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.get(
                f"{self.base_url}/courier/track/awb/{awb_code}",
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "awb_code": awb_code,
                "tracking_data": data.get('tracking_data', {}),
                "current_status": data.get('tracking_data', {}).get('shipment_status')
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to track AWB: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to track shipment"
            }
    
    async def get_available_couriers(self, pickup_pincode: str, delivery_pincode: str, weight: float = 0.5) -> List[Dict[str, Any]]:
        """
        Get list of available courier services for delivery
        Returns courier recommendations with pricing
        """
        if self.mock_mode:
            return [
                {
                    "courier_name": "Delhivery",
                    "rate": 50.0,
                    "estimated_delivery_days": "3-5",
                    "cod_charges": 0,
                    "available": True
                },
                {
                    "courier_name": "Bluedart",
                    "rate": 75.0,
                    "estimated_delivery_days": "2-3",
                    "cod_charges": 0,
                    "available": True
                }
            ]
        
        try:
            token = await self.get_auth_token()
            if not token:
                raise Exception("Failed to authenticate with Shiprocket")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            params = {
                "pickup_postcode": pickup_pincode,
                "delivery_postcode": delivery_pincode,
                "weight": weight,
                "cod": 0  # Prepaid
            }
            
            response = requests.get(
                f"{self.base_url}/courier/serviceability/",
                params=params,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            available_couriers = data.get('data', {}).get('available_courier_companies', [])
            
            return available_couriers
            
        except Exception as e:
            logger.error(f"❌ Failed to get available couriers: {e}")
            return []
    
    async def generate_label(self, shipment_id: str) -> Optional[str]:
        """
        Generate shipping label PDF URL
        """
        if self.mock_mode:
            return f"https://shiprocket.co/labels/{shipment_id}.pdf"
        
        try:
            token = await self.get_auth_token()
            if not token:
                raise Exception("Failed to authenticate with Shiprocket")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.post(
                f"{self.base_url}/courier/generate/label",
                json={"shipment_id": [shipment_id]},
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            label_url = data.get('label_url')
            logger.info(f"✅ Label generated for shipment {shipment_id}")
            
            return label_url
            
        except Exception as e:
            logger.error(f"❌ Failed to generate label: {e}")
            return None
    
    async def cancel_shipment(self, awb_codes: List[str]) -> Dict[str, Any]:
        """
        Cancel shipment by AWB codes
        """
        if self.mock_mode:
            return {
                "success": True,
                "message": f"Mock cancellation successful for {len(awb_codes)} shipments"
            }
        
        try:
            token = await self.get_auth_token()
            if not token:
                raise Exception("Failed to authenticate with Shiprocket")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.post(
                f"{self.base_url}/orders/cancel/shipment/awbs",
                json={"awbs": awb_codes},
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "message": data.get('message', 'Shipment cancelled successfully')
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel shipment: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to cancel shipment"
            }

# Global Shiprocket client instance
shiprocket_client = ShiprocketClient()
