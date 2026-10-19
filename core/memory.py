"""
Persistent memory — SQLite-backed storage for facts, preferences,
and conversation history. Survives restarts.

Three stores:
  1. facts     — key-value pairs ("user_name" → "Tony", "home_city" → "Singapore")
  2. history   — full conversation messages for context window management
  3. summaries — compressed session summaries for long-term recall
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Fact:
    key: str
    value: str
    category: str  # "preference", "identity", "context", "system"
    created_at: float
    updated_at: float


class Memory:
    """Jarvis's persistent memory."""

    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS facts (
                key       TEXT PRIMARY KEY,
                value     TEXT NOT NULL,
                category  TEXT NOT NULL DEFAULT 'context',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS history (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role      TEXT NOT NULL,
                content   TEXT NOT NULL,
                timestamp REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_history_session
                ON history(session_id);

            CREATE TABLE IF NOT EXISTS summaries (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                summary    TEXT NOT NULL,
                created_at REAL NOT NULL
            );
        """)
        self._conn.commit()

    # ── Facts ──────────────────────────────────────────────────────────

    def set_fact(self, key: str, value: str, category: str = "context") -> None:
        now = time.time()
        self._conn.execute(
            """
            INSERT INTO facts (key, value, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                category = excluded.category,
                updated_at = excluded.updated_at
            """,
            (key, value, category, now, now),
        )
        self._conn.commit()

    def get_fact(self, key: str) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM facts WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def get_facts_by_category(self, category: str) -> list[Fact]:
        rows = self._conn.execute(
            "SELECT * FROM facts WHERE category = ? ORDER BY updated_at DESC",
            (category,),
        ).fetchall()
        return [Fact(**dict(r)) for r in rows]

    def get_all_facts(self) -> list[Fact]:
        rows = self._conn.execute(
            "SELECT * FROM facts ORDER BY category, key"
        ).fetchall()
        return [Fact(**dict(r)) for r in rows]

    def delete_fact(self, key: str) -> bool:
        cur = self._conn.execute("DELETE FROM facts WHERE key = ?", (key,))
        self._conn.commit()
        return cur.rowcount > 0

    def facts_as_prompt_block(self) -> str:
        """Format all facts as a block to inject into the system prompt."""
        facts = self.get_all_facts()
        if not facts:
            return ""
        lines = ["<user_memory>"]
        current_cat = ""
        for f in facts:
            if f.category != current_cat:
                current_cat = f.category
                lines.append(f"  [{current_cat}]")
            lines.append(f"    {f.key}: {f.value}")
        lines.append("</user_memory>")
        return "\n".join(lines)

    # ── Conversation history ───────────────────────────────────────────

    def save_message(self, session_id: str, role: str, content: str) -> None:
        self._conn.execute(
            "INSERT INTO history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, content, time.time()),
        )
        self._conn.commit()

    def get_session_history(
        self, session_id: str, limit: int = 50
    ) -> list[dict[str, str]]:
        rows = self._conn.execute(
            """
            SELECT role, content FROM history
            WHERE session_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def get_recent_sessions(self, limit: int = 10) -> list[str]:
        rows = self._conn.execute(
            """
            SELECT DISTINCT session_id FROM history
            ORDER BY MAX(id) DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [r["session_id"] for r in rows]

    # ── Session summaries ──────────────────────────────────────────────

    def save_summary(self, session_id: str, summary: str) -> None:
        self._conn.execute(
            "INSERT INTO summaries (session_id, summary, created_at) VALUES (?, ?, ?)",
            (session_id, summary, time.time()),
        )
        self._conn.commit()

    def get_recent_summaries(self, limit: int = 5) -> list[dict[str, str]]:
        rows = self._conn.execute(
            "SELECT session_id, summary FROM summaries ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Lifecycle ──────────────────────────────────────────────────────

    def close(self) -> None:
        self._conn.close()
