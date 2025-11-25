"""
Enhanced FastAPI backend with Astra persona, multilingual support, and Supabase integration
"""

import asyncio
import logging
import os
import uuid
import time
import json
import traceback
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import uvicorn

from app.models import (
    ChatRequest, ChatResponse, HealthResponse, ModelStatus,
    EnhancedChatRequest, EnhancedChatResponse, ChatSessionRequest, 
    ChatSessionResponse, ChatHistoryResponse, UserSessionsResponse,
    AuthRequest, SessionResponse, AuthenticatedChatRequest, AuthenticatedChatResponse,
    StreamingChatRequest
)
from datetime import datetime
from app.config import settings
from app.enhanced_inference import AstraModelInference
from app.database import db_manager
from app.language_utils import language_manager
from app.database_models import create_tables, get_db_dependency
from app.auth_routes import auth_router, chat_router
from app.frontend import frontend_router
from app.simplified_auth import simple_auth_router
from app.smart_auto_cart import router as smart_auto_cart_router
from app.catchy_prescription.routes import router as catchy_prescription_router
from app.notification_routes import router as notification_router
from app.patient_management import router as patient_management_router
from app.order_management import router as order_management_router
from app.prescription_pdf_endpoint import router as prescription_pdf_router
from app.medicine_reminders.routes import router as medicine_reminder_router
from app.medicine_reminders.webhook_handler import router as whatsapp_webhook_router
from app.multilang.routes import router as multilang_router
from app.advanced_notifications.routes import router as advanced_notifications_router
from app.documents.routes import router as documents_router
from app.api.compliance_routes import router as compliance_router
from app.security.compliance_middleware import ComplianceMiddleware
from app.unified_prescription_workflow import router as unified_prescription_router
from app.shopify_webhook import router as shopify_webhook_router
from app.companion_api import router as companion_router

# Enhanced structured logging configuration
class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
            
        # Add request details if available
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'route'):
            log_data['route'] = record.route
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'latency_ms'):
            log_data['latency_ms'] = record.latency_ms
            
        return json.dumps(log_data)

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Apply structured formatter to root logger
handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter())
logging.getLogger().handlers = [handler]
logging.getLogger().setLevel(logging.INFO)

