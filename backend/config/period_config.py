# ============================================================================
# FILE: backend/config/period_config.py
# ============================================================================
"""
Centralized period configuration for dynamic period selection across all entities.
This allows setting the period once and applying it to all note generations.
"""

from typing import Dict, Optional
from pathlib import Path
import json
from datetime import datetime


class PeriodConfig:
    """Manages period configuration for financial statement generation."""
    
    # Default period mapping - maps common period names to column names
    DEFAULT_PERIOD_MAPPINGS = {
        "mar_2025": "Total Mar'25",
        "jun_2025": "Total June 25",
        "sep_2025": "Total Sep'25",
        "dec_2024": "Total Dec'24",
        "mar_2024": "Total Mar'24",
    }
    
    # Runtime period selection (can be set via API or config file)
    _current_period: Optional[str] = None
    _current_period_column: Optional[str] = None
    
    @classmethod
    def set_period(cls, period_key: str) -> str:
        """
        Set the current period for all generations.
        
        Args:
            period_key: Period identifier (e.g., 'mar_2025', 'jun_2025')
            
        Returns:
            The column name for the period
            
        Raises:
            ValueError: If period_key is not found in mappings
        """
        if period_key not in cls.DEFAULT_PERIOD_MAPPINGS:
            raise ValueError(
                f"Period '{period_key}' not found. Available periods: "
                f"{list(cls.DEFAULT_PERIOD_MAPPINGS.keys())}"
            )
        
        cls._current_period = period_key
        cls._current_period_column = cls.DEFAULT_PERIOD_MAPPINGS[period_key]
        
        print(f"✅ Period set to: {period_key} (Column: {cls._current_period_column})")
        return cls._current_period_column

    @classmethod
    def set_period_column(cls, column_name: str):
        """Directly set the current period column when a key mapping isn't available."""
        cls._current_period = cls._current_period or None
        cls._current_period_column = column_name
        print(f"✅ Period column set directly: {column_name}")
    
    @classmethod
    def get_current_period_column(cls, default: str = "Total Mar'25") -> str:
        """
        Get the currently active period column.
        
        Args:
            default: Default period column if none is set
            
        Returns:
            Current period column name or default
        """
        if cls._current_period_column:
            return cls._current_period_column
        
        # If no period is set, return default (only warn if default is not None)
        if default is not None:
            print(f"⚠️  No runtime period set, using default: {default}")
        return default
    
    @classmethod
    def get_current_period(cls) -> Optional[str]:
        """Get the currently active period key."""
        return cls._current_period
    
    @classmethod
    def add_custom_period(cls, period_key: str, column_name: str):
        """
        Add a custom period mapping.
        
        Args:
            period_key: Period identifier (e.g., 'custom_2025')
            column_name: Column name in CSV (e.g., "Total Custom'25")
        """
        cls.DEFAULT_PERIOD_MAPPINGS[period_key] = column_name
        print(f"✅ Added custom period: {period_key} -> {column_name}")
    
    @classmethod
    def get_available_periods(cls) -> Dict[str, str]:
        """Get all available period mappings."""
        return cls.DEFAULT_PERIOD_MAPPINGS.copy()
    
    @classmethod
    def reset(cls):
        """Reset period configuration to None."""
        cls._current_period = None
        cls._current_period_column = None
        print("🔄 Period configuration reset")


# Singleton instance
period_config = PeriodConfig()
