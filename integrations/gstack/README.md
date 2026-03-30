# GStack-style (Claude Code) skills × GHOST

**GStack** in the [gstacks.org](https://gstacks.org/) sense is typically installed as **Claude Code skills** under `~/.claude/skills/` (see their setup guide). There is **no stable `pip install gstack`** for embedding inside this Python repo.

## What this folder provides

- **[`SKILL_GHOST_MAINTAINER.md`](SKILL_GHOST_MAINTAINER.md)** — a single skill-style instruction file you can symlink or copy into your Claude Code / GStack skills directory, or paste into a project rule.

## Workflow

1. Human or IDE agent edits `skills/` per the maintainer skill.  
2. Run `python data/seed.py` and `python harness.py` from the **repository root**.  
3. Open a PR; CI (GitHub Actions) should stay green.

## Boundary

GStack operates at the **editor / chat** layer. **GHOST `harness.py`** remains the mechanical gate for policy correctness in this repository.
