"""Step model representing a single pipeline step."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Step:
    id: str
    prompt: str
    output_key: str | None = None
    depends_on: list[str] = field(default_factory=list)
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048
    status: StepStatus = StepStatus.PENDING
    result: str | None = None
    error: str | None = None
    duration: float = 0.0

    def mark_running(self) -> None:
        self.status = StepStatus.RUNNING

    def mark_success(self, result: str, duration: float = 0.0) -> None:
        self.status = StepStatus.SUCCESS
        self.result = result
        self.duration = duration

    def mark_failed(self, error: str, duration: float = 0.0) -> None:
        self.status = StepStatus.FAILED
        self.error = error
        self.duration = duration

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Step:
        return cls(
            id=d["id"],
            prompt=d["prompt"],
            output_key=d.get("output_key"),
            depends_on=d.get("depends_on", []),
            model=d.get("model"),
            temperature=d.get("temperature", 0.7),
            max_tokens=d.get("max_tokens", 2048),
        )
