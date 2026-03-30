# Optional integrations: Hermes Agent & GStack-style workflows

This folder does **not** vendor third-party agent runtimes. It provides **contracts** (policies, checklists, skill text) so you can attach external tools **without** blurring the boundary between:

- **GHOST runtime loop** (deterministic `skills/` + `harness.py` in this repo), and  
- **LLM / IDE orchestration** (Hermes, Claude Code + GStack skills, etc.).

## Contents

| Path | What it is |
|------|------------|
| [`hermes/`](hermes/) | Tool/write boundaries + notes for [Nous Hermes Agent](https://hermes-agent.nousresearch.com/) (install from their GitHub, not PyPI). |
| [`gstack/`](gstack/) | Markdown skill-style instructions for **Claude Code / GStack**-style workflows (editor layer; not `import gstack` in Python). |
| [`validate.py`](validate.py) | **Stdlib-only** checks that policy files exist and required repo paths are present. Run in CI. |

## Trade-offs (no marketing)

| Approach | Upside | Downside |
|----------|--------|----------|
| **Hermes Python API** (`pip install git+…`) | Rich agent loop, delegation | Extra deps, API keys, supply chain from git, harder CI reproduction |
| **GStack / Claude Code skills** | Fast human+AI editing of `skills/` | Not importable from `harness.py`; governance is in your IDE/org |
| **This repo only (default)** | Reproducible, stdlib CI | No built-in LLM reasoning |

## Recommended use

1. Keep **production healing** behind reviewed `skills/` + tests.  
2. Use **Hermes or GStack** to **propose** diffs to `skills/` or docs; merge only after `python data/seed.py` and `python harness.py` pass.  
3. Run `python integrations/validate.py` locally or rely on CI after changing integration contracts.
