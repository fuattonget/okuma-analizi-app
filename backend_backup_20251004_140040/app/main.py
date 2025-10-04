from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import uuid
import os
from datetime import datetime
from loguru import logger
from app.config import settings
from app.db import connect_to_mongo, close_mongo_connection, connect_to_redis, redis_conn
from app.routers import texts, analyses, upload, audio, sessions, auth, students


# Configure loguru based on settings
def setup_logging():
    # Remove default handler
    logger.remove()
    
    # Configure log level
    log_level = settings.log_level.upper()
    
    # Configure format
    if settings.log_format.lower() == "json":
        log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}"
    else:
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
    
    # Add console handler
    logger.add(
        sink=lambda msg: print(msg, end=""),
        format=log_format,
        level=log_level,
        colorize=settings.log_format.lower() != "json"
    )
    
    # Add file handler with rotation
    if settings.log_file:
        os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
        logger.add(
            sink=settings.log_file,
            format=log_format,
            level=log_level,
            rotation="5 MB",
            retention="7 days",
            compression="zip"
        )


# Setup logging
setup_logging()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Request timing middleware
class RequestTimingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        request_id = str(uuid.uuid4())
        
        # Add request_id to logger context
        logger.bind(request_id=request_id)
        
        # Start timing
        start_time = time.time()
        
        # Add request_id to request state
        request.state.request_id = request_id
        
        # Process request
        response_sent = False
        
        async def send_wrapper(message):
            nonlocal response_sent
            if message["type"] == "http.response.start" and not response_sent:
                response_sent = True
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Get client IP
                client_ip = request.client.host if request.client else "unknown"
                
                # Prepare log data
                log_data = {
                    "method": request.method,
                    "path": request.url.path,
                    "status": message.get("status", 0),
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": client_ip,
                    "request_id": request_id
                }
                
                # Add slow request flag
                if duration_ms >= settings.trace_slow_ms:
                    log_data["slow"] = True
                
                # Log the request
                logger.info("Request completed", **log_data)
                
                # Add request_id to response headers
                message["headers"] = list(message.get("headers", []))
                message["headers"].append([b"x-request-id", request_id.encode()])
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


# Global exception handler
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.bind(request_id=request_id).error("Unhandled exception: {}", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id}
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info("🚀 Starting application")
        
        # MongoDB connection
        try:
            logger.info("📊 Connecting to MongoDB...")
            await connect_to_mongo()
            logger.info("✅ MongoDB connected successfully")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            logger.error(f"MongoDB error type: {type(e).__name__}")
            logger.error(f"MongoDB error details: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
        # Redis connection
        try:
            logger.info("📊 Connecting to Redis...")
            connect_to_redis()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.error(f"Redis error type: {type(e).__name__}")
            logger.error(f"Redis error details: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
        logger.info("🎉 Application started successfully")
        
    except Exception as e:
        logger.error(f"Critical error during application startup: {e}")
        logger.error(f"Startup error type: {type(e).__name__}")
        logger.error(f"Startup error details: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    
    yield
    
    # Shutdown
    try:
        logger.info("🛑 Shutting down application")
        await close_mongo_connection()
        logger.info("✅ Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")
        logger.error(f"Shutdown error type: {type(e).__name__}")
        logger.error(f"Shutdown error details: {str(e)}")
        import traceback
        traceback.print_exc()


app = FastAPI(
    title="Okuma Analizi API",
    description="API for reading analysis and assessment",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add global exception handler
app.add_exception_handler(Exception, global_exception_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing middleware
app.add_middleware(RequestTimingMiddleware)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint
    
    Returns the current status of the API service.
    """
    return {"status": "ok"}


# Debug endpoint
@app.get("/v1/_debug", tags=["debug"])
async def debug_info():
    """
    Debug information endpoint
    
    Returns debug information about the system.
    Only available when DEBUG=true.
    """
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Debug mode is disabled")
    
    # Check Redis connection
    redis_ok = False
    redis_error = None
    try:
        if hasattr(redis_conn, 'connection') and redis_conn.connection:
            redis_conn.connection.ping()
            redis_ok = True
        else:
            redis_error = "Connection not initialized"
    except Exception as e:
        redis_error = str(e)
    
    # Calculate uptime (simplified)
    uptime_s = int(time.time() - time.time())  # This would be better with actual start time
    
    return {
        "debug": settings.debug,
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "long_pause_ms": settings.long_pause_ms,
        "mongo_db": settings.mongo_db,
        "redis_ok": redis_ok,
        "redis_error": redis_error,
        "uptime_s": uptime_s
    }


# Note: Media files are now served from GCS, no local static file mounting needed

# Include routers
app.include_router(
    texts.router, 
    prefix="/v1/texts", 
    tags=["texts"],
    responses={
        404: {"description": "Text not found"},
        400: {"description": "Invalid text ID"}
    }
)
app.include_router(
    analyses.router, 
    prefix="/v1/analyses", 
    tags=["analyses"],
    responses={
        404: {"description": "Analysis not found"},
        400: {"description": "Invalid analysis ID"}
    }
)
app.include_router(
    upload.router, 
    prefix="/v1/upload", 
    tags=["upload"],
    responses={
        400: {"description": "Invalid file format"},
        413: {"description": "File too large"}
    }
)
app.include_router(
    audio.router, 
    prefix="/v1/audio", 
    tags=["audio"],
    responses={
        404: {"description": "Audio file not found"},
        400: {"description": "Invalid audio ID"}
    }
)
app.include_router(
    sessions.router, 
    prefix="/v1/sessions", 
    tags=["sessions"],
    responses={
        404: {"description": "Session not found"},
        400: {"description": "Invalid session ID"}
    }
)
app.include_router(
    auth.router, 
    prefix="/v1/auth", 
    tags=["authentication"],
    responses={
        401: {"description": "Invalid credentials"},
        403: {"description": "Access denied"}
    }
)
app.include_router(
    students.router, 
    prefix="/v1/students", 
    tags=["students"],
    responses={
        404: {"description": "Student not found"},
        400: {"description": "Invalid student data"}
    }
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )