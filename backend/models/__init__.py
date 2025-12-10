# ============================================================================
# FILE: src/models/__init__.py
# ============================================================================
"""Data models package."""

from .auth import TokenData  # NEW
from .auth import (
    LoginRequest,
    RefreshTokenRequest,
    Token,
    UserBase,
    UserCreate,
    UserInDB,
    UserResponse,
)
from .company import Company, CompanyWithCategories, NoteCategory
from .generation import (
    BatchGenerationRequest,
    BatchGenerationStatus,
    GenerationResponse,
    NoteGenerationRequest,
)
from .bs_schedule_finalyzer import BSScheduleGenerationResponse

__all__ = [
    "Company",
    "NoteCategory",
    "CompanyWithCategories",
    "NoteGenerationRequest",
    "BatchGenerationRequest",
    "GenerationResponse",
    "BatchGenerationStatus",

    # Auth models
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserInDB",
    "Token",
    "TokenData",
    "LoginRequest",
    "RefreshTokenRequest",
]
