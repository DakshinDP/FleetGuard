"""Synthetic multi-OEM feed; VEHICLE_COUNT is logical fleet size, not event rate."""
import json
import logging
import random
import time
from datetime import datetime, timezone
from uuid import uuid4

from confluent_kafka import Producer

from fleetguard.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
producer = Producer({"bootstrap.servers": settings.kafka, "linger.ms": 10, "compression.type": "lz4"})


def make_event(sequence: int) -> tuple[str, dict]:
    vehicle_n = random.randint(1, max(settings.vehicle_count, 1))
    vehicle = f"FG-{vehicle_n:06d}"
    event_id = str(uuid4())
    # A small fraction arrives late/out of order to exercise event-time handling.
    timestamp = datetime.now(timezone.utc).timestamp() - (random.randint(2, 90) if random.random() < .01 else 0)
    timestamp = datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
    speed = round(max(0, random.gauss(48, 22)), 1)
    temp = round(random.gauss(91, 8), 1)
    brake = random.random() < .002
    dtc = [random.choice(["P0301", "P0420", "P0171"])] if random.random() < .001 else []
    oem = random.choice(["oem-a", "oem-b", "oem-c"])
    common = {"tenant_id": settings.tenant_id, "source_oem": oem, "schema_version": 1}
    if oem == "oem-b":
        body = {**common, "id": event_id, "vehicle": vehicle, "time": timestamp, "speed": speed, "temp_c": temp,
                "soc": round(random.uniform(10, 100), 1), "odometer": round(vehicle_n * 3.7, 1), "lat": 13.08 + random.random() * .1,
                "lon": 80.2 + random.random() * .1, "faults": dtc, "brake_hard": brake}
    elif oem == "oem-c":
        body = {**common, "eventId": event_id, "vin_ref": vehicle, "ts_utc": timestamp, "velocity": speed, "coolant": temp,
                "charge": round(random.uniform(10, 100), 1), "odo": round(vehicle_n * 3.7, 1), "gps": {"lat": 13.08, "lng": 80.2},
                "dtc_codes": dtc, "event": "HARSH_BRAKE" if brake else "TELEMETRY"}
    else:
        body = {**common, "event_id": event_id, "vehicle_id": vehicle, "event_ts": timestamp, "speed_kmh": speed,
                "engine_temp_c": temp, "battery_soc_pct": round(random.uniform(10, 100), 1), "odometer_km": round(vehicle_n * 3.7, 1),
                "latitude": 13.08 + random.random() * .1, "longitude": 80.2 + random.random() * .1, "dtc": dtc, "harsh_brake": brake}
    return vehicle, body


def main():
    interval = 1 / max(settings.events_per_second, 1)
    logging.info("simulating %s logical vehicles at target %s events/s", settings.vehicle_count, settings.events_per_second)
    n = 0
    while True:
        started = time.perf_counter()
        key, event = make_event(n)
        raw = json.dumps(event, separators=(",", ":")).encode()
        producer.produce("telemetry.raw", key=key.encode(), value=raw)
        if random.random() < .01:  # replay sample to demonstrate worker idempotency
            producer.produce("telemetry.raw", key=key.encode(), value=raw)
        if random.random() < .002:  # occasional malformed payload enters the DLQ
            producer.produce("telemetry.raw", key=key.encode(), value=b'{"source_oem":"unknown","bad":true}')
        producer.poll(0)
        n += 1
        if n % 5000 == 0:
            producer.flush(2)
            logging.info("published %s events", n)
        burst_multiplier = 3 if int(time.time()) % 300 < 15 else 1
        time.sleep(max(0, interval / burst_multiplier - (time.perf_counter() - started)))


if __name__ == "__main__":
    main()
