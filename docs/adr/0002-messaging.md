# ADR 0002: Use a replayable partitioned event log

**Status:** Accepted for prototype

**Context:** OEM payloads arrive independently, may repeat or arrive late, and should be replayable after consumer failures.

**Options:** Direct writes from simulator to API; a work queue; a Kafka-compatible event log.

**Decision:** Redpanda exposes Kafka protocol locally. `telemetry.raw` partitions by vehicle key. The worker commits offsets only after writes complete; bad schemas go to `telemetry.dlq`.

**Consequences:** Delivery is at least once. `(tenant_id,event_id)` deduplicates PostgreSQL state. A failed ClickHouse write is retried before committing the source offset. Offset/order behavior across partitions is not global ordering.
