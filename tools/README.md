# Tools (local external-data pipeline)

These scripts support local collection and replay of external/lab data:

- `collect_k8s_lab_data.py` — fetches `kubectl` events/logs into `data/external/runs/<run-id>/`.
- `normalize_external_capture.py` — converts raw captures into GHOST replay records + ground truth.
- `run_external_replay.py` — runs normalized data through `experiments/run_experiment_external.py`.

None of these scripts run in CI by default.
