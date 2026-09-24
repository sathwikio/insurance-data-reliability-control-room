# Contributing

Thanks for your interest in contributing. This project uses only synthetic data — do not submit customer or insurer data.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"

cp .env.example .env  # then set AI_GATEWAY_API_KEY for the Jev step only
make test
```

## Workflow

1. Fork and create a branch: `feat/<short-name>`.
2. Keep deterministic layer (`src/metrics.py`) and decision layer (`jev/`) separate:
   - Python computes metrics, never assigns `HEALTHY/WATCH/INVESTIGATE/BLOCK`.
   - Jev selects one label, never computes metrics.
3. Add or update tests in `tests/` for any metric, generation, or validation change.
4. Run before opening a PR:

```bash
make lint
make test
```

5. If you change `data/final_analytics.csv`, regenerate the web snapshot:

```bash
python scripts/sync_web_data.py
```

## PR checklist

- [ ] Tests pass (`make test`)
- [ ] Lint passes (`make lint`)
- [ ] `web/src/data/runs.json` regenerated if final data changed
- [ ] Docs updated (`README.md`, `docs/` as needed)
- [ ] No secrets committed (`.env`, keys, volumes)

## Reporting issues

Include: command run, Python/Java/Node versions, full error output, and whether `AI_GATEWAY_API_KEY` was set.
