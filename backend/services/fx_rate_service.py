"""Foreign exchange rate service with SAP + external fallback."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import requests

from backend.config.settings import settings
from backend.models.currency import FxConversionResult, FxRate

logger = logging.getLogger(__name__)


class FxRateService:
    """Fetch and cache FX rates from SAP (when available) or external sources."""

    def __init__(self, cache_hours: int = 24) -> None:
        self.cache_hours = cache_hours
        self.cache_file = settings.DATA_DIR / "fx_rates.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, dict] = self._load_cache()
        self._converter = None  # Lazy-loaded CurrencyConverter instance

    # ------------------------------------------------------------------ #
    # Cache helpers
    # ------------------------------------------------------------------ #
    def _load_cache(self) -> Dict[str, dict]:
        if not self.cache_file.exists():
            return {}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to read FX cache: %s", exc)
            return {}

    def _save_cache(self) -> None:
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, default=str)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to write FX cache: %s", exc)

    @staticmethod
    def _cache_key(base: str, target: str) -> str:
        return f"{base.upper()}->{target.upper()}"

    def _is_stale(self, entry: dict) -> bool:
        if not entry:
            return True
        try:
            refreshed = datetime.fromisoformat(entry.get("as_of"))
        except Exception:
            return True
        return datetime.utcnow() - refreshed > timedelta(hours=self.cache_hours)

    # ------------------------------------------------------------------ #
    # Fetchers
    # ------------------------------------------------------------------ #
    def _fetch_from_sap(self, base: str, target: str) -> Optional[FxRate]:
        """
        Placeholder for SAP rate fetch.
        Returns None when SAP is not reachable.
        """
        logger.info(
            "SAP FX source not configured or unreachable. Skipping SAP fetch for %s/%s.",
            base,
            target,
        )
        return None

    def _fetch_from_external(self, base: str, target: str) -> Optional[FxRate]:
        """
        Fetch from a public FX API (exchangerate.host) without static mappings.
        """
        url = f"https://api.exchangerate.host/latest?base={base.upper()}&symbols={target.upper()}"
        try:
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            payload = resp.json()
            rate_value = payload.get("rates", {}).get(target.upper())
            date_str = payload.get("date")
            if rate_value is None:
                logger.warning("No rate returned for %s/%s", base, target)
                return None
            as_of = (
                datetime.fromisoformat(date_str)
                if date_str
                else datetime.utcnow()
            )
            return FxRate(
                base_currency=base.upper(),
                target_currency=target.upper(),
                rate=float(rate_value),
                as_of=as_of,
                source="exchangerate.host",
            )
        except Exception as exc:
            logger.info("External FX fetch failed for %s/%s: %s", base, target, exc)
            return None

    def _fetch_from_currency_converter(self, base: str, target: str) -> Optional[FxRate]:
        """
        Fetch using the currencyconverter package (ECB data, offline-capable).
        """
        try:
            if self._converter is None:
                from currency_converter import CurrencyConverter

                # Initialize with cached ECB data; set fallback_on_wrong_date=True to avoid errors on missing dates
                self._converter = CurrencyConverter(fallback_on_wrong_date=True, fallback_on_missing_rate=True)

            rate_val = self._converter.convert(1, base.upper(), target.upper())
            last_update = getattr(self._converter, "last_update", None)
            as_of = last_update if isinstance(last_update, datetime) else datetime.utcnow()
            return FxRate(
                base_currency=base.upper(),
                target_currency=target.upper(),
                rate=float(rate_val),
                as_of=as_of,
                source="currencyconverter-ecb",
            )
        except Exception as exc:
            logger.warning("CurrencyConverter fallback failed for %s/%s: %s", base, target, exc)
            return None

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def get_rate(
        self, base: str, target: str, force_refresh: bool = False
    ) -> Optional[FxRate]:
        """Get a single FX rate with caching."""
        base = base.upper()
        target = target.upper()

        if base == target:
            now = datetime.utcnow()
            return FxRate(
                base_currency=base,
                target_currency=target,
                rate=1.0,
                as_of=now,
                source="identity",
            )

        key = self._cache_key(base, target)
        cached = self._cache.get(key)
        if cached and not force_refresh and not self._is_stale(cached):
            return FxRate(**cached)

        # Try SAP first, then external
        # Try SAP first, then local ECB cache (currencyconverter), then public API
        rate_obj = (
            self._fetch_from_sap(base, target)
            or self._fetch_from_currency_converter(base, target)
            or self._fetch_from_external(base, target)
        )
        if rate_obj:
            self._cache[key] = rate_obj.model_dump()
            self._save_cache()
            return rate_obj

        # Fallback to cached even if stale
        if cached:
            logger.warning(
                "Returning stale FX rate for %s/%s due to fetch failure.", base, target
            )
            return FxRate(**cached)
        return None

    def get_rates(
        self, base: str, targets: Iterable[str], force_refresh: bool = False
    ) -> List[FxRate]:
        """Get multiple FX rates."""
        results: List[FxRate] = []
        seen = set()
        for target in targets:
            normalized = target.upper()
            if normalized in seen:
                continue
            seen.add(normalized)
            rate = self.get_rate(base, normalized, force_refresh=force_refresh)
            if rate:
                results.append(rate)
        return results

    def convert(
        self, amount: float, base: str, targets: Iterable[str]
    ) -> List[FxConversionResult]:
        """Convert an amount into the provided targets."""
        conversions: List[FxConversionResult] = []
        for rate in self.get_rates(base, targets):
            conversions.append(
                FxConversionResult(
                    target_currency=rate.target_currency,
                    converted_amount=amount * rate.rate,
                    rate=rate.rate,
                    as_of=rate.as_of,
                    source=rate.source,
                )
            )
        return conversions
