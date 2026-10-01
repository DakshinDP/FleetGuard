# Feature traceability

| ID | Feature | Priority | Status | Code path | Demo timestamp |
| --- | --- | --- | --- | --- | --- |
| F-01 | Generate telemetry for 100K logical vehicles | Must | Implemented; local rate configurable | `src/fleetguard/simulator.py`, `database/postgres/001_schema.sql` | Record after demo |
| F-02 | Map three OEM payload shapes to canonical events | Must | Implemented | `src/fleetguard/events.py` | Record after demo |
| F-03 | Dedupe, rule score and alert by event | Must | Implemented | `src/fleetguard/worker.py`, `src/fleetguard/risk.py` | Record after demo |
| F-04 | Tenant-scoped fleet/alert API with JWT/RBAC/audit | Must | Prototype | `src/fleetguard/api.py`, `src/fleetguard/security.py` | Record after demo |
| F-05 | Analytics telemetry store and grouped endpoint | Must | Implemented; local retention 90 days | `database/clickhouse/init.sql`, `src/fleetguard/api.py` | Record after demo |
| F-06 | Dashboard search, metrics and alert acknowledgement | Must | Implemented | `frontend/` | Record after demo |
| F-07 | One-command containerized local stack | Must | Implemented; needs Docker validation | `docker-compose.yml`, `Dockerfile` | Record after demo |
| F-08 | Cloud deployment and HA evidence | Should | Partial starter manifests | `infra/` | Pending |
| F-09 | Unit, integration, load, security and chaos evidence | Must | 9 pure unit tests pass; integration/load/security/chaos evidence pending | `tests/test_core.py`, `docs/solution-document/performance-evidence.md` | Pending |
