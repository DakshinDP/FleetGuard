# Connected Vehicle Intelligence Hackathon
## FleetGuard AI Solution Document Draft


> This is a solution draft based on the supplied hackathon problem statement and template. It separates implemented behavior, assumptions and unmeasured targets. Replace the bracketed team and demo fields and attach real run evidence before submission.

## 1. Executive Summary

FleetGuard helps a fleet manager find synthetic vehicles that may need maintenance attention. It consumes normalized and OEM-specific telemetry from a Kafka-compatible stream, applies explicit fault rules, records tenant-scoped alerts, and shows the results in a browser dashboard. PostgreSQL holds operational records; ClickHouse supports time-series summaries; Redis stores short-lived latest-event state. A transactionally recorded outbox marker and event key make stream retries safe across the PostgreSQL/ClickHouse boundary.

The prototype seeds 100,000 logical vehicles and runs a configurable local event simulator. The 100K events/second, 3× burst for five minutes, dashboard freshness, alert latency, API percentiles and availability figures in the challenge are target values only. This environment has not produced benchmark, coverage, security-scan or uptime evidence. The unique project focus is onboarding three differing synthetic OEM payload shapes into one auditable event flow, with transparent alerts instead of unvalidated model predictions.

## 2. Problem Statement and Validation

### 2.1 Problem Statement

Fleet managers need a way to prioritize vehicle maintenance from many different connected-vehicle signals because OEM payloads vary and raw event volume obscures actionable faults. The supplied case study estimates 100,000 vehicles at one approximately 1 KB event per second could produce roughly 8.6 TB/day and 3 PB/year before compression, downsampling and filtering. Those are scenario estimates from the supplied problem statement, not measurements from FleetGuard.

**Primary user:** Fleet manager. **Secondary stakeholders:** service teams, OEM data teams, fleet finance, drivers and safety/compliance teams.

### 2.2 Evidence and Validation

| Evidence / assumption | Source or method | What it shows | Confidence |
| --- | --- | --- | --- |
| At 100K vehicles × 1 event/s × 1 KB, raw input approaches 8.6 TB/day | Arithmetic on case-study values in supplied problem statement | A single transactional SQL table is a poor fit for every workload | Medium; depends on event rate/size |
| OEM event fields and semantics vary | Three deliberately different synthetic payload adapters in `src/fleetguard/events.py` | A canonical contract simplifies consumers | High for this simulator; not proof of real OEM formats |
| Fault signals can be prioritized with simple rules | Deterministic DTC, temperature and braking rules in `src/fleetguard/risk.py` | Explainable triage behavior for the demo | Medium; not validated against maintenance outcomes |
| Operator time saved and breakdowns avoided | No interviews, public outcome dataset or field trial completed | Impact is not yet known | Low / open assumption |

**Validation method:** Synthetic end-to-end event flow and proposed reproducible load test. No user interviews, production data or predictive-maintenance outcomes are claimed. Existing OEM portals and telematics tools offer vehicle data, but this project does not claim measured superiority over a named product.

### 2.3 Impact and Success Metrics

| Metric | Baseline today | Prototype target | How to measure |
| --- | --- | --- | --- |
| Unique logical vehicles | None in this local demo | 100,000 seeded | `SELECT count(*) FROM vehicles` |
| Ingest rate | Not measured | Case-study reference: 100K/s | Acknowledged broker records / wall time, plus consumer lag |
| Alert time | Not measured | Under 5 s for critical target | Event creation timestamp to alert visibility trace |
| API response | Not measured | p95 under 200 ms, p99 under 500 ms | Locust report on declared topology |
| Prevented downtime / cost | No observed baseline | Not claimed | Requires fleet interviews and retrospective maintenance data |

Potential safety, cost and emissions benefits are hypotheses only. The demo uses synthetic location and no personal data.

## 3. Solution Description

### 3.1 Overview and User Journey

The simulator emits one of three OEM payload shapes, occasional duplicates, late events, faults and malformed messages. Redpanda accepts the raw event. A worker validates and normalizes it, applies transparent rules, stores telemetry and alerts, and sends invalid records to a dead-letter topic. The user logs in, reviews fleet metrics and risk alerts, searches vehicles, and acknowledges alerts. Vehicle-to-dashboard freshness is not yet measured.

**Screenshot:** Capture the running dashboard for the final submission. No screenshot is included in this draft because the stack has not been run in this environment.

### 3.2 Key Value Proposition

- **Customer job:** Find vehicles that need timely service attention.
- **Pain reduced:** Manual interpretation of multiple OEM-specific formats.
- **Gain:** A unified alert queue with a reason and tenant context.
- **Differentiation:** A code-traceable, replayable synthetic flow with explicit data-store boundaries. Superiority over commercial alternatives is not established.

### 3.3 Innovative Ideas

1. **Adapter-first onboarding:** three different synthetic OEM payload shapes map to one canonical event. Evidence: `events.py` and `F-02`; real OEM partner payload tests remain future work.
2. **Explainable risk hints:** each risk increment has a named reason. Evidence: `risk.py`; no failure-probability calibration is claimed.
3. **Replay-safe multi-store delivery:** PostgreSQL records event identity and an outbox state before ClickHouse delivery; Kafka offsets commit after successful completion. Evidence: `worker.py` and `telemetry_outbox`; recovery has not yet been chaos-tested.

