# Performance evidence plan

## Reference targets

| Metric | Hackathon target | Achieved | Evidence status |
| --- | --- | --- | --- |
| Sustained ingest | 100,000+ events/s | Not measured | Pending benchmark cluster |
| Burst | 3× for five minutes without loss | Not measured | Local simulator only has a short 3× cadence; no evidence |
| Dashboard freshness | under 2 s | Not measured | Pending timestamp instrumentation and load run |
| Critical alert | under 5 s | Not measured | Pending end-to-end trace |
| API p95 / p99 | under 200 ms / 500 ms | Not measured | Pending Locust report |
| Availability | 99.9% target | Not measured | Requires monitored deployment period and failure exercise |

## Reproducible collection

1. Record CPU, RAM, storage, Docker versions, service replica counts and git SHA.
2. Pre-seed the configured vehicle population. Warm the stack and confirm broker partitions and consumer group.
3. Run Locust/API load plus a dedicated Kafka producer calibrated to 1×, then 3× reference input for five minutes. Keep payload around 1 KB. Record producer acknowledgements and broker/consumer lag.
4. Add source and sink timestamps with one trace/event ID. Report ingest-to-dashboard and critical-alert percentiles, p50/p95/p99, throughput, errors and data-loss reconciliation.
5. Run a one-hour soak, restart a worker and a broker, and repeat checks. Attach raw Locust CSV, Prometheus snapshots, SQL reconciliation output and machine topology.
6. Report each result with command, date, environment, sample count and confidence caveat. Never substitute generator publish counts for end-to-end throughput.

## SQL optimization evidence

No `EXPLAIN ANALYZE` result is claimed. Capture plans on seeded data for tenant alert listing, vehicle search and 24-hour telemetry aggregation before tuning. The relational schema has tenant/time and tenant/status composite indexes; analytics uses ClickHouse order keys. Store the exact plans, data cardinalities, DB versions and before/after milliseconds here after measurement.
