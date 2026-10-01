"""Create the demo ClickHouse schema on startup so fresh installs are self-contained."""
import clickhouse_connect

from fleetguard.config import settings


def client():
    return clickhouse_connect.get_client(host=settings.clickhouse_host, port=settings.clickhouse_port)


def ensure_schema():
    ch = client()
    ch.command("CREATE DATABASE IF NOT EXISTS fleetguard")
    ch.command("""
        CREATE TABLE IF NOT EXISTS fleetguard.telemetry (
          event_date Date,
          event_ts DateTime64(3, 'UTC'),
          event_id String,
          tenant_id LowCardinality(String),
          vehicle_id String,
          source_oem LowCardinality(String),
          speed_kmh Float32,
          engine_temp_c Float32,
          battery_soc_pct Nullable(Float32),
          odometer_km Float32,
          latitude Nullable(Float64),
          longitude Nullable(Float64),
          dtc Array(String),
          harsh_brake UInt8,
          risk_score UInt8,
          schema_version UInt16
        ) ENGINE = ReplacingMergeTree
        PARTITION BY toYYYYMM(event_date)
        ORDER BY (tenant_id, vehicle_id, event_ts, event_id)
        TTL event_date + INTERVAL 90 DAY DELETE
    """)
    return ch
