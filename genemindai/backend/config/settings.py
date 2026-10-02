"""
Configuration and settings management for GeneMindAI backend.

Loads environment variables from .env securely on the server-side,
ensuring API keys and secrets remain protected from frontend exposure.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# Path to project root
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


def _load_env_file(filepath: Path) -> None:
    """Parse key=value pairs from a local .env file into os.environ."""
    if not filepath.is_file():
        return

    try:
        content = filepath.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            os.environ.setdefault(key, val)
    except Exception as exc:
        print(f"Warning: Failed to parse .env file at {filepath}: {exc}")


# Load .env file automatically
_load_env_file(PROJECT_ROOT / ".env")


class Settings:
    """Server-side settings container."""

    def __init__(self) -> None:
        self.project_root: Path = PROJECT_ROOT
        self.hatchable_api_key: Optional[str] = os.environ.get("HATCHABLE_API_KEY")
        self.hatchable_mcp_url: str = os.environ.get(
            "HATCHABLE_MCP_URL", "https://hatchable.com/mcp"
        )

    @property
    def is_hatchable_configured(self) -> bool:
        """Return True if a Hatchable API key is present."""
        return bool(self.hatchable_api_key and self.hatchable_api_key.strip())

    def get_masked_api_key(self) -> Optional[str]:
        """
        Return a safely masked representation of the API key for logging.

        Example: 'hb_SST...AbjaD'
        """
        if not self.hatchable_api_key:
            return None
        key = self.hatchable_api_key.strip()
        if len(key) <= 8:
            return "***"
        return f"{key[:6]}...{key[-5:]}"


# Global settings singleton
settings = Settings()
