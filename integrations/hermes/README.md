# Hermes Agent × GHOST

**Hermes** here means [Nous Research Hermes Agent](https://github.com/NousResearch/hermes-agent) (documentation: [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com/)). It is **not** installed by default in this repository.

## Installation (upstream)

Follow the official guide: install script or `pip install git+https://github.com/NousResearch/hermes-agent.git` as they document. You will need their runtime requirements (Python version, optional Node tooling per their installer) and **API credentials** for your chosen model provider.

## How to use with this repo

1. Load **`TOOL_POLICY.json`** (same directory) into your Hermes deployment as the **allowlist** for filesystem and shell tools — or translate it into Hermes’ native tool configuration if their format differs.  
2. Use **`COORDINATOR_PROMPT_SNIPPET.md`** as a starting point for the coordinator persona: read signals, propose `skills/` edits, **never** claim prod access through this PoC.  
3. After any change to `skills/*.py`, run:

   ```bash
   python data/seed.py
   python harness.py
   ```

4. Record outcomes in your incident / PR process; optional: this repo already appends **`feedback_rows`** in `metrics/results.db` when `harness.py` runs.

`TOOL_POLICY.json` **shell_allowlist** includes the CI commands plus optional local tools, for example:

- `python adapters/observe.py data/mixed_stream.json`  
- `python adapters/lab_run.py --dry-run data/near_real_stream.json`  
- `python tools/run_external_replay.py --data data/external/runs/demo/normalized.json --ground-truth data/external/runs/demo/ground_truth.json`  

Adapt the allowlist if your paths differ; do not widen shell access without review.

## Limitations

- Hermes’ feature set and install path **change upstream**; this repo only ships **policy JSON + prompts**, not a pinned integration test against their library.  
- **No warranty** that a given Hermes version respects `TOOL_POLICY.json` unless you wire it yourself.
