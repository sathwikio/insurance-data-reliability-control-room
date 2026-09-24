# Insurance Data Reliability Control Room

A small data engineering project for insurance pipeline reliability.

Python and PySpark calculate deterministic health metrics from synthetic pipeline runs. Jev maps each measured run state to one bounded operational label.

Databricks stores the final Delta table and presents it through a native AI/BI dashboard.

All data is synthetic. The project does not use customer data. It does not connect to any insurer system.

## System design

The project separates measurement from judgment.

- **Deterministic layer:** Python and PySpark calculate reliability metrics from source fields.
- **Decision layer:** Jev receives only the measured state and returns one allowed operational label.
- **Analytics layer:** Delta tables keep the metrics, decision, and model confidence together.
- **Presentation layer:** Databricks AI/BI presents the final table through SQL-backed visuals.

Jev does not calculate pipeline metrics. The Python metric functions do not assign operational labels.

```text
Synthetic insurance pipeline runs
        |
        v
Python / PySpark
deterministic metrics
        |
        v
Delta table: pipeline_metrics
        |
        +---- measured state ----> Jev
        |                           |
        |                           v
        |                 HEALTHY / WATCH /
        |                 INVESTIGATE / BLOCK
        |                           |
        +----------- join on run_id-+
                    |
                    v
Delta table: pipeline_analytics
                    |
                    v
Databricks AI/BI Dashboard
```

## Data and results

The fixed data seed creates 40 pipeline runs across five insurance domains.

| Domain | Runs |
|---|---:|
| Auto claims | 8 |
| Home claims | 8 |
| Policies | 8 |
| Billing | 8 |
| Customers | 8 |

The deterministic layer calculates these signals for every run:

- failure rate
- row count variance
- duration variance
- freshness severity
- schema drift state
- error presence

Jev returns one label for each run.

| Label | Meaning |
|---|---|
| `HEALTHY` | Normal operation |
| `WATCH` | Small anomaly that needs observation |
| `INVESTIGATE` | Material anomaly that needs review |
| `BLOCK` | Severe condition that makes downstream data unsafe |

The recorded decision distribution is 23 `HEALTHY`, 2 `WATCH`, 7 `INVESTIGATE`, and 8 `BLOCK`.

The final join requires one valid Jev decision for every source run. The pipeline stops if coverage or label checks fail.

## Databricks dashboard

The verified presentation layer is a native Databricks AI/BI dashboard.

It reads from the Delta table `pipeline_analytics`. The dashboard uses SQL queries from `notebooks/databricks_pipeline.py`.

The dashboard contains:

- four KPI cards
- decision distribution
- domain distribution
- freshness delay trend
- pipeline health table
- investigation queue

![Databricks Insurance Data Reliability Control Room](docs/screenshots/databricks-dashboard.png)

[Open the PDF export](docs/screenshots/databricks-dashboard.pdf)

## Technology

| Area | Technology |
|---|---|
| Metrics | Python 3.12, PySpark 3.5 |
| Storage | Delta Lake 3.2 |
| Decision layer | `typesafe-ai/jev`, Vercel AI SDK |
| Verified cloud platform | Databricks Free Edition |
| Dashboard | Databricks AI/BI |
| Portability target | Microsoft Fabric Lakehouse |
| Tests | pytest |

## Repository map

```text
data/
  pipeline_runs.csv
  jev_input.json
  jev_decisions.json
  final_analytics.csv

src/
  generate_data.py
  metrics.py
  spark_pipeline.py
  build_final.py

jev/
  evaluate.mjs
  package.json

notebooks/
  databricks_pipeline.py
  fabric_pipeline.py

docs/
  dashboard-spec.md
  screenshots/

tests/
  test_metrics.py
  test_generation.py
  test_decisions.py
```

The repository keeps the source data, measured state, Jev output, and final analytics export visible for review.

## Local run

Use Python 3.12, Java 17, and Node.js.

1. Create a Python environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install the Python packages.

```bash
pip install -r requirements.txt
```

3. Set `JAVA_HOME` to a Java 17 installation.

```bash
export JAVA_HOME=/path/to/jdk17
```

4. Create the synthetic source data.

```bash
python -m src.generate_data
```

5. Calculate the deterministic metrics.

```bash
python -m src.spark_pipeline
```

6. Install the Jev layer dependencies.

```bash
cd jev
npm install
```

7. Set the Vercel AI Gateway key.

```bash
export AI_GATEWAY_API_KEY=...
```

8. Run the Jev decision layer.

```bash
npm run evaluate
cd ..
```

9. Build the final Delta table and CSV export.

```bash
python -m src.build_final
```

10. Run the test suite.

```bash
python -m pytest tests/ -q
```

The key stays in the process environment. The repository does not store it.

## Databricks reproduction

The Databricks notebook ran end to end in Databricks Free Edition.

1. Create a Databricks Free Edition workspace.
2. Create or select a catalog and schema.
3. Create a Unity Catalog volume for the project files.
4. Upload `data/pipeline_runs.csv` to the volume.
5. Upload `data/jev_decisions.json` to the same volume.
6. Import `notebooks/databricks_pipeline.py`.
7. Set `CATALOG` at the top of the notebook.
8. Set the volume path if your schema or volume name differs.
9. Run all notebook cells.
10. Create the AI/BI dashboard from the final SQL queries.

The notebook creates `pipeline_metrics` and `pipeline_analytics` as Delta tables.

The notebook also verifies decision coverage and allowed labels before the final join.

## Microsoft Fabric status

The Fabric notebook mirrors the core PySpark logic and targets a Fabric Lakehouse.

The notebook creates `pipeline_metrics` and `pipeline_analytics` as Delta tables. A live Fabric workspace test is not part of this project.

The repository does not claim a verified Fabric deployment.

## Tests

The suite contains 45 pytest cases.

The tests cover metric formulas, fixed-seed data, decision coverage, allowed labels, confidence bounds, and final table consistency.

```bash
python -m pytest tests/ -q
```

## Scope limits

This project uses 40 synthetic runs across two days. It does not model live event streams, backfills, alerts, or job schedules.

The Jev step needs `AI_GATEWAY_API_KEY`. The decision layer cannot run without that key.

The dashboard is read-only. The Fabric path remains unverified in a live workspace.
