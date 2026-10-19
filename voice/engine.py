"""
Voice Engine — concurrent listen + speak with interrupt support.

Always listening. If you talk while Tadashi is speaking, it stops
and processes your new input. Like talking to a real person.
"""

from __future__ import annotations

import asyncio
import threading
import queue
import uuid
import tempfile
from pathlib import Path

import speech_recognition as sr
import edge_tts
import pygame


DEFAULT_VOICE = "en-US-ChristopherNeural"


class VoiceEngine:
    def __init__(self, voice: str = DEFAULT_VOICE) -> None:
        self.voice = voice
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self._temp_dir = Path(tempfile.mkdtemp(prefix="tadashi_voice_"))

        pygame.mixer.init()
        pygame.mixer.music.set_volume(0.7)

        # Shared state
        self._is_speaking = False
        self._interrupted = False
        self._input_queue: queue.Queue[str] = queue.Queue()
        self._stop_listening = False

        # Calibrate mic
        self.recognizer.pause_threshold = 2.0      # seconds of silence before "done" (default 0.8)
        self.recognizer.phrase_threshold = 0.5      # min seconds to count as speech (default 0.3)
        self.recognizer.non_speaking_duration = 1.5  # silence padding (default 0.5)
        print("  Calibrating microphone...", flush=True)
                # Give more time to finish sentences
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("  Microphone ready.", flush=True)

    def start_listening(self) -> None:
        """Start background listening thread — always on."""
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()

    def _listen_loop(self) -> None:
        """Continuously listen for speech in the background."""
        while not self._stop_listening:
            try:
                with self.microphone as source:
                    if self._is_speaking:
                        # INTERRUPT MODE: check for any sound quickly
                        try:
                            audio = self.recognizer.listen(source, timeout=0.5, phrase_time_limit=10)
                            self._interrupted = True
                            self.stop_speaking()
                            # Transcribe what they said
                            try:
                                text = self.recognizer.recognize_google(audio)
                                if text and text.strip():
                                    print(f"  You: {text}", flush=True)
                                    self._input_queue.put(text)
                            except sr.UnknownValueError:
                                pass
                            except sr.RequestError:
                                pass
                        except sr.WaitTimeoutError:
                            continue
                    else:
                        # NORMAL MODE: patient listening
                        try:
                            audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=30)
                        except sr.WaitTimeoutError:
                            continue

                        try:
                            text = self.recognizer.recognize_google(audio)
                            if text and text.strip():
                                print(f"  You: {text}", flush=True)
                                self._input_queue.put(text)
                        except sr.UnknownValueError:
                            pass
                        except sr.RequestError as e:
                            print(f"  Transcription error: {e}", flush=True)

            except Exception as e:
                print(f"  Listen error: {e}", flush=True)
                continue

    async def get_input(self) -> str:
        """Wait for the next user input from the background listener."""
        while True:
            try:
                text = self._input_queue.get_nowait()
                return text
            except queue.Empty:
                await asyncio.sleep(0.1)

    def was_interrupted(self) -> bool:
        """Check if speech was interrupted and reset flag."""
        if self._interrupted:
            self._interrupted = False
            return True
        return False

    async def speak(self, text: str) -> None:
        """Speak text. Can be interrupted by user talking."""
        if not text.strip():
            return

        try:
            audio_file = self._temp_dir / f"response_{uuid.uuid4().hex[:8]}.mp3"

            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(str(audio_file))

            self._is_speaking = True
            self._interrupted = False
            self._play_audio(str(audio_file))
            self._is_speaking = False

        except Exception as e:
            self._is_speaking = False
            print(f"  TTS error: {e}", flush=True)

    def _play_audio(self, file_path: str) -> None:
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if self._interrupted:
                    pygame.mixer.music.stop()
                    break
                pygame.time.wait(50)

            pygame.mixer.music.unload()
        except Exception as e:
            print(f"  Playback error: {e}", flush=True)

    def stop_speaking(self) -> None:
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def cleanup(self) -> None:
        self._stop_listening = True
        try:
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            pygame.mixer.quit()
        except Exception:
            pass