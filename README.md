# Insurance Data Reliability Control Room

A small MVP that monitors synthetic insurance data pipelines with two clearly
separated layers:

1. **Deterministic metrics** — computed in Python and PySpark from pipeline run
   facts (row counts, failure share, duration, freshness, schema drift).
2. **Jev decision layer** — the `typesafe-ai/jev` evaluation model turns each
   run's measured state into exactly one operational decision
   (`HEALTHY`, `WATCH`, `INVESTIGATE`, `BLOCK`) with a native confidence value.

Both layers are preserved in the final Delta-compatible analytics table and in
every dashboard. Jev never computes metrics; the metrics never decide.

All data is synthetic. Nothing here touches real customer data or any real
insurer's systems.

## Architecture

```text
Synthetic insurance pipeline data
        ↓
Python and PySpark metrics
        ↓
Jev decision input
        ↓
Jev
        ↓
HEALTHY / WATCH / INVESTIGATE / BLOCK
        ↓
Final Delta-compatible analytics table
        ↓
Streamlit / Databricks / Microsoft Fabric
```

## Repository structure

```text
data/
  pipeline_runs.csv        synthetic source data (40 runs, fixed seed)
  jev_input.json          one compact record per run (deterministic state only)
  jev_decisions.json       Jev output (run_id, decision, confidence)
  final_analytics.csv      dashboard export of the final Delta table
  delta/                   local Delta tables (pipeline_metrics, pipeline_analytics)
src/
  generate_data.py         deterministic synthetic data generation
  metrics.py               deterministic metric functions (single source of truth)
  spark_pipeline.py        PySpark: CSV -> metrics -> Delta + jev_input.json
  build_final.py           join Jev decisions -> final Delta table + CSV
jev/
  evaluate.mjs             Jev integration (Vercel AI SDK evaluation API)
  package.json             minimum Node dependencies (ai, @ai-sdk/gateway)
dashboard/
  app.py                   local Streamlit dashboard
notebooks/
  databricks_pipeline.py   Databricks notebook source (Free Edition)
  fabric_pipeline.py       Microsoft Fabric notebook source (Lakehouse)
docs/
  dashboard-spec.md        one dashboard spec for all three surfaces
tests/                    pytest suite (45 tests)
sandbox/                  environment workarounds for this sandbox only
env.sh                    environment bootstrap for local runs
```

## Setup

Requires Python 3.12 and a JDK (17) on `JAVA_HOME`. In this sandbox the
workarounds in `sandbox/` and `env.sh` are also required (broken system DNS, no
passwd entry for the current user — see `sandbox/install.sh`).

```bash
python -m venv .venv
source env.sh
.venv/bin/python -m pip install -r requirements.txt
```

## Local run commands

```bash
source env.sh

# 1. deterministic synthetic data -> data/pipeline_runs.csv
.venv/bin/python -m src.generate_data

# 2. metrics -> Delta table + Jev input (data/jev_input.json)
.venv/bin/python -m src.spark_pipeline

# 3. Jev decisions (needs AI_GATEWAY_API_KEY in the environment; never stored)
cd jev && npm install && \
  AI_GATEWAY_API_KEY=... NODE_OPTIONS="--require ./dns-shim.cjs" node evaluate.mjs && cd ..

# 4. join -> final Delta table + dashboard CSV
.venv/bin/python -m src.build_final

# 5. tests
.venv/bin/python -m pytest tests/ -q

# 6. dashboard (http://localhost:8501)
.venv/bin/python -m streamlit run dashboard/app.py
```

## Deterministic metrics

`src/metrics.py` computes every measurable fact in plain Python:

- `failure_rate` — failed rows / expected rows
- `row_count_variance` — (actual − expected) / expected
- `duration_variance` — (duration − expected duration) / expected duration
- `freshness_severity` — ON_TIME / MINOR / MAJOR / SEVERE bands
- `schema_drift` — whether any drift was reported
- `error_present` — whether an error message was recorded

Data generation uses a fixed seed (42), and the Spark pipeline applies these
functions through UDFs, so identical input always yields identical output —
verified by tests and by byte-identical re-runs.

## Jev decision layer

`jev/evaluate.mjs` is intentionally isolated from the Python/PySpark code. It
uses the official Vercel AI SDK evaluation API (`experimental_evaluate` from
the `ai` package) with the model `typesafe-ai/jev`. For each of the 40 runs it
asks exactly one bounded `choice` question with the four allowed criteria and
passes only the run's deterministic state — no metric computation, no
explanations. The decision is Jev's native answer; the confidence is the native
probability the API returns for the chosen option (never invented, `null` if
absent). The API key is read from `AI_GATEWAY_API_KEY` at runtime and is never
written to any file.

## Manual Jev model switch

This project was built in three phases with a manual model switch between the
coding model and Jev: Phase A (coding model) produced the deterministic layer,
Phase B (Jev, via the API above) produced `data/jev_decisions.json`, Phase C
(coding model) joined the two. The Jev call is re-runnable any time the input
changes — it is a standalone script, not a chat session.

## Databricks steps

1. Create a Databricks Free Edition workspace and a Volume (or use
   `/Volumes/main/default/insurance`; edit the path in the notebook if different).
2. Upload `data/pipeline_runs.csv` and `data/jev_decisions.json` to the volume.
3. Import `notebooks/databricks_pipeline.py` as a notebook source file.
4. Run all cells: it loads the CSV, applies the same metric functions
   (mirrored from `src/metrics.py`), writes the Delta table
   `pipeline_metrics`, joins the Jev decisions, and writes
   `pipeline_analytics`.
5. The included `%sql` queries are dashboard-ready; build the Databricks
   dashboard from them following `docs/dashboard-spec.md`.

## Microsoft Fabric steps

1. Create a Fabric workspace with a Lakehouse.
2. Upload `data/pipeline_runs.csv` and `data/jev_decisions.json` into
   `Files/insurance/`.
3. Import `notebooks/fabric_pipeline.py` into a Fabric notebook and attach
   the Lakehouse.
4. Run all cells: Lakehouse load, the same PySpark transformations and Delta
   writes (`pipeline_metrics`, `pipeline_analytics`), Jev join, and a
   validated final table.
5. From the Lakehouse, select **New Power BI report** on `pipeline_analytics`
   and follow the manual steps in the notebook (also in
   `docs/dashboard-spec.md`) to build the dashboard.

## Dashboard steps (local)

```bash
source env.sh
.venv/bin/python -m streamlit run dashboard/app.py
```

Four KPI cards (total runs, healthy %, requires attention, blocked),
decision distribution, domain distribution, a freshness/duration trend, the
pipeline health table, and a per-run detail view showing the deterministic
metrics beside the Jev decision and confidence. Filters: domain, decision,
schema-drift-only. The full layout is specified in `docs/dashboard-spec.md`.

## Tests

```bash
.venv/bin/python -m pytest tests/ -q   # 45 tests
```

- `test_metrics.py` — hand-computed values for every metric function
- `test_generation.py` — determinism, field coverage, status consistency
- `test_decisions.py` — Jev coverage/labels/confidence, final-dataset
  consistency (recomputed metrics match the final table)

## Limitations

- Synthetic data only — 40 runs over 2 days; no backfills, no streaming.
- The Jev integration requires a `AI_GATEWAY_API_KEY` at runtime; without it
  the evaluation step cannot run (the project never stores the key).
- Local Spark runs on a single local JVM with the sandbox workarounds in
  `env.sh`; the notebooks are the intended production path.
- The dashboard is read-only; no alerting, no scheduling.
