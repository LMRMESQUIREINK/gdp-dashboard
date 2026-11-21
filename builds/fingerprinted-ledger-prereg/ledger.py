"""A fingerprinted call ledger: one SQLite table that is a cache, a replay
source, and a resume journal at once, because all three are the same
property — the same request always gets the same cached answer.

Independently reimplemented from reading FareedKhan-dev/dynamic-workflow-agents'
real ledger design (both editions' notebooks, section "S8 - The ledger"), not
copied from its source.
"""
import hashlib
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path


class LedgerMiss(Exception):
    """Raised in replay mode when a request has no cached answer."""


class FingerprintedLedger:
    """
    mode="collect": serve cached answers; call live_fn() on a genuine miss and save it.
    mode="replay":  serve cached answers only; raise LedgerMiss on a miss. Never calls live_fn.
    mode="smoke":   never touches the ledger at all; always calls smoke_fn().
    """

    def __init__(self, path, mode="collect"):
        if mode not in ("collect", "replay", "smoke"):
            raise ValueError(f"unknown mode: {mode!r}")
        self.path = Path(path)
        self.mode = mode
        if mode != "smoke":
            self._init_db()

    def _init_db(self):
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """CREATE TABLE IF NOT EXISTS answers (
                    fingerprint TEXT PRIMARY KEY,
                    request TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at REAL NOT NULL
                )"""
            )
            conn.commit()

    @staticmethod
    def fingerprint(model, messages, params, sample_index=0):
        """A SHA-256 hash of the normalized request. Identical calls get the
        same fingerprint; a different sample_index gives a different one even
        for an otherwise identical request, so a deliberate repeat (three
        skeptics asked the same question) is cached as three distinct answers,
        not collapsed into one.
        """
        payload = json.dumps(
            {"model": model, "messages": messages, "params": params, "sample_index": sample_index},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, fp):
        with closing(sqlite3.connect(self.path)) as conn:
            row = conn.execute("SELECT answer FROM answers WHERE fingerprint = ?", (fp,)).fetchone()
            return json.loads(row[0]) if row else None

    def put(self, fp, request, answer):
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO answers (fingerprint, request, answer, created_at) VALUES (?, ?, ?, ?)",
                (fp, json.dumps(request), json.dumps(answer), time.time()),
            )
            conn.commit()

    def call(self, model, messages, params, sample_index=0, live_fn=None, smoke_fn=None):
        """Returns (answer, cached: bool)."""
        if self.mode == "smoke":
            if smoke_fn is None:
                raise RuntimeError("smoke mode requires smoke_fn")
            return smoke_fn(), False

        fp = self.fingerprint(model, messages, params, sample_index)
        cached = self.get(fp)
        if cached is not None:
            return cached, True

        if self.mode == "replay":
            raise LedgerMiss(f"no cached answer for fingerprint {fp[:12]}... in replay mode")

        if live_fn is None:
            raise RuntimeError("collect mode requires live_fn")
        answer = live_fn()
        self.put(fp, {"model": model, "messages": messages, "params": params, "sample_index": sample_index}, answer)
        return answer, False

    def count(self):
        with closing(sqlite3.connect(self.path)) as conn:
            return conn.execute("SELECT COUNT(*) FROM answers").fetchone()[0]
