# JARVIS — Development Roadmap

## Vision

A personal AI assistant that runs locally, understands voice, executes real tasks,
remembers context across sessions, and proactively surfaces useful information.

---

## Phase 1: Core Intelligence (Text Mode)  
**Goal**: Rock-solid orchestrator loop with tool calling and memory.  
**Status**: 🔨 In Progress

- [x] Project scaffold and architecture
- [ ] Configuration management (.env-based)
- [ ] Claude API integration with tool use (function calling)
- [ ] Tool registry (decorator-based, auto-discovery)
- [ ] Starter tools: weather, datetime, system info
- [ ] Orchestrator: input → brain → tool execution → response loop
- [ ] Persistent memory store (SQLite — facts, preferences, conversation history)
- [ ] CLI interface for text interaction
- [ ] Error handling, retries, graceful degradation

**Done when**: You can type a request, Jarvis calls the right tool, remembers
what you told it last session, and responds coherently.

---

## Phase 2: Voice Interface  
**Goal**: Talk to Jarvis, hear it respond.

- [ ] Speech-to-text via `faster-whisper` (local, no API cost)
- [ ] Text-to-speech via `piper` (local) or ElevenLabs (cloud, better quality)
- [ ] Audio I/O pipeline (mic capture → STT → orchestrator → TTS → speaker)
- [ ] Interrupt handling (stop speaking when user talks)
- [ ] Latency optimization (streaming TTS, partial transcription)

**Done when**: You speak → Jarvis responds aloud, with natural latency.

---

## Phase 3: Always-On Presence  
**Goal**: Jarvis is always listening, ready to help.

- [ ] Wake word detection via `openWakeWord` or Porcupine
- [ ] Persistent background process (daemon / systemd service)
- [ ] State machine: sleeping → listening → processing → responding
- [ ] Audio feedback (chime on wake, subtle sounds for state changes)
- [ ] Resource management (low CPU when idle)

**Done when**: "Hey Jarvis" wakes it from standby, hands-free.

---

## Phase 4: Tool Expansion  
**Goal**: Jarvis can actually do things in your life.

- [ ] Google Calendar integration (read/write events)
- [ ] Email (Gmail API — read, draft, send)
- [ ] Smart home control (Home Assistant API)
- [ ] Web search (Brave Search API or similar)
- [ ] File system operations (find, read, organize files)
- [ ] App launcher / OS control
- [ ] Note-taking / knowledge base
- [ ] Music control (Spotify API)
- [ ] Code execution sandbox

**Done when**: Jarvis handles your daily workflow tasks end-to-end.

---

## Phase 5: Long-Term Memory & Personalization  
**Goal**: Jarvis knows you — preferences, habits, context.

- [ ] Structured fact store (who you are, what you like, your schedule patterns)
- [ ] Conversation summarization (compress old chats, retain key facts)
- [ ] Vector search for semantic memory retrieval (ChromaDB / local)
- [ ] User profile that evolves over time
- [ ] Context-aware responses (knows your calendar before you ask)

**Done when**: Jarvis references past conversations naturally and adapts to you.

---

## Phase 6: Proactive Intelligence  
**Goal**: Jarvis speaks up when it should — without being annoying.

- [ ] Background scheduler (periodic checks on calendar, weather, email)
- [ ] Notification engine with priority scoring
- [ ] "Should I interrupt?" classifier (LLM-judged relevance)
- [ ] Morning briefing (auto-generated daily summary)
- [ ] Anomaly detection (unusual calendar conflicts, weather alerts, etc.)
- [ ] User feedback loop (thumbs up/down on proactive alerts to tune behavior)

**Done when**: Jarvis tells you "you have a meeting in 15 minutes" without
being asked, and you're glad it did.

---

## Architecture Principles

1. **No frameworks for the sake of frameworks.** No LangChain, no bloated abstractions.
   Raw Python + asyncio + the Anthropic SDK. You own every line.

2. **Tools are plugins.** Drop a file in `tools/`, decorate a class, it's registered.
   No config files, no manual wiring.

3. **Memory is durable.** SQLite for structured data. Vector DB only when needed.
   Everything survives a restart.

4. **Voice is a transport, not the architecture.** The orchestrator works identically
   whether input comes from keyboard or microphone. Voice is an I/O adapter.

5. **Fail gracefully.** If a tool errors, Jarvis says so and moves on.
   If the API is down, it tells you. No silent failures.

6. **Respect resources.** Local-first where possible. Cloud APIs only where they
   add real value (LLM brain, specific integrations).
