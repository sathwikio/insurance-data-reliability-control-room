# Security Policy

## Supported versions

Only the latest `main` branch is supported with security updates.

## Reporting a vulnerability

Open a GitHub private security advisory or contact the maintainer directly. Do not open a public issue for sensitive reports.

Please include:

- Description and impact
- Steps to reproduce
- Affected commit or version

We aim to acknowledge reports within 72 hours.

## Secrets handling

- Never commit `AI_GATEWAY_API_KEY`, `.env`, Databricks tokens, or Unity Catalog paths with customer data.
- The Jev step reads `AI_GATEWAY_API_KEY` from the process environment only.
- All data in `data/` is synthetic. Do not add real insurer data.

## Scope

This project does not connect to any insurer system. The dashboard is read-only.
