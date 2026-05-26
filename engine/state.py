"""Shared state management between pipeline steps."""

from __future__ import annotations
import re
from typing import Any


class SharedState:
    """Thread-safe shared state with Jinja-lite {{ var }} templating."""

    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self._data: dict[str, Any] = dict(initial or {})
        self._history: list[tuple[str, Any]] = []

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._history.append((key, value))

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def render(self, template: str) -> str:
        """Replace {{ key }} placeholders with state values."""
        def _replace(m: re.Match) -> str:
            k = m.group(1).strip()
            v = self._data.get(k, m.group(0))
            return str(v)
        return re.sub(r"\{\{\s*(.+?)\s*\}\}", _replace, template)

    @property
    def snapshot(self) -> dict[str, Any]:
        return dict(self._data)

    @property
    def history(self) -> list[tuple[str, Any]]:
        return list(self._history)

    def __repr__(self) -> str:
        return f"SharedState({self._data})"
