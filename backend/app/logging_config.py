import sys
import json
from loguru import logger
from typing import Dict, Any


class JSONFormatter:
    """Custom JSON formatter for loguru"""
    
    def format(self, record: Dict[str, Any]) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
        }
        
        # Add request_id if available
        if "request_id" in record["extra"]:
            log_data["request_id"] = record["extra"]["request_id"]
        
        # Add any other extra fields
        for key, value in record["extra"].items():
            if key not in ["request_id"]:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging():
    """Setup loguru with JSON formatting"""
    # Remove default handler
    logger.remove()
    
    # Add JSON formatter for stdout
    logger.add(
        sys.stdout,
        format=JSONFormatter().format,
        level="INFO",
        serialize=False,
    )
    
    # Add file logging with JSON format
    logger.add(
        "logs/app.log",
        format=JSONFormatter().format,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        serialize=False,
    )
    
    return logger


# Global logger instance
app_logger = setup_logging()



