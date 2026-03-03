import logging
import json
import sys
import time
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields if available
        if hasattr(record, "extra"):
             log_record.update(record.extra)
             
        return json.dumps(log_record, ensure_ascii=False)

def setup_logging():
    """
    Configure the root logger to output JSON to stdout.
    """
    logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    
    # Set levels for noisy libraries if needed
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    return logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs requests and responses with execution time.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger = logging.getLogger("api.request")
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            log_data = {
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time_ms": round(process_time, 2),
                "client_ip": request.client.host if request.client else None
            }
            
            extra = {"extra": log_data}
            
            if response.status_code >= 400:
                logger.error(f"请求失败: {request.method} {request.url.path}", extra=extra)
            else:
                logger.info(f"请求完成: {request.method} {request.url.path}", extra=extra)
                
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"请求异常: {request.method} {request.url.path}", 
                exc_info=True,
                extra={"extra": {
                    "method": request.method,
                    "url": str(request.url),
                    "process_time_ms": round(process_time, 2),
                    "error": str(e)
                }}
            )
            raise e
