"""
Centralized configuration â€” reads from .env, provides typed access.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).parent
load_dotenv(_PROJECT_ROOT / ".env")


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass(frozen=True)
class Config:
    # Core
    api_key: str = field(default_factory=lambda: _env("ANTHROPIC_API_KEY"))
    model: str = field(default_factory=lambda: _env("JARVIS_MODEL", "claude-haiku-4-5-20251001"))
    model_light: str = field(default_factory=lambda: _env("JARVIS_MODEL_LIGHT", "claude-haiku-4-5-20251001"))
    max_tokens: int = field(default_factory=lambda: int(_env("JARVIS_MAX_TOKENS", "2048")))

    # Persona
    name: str = field(default_factory=lambda: _env("JARVIS_NAME", "Jarvis"))
    wake_word: str = field(default_factory=lambda: _env("JARVIS_WAKE_WORD", "jarvis"))

    # Memory
    db_path: Path = field(default_factory=lambda: _PROJECT_ROOT / _env("JARVIS_DB_PATH", "data/jarvis.db"))

    # Voice
    stt_model: str = field(default_factory=lambda: _env("JARVIS_STT_MODEL", "base.en"))
    tts_voice: str = field(default_factory=lambda: _env("JARVIS_TTS_VOICE", "en_US-ryan-medium"))
    elevenlabs_key: str = field(default_factory=lambda: _env("ELEVENLABS_API_KEY"))

    # Tool keys
    openweather_key: str = field(default_factory=lambda: _env("OPENWEATHER_API_KEY"))
    brave_search_key: str = field(default_factory=lambda: _env("BRAVE_SEARCH_API_KEY"))
    home_assistant_url: str = field(default_factory=lambda: _env("HOME_ASSISTANT_URL"))
    home_assistant_token: str = field(default_factory=lambda: _env("HOME_ASSISTANT_TOKEN"))

    def validate(self) -> list[str]:
        """Return list of critical config issues."""
        issues = []
        if not self.api_key:
            issues.append("ANTHROPIC_API_KEY is not set")
        return issues


# Singleton
cfg = Config()

