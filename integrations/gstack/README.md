# [gstack](https://github.com/garrytan/gstack)-compatible maintainer skill × GHOST

**gstack** is Garry Tan’s open-source **Claude Code** skill pack (MIT): slash-command workflows, `SKILL.md` layout, and a `setup` script that registers skills under **`~/.claude/skills/gstack`** (or a **repo-local** copy under **`.claude/skills/gstack`**). The upstream repo also documents **Codex / Gemini CLI / Cursor** installs via **`.agents/skills/gstack`** and `./setup --host …`. See the official README: [github.com/garrytan/gstack](https://github.com/garrytan/gstack).

There is **no** `pip install gstack` for use inside this Python harness; gstack is **IDE/agent** tooling, not a library import.

## What this folder provides

- **[`SKILL_GHOST_MAINTAINER.md`](SKILL_GHOST_MAINTAINER.md)** — project-specific maintainer instructions in the same spirit as gstack’s skills. Copy or symlink it next to your other skills (per your host’s discovery rules), or paste excerpts into **`CLAUDE.md`** / project rules.

## Workflow

1. Install gstack from upstream if you want the full command set; optionally add this repo’s maintainer skill alongside it.  
2. Human or IDE agent edits `skills/` per the maintainer skill.  
3. From the **repository root**: `python data/seed.py` and `python harness.py` (five experiments + `integrations/validate.py` gate).  
4. Open a PR; CI should stay green.

Optional local checks (not gstack-specific): **[`adapters/`](../adapters/)** for `observe.py` / `lab_run.py`; org rollout template **[`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)**.

## Boundary

gstack operates at the **editor / chat** layer. **GHOST `harness.py`** remains the mechanical gate for policy correctness in this repository.
