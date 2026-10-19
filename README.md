<div align="center">

# T.A.D.A.S.H.I.

**T**ool-**A**ugmented **D**ynamic **A**utonomous **S**elf-**H**ealing **I**ntelligence

A self-evolving personal AI assistant with voice control, system-level access, and the ability to modify its own source code at runtime.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Claude API](https://img.shields.io/badge/LLM-Claude%20API-blueviolet.svg)](https://docs.anthropic.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## What is Tadashi?

Tadashi is an AI assistant that doesn't just answer questions — it **acts**. It controls your computer, manages files, installs packages, and when it encounters something it can't do, it **writes the code to teach itself how**.

Built from scratch with raw Python and the Anthropic SDK — no LangChain, no bloated frameworks, no abstractions you don't own.

### Key Highlights

- **Self-Evolving** — Tadashi reads, writes, and edits its own source code at runtime. Ask it to gain a new capability and it builds it on the spot.
- **Voice-First** — Full duplex voice conversation with interrupt support. Say "hold on" mid-response and it stops, listens, and recalibrates.
- **System-Level Control** — Opens apps, manages files, adjusts system settings, downloads files, runs arbitrary commands on your machine.
- **Persistent Memory** — Remembers facts, preferences, and conversation context across sessions via SQLite.
- **Token-Efficient** — Prompt caching, model routing (Haiku for speed, Sonnet for depth), local intent matching, and automatic history compression keep costs minimal.
- **Zero-Config Tools** — Drop a Python file in `tools/`, use the `@register_tool` decorator, and it's live on next startup. No config files, no manual wiring.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     main.py                         │
│              (entry point, --voice flag)             │
└──────────────────────┬──────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │      Orchestrator       │
          │  • Local intent match   │
          │  • History compression  │
          │  • Session management   │
          └────────────┬────────────┘
                       │
         ┌─────────────▼──────────────┐
         │          Brain             │
         │  • Claude API (tool use)   │
         │  • Prompt caching          │
         │  • Model routing           │
         └─────┬───────────────┬──────┘
               │               │
    ┌──────────▼──────┐  ┌─────▼──────────┐
    │  Tool Registry  │  │  Voice Engine   │
    │  (auto-discover)│  │  • STT (Google) │
    │                 │  │  • TTS (Edge)   │
    │  8 self-modify  │  │  • Interrupt    │
    │  tools + more   │  │  • Background   │
    └─────────────────┘  │    listener     │
                         └────────────────┘
```

---

## Features in Detail

### Self-Modification Engine

Tadashi has 8 core self-modification tools that give it full autonomy over its own codebase:

| Tool | What it does |
|------|-------------|
| `read_source` | Reads any of its own source files |
| `write_source` | Creates or overwrites source files |
| `edit_source` | Targeted find-and-replace on its own code |
| `install_package` | Installs Python packages via pip |
| `run_command` | Executes any shell/PowerShell command |
| `control_app` | Opens, closes, or checks running applications |
| `manage_files` | Full file operations — read, write, search, copy, move, delete |
| `download_file` | Downloads files from the internet |

> Ask Tadashi to do something it can't? It reads its own code, figures out what's missing, writes the fix, and executes — all in one conversation turn.

### Voice Interface

- **Speech-to-Text**: Google Speech Recognition (free, no API key)
- **Text-to-Speech**: Microsoft Edge neural voices via `edge-tts`
- **Concurrent Listening**: Background listener thread always running
- **Smart Interrupts**: Fast mode (0.5s timeout) while Tadashi is speaking, patient mode (2s pause) while waiting for you
- **Natural Conversation**: Configurable pause thresholds so it waits for you to finish your thought

### Token Optimization

Running an AI assistant 24/7 can get expensive. Tadashi minimizes costs with a multi-layer approach:

1. **Local Intent Matching** — Greetings, time checks, and simple queries handled with zero API calls
2. **Haiku-First Routing** — Uses Claude Haiku by default (25x cheaper than Sonnet), escalating only when needed
3. **Prompt Caching** — System prompt cached via `cache_control: ephemeral` for 90% discount on repeated context
4. **History Compression** — After 20 messages, older turns are summarized by Haiku and replaced with the summary

### Persistent Memory

SQLite-backed storage with three tables:
- **Facts** — Key-value pairs for things Tadashi should remember about you
- **History** — Full conversation logs per session
- **Summaries** — Compressed session summaries for long-term context

Memory is injected into the system prompt so Tadashi always knows who you are and what you've told it.

---

## Quick Start

### Prerequisites

- Python 3.10+
- Windows 10/11 (PowerShell integration; Linux/macOS support planned)
- [Anthropic API key](https://console.anthropic.com/)

### Installation

```bash
# Clone the repo
git clone https://github.com/averagec/T.A.D.A.S.H.I.git
cd T.A.D.A.S.H.I

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux

# Edit .env and add your ANTHROPIC_API_KEY
```

### Run

```bash
# Text mode
python main.py

# Voice mode
python main.py --voice
```

On first voice run, Tadashi auto-installs the voice packages (`SpeechRecognition`, `PyAudio`, `edge-tts`, `pygame`).

---

## Configuration

All configuration is managed through `.env`. See [`.env.example`](.env.example) for all available keys:

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Claude API key | *required* |
| `TADASHI_MODEL` | Primary model | `claude-sonnet-4-6` |
| `TADASHI_MODEL_LIGHT` | Fast/cheap model | `claude-haiku-4-5-20251001` |
| `TADASHI_NAME` | Assistant name | `Tadashi` |
| `TADASHI_TTS_VOICE` | TTS voice ID | `en-US-ChristopherNeural` |
| `OPENWEATHER_API_KEY` | Weather tool API key | *optional* |

---

## Project Structure

```
T.A.D.A.S.H.I/
├── main.py                 # Entry point (--voice / -v flag)
├── config.py               # Centralized .env configuration
├── core/
│   ├── orchestrator.py     # Main loop — routing, compression, sessions
│   ├── brain.py            # Claude API — tool use, caching, model routing
│   └── memory.py           # SQLite persistent storage
├── tools/
│   ├── registry.py         # BaseTool ABC + auto-discovery engine
│   ├── self_modify.py      # 8 self-evolution tools (read/write/edit code)
│   ├── persona_tool.py     # Runtime personality modification
│   ├── system_control.py   # OS-level settings (volume, brightness)
│   ├── system_info.py      # System diagnostics (CPU, memory, battery)
│   ├── datetime_tool.py    # Time/date with timezone support
│   ├── weather.py          # OpenWeatherMap integration
│   └── memory_tool.py      # LLM-callable memory read/write
├── voice/
│   ├── engine.py           # Voice I/O — STT, TTS, interrupt handling
│   ├── stt.py              # Speech-to-text adapter
│   ├── tts.py              # Text-to-speech adapter
│   └── wake_word.py        # Wake word detection (Phase 3)
├── scheduler/
│   └── proactive.py        # Background task scheduler (Phase 6)
├── requirements.txt        # Dependencies
├── .env.example            # Configuration template
└── ROADMAP.md              # 6-phase development plan
```

---

## Adding Custom Tools

The tool system uses decorator-based auto-discovery. Create a file in `tools/`:

```python
from tools.registry import BaseTool, register_tool

@register_tool
class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to look up"}
        },
        "required": ["query"]
    }

    async def execute(self, query: str, **kwargs) -> str:
        # Your logic here
        return f"Result for: {query}"
