# Lab Run Report — 2026-03-31

## Scope

First end-to-end execution of the optional local lab pipeline:

1. `lab/bootstrap_lab.ps1`
2. `lab/inject_failures.ps1`
3. `lab/collect_and_normalize.ps1`

Cluster: `kind-ghost-lab` (namespace `ghost-lab`).

## Artifacts

Run directory:

- `data/external/runs/20260331-135346/`
  - `events.json`
  - `logs.txt`
  - `normalized.json`
  - `ground_truth.json`

## Replay results (external experiment)

From `tools/run_external_replay.py` output:

- `records`: 183
- `ground_truth`: 11
- `detected`: 6
- `false_positives`: 0
- `healthy_count`: 172
- `resolved`: 6
- `avg_mttr_ms`: ~0.491

## Observations

- Pipeline executed successfully and produced replayable normalized data.
- No false positives were observed in this run.
- Recall is incomplete (`6/11`), so normalization mappings and/or detection patterns need refinement.

## Immediate next actions

1. Inspect missed ground-truth indices in `ground_truth.json` vs replay detections.
2. Improve `tools/normalize_external_capture.py` event-to-failure mapping for uncovered reasons.
3. Re-run injection + collection and compare metrics over multiple runs.
