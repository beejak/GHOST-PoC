# Tools (local external-data pipeline)

These scripts support local collection and replay of external/lab data:

- `collect_k8s_lab_data.py` — fetches `kubectl` events/logs into `data/external/runs/<run-id>/`.
- `normalize_external_capture.py` — converts raw captures into GHOST replay records + ground truth.
- `run_external_replay.py` — runs normalized data through `experiments/run_experiment_external.py`.

None of these scripts run in CI by default.

## Command help

Run from repository root.

### 1) Collect raw lab data

```bash
python tools/collect_k8s_lab_data.py --namespace ghost-lab --selector app=app-service
```

### 2) Normalize for GHOST replay

```bash
python tools/normalize_external_capture.py \
  --events data/external/runs/<run-id>/events.json \
  --logs data/external/runs/<run-id>/logs.txt \
  --out-records data/external/runs/<run-id>/normalized.json \
  --out-gt data/external/runs/<run-id>/ground_truth.json
```

### 3) Replay and score

```bash
python tools/run_external_replay.py \
  --data data/external/runs/<run-id>/normalized.json \
  --ground-truth data/external/runs/<run-id>/ground_truth.json \
  --record
```

## Use cases

- Validate normalization quality against known ground truth.
- Compare replay metrics before/after rule or mapping changes.
- Build a local benchmark history in `metrics/results.db` without changing CI.
- Feed real-ish local Kubernetes failures into the same Watcher/Healer evaluation loop.
