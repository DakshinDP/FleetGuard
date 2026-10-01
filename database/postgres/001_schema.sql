CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS tenants (
  tenant_id text PRIMARY KEY, name text NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS users (
  user_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id text NOT NULL REFERENCES tenants,
  email text NOT NULL UNIQUE, password_salt text NOT NULL, password_hash text NOT NULL,
  role text NOT NULL CHECK (role IN ('admin','manager','viewer')), active boolean NOT NULL DEFAULT true
);
CREATE TABLE IF NOT EXISTS vehicles (
  vehicle_id text PRIMARY KEY, tenant_id text NOT NULL REFERENCES tenants, make text NOT NULL,
  model text NOT NULL, model_year smallint NOT NULL, powertrain text NOT NULL,
  status text NOT NULL DEFAULT 'active', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS vehicles_tenant_status_idx ON vehicles(tenant_id,status,vehicle_id);
CREATE TABLE IF NOT EXISTS alerts (
  alert_id uuid PRIMARY KEY, tenant_id text NOT NULL REFERENCES tenants,
  vehicle_id text NOT NULL REFERENCES vehicles, event_id text NOT NULL, severity text NOT NULL,
  code text NOT NULL, title text NOT NULL, detail text NOT NULL, risk_score smallint NOT NULL,
  event_ts timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  acknowledged_at timestamptz, acknowledged_by text, UNIQUE(vehicle_id,event_id,code)
);
CREATE INDEX IF NOT EXISTS alerts_tenant_time_idx ON alerts(tenant_id,event_ts DESC,alert_id);
CREATE TABLE IF NOT EXISTS audit_log (
  audit_id bigserial PRIMARY KEY, tenant_id text NOT NULL, actor text NOT NULL,
  action text NOT NULL, resource text NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS audit_tenant_time_idx ON audit_log(tenant_id,occurred_at DESC);
CREATE TABLE IF NOT EXISTS telemetry_seen (
  tenant_id text NOT NULL, event_id text NOT NULL, seen_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(tenant_id,event_id)
);
CREATE INDEX IF NOT EXISTS telemetry_seen_time_idx ON telemetry_seen(tenant_id,seen_at DESC);
CREATE TABLE IF NOT EXISTS telemetry_outbox (
  tenant_id text NOT NULL, event_id text NOT NULL, payload jsonb NOT NULL,
  delivered_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(tenant_id,event_id)
);
CREATE INDEX IF NOT EXISTS telemetry_outbox_pending_idx ON telemetry_outbox(created_at) WHERE delivered_at IS NULL;

INSERT INTO tenants(tenant_id,name) VALUES ('demo-fleet','Synthetic demonstration fleet') ON CONFLICT DO NOTHING;
INSERT INTO vehicles(vehicle_id,tenant_id,make,model,model_year,powertrain)
SELECT 'FG-' || lpad(n::text,6,'0'),'demo-fleet',
       (ARRAY['Volvo','Subaru','Stellantis','Generic'])[1+(n%4)::int],
       (ARRAY['E-Transit','XC60','Outback','e-208'])[1+(n%4)::int],
       2019+(n%8)::int, (ARRAY['ICE','Hybrid','EV'])[1+(n%3)::int]
FROM generate_series(1, greatest(1, coalesce(nullif(current_setting('fleetguard.vehicle_count',true),''),'100000')::int)) AS n
ON CONFLICT(vehicle_id) DO NOTHING;
