# FleetGuard AI

FleetGuard is a connected-fleet predictive maintenance prototype. It accepts synthetic OEM telemetry, normalizes it into a versioned event shape, evaluates explainable fault rules, and exposes tenant-scoped vehicle, alert, and analytics views.

## Start locally

Requirements: Docker Compose v2 and 4 GB available memory.

```sh
cp .env.example .env
docker compose up --build
```

Open the dashboard at <http://localhost:3000>, the API docs at <http://localhost:8000/docs>, Redpanda Console at <http://localhost:8080>, and Grafana at <http://localhost:3001>. Demo login is `demo@fleetguard.local` / `ChangeMe-123!`; change it before exposing the stack to a network. The simulator creates 100,000 logical vehicle records and emits synthetic telemetry. Use `VEHICLE_COUNT` and `EVENTS_PER_SECOND` in `.env` to tune the demo.

Stop with `docker compose down`; `docker compose down -v` also removes local data.

## What runs

| Component | Responsibility | Store / protocol |
| --- | --- | --- |
| Simulator | Synthetic OEM A/B/C payloads, duplicates, disorder, bursts | Kafka `telemetry.raw` |
| Stream worker | Validation, canonicalization, deduplication, risk rules, alerting | Kafka, PostgreSQL, ClickHouse, Redis |
| API | JWT login, role checks, tenant-scoped fleet and alert queries | HTTPS/JSON, PostgreSQL, ClickHouse |
| PostgreSQL | Tenant, vehicle, alert and audit records with transactional consistency | CP relational core |
| ClickHouse | Append-oriented telemetry history and grouped analytics | AP/eventual analytics |
| Redis | Short-lived latest-event and dedupe state | Ephemeral cache |
| Static dashboard | Login, fleet summary, risk table, alert acknowledgement | Browser → API |

## Scale and evidence

100,000 is the number of synthetic logical vehicles seeded in PostgreSQL, not a claim that this laptop stack sustains 100,000 events/second. The reference targets (100K events/s, 3× burst for five minutes, dashboard under 2s, critical alert under 5s, API p95 under 200ms/p99 under 500ms, 99.9% availability) require benchmark runs on a declared cluster. No benchmark values are fabricated. See `docs/solution-document/performance-evidence.md` for a reproducible Locust plan and evidence table.

## Commands

```sh
docker compose up --build                 # entire demo
docker compose --profile loadtest up --build
docker compose logs -f worker simulator
docker compose down
```

## Cloud demo

`infra/terraform-compose/` contains an AWS EC2 deployment for the whole Compose stack. It requires an existing public subnet, a trusted client CIDR, an AWS session, and review of monthly resource costs. It is demo-only (single node, HTTP, no HA/backup). Read its deployment guide before applying. `infra/terraform/` is a separate API-only ECS starter.

API endpoints are documented by OpenAPI at `/docs`. Key routes: `POST /api/v1/auth/token`, `GET /api/v1/fleet/summary`, `GET /api/v1/vehicles`, `GET /api/v1/alerts`, `POST /api/v1/alerts/{id}/ack`, and `GET /api/v1/analytics/telemetry`.

## Design and limitations

The demo uses at-least-once Kafka delivery with an idempotent `(vehicle_id, event_id)` unique key; it does not promise cross-store exactly-once writes. A transactional PostgreSQL core holds ownership, alerts and audit data. ClickHouse is the analytical telemetry store; Redis state can be rebuilt. Synthetic location is generated around Chennai and is not personal data. Authentication is a compact HS256 JWT implementation with PBKDF2 password hashing for a reproducible local demo; production should use a managed OIDC provider, TLS, managed secrets, key rotation, stronger rate-limiting and a formal privacy-erasure workflow.

The UI is intentionally a lightweight static client to keep local startup simple. The AWS Terraform and Kubernetes files are deployment starting points and need environment-specific state, secrets, capacity, policy and review before use. The challenge's multi-region availability and throughput objectives are targets, not achieved properties of Docker Compose.

## Development

Python package is under `src/fleetguard`. Configuration is environment based; `.env.example` documents each variable. SQL DDL and the 100K synthetic vehicle seed are in `database/`. Architecture, ADRs, threat model, feature traceability, operations and submission draft are in `docs/`. CI definitions are in `.github/workflows/`.

Run the pure unit suite with `python -m pip install -e ".[dev]"` followed by `python -m unittest discover -s tests -v`. The unit suite does not replace the broker/database integration, load, security or chaos evidence still required by the challenge.

## License and declarations

This independent hackathon prototype is not affiliated with Motorq. All generated telemetry is synthetic. Third-party packages and their licenses are enumerated in `docs/solution-document/declarations.md`; verify the generated dependency SBOM before distribution. AI assistance was used to scaffold and document this implementation and must be declared by the submitting team.
