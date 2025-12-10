"""
SAP B1 Connection - Configuration Management
============================================
Purpose: Centralized configuration management for SAP B1 API connections
Author: SAP Connection Module
Date: November 2025
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration manager for SAP B1 connection and settings."""
    
    def __init__(self, config_file: str = "config/sap_connect/config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to the configuration JSON file
        """
        self.config_file = config_file
        self.config = self._load_config()
        self._setup_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Return default configuration
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "sap_connection": {
                "service_layer_url": "https://vmsapb1han.centralindia.cloudapp.azure.com:50000/b1s/v1",
                "username": "U0036",
                "password": "Thl@369",
                "company_db": "THLMAIN",
                "verify_ssl": False
            },
            "date_range": {
                "start_date": "2024-04-01",
                "end_date": "2025-03-31"
            },
            "filters": {
                "related_bp_codes": ["BP001", "BP002"]
            },
            "api": {
                "timeout": 120,
                "max_retries": 3,
                "records_per_page": 1000
            },
            "paths": {
                "output_dir": "output",
                "financial_statements_dir": "output/financial_statements",
                "journal_entries_dir": "output/journal_entries",
                "invoices_dir": "output/invoices",
                "reports_dir": "output/reports",
                "logs_dir": "logs"
            },
            "external_services": {
                "anthropic_api_key": "YOUR_ANTHROPIC_API_KEY",
                "sap_help_url": "https://help.sap.com/doc/056f69366b5345a386bb8149f1700c19/10.0/en-US/Service%20Layer%20API%20Reference.html"
            }
        }
    
    def _setup_directories(self):
        """Create necessary directories if they don't exist."""
        for key, path in self.config.get("paths", {}).items():
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key using dot notation.
        
        Args:
            key: Configuration key (e.g., 'sap_connection.username')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def save(self):
        """Save current configuration to file."""
        Path(self.config_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def update(self, key: str, value: Any):
        """
        Update configuration value.
        
        Args:
            key: Configuration key using dot notation
            value: New value
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save()
    
    @property
    def sap_url(self) -> str:
        """Get SAP Service Layer URL."""
        return self.get('sap_connection.service_layer_url')
    
    @property
    def username(self) -> str:
        """Get SAP username."""
        return self.get('sap_connection.username')
    
    @property
    def password(self) -> str:
        """Get SAP password."""
        return self.get('sap_connection.password')
    
    @property
    def company_db(self) -> str:
        """Get SAP company database."""
        return self.get('sap_connection.company_db')
    
    @property
    def start_date(self) -> str:
        """Get start date for queries."""
        return self.get('date_range.start_date')
    
    @property
    def end_date(self) -> str:
        """Get end date for queries."""
        return self.get('date_range.end_date')
    
    @property
    def output_dir(self) -> str:
        """Get output directory path."""
        return self.get('paths.output_dir', 'output')
    
    def get_output_path(self, category: str, filename: str = None) -> str:
        """
        Get full output path for a specific category.
        
        Args:
            category: Output category (financial_statements, journal_entries, etc.)
            filename: Optional filename to append
            
        Returns:
            Full path to output file/directory
        """
        base_path = self.get(f'paths.{category}_dir', f'output/{category}')
        
        if filename:
            return os.path.join(base_path, filename)
        return base_path


# Global configuration instance
config = Config()