## 4. Feature List

See `feature-matrix.md` for code-path traceability and implementation state. Video timestamps remain pending until a live demo is recorded. “Implemented” means code exists; it does not imply successful production-scale verification.

## 5. Solution Architecture

### 5.1 Architecture Overview

The C4 context/container flow, data relationships, store choices and approximate capacity model are in `../architecture/overview.md`. Telemetry travels simulator → Redpanda `telemetry.raw` → worker → PostgreSQL/outbox and ClickHouse → secured API → dashboard. Invalid messages go to `telemetry.dlq`. The prototype has no MQTT/OEM cloud integration and no external identity or LLM service.

Latency per hop is unknown until instrumented and benchmarked. The case-study goal is under two seconds from ingest to dashboard and under five seconds for a critical alert.

### 5.2 Technology Stack and Justification

| Layer | Choice | Why chosen / alternative considered |
| --- | --- | --- |
| Ingestion / messaging | Kafka protocol via Redpanda | Durable partitioned replay; direct API writes were rejected to decouple producers/consumers |
| Stream / batch | Python worker + ClickHouse queries | Small local path; Flink/Spark remains an option at measured scale |
| Relational / NoSQL / cache | PostgreSQL, ClickHouse, Redis | ACID operational core, columnar telemetry, disposable latest-state cache |
| Backend / frontend | FastAPI + static HTML/JS | Fast local setup and OpenAPI; a larger multi-team UI can move to React |
| ML / AI | Explainable deterministic rules | No labeled data to train/evaluate a model; external LLM not connected |
| Infrastructure / CI / observability | Docker Compose, K8s/ECS starter, GitHub Actions, Prometheus/Grafana | Local reproducibility plus deployment starting points; no cloud apply or full dashboard evidence |

### 5.3 Data Architecture

The relational schema is normalized into tenants, users, vehicles, alerts and audit records. The event identity and transactional outbox tables support dedupe and replay. ClickHouse intentionally denormalizes event attributes and partitions by month, ordered by tenant, vehicle and event time. Redis holds a one-hour latest-state cache. PostgreSQL is the source of truth for ownership and alert state; ClickHouse is eventually consistent analytics. A 90-day demo TTL is configured in ClickHouse; an S3/Parquet archive is not implemented.

Capacity arithmetic is 100K events/s × 1 KB ≈ 8.64 TB/day and ≈3.15 PB/year before compression/downsampling. No query `EXPLAIN ANALYZE` before/after result is claimed; measurement steps are documented in `performance-evidence.md`.

### 5.4 Deployment View

`docker-compose.yml` starts the local stack. `infra/k8s/` has namespace, service, deployment and worker autoscaling examples; the data plane and secrets must be provided. `infra/terraform/` deploys an API service to private AWS ECS/Fargate subnets with CloudWatch logging and Secrets Manager integration; networking, ingress, managed data services and image publishing are deployment inputs. Neither cloud deployment has been applied. Container portability is intended, but cloud readiness has not been operationally verified.

## 6. Low-Level Design

### 6.1 Layering and Separation

The API is organized by HTTP/auth/data access in `api.py`, event adapters in `events.py`, risk rules in `risk.py`, and store configuration in `config.py`. The worker handles broker orchestration and sink delivery. A future refactor should move repository operations behind ports and extract each adapter/worker dependency.

### 6.2 Design Principles Applied

- Environment configuration is centralized in `config.py`; no secret is intended to be committed.
- Tenant identity is taken from signed token claims and used in SQL filters.
- Event identity is idempotent in PostgreSQL; duplicates do not create duplicate alerts.
- Data validation fails early to a dead-letter topic.
- Components can be restarted; Kafka retains uncommitted work.
- Least privilege is only partially addressed: demo roles exist, but production OIDC, broker ACLs, network policy and secret rotation remain necessary.

### 6.3 Design Patterns Used

| Pattern | Use | Location |
| --- | --- | --- |
| Adapter | Maps OEM payload variants to canonical event fields | `src/fleetguard/events.py` |
| Strategy-like rule set | Named diagnostic and behavior checks contribute explainable risk | `src/fleetguard/risk.py` |
| Transactional outbox | Stores telemetry delivery state with dedupe identity | `database/postgres/001_schema.sql`, `src/fleetguard/worker.py` |
| Repository boundary | Not yet extracted; SQL is explicit in API/worker | `api.py`, `worker.py` |

### 6.4 Interfaces, Contracts and Runtime Flows

OpenAPI is generated at `/docs`; APIs are versioned under `/api/v1`. Lists are bounded to 200 rows and vehicle search uses an `after` key. Authentication uses a short-lived JWT in this local demo; the solution requires production OIDC and rate limiting. Event shape is documented in `events.py` as JSON version 1; a schema registry and compatibility automation are future work. Two critical flows are the normal event path and worker sink retry/outbox path described in `overview.md` and ADR 0002.

