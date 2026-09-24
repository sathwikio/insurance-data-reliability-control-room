.PHONY: setup test lint data metrics decisions final e2e-no-key sync-web web-install web-dev web-build

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -U pip && pip install -r requirements.txt && pip install -e ".[dev]"
	cd jev && npm install

test:
	python -m pytest tests/ -q

test-cov:
	python -m pytest tests/ --cov=src --cov-report=term-missing -q

lint:
	ruff check src tests scripts
	ruff format --check src tests scripts

data:
	python -m src.generate_data

metrics:
	python -m src.spark_pipeline

decisions:
	cd jev && npm run evaluate && cd ..

final:
	python -m src.build_final

e2e-no-key: data metrics final test

sync-web:
	python scripts/sync_web_data.py

web-install:
	cd web && npm ci

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build
