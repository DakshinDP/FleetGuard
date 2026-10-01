"""Short burst generator for smoke-load runs; not a capacity benchmark."""
import json
import time
from datetime import datetime, timezone
from uuid import uuid4

from confluent_kafka import Producer

from fleetguard.config import settings

producer = Producer({"bootstrap.servers": settings.kafka, "linger.ms": 20, "compression.type": "lz4"})
deadline = time.time() + 30
count = 0
while time.time() < deadline:
    now = datetime.now(timezone.utc).isoformat()
    body = {"event_id": str(uuid4()), "vehicle_id": f"FG-{count % max(1, settings.vehicle_count)+1:06d}",
            "tenant_id": settings.tenant_id, "source_oem": "oem-a", "schema_version": 1, "event_ts": now,
            "speed_kmh": 44, "engine_temp_c": 90, "battery_soc_pct": 68, "odometer_km": count % 100000,
            "latitude": 13.08, "longitude": 80.2, "dtc": [], "harsh_brake": False}
    producer.produce("telemetry.raw", key=body["vehicle_id"].encode(), value=json.dumps(body).encode())
    producer.poll(0)
    count += 1
producer.flush(30)
print(f"published {count} events in 30 seconds; this is a generator count, not measured end-to-end capacity")
