# ============================================================================
# FILE: backend/routes/__init__.py
# ============================================================================
"""Routes package."""

from fastapi import APIRouter

from backend.routes.pl_statement_routes import router as pl_router

# from .auth_routes import router as auth_router  # Disabled to avoid bcrypt issues
from .company_routes import router as company_router
from .generation_routes import router as generation_router
from .pl_statement_routes import router as pl_statement_routes

# Main API router
api_router = APIRouter()

# Auth routes (disabled to avoid bcrypt issues)
# api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Public routes (authentication disabled)
api_router.include_router(company_router, tags=["Companies"])
api_router.include_router(generation_router, tags=["Note Generation"])
api_router.include_router(pl_statement_routes, tags=["Statement Generator"])
api_router.include_router(pl_router, tags=["P&L Statement"])
__all__ = ["api_router"]
