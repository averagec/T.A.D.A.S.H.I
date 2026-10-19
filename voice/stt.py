"""
Speech-to-Text — Phase 2.

Will use faster-whisper for local transcription.
Install: pip install faster-whisper

Interface is ready; implementation slots in without changing the orchestrator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class STTProvider(ABC):
    """Base interface for speech-to-text providers."""

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str:
        """Convert audio to text."""
        ...

    @abstractmethod
    async def stream_transcribe(self, audio_stream):
        """Yield partial transcriptions from a live audio stream."""
        ...


class WhisperSTT(STTProvider):
    """Local STT using faster-whisper. Not yet implemented."""

    def __init__(self, model_size: str = "base.en"):
        self.model_size = model_size
        # TODO Phase 2: Load the model
        # from faster_whisper import WhisperModel
        # self.model = WhisperModel(model_size, device="auto", compute_type="int8")

    async def transcribe(self, audio_bytes: bytes) -> str:
        raise NotImplementedError("Phase 2 — install faster-whisper and implement")

    async def stream_transcribe(self, audio_stream):
        raise NotImplementedError("Phase 2 — streaming transcription")
