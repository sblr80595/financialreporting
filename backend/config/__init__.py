# ============================================================================
# FILE: src/config/__init__.py
# ============================================================================
"""Configuration package."""

from .notes_prompts import BALANCE_SHEET_TEMPLATE, CASH_FLOW_TEMPLATE, PROFIT_LOSS_TEMPLATE
from .settings import settings

__all__ = [
    "settings",
    "PROFIT_LOSS_TEMPLATE",
    "BALANCE_SHEET_TEMPLATE",
    "CASH_FLOW_TEMPLATE",
]
