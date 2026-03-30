# GHOST — Help, FAQ & operations guide

This document expands on the [README](../README.md). Use it for troubleshooting, extending the PoC, and decisions about **real** versus **synthetic** log data.

---

## Quick troubleshooting

| Symptom | Likely cause | What to do |
|--------|----------------|------------|
| `FileNotFoundError` for `clean_failures.json` (or other `data/*.json`) | Generated data not created yet | Run `python data/seed.py` from the repository root, then `python harness.py`. |
| `Experiment 1/2/3/4 failed` | Logic regression or stale `skills/` out of sync with `seed.py` | Re-run `seed.py`; if it still fails, compare `skills/watcher_skills.py` / `k8s_signal_skills.py` / `healer_skills.py` with the failing experiment in `experiments/`. |
| `Healthy baseline assertion failed` | A healthy template now overlaps a detection pattern | Adjust `HEALTHY_TEMPLATES` in `data/seed.py` or narrow patterns in `skills/watcher_skills.py`; keep casefold behavior in mind. |
| `UnicodeEncodeError` on Windows console | Rare if seed uses ASCII separators | Prefer UTF-8 console (`chcp 65001`) or run in CI (Linux). |
| All timings show `0 ms` | Normal on fast hardware | Correctness is from assertions; add delay in `data/generator.py` if you need wall-clock spread. |
| Import errors when running `seed.py` | Wrong working directory | Run from repo root so `skills` resolves: `python data/seed.py`, not `cd data && python seed.py` (unless `PYTHONPATH` is set). |

---

## Frequently asked questions

### What is GHOST *not*?

- Not a hosted product or managed service.  
- Not a replacement for your cloud provider’s control plane or Kubernetes.  
- Not an LLM-first incident bot in Phase 1.  
- Not authorized to touch your real infrastructure unless **you** add that code and credentials under **your** governance.

### Why standard library only?

So anyone can **clone → seed → harness** without dependency drift, supply-chain surprises, or “works on my laptop” pip conflicts. Optional Phase 2 dependencies belong in `requirements.txt` with explicit versions when you add them.

### How do I change what gets detected or healed?

1. **Logs:** edit `skills/watcher_skills.py` (`DETECTABLE_PATTERNS`) and/or `skills/healer_skills.py` (`DECISION_TABLE`).  
2. **K8s-style JSON signals:** edit `skills/k8s_signal_skills.py` (`SIGNAL_RULES`).  
3. **Actions:** add a function in `simulator/infra_state.py`, register it in `ACTION_REGISTRY`, then reference it from the decision table.  
4. **Never** embed pattern strings or decision tables inside `agents/*.py` — that breaks the skills-as-policy rule.

### Can we download real scenarios from open-source log providers and store them in this project?

**Yes, you can — but the repository defaults to synthetic data on purpose.** Nothing in the architecture forbids real samples.

**Why the default is synthetic**

| Concern | Why it matters |
|--------|----------------|
| **Reproducibility** | CI and collaborators need identical inputs; public dumps change or disappear. |
| **Privacy & secrets** | Production logs often contain tokens, emails, internal hostnames, customer data — unsafe to commit. |
| **Licensing** | “Open” datasets still have licenses (CC-BY, academic-only, no redistribution). You must **comply** and **attribute**. |
| **Schema mismatch** | Raw logs are lines or JSON blobs; GHOST experiments expect **structured records** (`severity`, `message`, `service`, …). You need an **ETL** step. |
| **Ground truth** | To score detection you need **labels** (failure class) or a controlled injection protocol. Public dumps are often unlabeled or labeled for a different task. |

**What “train our agents” means here**

Today’s agents are **not** machine-learning models. They do **substring / rule matching** and **lookup-table remediation**. “Training” in this PoC means **engineering**: adding patterns, tuning order, validating on harnesses. If you later add ML, you would still need **labeled**, **consent-cleared** data and a separate training pipeline — not a single drop-in folder.

**Practical way to use real or public logs safely**

1. Pick a dataset whose **license** allows your use (commercial vs research, attribution, redistribution).  
2. **Do not commit** raw production logs to git. Use a local path or private storage.  
3. **Normalize** lines into the same JSON shape as `clean_failures.json` (see examples under `data/` after `seed.py`).  
4. **Redact** aggressively (IPs, tokens, user paths) before sharing or committing **derived** fixtures.  
5. Add a **private** or **gitignored** directory (e.g. `data/external/`) and optional scripts to convert vendor format → GHOST JSON.  
6. Extend the harness or add Experiment 5 that reads your file — keep CI on **synthetic** data only unless you use a **public** pinned snapshot with a documented license.

**Categories of public sources people use** (verify license yourself)

- Research / benchmark log collections (often system or batch-job logs).  
- Anonymized “log hub” style corpora maintained for anomaly detection research.  
- Vendor or CNCF **sample** configurations (not your prod traffic).  

We do **not** ship third-party log files in this repo to avoid legal and hygiene risk; you bring data under **your** compliance review.

### How do I run only one experiment?

The harness runs all four. For ad-hoc runs, use a short Python snippet or temporary script that `asyncio.run()`s the specific `experiments/run_experimentN.run(...)` with a `Recorder` or `None`. (Keeping one entrypoint avoids drift in CI.)

### Where are results stored?

`metrics/results.db` (SQLite). It is gitignored. Inspect with `sqlite3`, the `metrics/reporter.py` helpers, or any SQLite browser.

---

## Layered failures, swarms & learning (longer arc)

For a **systems-level** view (logs vs manifests vs network vs API vs DB, troubleshooting with **incomplete** data, coordinator + specialist “swarm”, and **feedback loops** for policy improvement), read **[VISION_LAYERED_LEARNING.md](VISION_LAYERED_LEARNING.md)**.

After each successful or failed harness run, check **`metrics/results.db`** table **`feedback_rows`** for the JSON summary written by **`metrics/feedback.py`** (`run_id` is printed at the end of `harness.py`).

---

## Extending toward production-shaped workflows

1. **Multi-signal Watcher** — combine logs + Kubernetes API watches + metrics; normalize to one event schema.  
2. **Guardrails** — rate limits, max actions per hour, dry-run mode, allowlisted namespaces.  
3. **Verification** — after heal, assert SLO or synthetic check before declaring success.  
4. **Audit** — log policy version, input hash, action, outcome (you already persist rows; tighten schema).  

---

## External agent tools (Hermes, [gstack](https://github.com/garrytan/gstack))

This repo ships **contracts**, not bundled LLM runtimes:

- **[`integrations/README.md`](../integrations/README.md)** — Hermes Agent policy JSON + GStack-compatible maintainer skill text.  
- **`harness.py`** runs **`integrations/validate.py`** first so those files stay consistent.

Hermes installs from **Nous Research’s GitHub** (see `integrations/hermes/README.md`). **[gstack](https://github.com/garrytan/gstack)** is a separate MIT skill pack for **Claude Code** (and related hosts per its README); it lives under your skills directory / project `.claude` or `.agents` layout—not `pip install`.

---

## Getting support

- **Specification & design intent:** [Ghost PoC.md.txt](../Ghost%20PoC.md.txt)  
- **Build / CI issues:** Check [GitHub Actions](https://github.com/beejak/GHOST-PoC/actions/workflows/ci.yml) for the latest `main` run.  
- **Bugs / features:** Open an issue on the repository with `seed` value, OS, Python version, and the **first failing experiment** line from the harness output.

---

## Document history

This file is maintained alongside the code. When you add experiments or change the data contract, update **this file** and the **README** “Documentation” table so newcomers are not misled.
