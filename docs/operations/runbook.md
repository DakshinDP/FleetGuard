# Local operations and recovery

1. Copy `.env.example` to `.env`; replace database and JWT secrets before network use.
2. Run `docker compose up --build` and wait for database, broker and API health.
3. Check `docker compose ps`, then `docker compose logs -f simulator worker api`.
4. API `/healthz` reports process health. Prometheus at `:9090` scrapes API handler counters and latency; Grafana is available at `:3001`.
5. Redpanda Console at `:8080` shows `telemetry.raw` and `telemetry.dlq`. Invalid schemas are written to DLQ. Review them before any manual replay.
6. If a sink is unavailable, the worker does not commit that Kafka offset and seeks back to retry. Check the outbox pending rows with `SELECT count(*) FROM telemetry_outbox WHERE delivered_at IS NULL;`.
7. Restarting a consumer group replays uncommitted events. PostgreSQL idempotency and the outbox avoid duplicate alerts; ClickHouse `ReplacingMergeTree` eventually merges identical ordering keys.
8. `docker compose down` preserves named volumes. `docker compose down -v` deletes local data.

This is a development runbook, not a production incident procedure. There is no configured paging, backup restore exercise, HA deployment, or S3 archive job.
