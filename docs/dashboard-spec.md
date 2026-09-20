# Dashboard Specification — Insurance Data Reliability Control Room

One dashboard definition, implemented identically on three surfaces:

| Surface | Data source |
|---|---|
| Local (Streamlit, `dashboard/app.py`) | `data/final_analytics.csv` |
| Databricks dashboard | Delta table `pipeline_analytics` (notebook: `notebooks/databricks_pipeline.py`) |
| Microsoft Fabric / Power BI | Lakehouse Delta table `pipeline_analytics` (notebook: `notebooks/fabric_pipeline.py`) |

The two platform dashboards must stay visually comparable: same KPI cards,
same chart titles, same table columns, same filters.

## KPI cards (four, one row)

| Card | Definition | Visual |
|---|---|---|
| Total pipeline runs | `COUNT(*)` | card, integer |
| Healthy % | share of runs with `jev_decision = HEALTHY` | card, percent |
| Requires attention | runs with `jev_decision IN (WATCH, INVESTIGATE)` | card, integer |
| Blocked pipelines | runs with `jev_decision = BLOCK` | card, integer |

## Charts

| Title | Type | Fields |
|---|---|---|
| Decision distribution | bar | axis: `jev_decision`; value: run count |
| Domain distribution | bar | axis: `domain`; value: run count; legend: `jev_decision` |
| Freshness and duration trend | line | axis: `run_timestamp`; value: `freshness_delay_minutes` (toggle to `duration_variance`) |

## Filters (available on every page/section)

- `domain` — multi-select
- `jev_decision` — multi-select over HEALTHY / WATCH / INVESTIGATE / BLOCK
- `schema_drift_present` — boolean toggle ("schema drift only")

## Pipeline health table

Columns, in order:

`run_id`, `pipeline_name`, `domain`, `run_timestamp`, `status`,
`jev_decision`, `jev_confidence`, `failure_rate`, `row_count_variance`,
`duration_variance`, `freshness_delay_minutes`, `freshness_severity`,
`schema_drift`

Default sort: `run_timestamp` descending. Row count visible.

## Detail view (single run)

Selected by `run_id`. Shows both layers side by side:

**Deterministic metrics (left):** `pipeline_name`, `domain`,
`run_timestamp`, `status`, `expected_rows`, `actual_rows`, `failed_rows`,
`failure_rate`, `row_count_variance`, `duration_seconds`,
`expected_duration_seconds`, `duration_variance`,
`freshness_delay_minutes`, `freshness_severity`, `schema_drift`,
`schema_drift_present`, `error_present`, `error_message`.

**Jev decision (right):** `jev_decision` (prominent), `jev_confidence`
(native probability from the model, `n/a` when absent).

## Design rules

- Minimal, professional, information-dense; no decoration, animations, or
  generated text.
- The two layers are always visually distinguishable: deterministic metrics
  are facts, the Jev decision is a labeled decision layer.
- No chat, agents, or RAG surfaces anywhere.