# Global model inference instance
model_inference: Optional[AstraModelInference] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for model loading and auto-sync"""
    global model_inference
    
    try:
        logger.info("Initializing Astra - Your Ayurvedic Wellness Assistant...")
        model_inference = AstraModelInference(
            base_model_id=settings.BASE_MODEL,
            lora_model_id=settings.LORA_MODEL,
            device=settings.DEVICE
        )
        
        # Load model in background (non-blocking) - server starts immediately with fallback responses
        async def load_model_background():
            logger.info("🔄 Loading Llama model in background (this may take a few minutes)...")
            logger.info("⚡ Server will use friendly fallback responses until model loads")
            await model_inference.load_model()
        
        asyncio.create_task(load_model_background())
        
        # Configure ModelService with model_inference
        from app.model_service import ModelService
        ModelService.set_model_inference(model_inference)
        logger.info("✅ ModelService configured for companion system")
        
        # Initialize database tables if available
        try:
            create_tables()
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            logger.info("Continuing without database features")
        
        # Start Shopify auto-sync service
        try:
            from app.shopify_auto_sync import shopify_auto_sync
            await shopify_auto_sync.start()
            logger.info("✅ Shopify auto-sync service started")
        except Exception as e:
            logger.warning(f"Shopify auto-sync failed to start: {e}")
        
        logger.info("Astra is ready to guide your wellness journey")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize Astra: {e}")
        yield
    finally:
        # Stop auto-sync service gracefully
        try:
            from app.shopify_auto_sync import shopify_auto_sync
            await shopify_auto_sync.stop()
            logger.info("✅ Shopify auto-sync service stopped")
        except Exception as e:
            logger.warning(f"Shopify auto-sync stop skipped: {e}")
            pass

# Import AI Agent API router
from app.ai_agent_api import router as ai_agent_router

# Initialize FastAPI app
app = FastAPI(
    title="Astra - Ayurvedic Wellness Assistant API",
    description="Multilingual Ayurvedic wellness assistant with chat history and personalized guidance",
    version="2.0.0",
    lifespan=lifespan
)

# Register AI Agent API routes
app.include_router(ai_agent_router)

# Enhanced CORS configuration (secure for production)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5000").split(",")
# For development, allow all if CORS_ORIGINS is set to "*"
if len(CORS_ORIGINS) == 1 and CORS_ORIGINS[0] == "*":
    cors_origins = ["*"]
    cors_credentials = False  # Security: don't allow credentials with wildcard
else:
    cors_origins = [origin.strip() for origin in CORS_ORIGINS if origin.strip()]
    cors_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Secure configurable origins
    allow_credentials=cors_credentials,  # Only allow credentials with explicit origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"],  # Expose correlation ID to frontend
)

# Add DISHA compliance middleware for automatic audit logging
app.add_middleware(ComplianceMiddleware)

# Enhanced Error Tracking Middleware
@app.middleware("http")
async def error_tracking_middleware(request: Request, call_next):
    """Enhanced error tracking with correlation IDs and structured logging"""
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    start_time = time.time()
    
    # Log request start
    logger.info(
        "Request started",
        extra={
            'correlation_id': correlation_id,
            'request_id': correlation_id[:8],
            'route': str(request.url.path),
            'method': request.method,
            'user_agent': request.headers.get('user-agent', 'unknown')
        }
    )
    
    try:
        response = await call_next(request)
        
        # Calculate latency
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        # Log successful request
        logger.info(
            "Request completed",
            extra={
                'correlation_id': correlation_id,
                'request_id': correlation_id[:8],
                'route': str(request.url.path),
                'status_code': response.status_code,
                'latency_ms': latency_ms
            }
        )
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response
        
    except Exception as e:
        # Calculate latency for failed requests
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        # Log error with correlation ID
        logger.error(
            f"Request failed: {str(e)}",
            extra={
                'correlation_id': correlation_id,
                'request_id': correlation_id[:8],
                'route': str(request.url.path),
                'latency_ms': latency_ms,
                'error_type': type(e).__name__
            }
        )
        
        # Send critical error notification for all unhandled exceptions on critical routes
        critical_routes = ["/chat", "/medicine-reminders", "/smart-auto-cart", "/shopify", "/multilang"]
        if any(critical_route in str(request.url.path) for critical_route in critical_routes):
            await notify_admin_error(correlation_id, str(e), str(request.url.path))
        
        # Re-raise the exception to be handled by global exception handler
        raise

# Admin Error Notification Function
async def notify_admin_error(correlation_id: str, error_message: str, route: str):
    """Send email notification for critical errors"""
    try:
        # Only send notifications for truly critical errors to avoid spam
        critical_routes = ["/chat", "/medicine-reminders", "/smart-auto-cart"]
        if any(critical_route in route for critical_route in critical_routes):
            
            # Check if replitmail is available
            try:
                import replitmail
                
                subject = f"🚨 Critical Error in Smart Auto-Cart Healthcare System"
                body = f"""
                Critical Error Alert:
                
                Correlation ID: {correlation_id}
                Route: {route}
                Error: {error_message}
                Timestamp: {datetime.now().isoformat()}
                
                Please investigate immediately to ensure patient care continuity.
                """
                
                # Send email notification
                replitmail.send_email(
                    to="admin@ayureze-healthcare.com",  # Configure admin email
                    subject=subject,
                    text=body
                )
                
                logger.info(f"Critical error notification sent for correlation ID: {correlation_id}")
                
            except ImportError:
                logger.warning("ReplitMail not available for error notifications")
            except Exception as e:
                logger.error(f"Failed to send error notification: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in notification system: {str(e)}")

# Include authentication routes
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(frontend_router)
app.include_router(simple_auth_router)

# Include Smart Auto-Cart routes  
app.include_router(smart_auto_cart_router)
app.include_router(catchy_prescription_router)
app.include_router(prescription_pdf_router)
app.include_router(medicine_reminder_router)
app.include_router(notification_router)
app.include_router(patient_management_router)
app.include_router(order_management_router)
app.include_router(multilang_router)
app.include_router(advanced_notifications_router)
app.include_router(documents_router)
app.include_router(compliance_router)  # DISHA compliance endpoints
app.include_router(unified_prescription_router)  # Unified prescription workflow
app.include_router(shopify_webhook_router)  # Shopify webhooks & auto-sync
app.include_router(whatsapp_webhook_router)  # Custom WhatsApp webhooks
app.include_router(companion_router)  # AI Wellness Companion system

# Mount static files for FCM token generator (if directory exists)
import os
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    @app.get("/fcm-test")
    async def fcm_test_page():
        """Serve FCM token generator for testing"""
        return FileResponse("static/fcm-token-generator.html")
else:
    logger.info("Static directory not found - FCM test page disabled")

# Utility functions
async def get_or_create_session(user_id: str, session_id: Optional[str], language: str) -> str:
    """Get existing session or create new one"""
    if session_id:
        return session_id
    
    if user_id and db_manager.is_connected():
        new_session_id = await db_manager.create_chat_session(user_id, language)
        return new_session_id or str(uuid.uuid4())
    
    return str(uuid.uuid4())

# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with Astra introduction"""
    return {
        "message": "Namaste! Welcome to Astra - Your Ayurvedic Wellness Assistant",
        "description": "I'm here to guide you on your journey to holistic health through ancient Ayurvedic wisdom",
        "status": "ready",
        "version": "2.0.0",
        "features": "Multilingual support, Chat history, Personalized guidance"
    }

