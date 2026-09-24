# Architecture

See also: `docs/architecture/system-architecture.svg`, `docs/architecture/jev-data-flow.svg`.

```text
Synthetic runs (seed 42)
  -> src/generate_data.py -> data/pipeline_runs.csv
  -> src/spark_pipeline.py (UDFs call src/metrics.py)
    -> data/delta/pipeline_metrics + data/jev_input.json
  -> jev/evaluate.mjs (typesafe-ai/jev, bounded choice)
    -> data/jev_decisions.json
  -> src/build_final.py (coverage + label validation, join on run_id)
    -> data/delta/pipeline_analytics + data/final_analytics.csv
  -> notebooks/databricks_pipeline.py -> Delta + AI/BI dashboard
  -> web/ (Next.js static export from final_analytics.csv)
```

## Key decisions

- Measurement and judgment are separate processes. Python computes facts; Jev assigns exactly one operational label.
- `src/metrics.py` is the single source of truth. Spark UDFs call it directly; the Databricks notebook mirrors it verbatim.
- The final join refuses partial coverage. Missing/extra/invalid decisions raise `ValueError`.
- All data is synthetic. No customer data, no insurer connection, dashboard is read-only.
