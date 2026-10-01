"""At-least-once stream processor; PostgreSQL idempotency key absorbs replays."""
import json
import logging
import time

import psycopg
import redis
from confluent_kafka import Consumer, KafkaError, Producer, TopicPartition

from fleetguard.config import settings
from fleetguard.clickhouse import ensure_schema
from fleetguard.events import normalize
from fleetguard.risk import evaluate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main():
    consumer = Consumer({"bootstrap.servers": settings.kafka, "group.id": "fleetguard-worker-v1",
                        "auto.offset.reset": "earliest", "enable.auto.commit": False,
                        "max.poll.interval.ms": 300000})
    dlq = Producer({"bootstrap.servers": settings.kafka})
    consumer.subscribe(["telemetry.raw"])
    ch = ensure_schema()
    cache = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    logging.info("worker subscribed to telemetry.raw")
    while True:
        message = consumer.poll(1.0)
        if message is None:
            continue
        if message.error():
            if message.error().code() != KafkaError._PARTITION_EOF:
                logging.warning("Kafka poll error: %s", message.error())
            continue
        try:
            event = normalize(json.loads(message.value()))
            score, findings = evaluate(event)
            with psycopg.connect(settings.postgres_dsn) as conn:
                inserted = conn.execute("INSERT INTO telemetry_seen(tenant_id,event_id) VALUES (%s,%s) ON CONFLICT DO NOTHING RETURNING event_id",
                                        (event["tenant_id"], event["event_id"])).fetchone()
                conn.execute("INSERT INTO telemetry_outbox(tenant_id,event_id,payload) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                             (event["tenant_id"], event["event_id"], json.dumps(event, default=str)))
                pending = conn.execute("SELECT delivered_at IS NULL FROM telemetry_outbox WHERE tenant_id=%s AND event_id=%s",
                                       (event["tenant_id"], event["event_id"])).fetchone()[0]
                if inserted:
                    conn.execute("INSERT INTO vehicles(vehicle_id,tenant_id,make,model,model_year,powertrain) VALUES (%s,%s,'Synthetic','Unknown',2025,'Unknown') ON CONFLICT DO NOTHING",
                                 (event["vehicle_id"], event["tenant_id"]))
                    for alert in findings:
                        conn.execute("INSERT INTO alerts(alert_id,tenant_id,vehicle_id,event_id,severity,code,title,detail,risk_score,event_ts) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                                     (alert["alert_id"], event["tenant_id"], event["vehicle_id"], event["event_id"], alert["severity"], alert["code"], alert["title"], alert["detail"], alert["risk_score"], event["event_ts"]))
            if pending:
                ch.insert("fleetguard.telemetry", [[event["event_ts"].date(), event["event_ts"], event["event_id"], event["tenant_id"], event["vehicle_id"], event["source_oem"], event["speed_kmh"], event["engine_temp_c"], event["battery_soc_pct"], event["odometer_km"], event["latitude"], event["longitude"], event["dtc"], int(event["harsh_brake"]), score, event["schema_version"]]],
                          column_names=["event_date","event_ts","event_id","tenant_id","vehicle_id","source_oem","speed_kmh","engine_temp_c","battery_soc_pct","odometer_km","latitude","longitude","dtc","harsh_brake","risk_score","schema_version"])
                with psycopg.connect(settings.postgres_dsn) as conn:
                    conn.execute("UPDATE telemetry_outbox SET delivered_at=now() WHERE tenant_id=%s AND event_id=%s", (event["tenant_id"], event["event_id"]))
            cache.set(f"latest:{event['tenant_id']}:{event['vehicle_id']}", json.dumps({"event_ts": event["event_ts"].isoformat(), "risk_score": score}), ex=3600)
            consumer.commit(message=message, asynchronous=False)
        except ValueError as exc:
            dlq.produce("telemetry.dlq", message.value(), key=message.key(), headers=[("reason", str(exc)[:200].encode())])
            dlq.flush(2)
            consumer.commit(message=message, asynchronous=False)
        except Exception:
            logging.exception("processing failed; leaving event uncommitted for replay")
            consumer.seek(TopicPartition(message.topic(), message.partition(), message.offset()))
            time.sleep(1)


if __name__ == "__main__":
    main()
