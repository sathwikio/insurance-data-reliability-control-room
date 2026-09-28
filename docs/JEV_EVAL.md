# Jev Decision Quality (checked-in, seed 42)

Offline semantic check — complements shape/coverage tests in `tests/test_decisions.py`.
Enforced by `tests/test_jev_quality.py`. Regenerate after any fresh `jev/evaluate.mjs` run.

## Confusion: synthetic `status` vs `jev_decision` (40 runs)

| status   | HEALTHY | WATCH | INVESTIGATE | BLOCK |
|----------|---------|-------|-------------|-------|
| healthy  | 23      | 0     | 0           | 0     |
| degraded | 0       | 2     | 7           | 0     |
| failed   | 0       | 0     | 0           | 8     |

## Invariants

- `failed` → `BLOCK` (8/8)
- `healthy` → `HEALTHY` (23/23)
- `degraded` → `WATCH` or `INVESTIGATE` (9/9)
- `HEALTHY` rows have `failure_rate < 0.01`
- `jev_confidence`: 0 nulls in checked-in run (nullable by contract when API returns no distribution)

## Provenance

- Model: `typesafe-ai/jev`, prompt version `v1` — see `data/jev_run_meta.json` for `promptHash`/`inputHash`.
- A fresh Jev run is not idempotent; update this table when decisions change.
