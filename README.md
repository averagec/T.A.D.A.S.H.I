# JARVIS

Personal AI assistant — voice-enabled, tool-calling, memory-persistent.

## Quick Start

```bash
# 1. Clone / copy this directory
cd jarvis

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env — at minimum set ANTHROPIC_API_KEY

# 5. Run
python main.py
```

## Project Structure

```
jarvis/
├── main.py              # Entry point
├── config.py            # Configuration (.env reader)
├── core/
│   ├── orchestrator.py  # Main loop — input → brain → tools → output
│   ├── brain.py         # Claude API with tool-use loop
│   └── memory.py        # Persistent SQLite memory
├── tools/
│   ├── registry.py      # Tool base class + auto-discovery
│   ├── datetime_tool.py # Current time/date
│   ├── weather.py       # Weather via OpenWeatherMap
│   ├── system_info.py   # Local system information
│   └── memory_tool.py   # LLM-callable memory read/write
├── voice/               # Phase 2 — STT, TTS, wake word
├── scheduler/           # Phase 6 — proactive background checks
├── ROADMAP.md           # Full development plan
└── data/                # SQLite database (auto-created)
```

## Adding a New Tool

Drop a file in `tools/`, subclass `BaseTool`, decorate with `@register_tool`:

```python
from tools.registry import BaseTool, register_tool

@register_tool
class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"
    parameters = {
        "type": "object",
        "properties": {
            "arg": {"type": "string", "description": "An argument"}
        },
        "required": ["arg"]
    }

    async def execute(self, arg: str, **kwargs) -> str:
        return f"Did the thing with {arg}"
```

That's it. No config files, no manual registration. The orchestrator
auto-discovers it on startup.

## Commands

While running in text mode:

| Command    | Description                    |
|------------|--------------------------------|
| `/memory`  | Show all stored facts          |
| `/clear`   | Clear conversation context     |
| `/session` | Show session info              |
| `/help`    | List commands                  |
| `quit`     | End session (saves summary)    |

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full 6-phase development plan.
