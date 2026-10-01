# ADR 0003: Prefer tenant correctness for commands and availability for telemetry

**Status:** Accepted for prototype

**Context:** An alert acknowledgement and an analytics aggregate have different correctness requirements.

**Decision:** PostgreSQL transactions own users, tenant scope, alerts and audit records (CP preference during partitions). Raw event ingestion is durable and replayable; ClickHouse aggregates may lag (AP preference). Redis is a cache, never the source of truth.

**Consequences:** Dashboards may temporarily show a delay in analytics. A missing cache key is safe. A multi-region production design must measure PACELC latency/consistency trade-offs and define tenant failover.
