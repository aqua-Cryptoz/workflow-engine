"""Parse YAML workflow definitions."""

from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml

from .step import Step


class WorkflowDefinition:
    """Parsed workflow with metadata and steps."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self.name: str = raw.get("name", "unnamed")
        self.description: str = raw.get("description", "")
        self.provider: str = raw.get("provider", "mimo")
        self.model: str = raw.get("model", "MiMo-7B-RL")
        self.variables: dict[str, Any] = raw.get("variables", {})
        self.steps: list[Step] = [Step.from_dict(s) for s in raw.get("steps", [])]

    @property
    def step_ids(self) -> list[str]:
        return [s.id for s in self.steps]


class WorkflowParser:
    """Load and validate YAML workflow files."""

    @staticmethod
    def parse(path: str | Path) -> WorkflowDefinition:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {path}")
        with open(path) as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict) or "steps" not in raw:
            raise ValueError(f"Invalid workflow: {path}")
        wf = WorkflowDefinition(raw)
        WorkflowParser._validate(wf)
        return wf

    @staticmethod
    def parse_string(content: str) -> WorkflowDefinition:
        raw = yaml.safe_load(content)
        wf = WorkflowDefinition(raw)
        WorkflowParser._validate(wf)
        return wf

    @staticmethod
    def _validate(wf: WorkflowDefinition) -> None:
        ids = set(wf.step_ids)
        for step in wf.steps:
            for dep in step.depends_on:
                if dep not in ids:
                    raise ValueError(
                        f"Step '{step.id}' depends on unknown step '{dep}'"
                    )
