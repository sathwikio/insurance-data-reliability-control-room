# Insurance Data Reliability Control Room

A data engineering project that monitors the reliability of insurance data
pipelines. Python and PySpark compute deterministic metrics from pipeline run
data. A separate decision layer, `typesafe-ai/jev` via the Vercel AI SDK
evaluation API, turns each measured run state into one operational decision.
Both layers land in one Delta table that feeds three dashboards.

All data is synthetic. The project does not use real customer data and has no
connection to any insurer's systems.

## What it does

- Generates 40 synthetic pipeline runs for five insurance domains: auto
  claims, home claims, policies, billing, customers. Each run records row
  counts, failed rows, duration, freshness delay, schema drift, status, and
  error text. A fixed random seed makes the dataset reproducible.
- Computes reliability metrics with short, tested Python functions applied
  through PySpark UDFs: failure rate, row count variance, duration variance,
  freshness severity, schema drift, error presence.
- Asks Jev one bounded choice question per run. The model returns exactly one
  label: `HEALTHY`, `WATCH`, `INVESTIGATE`, or `BLOCK`, plus the native
  probability for that label.
- Joins both layers into a final Delta table, `pipeline_analytics`, and serves
  dashboards from it.

Final decision distribution over the 40 runs: 23 HEALTHY, 2 WATCH,
7 INVESTIGATE, 8 BLOCK.

## Architecture

```text
Synthetic insurance pipeline runs
        |
Python / PySpark deterministic metrics
        |
Jev decision input (measured state only)
        |
Jev  ->  HEALTHY / WATCH / INVESTIGATE / BLOCK
        |
Final Delta table (metrics + decision)
        |
Streamlit / Databricks / Microsoft Fabric
```

### Why the two layers are separate

Metrics are facts. Short functions compute them from the source data, so the
same input always yields the same output. Decisions are judgments. They belong
to a model that sees only the measured state of a run.

The split has practical value:

- Each layer is testable on its own. The metric functions, the data
  generation, and the join between layers all have tests.
- Jev never recomputes a metric. The metrics never encode an operational
  decision. Neither layer can silently replace the other.
- The final table keeps both layers side by side. A reviewer can check what
  was measured and what was decided, including the model's confidence.

## Dashboard

One layout, three surfaces. `docs/dashboard-spec.md` defines it in full.

- Four KPI cards: total pipeline runs, healthy percentage, runs that need
  attention, blocked pipelines.
- Decision distribution and domain distribution bar charts.
- Freshness delay and duration variance trend over run time.
- A pipeline health table with both layers per run.
- A per-run detail view: deterministic metrics beside the Jev decision and
  confidence.
- Filters for domain, decision, and schema drift.

The local Streamlit dashboard reads the final table and was verified against
it: the KPI cards match the dataset. Databricks has a native AI/BI dashboard
built from the same queries (see below).

## Technology

| Area | Tools |
|---|---|
| Metrics and pipelines | Python 3.12, PySpark 3.5, Delta Lake 3.2 |
| Decision layer | Node, Vercel AI SDK (`ai`, `@ai-sdk/gateway`), `typesafe-ai/jev` |
| Local dashboard | Streamlit |
| Cloud platforms | Databricks Free Edition, Microsoft Fabric (Lakehouse) |
| Tests | pytest, 45 tests |

## Repository structure

```text
data/           pipeline_runs.csv, jev_input.json, jev_decisions.json,
                final_analytics.csv, Delta tables
src/
  generate_data.py   synthetic data generation (fixed seed)
  metrics.py        deterministic metric functions (single source of truth)
  spark_pipeline.py CSV -> metrics -> Delta table + Jev input
  build_final.py    joins Jev decisions -> final Delta table + dashboard CSV
jev/
  evaluate.mjs       Jev integration (isolated from the Python code)
  package.json       Node dependencies for the decision layer
dashboard/      app.py, the local Streamlit dashboard
notebooks/      databricks_pipeline.py, fabric_pipeline.py
docs/           dashboard-spec.md
tests/          test_metrics.py, test_generation.py, test_decisions.py
```

## Run locally

