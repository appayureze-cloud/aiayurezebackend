"""
WhatsApp Document Upload Handler
Handles medical document uploads via WhatsApp with authentication
"""

import os
import logging
import tempfile
import mimetypes
from typing import Dict, Any, Optional
from pathlib import Path
import aiohttp
from app.whatsapp_auth.session_store import session_store, AuthStage
from app.storj_client import StorjClient

logger = logging.getLogger(__name__)

class WhatsAppDocumentHandler:
    """Handles authenticated document uploads via WhatsApp"""
    
    # WhatsApp media limits
    MAX_FILE_SIZE_MB = 100
    ALLOWED_MIME_TYPES = [
        'application/pdf',
        'image/jpeg',
        'image/jpg',
        'image/png',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
        'application/msword'  # DOC
    ]
    
    ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
    
    def __init__(self):
        """Initialize document handler"""
        try:
            self.storj_client = StorjClient()
            logger.info("Document handler initialized with Storj client")
        except Exception as e:
            logger.error(f"Failed to initialize Storj client: {e}")
            self.storj_client = None
    
    async def handle_document_upload(
        self,
        phone_number: str,
        media_url: str,
        media_type: str,
        filename: Optional[str] = None,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle document upload from WhatsApp
        
        Args:
            phone_number: User's WhatsApp number
            media_url: URL to download the media from WhatsApp API
            media_type: MIME type of the media
            filename: Original filename
            caption: Document caption/description
            
        Returns:
            Dict with upload status and details
        """
        try:
            # Check if user is verified
            if not session_store.is_session_verified(phone_number):
                return {
                    "success": False,
                    "message": "❌ Please verify your account first.\n\nReply with: VERIFY",
                    "requires_verification": True
                }
            
            # Validate file type
            if not self._is_allowed_file_type(media_type, filename):
                return {
                    "success": False,
                    "message": f"❌ Unsupported file type.\n\nAllowed: PDF, JPG, PNG, DOC, DOCX",
                    "invalid_type": True
                }
            
            # Update session stage
            session_store.update_session_stage(phone_number, AuthStage.UPLOAD_PROCESSING)
            
            # Download media from WhatsApp
            temp_file_path = await self._download_media(media_url, filename)
            
            if not temp_file_path:
                session_store.update_session_stage(phone_number, AuthStage.VERIFIED)
                return {
                    "success": False,
                    "message": "❌ Failed to download document. Please try again."
                }
            
            # Check file size
            file_size_mb = os.path.getsize(temp_file_path) / (1024 * 1024)
            if file_size_mb > self.MAX_FILE_SIZE_MB:
                os.remove(temp_file_path)
                session_store.update_session_stage(phone_number, AuthStage.VERIFIED)
                return {
                    "success": False,
                    "message": f"❌ File too large ({file_size_mb:.1f}MB).\n\nMaximum: {self.MAX_FILE_SIZE_MB}MB"
                }
            
            # Get Firebase UID from session
            session = session_store.get_session(phone_number)
            firebase_uid = session.get("firebase_uid")
            
            if not firebase_uid:
                os.remove(temp_file_path)
                session_store.update_session_stage(phone_number, AuthStage.VERIFIED)
                return {
                    "success": False,
                    "message": "❌ User not found. Please verify again."
                }
            
            # Determine document type from caption or filename
            doc_type = self._determine_doc_type(caption, filename)
            
            # Upload to Storj
            if not self.storj_client:
                os.remove(temp_file_path)
                session_store.update_session_stage(phone_number, AuthStage.VERIFIED)
                return {
                    "success": False,
                    "message": "❌ Storage service unavailable. Please try again later."
                }
            
            object_key = self.storj_client.upload_document(
                file_path=temp_file_path,
                patient_id=firebase_uid,
                doc_type=doc_type,
                metadata={
                    'source': 'whatsapp',
                    'phone_number': phone_number,
                    'caption': caption or '',
                    'original_filename': filename or 'document'
                }
            )
            
            # Clean up temp file
            os.remove(temp_file_path)
            
            if not object_key:
                session_store.update_session_stage(phone_number, AuthStage.VERIFIED)
                return {
                    "success": False,
                    "message": "❌ Failed to upload document. Please try again."
                }
            
            # Update session stage
            session_store.update_session_stage(phone_number, AuthStage.READY)
            
            # Log successful upload (DISHA compliance - audit trail)
            logger.info(f"✅ Document uploaded - User: {firebase_uid[:8]}..., Key: {object_key}, Type: {doc_type}, Size: {file_size_mb:.2f}MB")
            
            return {
                "success": True,
                "message": f"✅ *Document Uploaded Successfully!*\n\n📁 Type: {doc_type.title()}\n📊 Size: {file_size_mb:.1f}MB\n🔐 Securely stored\n\nYour document is encrypted and safely stored.\n\nReply with: VIEW DOCS to see all your documents",
                "object_key": object_key,
                "doc_type": doc_type,
                "file_size_mb": file_size_mb
            }
            
        except Exception as e:
            logger.error(f"Document upload error: {e}")
            session_store.update_session_stage(phone_number, AuthStage.VERIFIED)
            return {
                "success": False,
                "message": "❌ Upload failed. Please try again."
            }
    
    async def list_user_documents(self, phone_number: str) -> Dict[str, Any]:
        """
        List all documents for a user
        
        Args:
            phone_number: User's WhatsApp number
            
        Returns:
            Dict with document list
        """
        try:
            # Check if user is verified
            if not session_store.is_session_verified(phone_number):
                return {
                    "success": False,
                    "message": "❌ Please verify your account first.\n\nReply with: VERIFY",
                    "requires_verification": True
                }
            
            # Get Firebase UID
            session = session_store.get_session(phone_number)
            firebase_uid = session.get("firebase_uid")
            
            if not firebase_uid or not self.storj_client:
                return {
                    "success": False,
                    "message": "❌ Unable to retrieve documents."
                }
            
            # List documents from Storj
            documents = self.storj_client.list_patient_documents(firebase_uid)
            
            if not documents:
                return {
                    "success": True,
                    "message": "📁 *Your Documents*\n\nNo documents found.\n\nUpload a document to get started!",
                    "documents": []
                }
            
            # Format document list
            doc_list = "📁 *Your Medical Documents*\n\n"
            for i, doc in enumerate(documents[:10], 1):  # Limit to 10 most recent
                doc_list += f"{i}. {doc.get('filename', 'Unknown')}\n"
                doc_list += f"   📅 {doc.get('uploaded_at', 'N/A')}\n"
                doc_list += f"   📂 {doc.get('doc_type', 'N/A').title()}\n\n"
            
            doc_list += "\n💡 To download a document, reply with:\nGET DOC [number]"
            
            return {
                "success": True,
                "message": doc_list,
                "documents": documents
            }
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return {
                "success": False,
                "message": "❌ Failed to retrieve documents."
            }
    
    async def get_document_link(
        self,
        phone_number: str,
        doc_index: int
    ) -> Dict[str, Any]:
        """
        Generate secure download link for a document
        
        Args:
            phone_number: User's WhatsApp number
            doc_index: Document index (1-based)
            
        Returns:
            Dict with download link
        """
        try:
            # Check if user is verified
            if not session_store.is_session_verified(phone_number):
                return {
                    "success": False,
                    "message": "❌ Please verify your account first."
                }
            
            # Get Firebase UID
            session = session_store.get_session(phone_number)
            firebase_uid = session.get("firebase_uid")
            
            if not firebase_uid or not self.storj_client:
                return {
                    "success": False,
                    "message": "❌ Unable to retrieve document."
                }
            
            # Get documents
            documents = self.storj_client.list_patient_documents(firebase_uid)
            
            if not documents or doc_index < 1 or doc_index > len(documents):
                return {
                    "success": False,
                    "message": f"❌ Document #{doc_index} not found."
                }
            
            # Get the requested document
            document = documents[doc_index - 1]
            object_key = document.get('object_key')
            
            # Generate pre-signed URL (expires in 24 hours)
            download_url = self.storj_client.generate_download_url(
                object_key,
                expiration_hours=24
            )
            
            if not download_url:
                return {
                    "success": False,
                    "message": "❌ Failed to generate download link."
                }
            
            # Log access (DISHA compliance - audit trail)
            logger.info(f"📥 Document access - User: {firebase_uid[:8]}..., Doc: {object_key}")
            
            return {
                "success": True,
                "message": f"📥 *Download Link Generated*\n\n📄 {document.get('filename', 'Document')}\n\n🔗 Link expires in 24 hours\n\n{download_url}",
                "download_url": download_url,
                "document": document
            }
            
        except Exception as e:
            logger.error(f"Failed to generate download link: {e}")
            return {
                "success": False,
                "message": "❌ Failed to generate download link."
            }
    
    async def _download_media(
        self,
        media_url: str,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Download media from WhatsApp API
        
        Args:
            media_url: URL to download from
            filename: Original filename
            
        Returns:
            Path to downloaded file or None
        """
        try:
            # Get WhatsApp API credentials
            bearer_token = os.getenv('CUSTOM_WA_BEARER_TOKEN')
            
            if not bearer_token:
                logger.error("WhatsApp bearer token not found")
                return None
            
            # Download file
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {bearer_token}'
                }
                
                async with session.get(media_url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download media: {response.status}")
                        return None
                    
                    # Create temp file
                    suffix = Path(filename).suffix if filename else '.pdf'
                    temp_file = tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=suffix
                    )
                    
                    # Write content
                    content = await response.read()
                    temp_file.write(content)
                    temp_file.close()
                    
                    logger.info(f"Downloaded media to: {temp_file.name}")
                    return temp_file.name
                    
        except Exception as e:
            logger.error(f"Media download error: {e}")
            return None
    
    def _is_allowed_file_type(
        self,
        mime_type: str,
        filename: Optional[str] = None
    ) -> bool:
        """Check if file type is allowed"""
        if mime_type in self.ALLOWED_MIME_TYPES:
            return True
        
        if filename:
            ext = Path(filename).suffix.lower()
            return ext in self.ALLOWED_EXTENSIONS
        
        return False
    
    def _determine_doc_type(
        self,
        caption: Optional[str],
        filename: Optional[str]
    ) -> str:
        """Determine document type from caption or filename"""
        if caption:
            caption_lower = caption.lower()
            if 'prescription' in caption_lower or 'medicine' in caption_lower:
                return 'prescription'
            elif 'lab' in caption_lower or 'test' in caption_lower or 'report' in caption_lower:
                return 'lab_report'
            elif 'xray' in caption_lower or 'x-ray' in caption_lower or 'scan' in caption_lower:
                return 'xray'
            elif 'mri' in caption_lower or 'ct' in caption_lower:
                return 'imaging'
        
        if filename:
            filename_lower = filename.lower()
            if 'prescription' in filename_lower:
                return 'prescription'
            elif 'lab' in filename_lower or 'test' in filename_lower:
                return 'lab_report'
            elif 'xray' in filename_lower or 'scan' in filename_lower:
                return 'xray'
        
        return 'medical_record'

# Global instance
document_handler = WhatsAppDocumentHandler()
