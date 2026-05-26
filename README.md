# 🔄 Workflow Engine

AI agent workflow engine that runs YAML-defined pipelines powered by [Xiaomi MiMo](https://huggingface.co/XiaomiMiMo).

## Quick Start

```bash
pip install -r requirements.txt
python main.py --demo          # Run demo simulation
python main.py workflow.yaml   # Run a workflow
```

## Workflow YAML Format

```yaml
name: my-workflow
description: Example pipeline
provider: mimo
model: MiMo-7B-RL

steps:
  - id: analyze
    prompt: |
      Analyze the following code for issues:
      {{ code }}
    output_key: analysis

  - id: review
    prompt: |
      Review this analysis and rate severity:
      {{ analysis }}
    depends_on: [analyze]
    output_key: review

  - id: suggest
    prompt: |
      Based on this review, suggest fixes:
      {{ review }}
    depends_on: [review]
    output_key: suggestions

    parallel: [step1, step2]  # optional: run steps concurrently
```

## Features

- **YAML-defined pipelines** — declarative workflow authoring
- **Step dependencies** — sequential or parallel execution via `depends_on`
- **Shared state** — `{{ variable }}` templating passes data between steps
- **MiMo provider** — built-in Xiaomi MiMo API integration
- **Rich terminal UI** — beautiful progress output with live state inspection
- **Demo mode** — simulate workflows without API keys

## Architecture

```
main.py                  CLI entry point
engine/
  parser.py              YAML workflow parser
  step.py                Step model
  executor.py            PipelineExecutor (sequential + parallel)
  state.py               SharedState between steps
providers/
  base.py                BaseProvider abstract class
  mimo_provider.py       Xiaomi MiMo API provider
examples/
  code_review.yaml       Analyze → Review → Suggest
  research.yaml          Decompose → Research → Synthesize
```

## Built for Xiaomi MiMo Token Giveaway

Powered by MiMo-7B-RL — reasoning model with RL-trained chain-of-thought.
