# External / real log samples (local only)

Place **redacted**, **license-compliant** normalized JSON here if you experiment with public or internal log corpora.

- **Do not commit** production logs, tokens, or PII.
- Expected shape matches GHOST log records (see `clean_failures.json` after running `seed.py`). The **near-real** synthetic shape in `near_real_stream.json` (also from `seed.py`) shows multi-line / prefixed `message` fields you might approximate after redaction.
- This directory’s contents are **gitignored** except this `README.md`.
- The lab pipeline stores runs in `data/external/runs/<run-id>/`:
  - `events.json`
  - `logs.txt`
  - `normalized.json`
  - `ground_truth.json`

See [docs/HELP.md](../../docs/HELP.md) for licensing, ETL, and why the default pipeline stays synthetic.
