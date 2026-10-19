"""
Proactive Intelligence — Phase 6.

Background scheduler that periodically checks various sources
and decides whether to surface information to the user.

Architecture:
  - Runs as an async background task alongside the main loop
  - Each "check" is a registered function (calendar, weather, email, etc.)
  - Results are scored for relevance/urgency
  - Only surfaces things above a threshold
  - User can tune aggressiveness via feedback
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Awaitable


@dataclass
class Alert:
    """A proactive notification candidate."""
    source: str          # "calendar", "weather", "email", etc.
    message: str         # Human-readable alert
    priority: float      # 0.0 (ignore) to 1.0 (interrupt immediately)
    context: dict = None # Extra data for the LLM to use


class ProactiveCheck(ABC):
    """Base class for background checks."""

    name: str = ""
    interval_seconds: int = 300  # How often to run (default: 5 min)

    @abstractmethod
    async def check(self) -> Alert | None:
        """Run the check and return an Alert if something is noteworthy."""
        ...


class Scheduler:
    """Manages and runs proactive checks. Not yet implemented."""

    def __init__(self) -> None:
        self._checks: list[ProactiveCheck] = []
        self._running = False
        self._alert_callback: Callable[[Alert], Awaitable[None]] | None = None

    def register_check(self, check: ProactiveCheck) -> None:
        self._checks.append(check)

    def set_alert_callback(self, callback: Callable[[Alert], Awaitable[None]]) -> None:
        self._alert_callback = callback

    async def start(self) -> None:
        """Start all background checks. Phase 6."""
        raise NotImplementedError("Phase 6 — proactive scheduling")

    def stop(self) -> None:
        self._running = False
