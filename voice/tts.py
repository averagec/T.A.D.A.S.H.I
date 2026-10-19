"""
Text-to-Speech — Phase 2.

Options:
  - piper (fully local, fast, decent quality)
  - ElevenLabs API (cloud, excellent quality, costs money)

Interface is ready; implementation slots in without changing the orchestrator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class TTSProvider(ABC):
    """Base interface for text-to-speech providers."""

    @abstractmethod
    async def speak(self, text: str) -> bytes:
        """Convert text to audio bytes."""
        ...

    @abstractmethod
    async def stream_speak(self, text: str):
        """Yield audio chunks for streaming playback."""
        ...


class PiperTTS(TTSProvider):
    """Local TTS using Piper. Not yet implemented."""

    def __init__(self, voice: str = "en_US-ryan-medium"):
        self.voice = voice
        # TODO Phase 2: Initialize Piper

    async def speak(self, text: str) -> bytes:
        raise NotImplementedError("Phase 2 — install piper-tts and implement")

    async def stream_speak(self, text: str):
        raise NotImplementedError("Phase 2 — streaming TTS")


class ElevenLabsTTS(TTSProvider):
    """Cloud TTS using ElevenLabs. Not yet implemented."""

    def __init__(self, api_key: str, voice_id: str = ""):
        self.api_key = api_key
        self.voice_id = voice_id
        # TODO Phase 2: Initialize ElevenLabs client

    async def speak(self, text: str) -> bytes:
        raise NotImplementedError("Phase 2 — install elevenlabs SDK and implement")

    async def stream_speak(self, text: str):
        raise NotImplementedError("Phase 2 — streaming ElevenLabs")
