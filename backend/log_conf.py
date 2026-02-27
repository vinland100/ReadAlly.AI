import logging
import sys
from datetime import datetime, timedelta, timezone

# China Standard Time (UTC+8)
CN_TZ = timezone(timedelta(hours=8))

class CSTFormatter(logging.Formatter):
    """Formatter that converts records to CST."""
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=CN_TZ)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]

def setup_logging():
    """Configures the root logger and specific loggers to use CST."""
    
    # Define format
    log_format = '[%(asctime)s] %(levelname)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    formatter = CSTFormatter(fmt=log_format, datefmt=date_format)
    
    # Console Handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Setup Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to prevent duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    root_logger.addHandler(handler)
    
    # Configure specific libraries to propagate or use this setup
    # SQLAlchemy
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    # Uvicorn - Uvicorn configures itself, we need to override if we want consistency
    # or let Uvicorn handle its own, but we want CST.
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        # Uvicorn usually adds handlers, we might want to override their formatter
        if logger.handlers:
            for h in logger.handlers:
                h.setFormatter(formatter)
        else:
            logger.addHandler(handler)
            logger.propagate = False  # Prevent double logging if root also catches it
            
    return root_logger