### 6.5 Algorithms and Data Structures

OEM adapter mapping is O(k) in payload field count and O(1) extra space beyond the normalized object. Fault rule evaluation is O(d) for `d` diagnostic codes and O(1) auxiliary state. PostgreSQL event dedupe uses a unique B-tree key; lookup/insert is expected O(log n), with database I/O and contention dominating at scale. No large-scale runtime measurement is available. The simulator generates events without materializing all 100K vehicle states in memory.

## 7. Non-Functional Requirements and Performance Benchmarks

Reference targets and the reproducible measurement plan are in `performance-evidence.md`. Tool: Locust plus a Kafka producer on a documented benchmark host. Results, percentile graphs, consumer lag, test environment, sample count, coverage and failure-recovery measurements are all pending. Local simulator event rate is a configurable demo value; it is not evidence of 100K/s.

## 8. Security and Compliance

See `../security/threat-model.md` for STRIDE risks and controls. The prototype applies short-lived signed JWTs, role checks, tenant-scoped query predicates, bounded API pages, PBKDF2 password hashing and access audit inserts. The database, broker and web dashboard are not fully TLS-protected in local Compose. Location values are synthetic. No claim of GDPR/DPDP compliance or legal review is made; privacy minimization, retention, export and erasure must be designed and verified for real data. No agent/LLM is connected.

## 9. Test Strategy

Nine pure unit tests covering adapters, risk rules and token/password behavior passed locally. Integration tests against broker/PostgreSQL/ClickHouse, tenant-isolation and role-denial contracts, BDD user flows, load/soak, security scans, and broker/worker restart tests remain pending. The code has not been run in Docker in this environment.

## 10. Observability

Prometheus scrapes API counters and handler latency summaries; Grafana is available for dashboards but no provisioned business dashboard is claimed. Worker logs include processing failures; broker consumer lag should be monitored. To investigate latency, correlate a vehicle/event ID through producer timestamp, broker lag, worker logs, ClickHouse delivery, API query and browser refresh. Trace IDs and end-to-end spans are future work.

## 11. AI / ML Component

No learned model or autonomous agent is part of the running prototype. Explainable rules provide a transparent baseline while no labeled breakdown outcomes have been assembled. Training, validation, leakage checks, model performance and AI cost therefore do not apply yet. A future model should be evaluated against these rules with time-based train/test splits, calibration, false-negative analysis, drift monitoring and human review; alerts must remain advisory until validated.

## 12. Architecture Decisions, Risks and Future Enhancements

Four ADRs in `../adr/` cover storage, messaging, consistency and authentication. Main risks: local single-node data services; demonstration credentials; no TLS or identity provider; polling dashboard; no tested restore/erasure workflow; small-codebase SQL coupling; no measured throughput; no cloud deployment evidence; no cold archive; and synthetic-only fault rules. Next steps are (1) run and instrument an end-to-end Docker demo, (2) collect real benchmark/security/test evidence and fix issues, and (3) deploy a reviewed cloud data plane, OIDC and archive lifecycle before pilot use.

## 13. Demo Video

Record a video under five minutes after the stack runs: problem/user (0:00–0:30), value (0:30–1:00), live event and alert acknowledgement (1:00–3:00), architecture and measured load/recovery evidence (3:00–4:15), results/team/next steps (4:15–5:00). **Video link:** [Add after recording]. Do not narrate target values as achieved measurements.

## 14. Repository Checklist

- README and architecture diagram: included.
- One-command local setup: `docker compose up --build`, not executed here.
- Environment example: `.env.example`.
- Service, docs and infrastructure structure: included.
- CI: Ruff, filesystem vulnerability scan and container build configured; suites are not executed here.
- Secrets: no intended live secrets; local demo defaults must be replaced before exposure.
- Final submission tag: create `v1.0-submission` only after team review and required evidence collection.

## 15. Conclusion

FleetGuard demonstrates a concrete path from heterogeneous synthetic vehicle signals to tenant-scoped, explainable maintenance alerts. The prototype makes storage trade-offs, event replay and code traceability visible. Its most significant remaining work is operational: test the stack, measure the reference targets, harden identity/network/data retention, and validate rules against real outcomes before a pilot.

## 16. Declarations

Open-source packages are listed in `declarations.md`; confirm exact resolved versions/licenses and generate an SBOM before submission. Generative AI assisted project scaffolding and documentation; the team should declare the actual tools and review originality. Data in the project is synthetic and does not contain real personal or vehicle-owner information. This project is independent and unaffiliated with Motorq.

## 17. Appendix

- Architecture and ER diagram: `../architecture/overview.md`.
- ADRs: `../adr/`.
- Threat model: `../security/threat-model.md`.
- Operations: `../operations/runbook.md`.
- Performance evidence plan: `performance-evidence.md`.
- References: supplied `Motorq_Hackathon_Problem_Statement.pdf` and `Motorq_Hackathon_Solution_Document_Template.docx`. Industry statements and targets summarized above are attributed to the provided case-study document and have not been independently verified.