@app.get("/health/comprehensive", response_model=Dict[str, Any], tags=["health"])
async def comprehensive_health_check():
    """Comprehensive health check for all system components"""
    correlation_id = str(uuid.uuid4())
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "correlation_id": correlation_id,
        "components": {}
    }
    
    # Check AI Model
    try:
        if model_inference and hasattr(model_inference, 'model') and model_inference.model:
            health_status["components"]["ai_model"] = {
                "status": "operational",
                "model_loaded": True,
                "base_model": settings.BASE_MODEL,
                "lora_model": settings.LORA_MODEL
            }
        else:
            health_status["components"]["ai_model"] = {
                "status": "degraded",
                "model_loaded": False,
                "message": "Model not loaded"
            }
    except Exception as e:
        health_status["components"]["ai_model"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Database
    try:
        from app.database_models import get_db_dependency
        db = next(get_db_dependency())
        # Simple database query to test connection
        db.execute("SELECT 1")
        health_status["components"]["database"] = {
            "status": "operational",
            "connection": "active"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Shopify Integration
    try:
        shopify_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        shopify_url = os.getenv('SHOPIFY_SHOP_URL')
        if shopify_token and shopify_url:
            health_status["components"]["shopify"] = {
                "status": "operational",
                "configured": True,
                "shop_url": shopify_url
            }
        else:
            health_status["components"]["shopify"] = {
                "status": "degraded",
                "configured": False,
                "message": "Missing configuration"
            }
    except Exception as e:
        health_status["components"]["shopify"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check WhatsApp Integration
    try:
        whatsapp_token = os.getenv('KWIKENGAGE_API_KEY')
        if whatsapp_token:
            health_status["components"]["whatsapp"] = {
                "status": "operational",
                "configured": True,
                "api": "KwikEngage"
            }
        else:
            health_status["components"]["whatsapp"] = {
                "status": "degraded",
                "configured": False,
                "message": "Missing API key"
            }
    except Exception as e:
        health_status["components"]["whatsapp"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Determine overall status
    component_statuses = [comp["status"] for comp in health_status["components"].values()]
    if "unhealthy" in component_statuses:
        health_status["status"] = "unhealthy"
    elif "degraded" in component_statuses:
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/health/readiness", tags=["health"])
async def readiness_check():
    """Simple readiness check for load balancers"""
    try:
        # Quick AI model check
        if model_inference and hasattr(model_inference, 'model') and model_inference.model:
            return {"status": "ready", "timestamp": datetime.now().isoformat()}
        else:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "AI model not loaded"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )

@app.get("/health/liveness", tags=["health"])
async def liveness_check():
    """Simple liveness check"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Legacy health check endpoint (maintained for compatibility)"""
    global model_inference
    
    model_loaded = model_inference is not None and model_inference.is_loaded()
    
    return HealthResponse(
        status="healthy" if model_loaded else "loading",
        model_loaded=model_loaded,
        gpu_available=False,  # Mock mode
        device="cpu"
    )

@app.get("/model/status", response_model=ModelStatus)
async def model_status():
    """Get detailed model status"""
    global model_inference
    
    if not model_inference:
        return ModelStatus(
            loaded=False,
            base_model=settings.BASE_MODEL,
            lora_model=settings.LORA_MODEL,
            device="cpu",
            memory_usage=None
        )
    
    return ModelStatus(
        loaded=model_inference.is_loaded(),
        base_model=settings.BASE_MODEL,
        lora_model=settings.LORA_MODEL,
        device="cpu",
        memory_usage={"allocated": 0, "cached": 0, "max_allocated": 0}
    )

@app.post("/chat/session", response_model=ChatSessionResponse)
async def create_chat_session(request: ChatSessionRequest):
    """Create a new chat session"""
    session_id = await db_manager.create_chat_session(request.user_id, request.language or "en")
    
    if not session_id:
        session_id = str(uuid.uuid4())
    
    return ChatSessionResponse(
        session_id=session_id,
        user_id=request.user_id,
        language=request.language or "en",
        created_at=datetime.utcnow()
    )

@app.post("/chat/enhanced", response_model=EnhancedChatResponse)
async def enhanced_chat_completion(request: EnhancedChatRequest):
    """Enhanced chat endpoint with Astra persona and multilingual support"""
    global model_inference
    
    if not model_inference or not model_inference.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Astra is still preparing her knowledge base. Please wait a moment."
        )
    
    try:
        # Enhanced language detection with auto-fallback
        if request.language:
            detected_language = request.language
            detection_confidence = 1.0
        else:
            # Use enhanced detection for better accuracy
            detection_result = language_manager.enhanced_language_detection(request.message)
            detected_language = detection_result.get('language', 'en')
            detection_confidence = detection_result.get('confidence', 0.0)
            
            # If detection is uncertain, fallback to English
            if detection_result.get('requires_confirmation') or detection_confidence < 0.6:
                detected_language = 'en'
                logger.info(f"Language detection uncertain (confidence: {detection_confidence}), using English")
        
        # Check if question is Ayurveda-related
        is_ayurveda_related = language_manager.is_ayurveda_related(request.message, detected_language)
        
        # Get or create session
        session_id = None
        if request.user_id:
            session_id = await get_or_create_session(
                request.user_id, request.session_id, detected_language
            )
        
        # Generate response with Astra's persona
        response_text = await model_inference.generate_response(
            prompt=request.message,
            language=detected_language,
            max_length=request.max_length or 512,
            temperature=request.temperature or 0.7,
            top_p=request.top_p or 0.9,
            top_k=request.top_k or 50,
            do_sample=request.do_sample if request.do_sample is not None else True
        )
        
        # Note: The model already generates responses in the detected language
        # No additional translation needed - Llama 3.1 handles multilingual output natively
        
        # Save to database if session exists
        if session_id and db_manager.is_connected():
            await db_manager.save_chat_message(
                session_id=session_id,
                user_message=request.message,
                assistant_response=response_text,
                language=detected_language,
                metadata={
                    "is_ayurveda_related": is_ayurveda_related,
                    "model_params": {
                        "temperature": request.temperature,
                        "max_length": request.max_length
                    }
                }
            )
        
        return EnhancedChatResponse(
            response=response_text,
            session_id=session_id,
            language=detected_language,
            is_ayurveda_related=is_ayurveda_related,
            model=f"Astra ({settings.BASE_MODEL} + {settings.LORA_MODEL})",
            usage={
                "prompt_tokens": len(request.message.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(request.message.split()) + len(response_text.split())
            }
        )
        
    except Exception as e:
        logger.error(f"Error during enhanced chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Astra encountered an issue: {str(e)}"
        )

@app.get("/chat/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, limit: int = 50):
    """Get chat history for a session"""
    if not db_manager.is_connected():
        raise HTTPException(
            status_code=503,
            detail="Chat history service is not available"
        )
    
    try:
        messages = await db_manager.get_chat_history(session_id, limit)
        
        return ChatHistoryResponse(
            messages=messages,
            session_info={
                "session_id": session_id,
                "message_count": len(messages),
                "limit": limit
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve chat history"
        )

@app.get("/chat/sessions/{user_id}", response_model=UserSessionsResponse)
async def get_user_sessions(user_id: str, limit: int = 20):
    """Get chat sessions for a user"""
    if not db_manager.is_connected():
        raise HTTPException(
            status_code=503,
            detail="Session management service is not available"
        )
    
    try:
        sessions = await db_manager.get_user_sessions(user_id, limit)
        
        return UserSessionsResponse(
            sessions=sessions,
            total_count=len(sessions)
        )
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user sessions"
        )

@app.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str, user_id: str):
    """Delete a chat session"""
    if not db_manager.is_connected():
        raise HTTPException(
            status_code=503,
            detail="Session management service is not available"
        )
    
    try:
        success = await db_manager.delete_session(session_id, user_id)
        
        if success:
            return {"message": "Session deleted successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail="Session not found or access denied"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete session"
        )

@app.get("/languages/supported")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "languages": language_manager.SUPPORTED_LANGUAGES,
        "default": language_manager.default_language
    }

@app.post("/languages/detect")
async def detect_language(request: dict):
    """Detect language of provided text"""
    text = request.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    detected = language_manager.detect_language(text)
    return {
        "detected_language": detected,
        "language_name": language_manager.get_language_name(detected),
        "is_ayurveda_related": language_manager.is_ayurveda_related(text, detected)
    }

# Legacy endpoints for backward compatibility
@app.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """Legacy chat endpoint for backward compatibility"""
    enhanced_request = EnhancedChatRequest(
        message=request.message,
        session_id=None,
        user_id=None,
        language=None,
        max_length=request.max_length,
        temperature=request.temperature,
        top_p=request.top_p,
        top_k=request.top_k,
        do_sample=request.do_sample
    )
    
    enhanced_response = await enhanced_chat_completion(enhanced_request)
    
    return ChatResponse(
        response=enhanced_response.response,
        model=enhanced_response.model,
        usage=enhanced_response.usage
    )

@app.post("/generate", response_model=ChatResponse)
async def generate_text(request: ChatRequest):
    """Alternative endpoint for text generation (compatibility)"""
    return await chat_completion(request)

@app.post("/stream")
async def stream_chat(request: StreamingChatRequest):
    """Stream chat responses with typing effect like ChatGPT"""
    global model_inference
    
    if not model_inference or not model_inference.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    try:
        # Detect language if not provided
        detected_language = request.language or language_manager.detect_language(request.message)
        
        async def generate_stream():
            async for chunk in model_inference.generate_streaming_response(
                prompt=request.message,
                language=detected_language,
                max_length=request.max_length or 1024,
                temperature=request.temperature or 0.7
            ):
                # Format as Server-Sent Events
                yield f"data: {chunk}\n\n"
            
            # Send completion signal
            yield "data: [DONE]\n\n"
        
        return EventSourceResponse(generate_stream(), media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Error in streaming response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Exception Classes
class ShopifyValidationError(HTTPException):
    """Custom exception for Shopify validation errors"""
    def __init__(self, detail: str, field_errors: dict = None):
        super().__init__(status_code=422, detail=detail)
        self.field_errors = field_errors or {}

class ShopifyRateLimitError(HTTPException):
    """Custom exception for Shopify rate limiting"""
    def __init__(self, detail: str, retry_after: int = 60):
        super().__init__(status_code=429, detail=detail)
        self.retry_after = retry_after

# Enhanced Exception Handlers
@app.exception_handler(ShopifyValidationError)
async def shopify_validation_handler(request: Request, exc: ShopifyValidationError):
    """Handle Shopify validation errors with detailed field information"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_failed",
            "message": "Order contains invalid data",
            "field_errors": exc.field_errors,
            "correlation_id": correlation_id
        }
    )

@app.exception_handler(ShopifyRateLimitError)
async def shopify_rate_limit_handler(request: Request, exc: ShopifyRateLimitError):
    """Handle Shopify rate limiting with retry information"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests, please try again later",
            "retry_after": exc.retry_after,
            "correlation_id": correlation_id
        },
        headers={"Retry-After": str(exc.retry_after)}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Enhanced HTTP exception handler with correlation ID"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "correlation_id": correlation_id
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Enhanced global exception handler with correlation ID and alerting"""
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            'correlation_id': correlation_id,
            'route': str(request.url.path),
            'error_type': type(exc).__name__
        }
    )
    
    # Send critical error notification for all unhandled exceptions
    await notify_admin_error(correlation_id, str(exc), str(request.url.path))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "Astra encountered an unexpected issue. Please try again.",
            "correlation_id": correlation_id
        }
    )

# ==================== Zixflow Webhook for Two-Way Messaging ====================

@app.post("/webhooks/zixflow/whatsapp")
async def zixflow_whatsapp_webhook(request: Request):
    """
    Receive incoming WhatsApp messages from Zixflow
    Handles patient responses: TAKEN, SKIP, LATER, HELP
    Official Zixflow webhook format: incoming.whatsapp.message
    """
    try:
        data = await request.json()
        logger.info(f"📥 Zixflow webhook received: {data}")
        
        # Extract event type (Zixflow format)
        event_type = data.get("event", "")
        
        # Handle incoming WhatsApp message
        if event_type == "incoming.whatsapp.message":
            # Extract sender information (Zixflow format)
            sender = data.get("sender", {})
            from_number = sender.get("number", "")
            sender_name = sender.get("name", "Unknown")
            
            # Extract message content (Zixflow format)
            message_data = data.get("message", {})
            message_type = message_data.get("type", "")
            message_id = data.get("messageId", "")
            
            # Extract text from message based on type
            message_text = ""
            if message_type == "text":
                text_obj = message_data.get("text", {})
                message_text = text_obj.get("body", "").upper().strip()
            elif message_type == "button":
                button_obj = message_data.get("button", {})
                message_text = button_obj.get("text", "").upper().strip()
            else:
                # Other types: image, video, audio, document, location, contacts, interactive, order
                logger.info(f"📎 Received {message_type} message from {from_number}")
                return {"status": "success", "message": f"{message_type} message received"}
            
            logger.info(f"📱 Message from {from_number} ({sender_name}): {message_text}")
            
            # Import Zixflow client
            from app.medicine_reminders.zixflow_client import ZixflowClient
            zixflow = ZixflowClient()
            
            # Process patient responses
            response_message = None
            
            if message_text in ["TAKEN", "T", "✅", "YES", "Y"]:
                response_message = "✅ Great! Recorded that you took your medicine. Keep up the good work! 🌿"
                # TODO: Update adherence record in database
                
            elif message_text in ["SKIP", "S", "SKIPPED", "❌", "NO", "N"]:
                response_message = "⚠️ We've noted that you skipped this dose. Please try not to miss your next dose. 💊"
                # TODO: Update adherence record as skipped
                
            elif message_text in ["LATER", "L", "⏰", "REMIND"]:
                response_message = "⏰ Okay, I'll remind you again in 30 minutes. Stay healthy! 🌿"
                # TODO: Schedule reminder for 30 minutes later
                
            elif message_text in ["HELP", "H", "?"]:
                response_message = """
🌿 *AyurEze Healthcare - Help*

Reply with:
• ✅ *TAKEN* or *T* - Mark medicine as taken
• ❌ *SKIP* or *S* - Skip this dose
• ⏰ *LATER* or *L* - Remind me in 30 min
• 📞 *CONTACT* - Talk to a doctor

– Team AyurEze
"""
            
            elif message_text in ["CONTACT", "DOCTOR", "CALL", "SUPPORT"]:
                response_message = """
📞 *Contact AyurEze Healthcare*

📱 WhatsApp: +91-XXXXXXXXXX
📧 Email: support@ayurezehealthcare.com
🕐 Hours: Mon-Sat, 9 AM - 6 PM IST

Our team will assist you shortly! 🌿
"""
            
            else:
                # General response for unrecognized messages
                response_message = f"""
Thank you for your message! 🌿

For medicine reminders, reply:
• *TAKEN* or *T*
• *SKIP* or *S*
• *LATER* or *L*
• *HELP* for more options

– Team AyurEze
"""
            
            # Send auto-reply
            if response_message and from_number:
                reply_id = zixflow.send_whatsapp_direct(from_number, response_message)
                if reply_id:
                    logger.info(f"✅ Auto-reply sent to {from_number}: {reply_id}")
                else:
                    logger.error(f"❌ Failed to send auto-reply to {from_number}")
            
            return {"status": "success", "message": "Webhook processed"}
        
        elif event_type in ["message.delivered", "message.read"]:
            # Just log delivery/read receipts
            logger.info(f"📬 Message status update: {event_type}")
            return {"status": "success", "message": "Status update received"}
        
        else:
            logger.warning(f"⚠️ Unknown webhook event: {event_type}")
            return {"status": "success", "message": "Event logged"}
            
    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        # Return 200 even on error to prevent Zixflow from retrying
        return {"status": "error", "message": str(e)}


@app.get("/webhooks/zixflow/whatsapp")
async def zixflow_whatsapp_webhook_verify(request: Request):
    """
    Verify webhook endpoint for Zixflow setup
    """
    return {
        "status": "active",
        "message": "Zixflow WhatsApp webhook is ready",
        "endpoint": "/webhooks/zixflow/whatsapp"
    }


if __name__ == "__main__":
    # Use port 7860 for Hugging Face Spaces, fallback to 5000 for local dev
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(
        "main_enhanced:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )