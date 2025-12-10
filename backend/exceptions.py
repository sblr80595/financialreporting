from typing import Any, Dict, Optional
from fastapi import status


class FinancialReportingException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(FinancialReportingException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class EntityNotFoundException(FinancialReportingException):
    def __init__(self, entity: str):
        super().__init__(
            message=f"Entity '{entity}' not found or not configured",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ENTITY_NOT_FOUND",
            details={"entity": entity}
        )


class FileNotFoundException(FinancialReportingException):
    def __init__(self, file_path: str, file_type: str = "file"):
        super().__init__(
            message=f"{file_type.capitalize()} not found: {file_path}",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="FILE_NOT_FOUND",
            details={"file_path": file_path, "file_type": file_type}
        )


class FileProcessingException(FinancialReportingException):
    def __init__(self, message: str, file_path: str, details: Optional[Dict[str, Any]] = None):
        error_details = {"file_path": file_path}
        if details:
            error_details.update(details)
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="FILE_PROCESSING_ERROR",
            details=error_details
        )


class TrialBalanceException(FinancialReportingException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="TRIAL_BALANCE_ERROR",
            details=details
        )


class AIProcessingException(FinancialReportingException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="AI_PROCESSING_ERROR",
            details=details
        )


class ConfigurationException(FinancialReportingException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CONFIGURATION_ERROR",
            details=details
        )


class StatementGenerationException(FinancialReportingException):
    def __init__(self, statement_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        error_details = {"statement_type": statement_type}
        if details:
            error_details.update(details)
        super().__init__(
            message=f"Failed to generate {statement_type}: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="STATEMENT_GENERATION_ERROR",
            details=error_details
        )


class DataIntegrityException(FinancialReportingException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="DATA_INTEGRITY_ERROR",
            details=details
        )


class AuthenticationException(FinancialReportingException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationException(FinancialReportingException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR"
        )
