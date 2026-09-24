# ADR 001 — Separate measurement from judgment

Date: 2026-09-19
Status: accepted

## Context

Pipeline health needs both numeric facts (failure rate, variance, freshness) and an operational call (`HEALTHY/WATCH/INVESTIGATE/BLOCK`). Mixing them makes results untestable and model-dependent.

## Decision

- `src/metrics.py` computes all deterministic metrics in pure Python.
- Spark (`src/spark_pipeline.py`) calls those functions via UDFs; it adds no new logic.
- `jev/evaluate.mjs` receives only measured state and returns one bounded label with native confidence.
- `src/build_final.py` joins on `run_id` only after coverage and label checks pass.

## Consequences

- Metrics are reproducible without any API key.
- Decisions are constrained to four labels and auditable beside the metrics.
- The Jev step requires `AI_GATEWAY_API_KEY`; CI and offline runs use the checked-in sample decisions.
