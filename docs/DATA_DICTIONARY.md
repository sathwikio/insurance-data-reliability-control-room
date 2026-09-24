# Data Dictionary

Source: `data/pipeline_runs.csv` (synthetic, seed 42). Metrics: `src/metrics.py`. Final: `data/final_analytics.csv`.

## Source fields (`pipeline_runs.csv`)

| Field | Type | Description |
|---|---|---|
| `run_id` | string | Unique run key: `{pipeline}_{yyyymmdd}_{n}` |
| `pipeline_name` | string | Pipeline, e.g. `auto_claims_raw_ingest` |
| `domain` | string | One of `auto_claims`, `home_claims`, `policies`, `billing`, `customers` |
| `run_timestamp` | ISO-8601 | Scheduled run time |
| `expected_rows` | int | Planned row count |
| `actual_rows` | int | Delivered row count |
| `failed_rows` | int | Rows that failed processing |
| `duration_seconds` | int | Actual duration |
| `expected_duration_seconds` | int | Planned duration |
| `freshness_delay_minutes` | int | Delay vs schedule |
| `schema_drift` | string | `none`, `column_added`, `type_changed`, `column_removed` |
| `status` | string | Generator health profile: `healthy`, `degraded`, `failed` |
| `error_message` | string/null | Synthetic error text |

## Metric fields

| Field | Definition |
|---|---|
| `failure_rate` | `failed_rows / expected_rows`, 6dp, `0.0` when expected is 0 |
| `row_count_variance` | `(actual - expected) / expected`, 6dp |
| `duration_variance` | `(duration - expected_duration) / expected_duration`, 6dp |
| `freshness_severity` | `ON_TIME` ≤15, `MINOR` ≤60, `MAJOR` ≤240, else `SEVERE` |
| `schema_drift_present` | `schema_drift != "none"` |
| `error_present` | non-empty `error_message` |

## Decision fields

| Field | Values |
|---|---|
| `jev_decision` | `HEALTHY`, `WATCH`, `INVESTIGATE`, `BLOCK` |
| `jev_confidence` | Native Jev probability for the chosen label, or null |

Final join is one-to-one on `run_id`. Build fails unless every source run has exactly one allowed decision (`src/build_final.py`).
