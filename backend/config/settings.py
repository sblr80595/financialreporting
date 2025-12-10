# ============================================================================
# FILE: src/config/settings.py
# ============================================================================
"""Application settings and environment configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "false").lower() == "true"
    API_VERSION: str = "2.0.0"

    # LLM Provider Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "anthropic").lower()
    # Options: "anthropic" or "gemini"

    # Anthropic AI Settings
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

    # Gemini AI Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

    # Directory Settings
    CONFIG_DIR: Path = Path(os.getenv("CONFIG_DIR", "config"))
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", "data"))
    CSV_DIR: Path = Path(os.getenv("CSV_DIR", "trialbalance"))
    REPORTS_DIR: Path = Path("reports")

    # Entity-based directory helper methods
    def get_entity_input_dir(self, entity: str) -> Path:
        """Get input directory for a specific entity."""
        return self.DATA_DIR / entity / "input"

    def get_entity_output_dir(self, entity: str) -> Path:
        """Get output directory for a specific entity."""
        return self.DATA_DIR / entity / "output"

    def get_entity_generated_notes_dir(self, entity: str) -> Path:
        """Get generated notes directory for a specific entity."""
        return self.DATA_DIR / entity / "output" / "generated_notes"

    # JWT Authentication Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )

    # Admin User
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@company.com")

    # CORS Settings
    CORS_ORIGINS: list = ["*"]

    def validate_llm_config(self) -> tuple[bool, str]:
        """
        Validate LLM configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.LLM_PROVIDER not in ["anthropic", "gemini"]:
            return False, f"Invalid LLM_PROVIDER: {self.LLM_PROVIDER}. Must be 'anthropic' or 'gemini'"
        
        if self.LLM_PROVIDER == "anthropic":
            if not self.ANTHROPIC_API_KEY:
                return False, "ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'anthropic'"
        elif self.LLM_PROVIDER == "gemini":
            if not self.GEMINI_API_KEY:
                return False, "GEMINI_API_KEY is required when LLM_PROVIDER is 'gemini'"
        
        return True, ""

    model_config = {
        "extra": "ignore",  # Ignore extra fields from .env
        "env_file": ".env",
        "case_sensitive": True
    }


settings = Settings()

# Validate LLM configuration on startup
is_valid, error_msg = settings.validate_llm_config()
if not is_valid:
    print(f"⚠️  LLM Configuration Error: {error_msg}")