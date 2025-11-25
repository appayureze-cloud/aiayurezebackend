"""
Ayureze Backend API Client
Connects to ayureze.org super admin backend to fetch patient data
"""

import os
import logging
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger(__name__)

class AyurezeBackendClient:
    """Client to access patient data from ayureze.org backend"""
    
    def __init__(self):
        # Remove /login suffix if present in env var
        base_url = os.getenv('AYUREZE_BACKEND_URL', 'https://ayureze.org')
        self.base_url = base_url.rstrip('/login').rstrip('/')
        self.email = os.getenv('AYUREZE_BACKEND_EMAIL')
        self.password = os.getenv('AYUREZE_BACKEND_PASSWORD')
        self.session_token = None
        self.initialized = False
    
    async def login(self) -> bool:
        """Login to ayureze.org backend and get session token"""
        if not self.email or not self.password:
            logger.warning("⚠️ Ayureze backend credentials not configured")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                # Attempt login - try correct endpoint
                response = await client.post(
                    f"{self.base_url}/api/admin/login",
                    json={
                        "email": self.email,
                        "password": self.password
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.session_token = data.get('token') or data.get('session_token')
                    self.initialized = True
                    logger.info("✅ Successfully logged in to Ayureze backend")
                    return True
                else:
                    logger.error(f"❌ Login failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error logging in to Ayureze backend: {str(e)}")
            return False
    
    async def get_patient_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get patient data from backend by phone number"""
        if not self.initialized:
            await self.login()
        
        if not self.initialized:
            return None
        
        try:
            # Normalize phone number
            normalized_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/admin/patients/search",
                    params={"phone": normalized_phone},
                    headers={"Authorization": f"Bearer {self.session_token}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data and isinstance(data, list) and len(data) > 0:
                        patient = data[0]
                        logger.info(f"✅ Found patient in backend: {patient.get('name', 'Unknown')}")
                        return patient
                    elif data and isinstance(data, dict):
                        logger.info(f"✅ Found patient in backend: {data.get('name', 'Unknown')}")
                        return data
                    else:
                        logger.warning(f"⚠️ No patient found for phone: {phone}")
                        return None
                elif response.status_code == 401:
                    # Token expired, re-login
                    logger.info("🔄 Session expired, re-logging in...")
                    await self.login()
                    # Retry once
                    return await self.get_patient_by_phone(phone)
                else:
                    logger.error(f"❌ Error fetching patient: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error fetching patient from backend: {str(e)}")
            return None
    
    async def get_patient_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get patient data from backend by email address"""
        if not self.initialized:
            await self.login()
        
        if not self.initialized:
            return None
        
        try:
            # Normalize email
            normalized_email = email.lower().strip()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/admin/patients/search",
                    params={"email": normalized_email},
                    headers={"Authorization": f"Bearer {self.session_token}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data and isinstance(data, list) and len(data) > 0:
                        patient = data[0]
                        logger.info(f"✅ Found patient by email: {patient.get('name', 'Unknown')}")
                        return patient
                    elif data and isinstance(data, dict):
                        logger.info(f"✅ Found patient by email: {data.get('name', 'Unknown')}")
                        return data
                    else:
                        logger.warning(f"⚠️ No patient found for email: {email}")
                        return None
                elif response.status_code == 401:
                    # Token expired, re-login
                    logger.info("🔄 Session expired, re-logging in...")
                    await self.login()
                    # Retry once
                    return await self.get_patient_by_email(email)
                else:
                    logger.error(f"❌ Error fetching patient: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error fetching patient by email from backend: {str(e)}")
            return None
    
    async def get_patient_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get patient data from backend by UID"""
        if not self.initialized:
            await self.login()
        
        if not self.initialized:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/admin/patients/{uid}",
                    headers={"Authorization": f"Bearer {self.session_token}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    patient = response.json()
                    logger.info(f"✅ Found patient by UID: {patient.get('name', 'Unknown')}")
                    return patient
                elif response.status_code == 401:
                    # Token expired, re-login
                    await self.login()
                    return await self.get_patient_by_uid(uid)
                else:
                    logger.warning(f"⚠️ Patient not found for UID: {uid}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error fetching patient by UID: {str(e)}")
            return None
    
    async def get_patient_medicines(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get patient's active medicine schedules from backend"""
        if not self.initialized:
            await self.login()
        
        if not self.initialized:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/admin/patients/{patient_id}/medicines",
                    headers={"Authorization": f"Bearer {self.session_token}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    medicines = response.json()
                    logger.info(f"✅ Found {len(medicines)} medicines for patient")
                    return medicines
                elif response.status_code == 401:
                    await self.login()
                    return await self.get_patient_medicines(patient_id)
                else:
                    logger.warning(f"⚠️ No medicines found for patient: {patient_id}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Error fetching medicines: {str(e)}")
            return []
    
    async def get_all_patients(self) -> List[Dict[str, Any]]:
        """Get all patients from backend"""
        if not self.initialized:
            await self.login()
        
        if not self.initialized:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/admin/patients",
                    headers={"Authorization": f"Bearer {self.session_token}"},
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    patients = response.json()
                    logger.info(f"✅ Retrieved {len(patients)} patients from backend")
                    return patients
                elif response.status_code == 401:
                    await self.login()
                    return await self.get_all_patients()
                else:
                    logger.error(f"❌ Error fetching patients: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Error fetching all patients: {str(e)}")
            return []


# Global instance
ayureze_backend = AyurezeBackendClient()


async def get_backend_client() -> AyurezeBackendClient:
    """Get Ayureze backend client instance"""
    if not ayureze_backend.initialized:
        await ayureze_backend.login()
    return ayureze_backend
