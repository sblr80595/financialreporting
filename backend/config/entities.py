"""
Entity Configuration
====================

Centralized entity definitions for consistent entity naming across the application.
This now loads from config/entities.json so new entities only need to be added once.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from backend.config.settings import settings


def _load_entities_from_file() -> List[Dict[str, str]]:
    """Load entities from the shared JSON config."""
    config_path = Path(settings.CONFIG_DIR) / "entities.json"
    if not config_path.exists():
        # Fallback to previous hardcoded list to avoid crashing if file is missing
        return [
            {
                "code": "cpm",
                "name": "CPM Malaysia",
                "short_code": "cpm",
                "description": "CPM Malaysia entity",
                "currency": {"code": "MYR", "symbol": "RM"},
            },
            {
                "code": "analisa_resource",
                "name": "Analisa Resource",
                "short_code": "analisa_resource",
                "description": "Analisa Resource entity",
                "currency": {"code": "MYR", "symbol": "RM"},
            },
            {
                "code": "neoscience_sdn",
                "name": "Neoscience SDN",
                "short_code": "neoscience_sdn",
                "description": "Neoscience SDN entity",
                "currency": {"code": "MYR", "symbol": "RM"},
            },
            {
                "code": "lifeline_holdings",
                "name": "Lifeline Holdings",
                "short_code": "lifeline_holdings",
                "description": "Lifeline Holdings entity",
                "currency": {"code": "PHP", "symbol": "₱"},
            },
            {
                "code": "lifeline_diagnostics",
                "name": "Lifeline Diagnostics",
                "short_code": "lifeline_diagnostics",
                "description": "Lifeline Diagnostics entity",
                "currency": {"code": "PHP", "symbol": "₱"},
            },
            {
                "code": "everlife_ph_holding",
                "name": "Everlife Ph Holding",
                "short_code": "everlife_ph_holding",
                "description": "Everlife Ph Holding entity",
                "currency": {"code": "PHP", "symbol": "₱"},
            },
            {
                "code": "ttpl_fs",
                "name": "Translumina Therapeutics Private Limited",
                "short_code": "ttpl_fs",
                "description": "Translumina Therapeutics Private Limited",
                "currency": {"code": "INR", "symbol": "₹"},
            },
            {
                "code": "cpc_diagnostics_india",
                "name": "CPC (CPC Diagnostics Pvt. Ltd India )",
                "short_code": "cpc_diagnostics_india",
                "description": "CPC (CPC Diagnostics Pvt. Ltd India )",
                "currency": {"code": "INR", "symbol": "₹"},
            },
            {
                "code": "hausen",
                "name": "Hausen",
                "short_code": "hausen",
                "description": "Hausen entity",
                "currency": {"code": "EUR", "symbol": "€"},
            },
            {
                "code": "integris",
                "name": "Integris",
                "short_code": "integris",
                "description": "Integris entity",
                "currency": {"code": "USD", "symbol": "$"},
            },
        ]

    with config_path.open(encoding="utf-8") as f:
        payload = json.load(f)
        entities = payload.get("entities", [])
        # Normalize keys
        normalized: List[Dict[str, str]] = []
        for entity in entities:
            entry = {
                "code": entity.get("code", "").lower(),
                "name": entity.get("name", ""),
                "short_code": entity.get("short_code", entity.get("code", "")).lower(),
                "description": entity.get("description", ""),
            }
            currency = entity.get("currency") or {}
            if currency:
                entry["currency"] = {
                    "code": currency.get("code"),
                    "symbol": currency.get("symbol"),
                    "name": currency.get("name"),
                    "decimal_places": currency.get("decimal_places"),
                    "format": currency.get("format"),
                }
            normalized.append(entry)
        return normalized


# Master entity configuration (loaded once at import)
ENTITIES = _load_entities_from_file()

class EntityConfig:
    """Entity configuration manager"""

    @staticmethod
    def get_all_entities() -> List[Dict[str, str]]:
        """Get all configured entities"""
        return ENTITIES.copy()

    @staticmethod
    def get_entity_by_code(code: str) -> Optional[Dict[str, str]]:
        """Get entity by its code"""
        code_lower = code.lower()
        for entity in ENTITIES:
            if entity["code"] == code_lower:
                return entity.copy()
        return None

    @staticmethod
    def get_entity_by_short_code(short_code: str) -> Optional[Dict[str, str]]:
        """Get entity by its short code"""
        for entity in ENTITIES:
            if entity.get("short_code") == short_code:
                return entity.copy()
        return None

    @staticmethod
    def get_entity_name(code: str) -> str:
        """Get entity display name by code"""
        entity = EntityConfig.get_entity_by_code(code)
        return entity["name"] if entity else code

    @staticmethod
    def get_entity_code(short_code: str) -> str:
        """Get entity code from short code"""
        entity = EntityConfig.get_entity_by_short_code(short_code)
        return entity["code"] if entity else short_code.lower()

    @staticmethod
    def get_short_code(code: str) -> str:
        """Get short code from entity code"""
        entity = EntityConfig.get_entity_by_code(code)
        return entity.get("short_code", code.upper()) if entity else code.upper()

    @staticmethod
    def is_valid_entity(code: str) -> bool:
        """Check if entity code is valid"""
        return EntityConfig.get_entity_by_code(code) is not None

    @staticmethod
    def get_currency_info(code: str) -> Optional[Dict[str, str]]:
        """Return currency metadata for an entity if configured."""
        entity = EntityConfig.get_entity_by_code(code)
        if not entity:
            return None
        currency = entity.get("currency") or {}
        currency.setdefault("entity_name", entity.get("name", code))
        return currency

    @staticmethod
    def normalize_entity_code(code_or_name: str) -> str:
        """
        Normalize entity code/name/short_code to standard internal code.
        Handles various input formats.
        """
        input_lower = code_or_name.lower().strip()

        # Handle legacy entity codes (for backward compatibility)
        legacy_mappings = {
            "cpm_my": "cpm",
            "cpm-my": "cpm",
            "cpmmy": "cpm",
        }
        if input_lower in legacy_mappings:
            return legacy_mappings[input_lower]

        # Check direct code match
        for entity in ENTITIES:
            if entity["code"] == input_lower:
                return entity["code"]

        # Check short code match
        for entity in ENTITIES:
            if entity.get("short_code", "").lower() == input_lower:
                return entity["code"]

        # Check name match (case-insensitive)
        for entity in ENTITIES:
            if entity["name"].lower() == input_lower:
                return entity["code"]

        # Default: return lowercase version
        return input_lower


# Export entity list for backward compatibility
def get_entities_list() -> List[Dict[str, str]]:
    """Get list of all entities"""
    return EntityConfig.get_all_entities()


# Export mapping dictionaries for backward compatibility
ENTITY_CODE_TO_NAME = {e["code"]: e["name"] for e in ENTITIES}
ENTITY_SHORT_TO_CODE = {e.get("short_code"): e["code"] for e in ENTITIES if e.get("short_code")}
ENTITY_CODE_TO_SHORT = {e["code"]: e.get("short_code") for e in ENTITIES if e.get("short_code")}
