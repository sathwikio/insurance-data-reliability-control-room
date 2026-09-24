# Changelog

All notable changes follow Keep a Changelog format.

## [0.2.0] — 2026-09-24

### Added

- MIT `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `.env.example`
- `pyproject.toml`, `.python-version`, `Makefile`, `Dockerfile`, GitHub Actions CI (Python + web)
- `scripts/sync_web_data.py` to regenerate `web/src/data/runs.json` from `data/final_analytics.csv`
- `docs/DATA_DICTIONARY.md`, `docs/ARCHITECTURE.md`, `docs/ADR/001-jev-separation.md`
- `tests/test_final_logic.py` (offline validation of decision coverage rules)
- Restored `web/` Next.js source (previously removed, only build output remained)

### Fixed

- Root `.gitignore` no longer ignores `package-lock.json`; ignores `.env`, `.next/`, `out/`, Spark metastore files

## [0.1.0] — 2026-09-20

- Deterministic 40-run synthetic dataset, PySpark metrics, Jev decision layer, Delta final join
- Databricks notebook + AI/BI dashboard spec with screenshot/PDF
- 45 pytest cases
