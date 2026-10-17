"""
The result contract every tool returns — adapted from the source
article's toolkit/result.py. "ok" is always derived from `checks`, never
set by hand, so a tool can't accidentally report success while one of
its own checks failed.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional


def result(summary: str, files: Optional[dict] = None,
           checks: Iterable[tuple] = (), **extra: Any) -> dict:
    checks_list = [[name, bool(passed)] for name, passed in checks]
    return {
        "ok": all(passed for _, passed in checks_list),
        "summary": summary,
        "files": {k: str(v) for k, v in (files or {}).items()},
        "checks": checks_list,
        **extra,
    }
