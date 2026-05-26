#!/usr/bin/env python3
"""Workflow Engine CLI — run AI agent pipelines from YAML."""

from __future__ import annotations
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.live import Live
from rich.rule import Rule

from engine.parser import WorkflowParser
from engine.executor import PipelineExecutor
from engine.step import Step, StepStatus
from engine.state import SharedState

console = Console()

BANNER = r"""
[bold cyan]╔══════════════════════════════════════════════════╗
║         🔄  WORKFLOW ENGINE  v1.0                 ║
║     AI Agent Pipelines · Powered by MiMo         ║
║         Xiaomi MiMo Token Giveaway                ║
╚══════════════════════════════════════════════════╝[/bold cyan]
"""

STATUS_COLORS = {
    StepStatus.PENDING: "dim",
    StepStatus.RUNNING: "bold yellow",
    StepStatus.SUCCESS: "bold green",
    StepStatus.FAILED: "bold red",
    StepStatus.SKIPPED: "dim yellow",
}

STATUS_ICONS = {
    StepStatus.PENDING: "⏳",
    StepStatus.RUNNING: "⚡",
    StepStatus.SUCCESS: "✅",
    StepStatus.FAILED: "❌",
    StepStatus.SKIPPED: "⏭️",
}


def print_state_update(step: Step, state: SharedState) -> None:
    """Show state after a step completes."""
    if step.output_key and step.status == StepStatus.SUCCESS:
        val = state.get(step.output_key, "")
        preview = val[:120].replace("\n", " ") + ("..." if len(val) > 120 else "")
        console.print(
            f"  [dim]state.[/dim][cyan]{step.output_key}[/cyan] "
            f"[dim]= {preview}[/dim]"
        )


def render_step_table(steps: list[Step]) -> Table:
    """Build a table of all steps and their status."""
    table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 1))
    table.add_column("", width=3)
    table.add_column("Step", style="bold")
    table.add_column("Status", width=12)
    table.add_column("Duration", justify="right", width=8)
    table.add_column("Output Key", style="cyan")
    for s in steps:
        color = STATUS_COLORS[s.status]
        icon = STATUS_ICONS[s.status]
        dur = f"{s.duration:.1f}s" if s.duration > 0 else "—"
        table.add_row(
            icon,
            f"[{color}]{s.id}[/{color}]",
            f"[{color}]{s.status.value}[/{color}]",
            dur,
            s.output_key or "—",
        )
    return table


def on_step_start(step: Step) -> None:
    console.print(f"\n[bold yellow]⚡ Running:[/bold yellow] [bold]{step.id}[/bold]")
    # Show rendered prompt preview
    preview = step.prompt.strip()[:200].replace("\n", "\n    ")
    console.print(f"  [dim]prompt: {preview}...[/dim]")


def on_step_done(step: Step, state: SharedState) -> None:
    color = STATUS_COLORS[step.status]
    icon = STATUS_ICONS[step.status]
    console.print(
        f"  {icon} [{color}]{step.status.value.upper()}[/{color}] "
        f"({step.duration:.1f}s)"
    )
    if step.result:
        preview = step.result[:150].replace("\n", " ")
        console.print(f"  [dim]→ {preview}...[/dim]")
    print_state_update(step, state)


def run_demo() -> None:
    """Simulate workflow execution with Rich output."""
    console.print(BANNER)
    console.print("[bold]Demo Mode[/bold] — simulating workflow execution\n")

    import os
    examples_dir = os.path.join(os.path.dirname(__file__), "examples")
    wf = WorkflowParser.parse(os.path.join(examples_dir, "code_review.yaml"))

    # Show workflow info
    info = Table.grid(padding=1)
    info.add_row("[bold]Name:[/bold]", wf.name)
    info.add_row("[bold]Description:[/bold]", wf.description)
    info.add_row("[bold]Provider:[/bold]", wf.provider)
    info.add_row("[bold]Model:[/bold]", wf.model)
    info.add_row("[bold]Steps:[/bold]", str(len(wf.steps)))
    console.print(Panel(info, title="📋 Workflow", border_style="blue"))

    # Show step dependency tree
    tree = Tree("[bold]Pipeline[/bold]")
    for step in wf.steps:
        deps = f" ← depends on: {', '.join(step.depends_on)}" if step.depends_on else ""
        tree.add(f"[cyan]{step.id}[/cyan]{deps}")
    console.print(tree)
    console.print()

    def start(step: Step, state: SharedState) -> None:
        on_step_start(step)

    def done(step: Step, state: SharedState) -> None:
        on_step_done(step, state)

    executor = PipelineExecutor(
        workflow=wf,
        dry_run=True,
        on_step_start=start,
        on_step_done=done,
    )

    console.print(Rule("[bold green]Executing Pipeline[/bold green]"))
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Pipeline progress", total=len(wf.steps))
        state = executor.run()
        progress.update(task, completed=len(wf.steps))

    console.print(Rule("[bold]Results[/bold]"))
    console.print(render_step_table(wf.steps))

    # Final state dump
    console.print("\n[bold]Final State:[/bold]")
    for key, val in executor.state.snapshot.items():
        preview = str(val)[:200].replace("\n", " ")
        console.print(f"  [cyan]{key}[/cyan] = {preview}")

    console.print(
        "\n[bold green]✅ Demo complete![/bold green] "
        "Powered by [bold]Xiaomi MiMo[/bold] 🚀"
    )


def run_workflow(path: str) -> None:
    """Execute a real workflow with API calls."""
    console.print(BANNER)
    from providers.mimo_provider import MiMoProvider

    wf = WorkflowParser.parse(path)
    provider = MiMoProvider()

    def start(step: Step, state: SharedState) -> None:
        on_step_start(step)

    def done(step: Step, state: SharedState) -> None:
        on_step_done(step, state)

    executor = PipelineExecutor(
        workflow=wf,
        provider=provider,
        on_step_start=start,
        on_step_done=done,
    )

    console.print(Rule(f"[bold green]Running: {wf.name}[/bold green]"))
    state = executor.run()
    state_holder["state"] = state

    console.print(Rule("[bold]Results[/bold]"))
    console.print(render_step_table(wf.steps))

    for key, val in executor.state.snapshot.items():
        console.print(f"\n[bold cyan]{key}:[/bold cyan]")
        console.print(Panel(str(val), border_style="dim"))


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        console.print("Usage: python main.py [--demo | workflow.yaml]")
        console.print("  --demo           Run demo simulation")
        console.print("  workflow.yaml    Execute a workflow file")
        sys.exit(0)

    if args[0] == "--demo":
        run_demo()
    else:
        run_workflow(args[0])


if __name__ == "__main__":
    main()
