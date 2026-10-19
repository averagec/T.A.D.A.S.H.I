#!/usr/bin/env python3
"""
TADASHI — Personal AI Assistant

Usage:
    python main.py          # Text mode
    python main.py --voice  # Voice mode
"""

import asyncio
import sys

from config import cfg
from core.orchestrator import Orchestrator


def preflight() -> None:
    issues = cfg.validate()
    if issues:
        print("\n  ⚠  Configuration issues:\n")
        for issue in issues:
            print(f"    • {issue}")
        print("\n  Copy .env.example to .env and fill in your values.\n")
        sys.exit(1)


async def main() -> None:
    preflight()

    voice_mode = "--voice" in sys.argv or "-v" in sys.argv

    if voice_mode:
        try:
            import speech_recognition
            import edge_tts
            import pygame
        except ImportError as e:
            print(f"\n  Voice mode requires extra packages. Installing...\n")
            import subprocess
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "SpeechRecognition", "PyAudio", "edge-tts", "pygame",
            ])
            print("\n  Packages installed. Run the command again.\n")
            sys.exit(0)

    orchestrator = Orchestrator()
    await orchestrator.start(voice_mode=voice_mode)


if __name__ == "__main__":
    asyncio.run(main())