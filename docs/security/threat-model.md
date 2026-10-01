# STRIDE threat model

| Threat | Example | Control in prototype | Remaining production work |
| --- | --- | --- | --- |
| Spoofing | Forged OEM event or stolen user token | Broker boundary, authenticated API, signed short-lived JWT | Per-device mTLS/OIDC, key rotation, broker ACLs, token revocation |
| Tampering | Altered telemetry or alert acknowledgement | JSON validation, event ID idempotency, role check, audit row | TLS everywhere, immutable audit export, schema registry/signatures |
| Repudiation | User denies alert action | `audit_log` records actor, tenant and action | Append-only managed audit store and retention controls |
| Information disclosure | Cross-tenant vehicle lookup | Tenant derived from JWT and included in every query | Automated isolation tests, row-level security, privacy assessment |
| Denial of service | Event burst exhausts worker or storage | Kafka buffering, bounded API page sizes, consumer replay | Per-tenant quotas, backpressure, autoscale, WAF/rate limits, load/chaos evidence |
| Elevation of privilege | Viewer acknowledges an alert | API checks admin/manager role | Central policy engine and negative authorization testing |

Location is synthetic in this build. For real fleet data, minimize location precision and retention, document lawful purpose, mask driver identifiers, encrypt transit/rest, support tenant export and deletion, and have counsel assess applicable privacy law (including India's DPDP Act and GDPR where relevant). The prototype has not received legal or compliance certification. AI actions are not autonomous: no LLM is connected, and rule scores are advisory.
