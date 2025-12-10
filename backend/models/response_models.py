"""
Pydantic models for API responses
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ProcessingStatus(BaseModel):
    """Model for tracking processing status"""
    id: str
    status: str  # started, processing, completed, failed
    progress: int  # 0-100
    message: str
    entity: str
    start_time: str
    end_time: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class FileUploadResponse(BaseModel):
    """Response model for file upload operations"""
    success: bool
    message: str
    file_path: str
    validation_result: Optional[Dict[str, Any]] = None


class ProcessingResult(BaseModel):
    """Detailed processing result with statistics"""
    success: bool
    message: str
    output_files: List[str]
    execution_time: float
    adjustments: List[Dict[str, Any]]


class ValidationResult(BaseModel):
    """Result model for validation operations"""
    success: bool
    message: str
    rules_passed: int
    rules_failed: int
    total_rules: int
    violations: List[Dict[str, Any]]
    report_path: str


class MappingResult(BaseModel):
    """Result model for mapping operations"""
    success: bool
    message: str
    total_records: int
    mapped_records: int
    unmapped_records: int
    output_path: str


class EntityInfo(BaseModel):
    """Information about an entity"""
    code: str
    name: str


class FileInfo(BaseModel):
    """Information about an uploaded file"""
    filename: str
    path: str
    size: int
    upload_time: str


class AdjustmentConfig(BaseModel):
    """Configuration for adjustment operations"""
    id: int
    name: str
    key: str
    icon: str
    prompt_file: str
    source_files: List[str]
    output_file: str


class ValidationRule(BaseModel):
    """Validation rule with compliance status"""
    name: str
    description: str
    is_compliant: bool
    details: str
    violations: List[str]


class ValidationAcknowledgment(BaseModel):
    """Model for acknowledging validation exceptions"""
    entity: str
    failed_rules: List[str]
    acknowledgment_note: str
    acknowledged_by: str
    acknowledged_at: str


class FinancialStatement(BaseModel):
    """Financial statement model"""
    type: str  # pnl, balance_sheet, cash_flow
    name: str
    file_path: str
    generated_at: str
