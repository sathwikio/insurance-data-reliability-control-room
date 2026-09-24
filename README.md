# Insurance Data Reliability Control Room

![CI](https://github.com/sathwikio/insurance-data-reliability-control-room/actions/workflows/ci.yml/badge.svg)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

Deterministic PySpark metrics + a bounded Jev decision layer over 40 synthetic insurance pipeline runs. Python computes facts; Jev assigns one of `HEALTHY / WATCH / INVESTIGATE / BLOCK`. The join is validated one-to-one on `run_id`.

All data is synthetic (seed 42). No customer data. No insurer connection.

## Quickstart (offline, no API key)

Prerequisites: Python 3.12, Java 17, Node.js 22.

```bash
# macOS
brew install openjdk@17
export JAVA_HOME=/opt/homebrew/opt/openjdk@17
# Linux: export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e ".[dev]"
cp .env.example .env   # set AI_GATEWAY_API_KEY only for a fresh Jev run

make e2e-no-key   # generate_data -> spark_pipeline -> build_final -> pytest
make sync-web     # regenerate web/src/data/runs.json from final_analytics.csv
cd web && npm ci && npm run build
```

Docker alternative:

```bash
docker build -t insurance-control-room:repro .
docker run --rm insurance-control-room:repro python -m pytest tests/ -q
```

## System design

- `src/metrics.py` computes all metrics (single source of truth).
- `src/spark_pipeline.py` calls those functions via UDFs; adds no logic.
- `jev/evaluate.mjs` receives measured state only; returns one label + native confidence.
- `src/build_final.py` joins on `run_id` after coverage and label checks; fails otherwise.

```text
data/pipeline_runs.csv (seed 42)
  -> src/spark_pipeline.py
    -> data/delta/pipeline_metrics + data/jev_input.json
  -> jev/evaluate.mjs
    -> data/jev_decisions.json
  -> src/build_final.py (validate, join on run_id)
    -> data/delta/pipeline_analytics + data/final_analytics.csv
  -> notebooks/databricks_pipeline.py -> Delta + AI/BI dashboard
  -> web/ (Next.js static mirror of final_analytics.csv)
```

## Data and results

Seed 42 produces 40 runs: 8 each in `auto_claims`, `home_claims`, `policies`, `billing`, `customers`, across 2026-09-18/19.

Per-run signals: `failure_rate`, `row_count_variance`, `duration_variance`, `freshness_severity` (`ON_TIME` ≤15, `MINOR` ≤60, `MAJOR` ≤240, else `SEVERE`), `schema_drift_present`, `error_present`.

Checked-in decision distribution: 23 `HEALTHY`, 2 `WATCH`, 7 `INVESTIGATE`, 8 `BLOCK` (40/40 coverage).

## Reproduction

Local offline uses the checked-in `data/jev_decisions.json` — no key needed. For a fresh Jev run:

```bash
cd jev && npm install
export AI_GATEWAY_API_KEY=...
npm run evaluate && cd ..
python -m src.build_final
```

Databricks: upload `data/pipeline_runs.csv` + `data/jev_decisions.json` to a Unity Catalog volume, set `CATALOG` in `notebooks/databricks_pipeline.py`, run all cells. Creates `pipeline_metrics` and `pipeline_analytics`; build the AI/BI dashboard per `docs/dashboard-spec.md` (screenshot + PDF in `docs/screenshots/`).

Fabric: `notebooks/fabric_pipeline.py` mirrors the logic for a Lakehouse target. Not tested live.

## Technology

| Area | Version |
|---|---|
| Metrics | Python 3.12, PySpark 3.5.6 |
| Storage | Delta Lake 3.2.1 |
| Decision layer | `typesafe-ai/jev` via Vercel AI SDK (`jev/package.json`) |
| Dashboards | Databricks AI/BI (verified), Next.js 16 static mirror in `web/` |
| Tests | pytest (53 cases), ruff |

## Repository map

```text
data/                  pipeline_runs.csv, jev_input.json,
                       jev_decisions.json, final_analytics.csv
src/                   generate_data.py, metrics.py,
                       spark_pipeline.py, build_final.py
jev/                   evaluate.mjs, package.json, dns-shim.cjs
notebooks/             databricks_pipeline.py, fabric_pipeline.py
web/src/               app/, components/, lib/stats.ts, data/runs.json
tests/                 test_metrics.py, test_generation.py,
                       test_decisions.py, test_final_logic.py
scripts/               sync_web_data.py
docs/                  ARCHITECTURE.md, DATA_DICTIONARY.md,
                       dashboard-spec.md, ADR/, architecture/, screenshots/
.github/workflows/    ci.yml (Python + web)
```

## Tests

53 cases: metric formulas, fixed-seed generation, Jev input fidelity, decision coverage, allowed labels, confidence bounds, final-table consistency, offline join-rule unit tests.

```bash
python -m pytest tests/ -q
ruff check src tests scripts
```

## Docs

- `docs/ARCHITECTURE.md`, `docs/DATA_DICTIONARY.md`, `docs/ADR/001-jev-separation.md`
- `docs/dashboard-spec.md`, `docs/screenshots/`
- `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`

## Scope limits

- 40 synthetic runs over two days. No live streams, backfills, alerts, or schedules.
- Offline path reuses checked-in Jev decisions. A fresh decision run needs `AI_GATEWAY_API_KEY` and may return a different distribution.
- Dashboards are read-only. Fabric is unverified live.

## License

MIT — see `LICENSE`.
