"""Pipeline executor: runs steps sequentially with dependency resolution."""

from __future__ import annotations
import time
from collections import defaultdict, deque
from typing import Any, Callable

from .parser import WorkflowDefinition
from .state import SharedState
from .step import Step, StepStatus
from providers.base import BaseProvider


class PipelineExecutor:
    """Execute a workflow definition step-by-step."""

    def __init__(
        self,
        workflow: WorkflowDefinition,
        provider: BaseProvider | None = None,
        on_step_start: Callable[[Step, SharedState], None] | None = None,
        on_step_done: Callable[[Step, SharedState], None] | None = None,
        dry_run: bool = False,
    ) -> None:
        self.workflow = workflow
        self.provider = provider
        self.state = SharedState(workflow.variables)
        self.on_step_start = on_step_start
        self.on_step_done = on_step_done
        self.dry_run = dry_run
        self._steps_by_id: dict[str, Step] = {s.id: s for s in workflow.steps}

    def run(self) -> SharedState:
        """Execute all steps respecting dependency order."""
        order = self._topo_sort()
        for step_id in order:
            step = self._steps_by_id[step_id]
            # Skip steps whose deps failed
            if any(
                self._steps_by_id[d].status == StepStatus.FAILED
                for d in step.depends_on
            ):
                step.status = StepStatus.SKIPPED
                continue

            step.mark_running()
            if self.on_step_start:
                self.on_step_start(step, self.state)

            start = time.time()
            try:
                rendered = self.state.render(step.prompt)
                if self.dry_run:
                    result = self._simulate(step, rendered)
                else:
                    result = self.provider.complete(
                        prompt=rendered,
                        model=step.model or self.workflow.model,
                        temperature=step.temperature,
                        max_tokens=step.max_tokens,
                    )
                duration = time.time() - start
                step.mark_success(result, duration)
                if step.output_key:
                    self.state.set(step.output_key, result)
            except Exception as e:
                duration = time.time() - start
                step.mark_failed(str(e), duration)

            if self.on_step_done:
                self.on_step_done(step, self.state)

        return self.state

    def _simulate(self, step: Step, prompt: str) -> str:
        """Demo mode: return canned response."""
        demo_responses = {
            "analyze": "## Code Analysis Complete\n\n"
                "**Issues Found:** 3\n"
                "- ⚠️ Unused import `os` on line 2\n"
                "- ⚠️ Function `process()` has cyclomatic complexity of 12\n"
                "- 🔴 Missing error handling in `fetch_data()`\n\n"
                "Complexity score: 6.2/10",
            "review": "## Review Summary\n\n"
                "**Severity: Medium**\n"
                "The unused import is cosmetic. High complexity in `process()` "
                "makes maintenance risky. Missing error handling could cause "
                "production crashes.\n\n"
                "Priority fixes: error handling > complexity > unused import",
            "suggest": "## Suggested Fixes\n\n"
                "```python\n"
                "# 1. Remove unused import\n"
                "# import os  # DELETE\n\n"
                "# 2. Split process() into sub-functions\n"
                "def process():\n"
                "    data = _load_data()\n"
                "    result = _transform(data)\n"
                "    return _output(result)\n\n"
                "# 3. Add error handling\n"
                "async def fetch_data():\n"
                "    try:\n"
                "        return await client.get(url)\n"
                "    except httpx.HTTPError as e:\n"
                "        logger.error(f'Fetch failed: {e}')\n"
                "        raise\n"
                "```\n\n"
                "Estimated effort: 2 hours",
            "decompose": "## Research Decomposition\n\n"
                "Topic split into 3 sub-questions:\n"
                "1. What are the core mechanisms?\n"
                "2. What existing solutions exist?\n"
                "3. What gaps remain in the literature?",
            "research": "## Research Findings\n\n"
                "- Found 12 relevant papers (2023-2025)\n"
                "- Key insight: transformer-based approaches dominate\n"
                "- MiMo-7B achieves SOTA on math reasoning benchmarks\n"
                "- Open question: scalability to 100B+ parameter regime",
            "synthesize": "## Synthesized Report\n\n"
                "### Executive Summary\n"
                "Current state-of-the-art favors RL-trained reasoning models. "
                "MiMo-7B demonstrates that smaller models can match larger ones "
                "with proper training methodology.\n\n"
                "### Key Takeaways\n"
                "1. Chain-of-thought training is essential\n"
                "2. Reward modeling beats pure SFT\n"
                "3. Domain-specific fine-tuning yields 15-20% gains",
        }
        return demo_responses.get(step.id, f"[Demo] Output for step '{step.id}'")

    def _topo_sort(self) -> list[str]:
        """Topological sort of steps by dependencies."""
        graph: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = {}
        for s in self.workflow.steps:
            in_degree.setdefault(s.id, 0)
            for dep in s.depends_on:
                graph[dep].append(s.id)
                in_degree[s.id] = in_degree.get(s.id, 0) + 1

        queue = deque(sid for sid, deg in in_degree.items() if deg == 0)
        order: list[str] = []
        while queue:
            sid = queue.popleft()
            order.append(sid)
            for neighbor in graph[sid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self.workflow.steps):
            raise ValueError("Cycle detected in step dependencies")
        return order
