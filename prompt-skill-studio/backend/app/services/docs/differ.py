from __future__ import annotations

import difflib


def unified_diff(old: str | None, new: str, *, context: int = 3, max_chars: int = 20000) -> str:
    """Return a unified diff. Truncates at max_chars to keep DB rows reasonable."""
    if not old:
        # First capture: summarize as a single-block insert.
        head = new[:max_chars]
        return f"+++ initial capture ({len(new)} chars)\n{head}"
    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile="prev",
        tofile="curr",
        n=context,
    )
    out = "".join(diff)
    if len(out) > max_chars:
        out = out[:max_chars] + "\n... [truncated]"
    return out
