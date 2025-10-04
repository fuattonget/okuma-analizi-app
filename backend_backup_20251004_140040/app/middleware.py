import uuid
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.logging_config import app_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging with request ID"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        app_logger.bind(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None
        ).info("Request started")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        app_logger.bind(
            request_id=request_id,
            status_code=response.status_code
        ).info(f"Request completed in {round(duration, 3)}s")
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response

