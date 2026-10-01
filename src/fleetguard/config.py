from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    postgres_dsn: str = os.getenv("POSTGRES_DSN", "postgresql://fleetguard:local-only-change-me@localhost/fleetguard")
    clickhouse_host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    clickhouse_port: int = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    kafka: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
    jwt_secret: str = os.getenv("JWT_SECRET", "local-dev-secret-change-before-deploy")
    demo_email: str = os.getenv("DEMO_EMAIL", "demo@fleetguard.local").lower()
    demo_password: str = os.getenv("DEMO_PASSWORD", "ChangeMe-123!")
    tenant_id: str = os.getenv("TENANT_ID", "demo-fleet")
    vehicle_count: int = int(os.getenv("VEHICLE_COUNT", "100000"))
    events_per_second: int = int(os.getenv("EVENTS_PER_SECOND", "250"))


settings = Settings()
