# ADR 0001: Split operational and telemetry storage

**Status:** Accepted for prototype

**Context:** Telemetry inserts and long-window scans have different write/query patterns from tenant ownership, alert acknowledgement and audit transactions.

**Options:** One PostgreSQL database; PostgreSQL plus a columnar telemetry store; a single document database.

**Decision:** PostgreSQL owns transactional entities and an idempotency/outbox boundary. ClickHouse stores append-oriented telemetry; Redis stores disposable latest-event cache state.

**Consequences:** Tenant and alert changes use ACID transactions (CP preference); analytical visibility is eventually consistent (AP preference). Cross-store delivery uses replay and an outbox marker rather than a distributed transaction. Local Compose does not prove production scale.
