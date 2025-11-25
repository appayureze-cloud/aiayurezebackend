"""
Patient FCM Token Management using Supabase
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class PatientTokenService:
    """Service for managing patient FCM tokens in PostgreSQL"""
    
    def __init__(self):
        self.db_available = False
        self._check_database_connection()
    
    def _check_database_connection(self):
        """Check if PostgreSQL database is available"""
        try:
            # Use the existing database connection parameters
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                self.db_available = True
                logger.info("PostgreSQL database available for patient tokens")
            else:
                logger.warning("Database not available. Token storage will be disabled.")
                
        except Exception as e:
            logger.error(f"Failed to check database connection: {e}")
    
    def _get_db_connection(self):
        """Get database connection"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise Exception("DATABASE_URL not configured")
        
        return psycopg2.connect(database_url)
    
    def create_table_if_not_exists(self):
        """Create patient_fcm_tokens table if it doesn't exist"""
        if not self.db_available:
            logger.warning("Database not available, cannot create table")
            return False
        
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'patient_fcm_tokens'
                        )
                    """)
                    table_exists = cur.fetchone()[0]
                    
                    if table_exists:
                        logger.info("patient_fcm_tokens table exists and accessible")
                        return True
                    else:
                        logger.info("patient_fcm_tokens table does not exist")
                        return False
                        
        except Exception as e:
            logger.error(f"Cannot check patient_fcm_tokens table: {e}")
            return False
    
    def store_fcm_token(
        self,
        patient_id: str,
        fcm_token: str,
        device_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store or update patient's FCM token
        
        Args:
            patient_id: Unique patient identifier
            fcm_token: Firebase Cloud Messaging token
            device_info: Optional device information
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.db_available:
            logger.error("Database not available, cannot store token")
            return False
        
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Upsert the token (insert or update if exists)
                    cur.execute("""
                        INSERT INTO patient_fcm_tokens (patient_id, fcm_token, device_info, updated_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (patient_id) 
                        DO UPDATE SET 
                            fcm_token = EXCLUDED.fcm_token,
                            device_info = EXCLUDED.device_info,
                            updated_at = NOW()
                    """, (patient_id, fcm_token, json.dumps(device_info or {})))
                    
                    conn.commit()
                    logger.info(f"FCM token stored successfully for patient: {patient_id}")
                    return True
                
        except Exception as e:
            logger.error(f"Error storing FCM token for patient {patient_id}: {e}")
            return False
    
    def get_fcm_token(self, patient_id: str) -> Optional[str]:
        """
        Get patient's FCM token
        
        Args:
            patient_id: Unique patient identifier
            
        Returns:
            str: FCM token if found, None otherwise
        """
        if not self.db_available:
            logger.error("Database not available, cannot retrieve token")
            return None
        
        try:
            with self._get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT fcm_token FROM patient_fcm_tokens WHERE patient_id = %s",
                        (patient_id,)
                    )
                    
                    result = cur.fetchone()
                    if result:
                        token = result["fcm_token"]
                        logger.info(f"FCM token retrieved for patient: {patient_id}")
                        return token
                    else:
                        logger.warning(f"No FCM token found for patient: {patient_id}")
                        return None
                
        except Exception as e:
            logger.error(f"Error retrieving FCM token for patient {patient_id}: {e}")
            return None
    
    def remove_fcm_token(self, patient_id: str) -> bool:
        """
        Remove patient's FCM token
        
        Args:
            patient_id: Unique patient identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.db_available:
            logger.error("Database not available, cannot remove token")
            return False
        
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM patient_fcm_tokens WHERE patient_id = %s",
                        (patient_id,)
                    )
                    conn.commit()
                    
                    logger.info(f"FCM token removed for patient: {patient_id}")
                    return True
            
        except Exception as e:
            logger.error(f"Error removing FCM token for patient {patient_id}: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if the service is available"""
        return self.db_available

# Global patient token service instance
patient_token_service = PatientTokenService()