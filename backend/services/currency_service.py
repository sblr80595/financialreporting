"""Currency configuration and mapping service."""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from backend.config.settings import settings
from backend.config.entities import EntityConfig
from backend.models.currency import CurrencyInfo

logger = logging.getLogger(__name__)


class CurrencyService:
    """Centralized currency mapping and lookup."""

    _CONFIG_FILENAME = "entity_currency_mapping.json"

    # Allow common aliases so lookups are resilient to spacing/case
    _ALIASES = {
        "everlife": "everlife_ph_holding",
        "everlife_ph": "everlife_ph_holding",
        "everlife_philippines": "everlife_ph_holding",
        "everlife_ph_holding": "everlife_ph_holding",
        "cpm_malaysia": "cpm",
        "cpm my": "cpm",
        "cpm-my": "cpm",
        "cpm_my": "cpm",
    }

    @classmethod
    @lru_cache(maxsize=1)
    def _load_config(cls) -> Dict:
        """Load currency config once and cache it."""
        config_path = settings.CONFIG_DIR / cls._CONFIG_FILENAME
        if not config_path.exists():
            logger.warning("Currency config not found at %s", config_path)
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:  # pragma: no cover - safety net
            logger.error("Failed to load currency config: %s", exc)
            return {}

    @classmethod
    def _normalize_entity(cls, entity: str) -> str:
        """Normalize entity name/code for lookup."""
        normalized = entity.strip().lower().replace(" ", "_")
        return cls._ALIASES.get(normalized, normalized)

    @classmethod
    def get_entity_currency(cls, entity: str) -> CurrencyInfo:
        """
        Get currency info for an entity. Defaults to INR when missing.
        """
        # Prefer the single entity config so adding an entity only requires one file change
        entity_currency = EntityConfig.get_currency_info(entity)
        if entity_currency:
            return CurrencyInfo(
                entity_name=entity_currency.get("entity_name", entity),
                default_currency=entity_currency.get("code", "INR"),
                currency_symbol=entity_currency.get("symbol", "₹"),
                currency_name=entity_currency.get("name", "Indian Rupee"),
                decimal_places=entity_currency.get("decimal_places", 2),
                format=entity_currency.get("format"),
            )

        config = cls._load_config()
        entities = config.get("entities", {})
        normalized = cls._normalize_entity(entity)

        # Try normalized key, then raw, then aliases again just in case
        entry = entities.get(normalized) or entities.get(entity) or entities.get(
            cls._ALIASES.get(normalized, normalized)
        )

        if not entry:
            logger.info(
                "Currency mapping not found for %s (normalized: %s). Falling back to INR.",
                entity,
                normalized,
            )
            return CurrencyInfo(
                entity_name=entity,
                default_currency="INR",
                currency_symbol="₹",
                currency_name="Indian Rupee",
                decimal_places=2,
                format="₹#,##,##0.00",
            )

        return CurrencyInfo(
            entity_name=entry.get("entity_name", entity),
            default_currency=entry.get("default_currency", "INR"),
            currency_symbol=entry.get("currency_symbol", "₹"),
            currency_name=entry.get("currency_name", "Indian Rupee"),
            decimal_places=entry.get("decimal_places", 2),
            format=entry.get("format"),
        )

    @classmethod
    def supported_currencies(cls) -> List[Dict]:
        """Return supported currency metadata."""
        config = cls._load_config()
        return config.get("supported_currencies", [])

    @classmethod
    def reporting_targets(cls, base_currency: str, preferred: Optional[List[str]] = None) -> List[str]:
        """
        Decide which reporting currencies to show above entity level.
        Always includes USD/INR unless they match base.
        """
        preferred_targets = preferred or ["USD", "INR"]
        unique: List[str] = []
        for code in preferred_targets:
            normalized = code.upper()
            if normalized != base_currency.upper() and normalized not in unique:
                unique.append(normalized)
        return unique

    @classmethod
    def refresh_config_cache(cls) -> None:
        """Clear cached config (used when config file changes)."""
        cls._load_config.cache_clear()