```

That's it — Tadashi finds it automatically on next startup.

---

## CLI Commands

In text mode, these slash commands are available:

| Command | Description |
|---------|-------------|
| `/memory` | Display all stored facts |
| `/clear` | Clear conversation history |
| `/session` | Show current session info |
| `/help` | List available commands |
| `quit` | End session (auto-saves summary) |

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full 6-phase plan:

1. ✅ **Core Intelligence** — Orchestrator, tool calling, memory, CLI
2. ✅ **Voice Interface** — STT, TTS, concurrent listening, interrupts
3. 🔲 **Always-On Presence** — Wake word, background daemon, state machine
4. 🔲 **Tool Expansion** — Calendar, email, smart home, web search, music
5. 🔲 **Advanced Memory** — Vector search, user profiling, context-aware responses
6. 🔲 **Proactive Intelligence** — Background monitoring, briefings, alerts

---

## Design Philosophy

> **No frameworks for the sake of frameworks.** Raw Python + asyncio + Anthropic SDK. Every line is yours.

> **Tools are plugins.** One decorator, one file, zero config.

> **The AI owns itself.** Tadashi can read, modify, and extend its own codebase. It's not a chatbot — it's a self-improving system.

> **Voice is a transport.** The orchestrator works identically whether input comes from keyboard or microphone.

> **Fail gracefully.** If a tool errors, Tadashi says so and moves on. No silent failures.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ / asyncio |
| LLM | Claude API (Anthropic) |
| Speech-to-Text | Google Speech Recognition |
| Text-to-Speech | Microsoft Edge TTS (neural) |
| Audio Playback | pygame |
| Database | SQLite |
| System Control | PowerShell / nircmd |
| HTTP Client | httpx |

---

## License

MIT — do whatever you want with it.

---

<div align="center">

*Built from scratch. No LangChain. No abstractions. Just raw intelligence.*

</div>
