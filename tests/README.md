# Verification plan

The current unit suite covers pure event normalization, rule scoring, password verification and JWT integrity. Run it from the repository root with:

```sh
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

Before submission, add:

- Unit checks for OEM normalization, malformed fields, fault score thresholds, JWT expiry/signature and password verification.
- Integration checks for duplicate/out-of-order events, PostgreSQL idempotency/outbox, ClickHouse insertion, and DLQ behavior.
- Contract checks for OpenAPI schemas, pagination, 401/403/404 responses and cross-tenant isolation.
- Acceptance flow for login → generated event → alert in dashboard → manager acknowledgement.
- Performance, soak, security scan, broker/worker restart and audit/erasure evidence.

The GitHub workflow runs the unit suite, Ruff, Trivy filesystem scan and container builds. Integration, contract, acceptance, performance, security-dynamic, chaos and erasure evidence remain outstanding; do not report the plan as executed evidence.
