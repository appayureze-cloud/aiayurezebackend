"""
Firebase Patient Data Service
Connects to Firebase using service account credentials to access patient data by UID
"""

import os
import json
import logging
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore, auth

logger = logging.getLogger(__name__)

class FirebasePatientService:
    """Service to access patient data from Firebase using UID"""
    
    def __init__(self):
        self.db = None
        self.initialized = False
        
    def initialize(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if firebase_admin._apps:
                logger.info("✅ Firebase already initialized")
                self.db = firestore.client()
                self.initialized = True
                return
            
            # Get service account credentials from environment
            service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT')
            
            if not service_account_json:
                logger.warning("⚠️ FIREBASE_SERVICE_ACCOUNT not found in environment")
                return
            
            # Parse service account JSON
            try:
                service_account_dict = json.loads(service_account_json)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid FIREBASE_SERVICE_ACCOUNT JSON: {e}")
                return
            
            # Initialize Firebase Admin
            cred = credentials.Certificate(service_account_dict)
            firebase_admin.initialize_app(cred)
            
            # Get Firestore client
            self.db = firestore.client()
            self.initialized = True
            
            logger.info("✅ Firebase Patient Service initialized successfully")
            logger.info(f"📊 Project ID: {service_account_dict.get('project_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase: {str(e)}")
            self.initialized = False
    
    async def get_patient_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get patient data from Firebase using UID"""
        if not self.initialized:
            logger.warning("Firebase not initialized")
            return None
        
        try:
            # Get patient document from Firestore
            doc_ref = self.db.collection('patients').document(uid)
            doc = doc_ref.get()
            
            if doc.exists:
                patient_data = doc.to_dict()
                logger.info(f"✅ Found patient data for UID: {uid}")
                return patient_data
            else:
                logger.warning(f"⚠️ No patient found for UID: {uid}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching patient by UID {uid}: {str(e)}")
            return None
    
    async def get_patient_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get patient data from Firebase using phone number"""
        if not self.initialized:
            logger.warning("Firebase not initialized")
            return None
        
        try:
            # Normalize phone number (remove +, spaces, etc.)
            normalized_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
            
            # Query patients collection by phone
            patients_ref = self.db.collection('patients')
            query = patients_ref.where('phone', '==', normalized_phone).limit(1)
            docs = query.stream()
            
            for doc in docs:
                patient_data = doc.to_dict()
                patient_data['uid'] = doc.id
                logger.info(f"✅ Found patient by phone: {normalized_phone}")
                return patient_data
            
            # Try with +91 prefix
            if not normalized_phone.startswith('91'):
                query = patients_ref.where('phone', '==', f'91{normalized_phone}').limit(1)
                docs = query.stream()
                
                for doc in docs:
                    patient_data = doc.to_dict()
                    patient_data['uid'] = doc.id
                    logger.info(f"✅ Found patient by phone with +91: {normalized_phone}")
                    return patient_data
            
            logger.warning(f"⚠️ No patient found for phone: {phone}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error fetching patient by phone {phone}: {str(e)}")
            return None
    
    async def get_patient_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get patient data from Firebase using email address"""
        if not self.initialized:
            logger.warning("Firebase not initialized")
            return None
        
        try:
            # Normalize email (lowercase, trim)
            normalized_email = email.lower().strip()
            
            # Query patients collection by email
            patients_ref = self.db.collection('patients')
            query = patients_ref.where('email', '==', normalized_email).limit(1)
            docs = query.stream()
            
            for doc in docs:
                patient_data = doc.to_dict()
                patient_data['uid'] = doc.id
                logger.info(f"✅ Found patient by email: {normalized_email}")
                return patient_data
            
            logger.warning(f"⚠️ No patient found for email: {email}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error fetching patient by email {email}: {str(e)}")
            return None
    
    async def get_patient_medicines(self, uid: str) -> list:
        """Get patient's active medicine schedules"""
        if not self.initialized:
            return []
        
        try:
            # Get medicines subcollection
            medicines_ref = self.db.collection('patients').document(uid).collection('medicines')
            query = medicines_ref.where('active', '==', True)
            docs = query.stream()
            
            medicines = []
            for doc in docs:
                medicine_data = doc.to_dict()
                medicine_data['id'] = doc.id
                medicines.append(medicine_data)
            
            logger.info(f"✅ Found {len(medicines)} active medicines for UID: {uid}")
            return medicines
            
        except Exception as e:
            logger.error(f"❌ Error fetching medicines for UID {uid}: {str(e)}")
            return []
    
    async def update_patient_data(self, uid: str, data: Dict[str, Any]) -> bool:
        """Update patient data in Firebase"""
        if not self.initialized:
            return False
        
        try:
            doc_ref = self.db.collection('patients').document(uid)
            doc_ref.update(data)
            logger.info(f"✅ Updated patient data for UID: {uid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating patient UID {uid}: {str(e)}")
            return False
    
    async def get_user_info_from_auth(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user info from Firebase Authentication"""
        if not self.initialized:
            return None
        
        try:
            user = auth.get_user(uid)
            
            user_info = {
                'uid': user.uid,
                'email': user.email,
                'phone': user.phone_number,
                'display_name': user.display_name,
                'photo_url': user.photo_url,
                'email_verified': user.email_verified,
                'disabled': user.disabled,
                'created_at': user.user_metadata.creation_timestamp,
                'last_sign_in': user.user_metadata.last_sign_in_timestamp
            }
            
            logger.info(f"✅ Found auth user for UID: {uid}")
            return user_info
            
        except Exception as e:
            logger.error(f"❌ Error fetching auth user UID {uid}: {str(e)}")
            return None


# Global instance
firebase_patient_service = FirebasePatientService()


def get_firebase_service() -> FirebasePatientService:
    """Get Firebase patient service instance"""
    if not firebase_patient_service.initialized:
        firebase_patient_service.initialize()
    return firebase_patient_service
