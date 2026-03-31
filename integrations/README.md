# Optional integrations: Hermes Agent & GStack-style workflows

This folder does **not** vendor third-party agent runtimes. It provides **contracts** (policies, checklists, skill text) so you can attach external tools **without** blurring the boundary between:

- **GHOST runtime loop** (deterministic `skills/` + `harness.py` in this repo), and  
- **LLM / IDE orchestration** (Hermes, Claude Code + GStack skills, etc.).

## Contents

| Path | What it is |
|------|------------|
| [`hermes/`](hermes/) | Tool/write boundaries + notes for [Nous Hermes Agent](https://hermes-agent.nousresearch.com/) (install from their GitHub, not PyPI). |
| [`gstack/`](gstack/) | Maintainer skill text compatible with **[gstack](https://github.com/garrytan/gstack)** (Claude Code skills; also Codex/Cursor paths in upstream docs). Not `import gstack` in Python. |
| [`validate.py`](validate.py) | **Stdlib-only** checks: Hermes `TOOL_POLICY.json` shape, and that core paths exist (`skills/`, `agents/`, `harness.py`, `docs/GOVERNANCE.md`, `adapters/observe.py`, `adapters/lab_run.py`, `experiments/run_experiment5.py`, etc.). **Invoked at the start of `harness.py`** (and thus in CI). |

## Trade-offs (no marketing)

| Approach | Upside | Downside |
|----------|--------|----------|
| **Hermes Python API** (`pip install git+…`) | Rich agent loop, delegation | Extra deps, API keys, supply chain from git, harder CI reproduction |
| **[gstack](https://github.com/garrytan/gstack) / Claude Code skills** | Structured slash workflows + fast human+AI editing of `skills/` | Not importable from `harness.py`; Bun/Node setup per upstream; governance in your IDE/org |
| **This repo only (default)** | Reproducible, stdlib CI | No built-in LLM reasoning |

## Recommended use

1. Keep **production healing** behind reviewed `skills/` + tests.  
2. Use **Hermes or GStack** to **propose** diffs to `skills/` or docs; merge only after `python data/seed.py` and `python harness.py` pass.  
3. Run `python integrations/validate.py` locally after changing integration contracts, or rely on **`harness.py`** (which runs it first).  
4. Rollout / autonomy tiers for your org are **not** enforced here — use **[`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)** as a template.
