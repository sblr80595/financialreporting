import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import Optional


class AuditLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.audit_logger = self._setup_audit_logger()
        self.app_logger = self._setup_app_logger()
        self.error_logger = self._setup_error_logger()
    
    def _setup_audit_logger(self) -> logging.Logger:
        logger = logging.getLogger("audit")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        if logger.handlers:
            return logger
        
        audit_file = self.log_dir / "audit.log"
        handler = TimedRotatingFileHandler(
            audit_file,
            when="midnight",
            interval=1,
            backupCount=90,
            encoding="utf-8"
        )
        
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_app_logger(self) -> logging.Logger:
        logger = logging.getLogger("app")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        if logger.handlers:
            return logger
        
        app_file = self.log_dir / "app.log"
        file_handler = RotatingFileHandler(
            app_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8"
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _setup_error_logger(self) -> logging.Logger:
        logger = logging.getLogger("error")
        logger.setLevel(logging.ERROR)
        logger.propagate = False
        
        if logger.handlers:
            return logger
        
        error_file = self.log_dir / "error.log"
        handler = RotatingFileHandler(
            error_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8"
        )
        
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(pathname)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def log_audit(
        self,
        action: str,
        entity: Optional[str] = None,
        user: Optional[str] = None,
        details: Optional[str] = None,
        status: str = "SUCCESS"
    ):
        parts = [f"ACTION={action}", f"STATUS={status}"]
        
        if entity:
            parts.append(f"ENTITY={entity}")
        if user:
            parts.append(f"USER={user}")
        if details:
            parts.append(f"DETAILS={details}")
        
        message = " | ".join(parts)
        self.audit_logger.info(message)
    
    def log_file_operation(
        self,
        operation: str,
        file_path: str,
        entity: str,
        user: Optional[str] = None,
        status: str = "SUCCESS"
    ):
        self.log_audit(
            action=f"FILE_{operation.upper()}",
            entity=entity,
            user=user,
            details=f"file={file_path}",
            status=status
        )
    
    def log_statement_generation(
        self,
        statement_type: str,
        entity: str,
        period: str,
        user: Optional[str] = None,
        status: str = "SUCCESS"
    ):
        self.log_audit(
            action=f"GENERATE_{statement_type.upper()}",
            entity=entity,
            user=user,
            details=f"period={period}",
            status=status
        )
    
    def log_validation(
        self,
        entity: str,
        validation_type: str,
        result: str,
        user: Optional[str] = None
    ):
        self.log_audit(
            action=f"VALIDATION_{validation_type.upper()}",
            entity=entity,
            user=user,
            details=f"result={result}",
            status="SUCCESS"
        )
    
    def log_ai_operation(
        self,
        operation: str,
        entity: str,
        details: Optional[str] = None,
        status: str = "SUCCESS"
    ):
        self.log_audit(
            action=f"AI_{operation.upper()}",
            entity=entity,
            details=details,
            status=status
        )


audit_logger = AuditLogger()