Requires Python 3.12, Java 17 on `JAVA_HOME`, and Node.js (tested with Node 22).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export JAVA_HOME=/path/to/jdk17

python -m src.generate_data     # data/pipeline_runs.csv
python -m src.spark_pipeline    # Delta metrics table + data/jev_input.json

cd jev && npm install            # Jev decision layer
AI_GATEWAY_API_KEY=... node evaluate.mjs   # data/jev_decisions.json
cd ..

python -m src.build_final        # final Delta table + data/final_analytics.csv
python -m pytest tests/ -q      # 45 tests
python -m streamlit run dashboard/app.py
```

`AI_GATEWAY_API_KEY` is read from the environment at call time. The project
never stores it.

## Jev decision layer

`jev/evaluate.mjs` is a Node script, isolated from the Python and PySpark
code. It calls the Vercel AI SDK evaluation API (`experimental_evaluate` from
the `ai` package) with the model `typesafe-ai/jev`.

For each run it sends one bounded `choice` question:

- `HEALTHY` — normal pipeline operation
- `WATCH` — a small anomaly needs observation
- `INVESTIGATE` — a material anomaly needs review
- `BLOCK` — a severe condition makes downstream data unsafe

The question contains only the run's measured state from
`data/jev_input.json`. Jev computes no metrics and generates no explanations.
The decision is the model's answer. The confidence is the native probability
the API returns for the chosen label, or `null` if the API returns none. The
script never writes a confidence value itself.

## Databricks

Tested end to end on Databricks Free Edition. The notebook
`notebooks/databricks_pipeline.py` completed the full flow on a live
workspace:

1. Loaded `pipeline_runs.csv` from a Unity Catalog volume, for example
   `/Volumes/<catalog>/default/insurance`.
2. Ran the PySpark transformations with the same metric functions as the
   local pipeline.
3. Wrote the Delta table `pipeline_metrics`.
4. Joined all 40 Jev decisions, with coverage and label checks.
5. Created the final Delta table `pipeline_analytics`.
6. Ran the six dashboard SQL queries (KPI cards, decision distribution,
   domain distribution, freshness trend, pipeline health table, severe-run
   queue).
7. Created and published a native AI/BI dashboard from those queries.

To reproduce: create a Free Edition workspace, upload
`data/pipeline_runs.csv` and `data/jev_decisions.json` to a volume such as
`/Volumes/<catalog>/default/insurance`, import the notebook, set the volume
path at the top, and run all cells.

### Dashboard evidence

The native Databricks AI/BI dashboard was tested and published.

![Databricks Insurance Data Reliability Control Room](docs/screenshots/databricks-dashboard.png)

[View the PDF export](docs/screenshots/databricks-dashboard.pdf)

## Microsoft Fabric

Fabric support is implemented but was not tested in a live Fabric workspace.
Treat it as prepared, not validated.

`notebooks/fabric_pipeline.py` mirrors the Databricks logic: it loads the two
files from a Lakehouse `Files/insurance/` folder, applies the same PySpark
transformations, writes `pipeline_metrics` and `pipeline_analytics` as Delta
tables, and joins the Jev decisions with the same checks. The notebook ends
with manual steps for a Power BI report on `pipeline_analytics`, following
`docs/dashboard-spec.md`.

## Tests

```bash
python -m pytest tests/ -q   # 45 tests pass
```

- `test_metrics.py` — every metric function against hand-computed values.
- `test_generation.py` — determinism, run count, status consistency, CSV
  round trip.
- `test_decisions.py` — Jev coverage and labels, confidence bounds, and
  consistency between the source runs, the Jev output, and the final table
  (metrics recomputed from source data match the final table).

## Limitations

- Synthetic data only: 40 runs across two days. No streaming, backfills,
  alerting, or scheduling.
- The Jev step needs `AI_GATEWAY_API_KEY` in the environment. Without it, the
  decision layer cannot run.
- The Fabric notebook was not run in a live workspace.
- The metric functions are mirrored inside both notebooks so cloud runs match
  the local pipeline; `src/metrics.py` is the reference copy.
- The dashboard is read-only.
