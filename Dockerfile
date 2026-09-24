FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless nodejs npm \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sfn /usr/lib/jvm/java-17-openjdk-* /usr/lib/jvm/default-jvm

ENV JAVA_HOME=/usr/lib/jvm/default-jvm
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements.txt pyproject.toml ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install -U pip \
    && /opt/venv/bin/pip install -r requirements.txt \
    && /opt/venv/bin/pip install -e ".[dev]"

COPY jev/package.json ./jev/
RUN cd jev && npm install && cd ..

COPY src ./src
COPY scripts ./scripts
COPY tests ./tests
COPY data/pipeline_runs.csv data/jev_input.json data/jev_decisions.json data/final_analytics.csv ./data/
COPY web/package.json web/package-lock.json ./web/
RUN cd web && npm ci && cd ..

COPY web/src ./web/src
COPY web/tsconfig.json web/next.config.mjs ./web/

CMD ["python", "-m", "pytest", "tests/", "-q"]
