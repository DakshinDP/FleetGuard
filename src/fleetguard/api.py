import base64
from datetime import datetime, timezone
import time
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from fleetguard.config import settings
from fleetguard.clickhouse import client as clickhouse_client, ensure_schema
from fleetguard.security import decode_token, issue_token, password_hash, password_matches

app = FastAPI(title="FleetGuard API", version="1.0.0", description="Tenant-scoped fleet risk and telemetry API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
bearer = HTTPBearer(auto_error=False)
REQUESTS = Counter("fleetguard_api_requests_total", "API requests", ["route"])
LATENCY = Histogram("fleetguard_api_request_seconds", "API handler latency", ["route"])


@app.middleware("http")
async def collect_metrics(request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    label = route.path if route else "unmatched"
    REQUESTS.labels(label).inc()
    LATENCY.labels(label).observe(time.perf_counter() - started)
    return response


def connection():
    return psycopg.connect(settings.postgres_dsn, connect_timeout=5)


@app.on_event("startup")
def bootstrap_demo_user():
    salt, hashed = password_hash(settings.demo_password)
    with connection() as conn:
        conn.execute("INSERT INTO users(tenant_id,email,password_salt,password_hash,role) VALUES (%s,%s,%s,%s,'admin') ON CONFLICT(email) DO NOTHING",
                     (settings.tenant_id, settings.demo_email, salt, hashed))
    ensure_schema().close()


class Login(BaseModel):
    email: str
    password: str


class Acknowledge(BaseModel):
    note: str | None = None


def actor(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if not credentials:
        raise HTTPException(status_code=401, detail="Bearer token required", headers={"WWW-Authenticate": "Bearer"})
    try:
        return decode_token(credentials.credentials, settings.jwt_secret)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def audit(claims: dict, action: str, resource: str):
    with connection() as conn:
        conn.execute("INSERT INTO audit_log(tenant_id,actor,action,resource) VALUES (%s,%s,%s,%s)",
                     (claims["tenant"], claims["sub"], action, resource))


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/v1/auth/token")
def login(body: Login):
    with connection() as conn:
        row = conn.execute("SELECT tenant_id,email,password_salt,password_hash,role,active FROM users WHERE email=%s", (body.email.lower(),)).fetchone()
    if not row or not row[5] or not password_matches(body.password, row[2], row[3]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = issue_token(row[1], row[0], row[4], settings.jwt_secret)
    claims = {"sub": row[1], "tenant": row[0]}
    audit(claims, "auth.login", "user")
    return {"access_token": token, "token_type": "bearer", "expires_in": 1800, "role": row[4]}


@app.get("/api/v1/fleet/summary")
def summary(claims: dict = Depends(actor)):
    with connection() as conn:
        vehicles = conn.execute("SELECT count(*) FROM vehicles WHERE tenant_id=%s AND status='active'", (claims["tenant"],)).fetchone()[0]
        alerts = conn.execute("SELECT count(*) FILTER (WHERE acknowledged_at IS NULL), count(*) FILTER (WHERE severity='critical' AND acknowledged_at IS NULL) FROM alerts WHERE tenant_id=%s", (claims["tenant"],)).fetchone()
        recent = conn.execute("SELECT count(*) FROM telemetry_seen WHERE tenant_id=%s AND seen_at > now()-interval '5 minutes'", (claims["tenant"],)).fetchone()[0]
    audit(claims, "fleet.summary.read", "fleet")
    return {"vehicles": vehicles, "open_alerts": alerts[0], "critical_alerts": alerts[1], "events_5m": recent}


@app.get("/api/v1/vehicles")
def vehicles(q: str = "", limit: int = Query(50, ge=1, le=200), after: str | None = None, claims: dict = Depends(actor)):
    with connection() as conn:
        rows = conn.execute("SELECT vehicle_id,make,model,model_year,powertrain,status FROM vehicles WHERE tenant_id=%s AND vehicle_id>%s AND vehicle_id ILIKE %s ORDER BY vehicle_id LIMIT %s",
                            (claims["tenant"], after or "", f"%{q[:80]}%", limit)).fetchall()
    audit(claims, "vehicles.list", "vehicle")
    return {"items": [dict(zip(("vehicle_id","make","model","model_year","powertrain","status"), r)) for r in rows], "next_after": rows[-1][0] if len(rows) == limit else None}


@app.get("/api/v1/alerts")
def alerts(limit: int = Query(50, ge=1, le=200), after: str | None = None, claims: dict = Depends(actor)):
    cursor = None
    if after:
        try:
            decoded = base64.urlsafe_b64decode(after + "==").decode().split("|", 1)
            cursor = (datetime.fromisoformat(decoded[0]), decoded[1])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid alert cursor")
    with connection() as conn:
        rows = conn.execute("SELECT alert_id,vehicle_id,severity,code,title,detail,risk_score,event_ts,acknowledged_at FROM alerts WHERE tenant_id=%s AND (%s::timestamptz IS NULL OR (event_ts,alert_id)<(%s::timestamptz,%s::uuid)) ORDER BY event_ts DESC,alert_id DESC LIMIT %s",
                            (claims["tenant"], cursor[0] if cursor else None, cursor[0] if cursor else None, cursor[1] if cursor else None, limit + 1)).fetchall()
    audit(claims, "alerts.list", "alert")
    keys = ("alert_id","vehicle_id","severity","code","title","detail","risk_score","event_ts","acknowledged_at")
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_after = None
    if has_more and rows:
        next_after = base64.urlsafe_b64encode(f"{rows[-1][7].isoformat()}|{rows[-1][0]}".encode()).decode().rstrip("=")
    return {"items": [dict(zip(keys, r)) for r in rows], "next_after": next_after}


@app.post("/api/v1/alerts/{alert_id}/ack")
def acknowledge(alert_id: str, body: Acknowledge, claims: dict = Depends(actor)):
    if claims["role"] not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Manager role required")
    with connection() as conn:
        row = conn.execute("UPDATE alerts SET acknowledged_at=%s,acknowledged_by=%s WHERE alert_id=%s AND tenant_id=%s RETURNING alert_id",
                           (datetime.now(timezone.utc), claims["sub"], alert_id, claims["tenant"])).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")
    audit(claims, "alert.acknowledge", f"alert:{alert_id}")
    return {"alert_id": alert_id, "acknowledged": True, "note": body.note}


@app.get("/api/v1/analytics/telemetry")
def telemetry(hours: int = Query(24, ge=1, le=720), claims: dict = Depends(actor)):
    ch = clickhouse_client()
    result = ch.query("SELECT toStartOfMinute(event_ts) AS bucket, count() AS events, avg(risk_score) AS avg_risk FROM fleetguard.telemetry WHERE tenant_id = {tenant:String} AND event_ts >= now() - INTERVAL {hours:UInt32} HOUR GROUP BY bucket ORDER BY bucket",
                      parameters={"tenant": claims["tenant"], "hours": hours})
    audit(claims, "analytics.telemetry.read", "telemetry")
    return {"items": [{"bucket": row[0].isoformat(), "events": row[1], "avg_risk": round(row[2], 2)} for row in result.result_rows]}
