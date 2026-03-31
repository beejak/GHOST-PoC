# Lab pipeline (minimal, optional)

Purpose: generate more realistic **local** data from a throwaway Kubernetes lab and replay it through GHOST without changing CI scope.

## Prerequisites

- Docker
- `kubectl`
- `kind` (not bundled in repo)

## Workflow

1. Bootstrap lab cluster + workload:

```powershell
./lab/bootstrap_lab.ps1
```

2. Inject deterministic failures (ImagePullBackOff, CrashLoopBackOff, probe-unhealthy):

```powershell
./lab/inject_failures.ps1
```

3. Collect + normalize + replay in one step:

```powershell
./lab/collect_and_normalize.ps1
```

## Command help

All commands are intended to be run from repository root.

- Bootstrap only: `./lab/bootstrap_lab.ps1`
- Inject only: `./lab/inject_failures.ps1`
- Collect/normalize/replay wrapper: `./lab/collect_and_normalize.ps1`

Equivalent direct script calls:

```powershell
python tools/collect_k8s_lab_data.py --namespace ghost-lab --selector app=app-service
python tools/normalize_external_capture.py --events data/external/runs/<run-id>/events.json --logs data/external/runs/<run-id>/logs.txt --out-records data/external/runs/<run-id>/normalized.json --out-gt data/external/runs/<run-id>/ground_truth.json
python tools/run_external_replay.py --data data/external/runs/<run-id>/normalized.json --ground-truth data/external/runs/<run-id>/ground_truth.json --record
```

Outputs are created under `data/external/runs/<run-id>/`:

- `events.json`
- `logs.txt`
- `normalized.json`
- `ground_truth.json`

Run replay manually if needed:

```powershell
python tools/run_external_replay.py --data data/external/runs/<run-id>/normalized.json --ground-truth data/external/runs/<run-id>/ground_truth.json --record
```

## Scope notes

- This pipeline is **not** in CI.
- It is intentionally narrow: one namespace (`ghost-lab`), one deployment (`app-service`), and a small failure set.
- Data under `data/external/` stays gitignored by default.
- Scripts are fail-fast: they now stop immediately on any failed `kubectl`/Python command.

## Published run

- Report: [`docs/LAB_RUN_REPORT_20260331.md`](../docs/LAB_RUN_REPORT_20260331.md)
- Reported improvement on same captured run after normalization update: `6/11` -> `11/11` detected/resolved with `0` false positives.
