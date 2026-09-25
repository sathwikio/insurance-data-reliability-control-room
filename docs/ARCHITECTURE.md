# Architecture

See also: `docs/architecture/system-architecture.svg`, `docs/architecture/jev-data-flow.svg`
(plus same-name `.html` explorable viewers).

```text
src/generate_data.py (seed 42)
  -> data/pipeline_runs.csv (40 runs, 5 domains)
  -> src/spark_pipeline.py (UDFs call src/metrics.py; pure Python, tested)
    -> data/delta/pipeline_metrics (Delta · local path)
    -> data/jev_input.json (JSON file · measured, unlabeled — no stream, no queue)
  -> jev/evaluate.mjs (typesafe-ai/jev, bounded choice, external, not idempotent)
    -> data/jev_decisions.json (one label + native confidence per run)
  -> src/build_final.py (coverage + label validation, join on run_id)
    -> on failure: stop, no output (no dead-letter; rerun from checked-in inputs)
    -> data/delta/pipeline_analytics + data/final_analytics.csv
       (Delta · Unity Catalog table + CSV export)
  -> notebooks/databricks_pipeline.py -> Delta + AI/BI dashboard (verified)
  -> web/ (Next.js static mirror of final_analytics.csv via scripts/sync_web_data.py)
  -x notebooks/fabric_pipeline.py (future target · not deployed)
```

## Key decisions

- Measurement and judgment are separate processes. Python computes facts; Jev assigns exactly one operational label.
- `src/metrics.py` is the single source of truth. Spark UDFs call it directly; the Databricks notebook mirrors it verbatim.
- `jev_input.json` is a plain JSON file, not a message bus. There is no streaming in this project.
- The final join refuses partial coverage. Missing/extra/invalid decisions raise `ValueError` and produce no output.
- Grain is `run_id`. Contract: exactly one allowed label per run (`HEALTHY/WATCH/INVESTIGATE/BLOCK`).
- `jev_confidence` is informational (nullable; null when the API returns no distribution). Nothing gates on it.
- A fresh Jev run is not idempotent — metrics reproduce byte-identically, decisions may not.
- All data is synthetic. No customer data, no insurer connection, dashboards are read-only.
- Fabric is a future target, not a deployment. The diagrams show it dashed for that reason.
