# Scope Limits (prototype — batch, 40 synthetic runs)

This project is a control-room **prototype**, not a production control room.

## What it is

- Batch over `data/pipeline_runs.csv` (seed 42, 40 runs, 2 days, 5 domains).
- Deterministic metrics in `src/metrics.py` + bounded Jev labels (`HEALTHY/WATCH/INVESTIGATE/BLOCK`).
- Offline path reuses checked-in `data/jev_decisions.json`; fresh Jev runs need `AI_GATEWAY_API_KEY` and are not idempotent (see `data/jev_run_meta.json`).

## What it is not

- No schedule, no streaming, no backfill, no alerts.
- `src/spark_pipeline.py` uses `local[1]`, `shuffle.partitions=1`, Python UDFs per row — chosen for determinism, ~10-100x slower than native functions.
- Delta writes are `overwrite`-only; `src/build_final.py` fail-stops with no output and no quarantine/dead-letter table.
- Dashboards are read-only. `notebooks/fabric_pipeline.py` is unverified live.

## When to replace

- Real volumes → replace UDFs with native Spark functions, partition by `domain`/`run_timestamp`, switch to incremental loads with watermarks.
- Real ops → add `run_id` PK enforcement in Delta (beyond the count check in `main`), quarantine table on validation failure, scheduled runs + alerting.
- Fresh evaluations → update `docs/JEV_EVAL.md` confusion table and `data/jev_run_meta.json`.
