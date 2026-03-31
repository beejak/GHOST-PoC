# Lab pipeline (minimal, optional)

Purpose: generate more realistic **local** data from a throwaway Kubernetes lab and replay it through GHOST without changing CI scope.

## Prerequisites

- Docker
- `kubectl`
- `kind` (not bundled in repo)

## Workflow

1. Bootstrap lab cluster + workload:

```powershell
pwsh ./lab/bootstrap_lab.ps1
```

2. Inject deterministic failures (ImagePullBackOff, CrashLoopBackOff, probe-unhealthy):

```powershell
pwsh ./lab/inject_failures.ps1
```

3. Collect + normalize + replay in one step:

```powershell
pwsh ./lab/collect_and_normalize.ps1
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
