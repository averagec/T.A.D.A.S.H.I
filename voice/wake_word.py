"""
Wake Word Detection — Phase 3.

Options:
  - openWakeWord (open source, customizable)
  - Porcupine (Picovoice, free tier available)

Listens continuously on the mic and fires a callback when the wake word is detected.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Awaitable


class WakeWordDetector(ABC):
    """Base interface for wake word detection."""

    @abstractmethod
    async def listen(self, on_wake: Callable[[], Awaitable[None]]) -> None:
        """
        Listen continuously for the wake word.
        Call on_wake() when detected, then resume listening.
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop listening."""
        ...


class OpenWakeWordDetector(WakeWordDetector):
    """Wake word detection using openWakeWord. Not yet implemented."""

    def __init__(self, wake_word: str = "jarvis"):
        self.wake_word = wake_word
        # TODO Phase 3: Load openWakeWord model

    async def listen(self, on_wake: Callable[[], Awaitable[None]]) -> None:
        raise NotImplementedError("Phase 3 — install openwakeword and implement")

    def stop(self) -> None:
        raise NotImplementedError("Phase 3")
