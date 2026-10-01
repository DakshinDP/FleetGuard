"""OEM payload adapters and canonical event validation."""
from datetime import datetime, timezone


def normalize(raw: dict) -> dict:
    source = raw.get("source_oem", "unknown").lower()
    if source == "oem-b":
        raw = {"event_id": raw.get("id"), "vehicle_id": raw.get("vehicle"), "event_ts": raw.get("time"),
               "speed_kmh": raw.get("speed"), "engine_temp_c": raw.get("temp_c"), "battery_soc_pct": raw.get("soc"),
               "odometer_km": raw.get("odometer"), "latitude": raw.get("lat"), "longitude": raw.get("lon"),
               "dtc": raw.get("faults", []), "harsh_brake": raw.get("brake_hard", False), "tenant_id": raw.get("tenant_id"),
               "source_oem": source, "schema_version": 1}
    elif source == "oem-c":
        raw = {"event_id": raw.get("eventId"), "vehicle_id": raw.get("vin_ref"), "event_ts": raw.get("ts_utc"),
               "speed_kmh": raw.get("velocity"), "engine_temp_c": raw.get("coolant"), "battery_soc_pct": raw.get("charge"),
               "odometer_km": raw.get("odo"), "latitude": raw.get("gps", {}).get("lat"), "longitude": raw.get("gps", {}).get("lng"),
               "dtc": raw.get("dtc_codes", []), "harsh_brake": raw.get("event") == "HARSH_BRAKE", "tenant_id": raw.get("tenant_id"),
               "source_oem": source, "schema_version": 1}
    else:
        raw.setdefault("schema_version", 1)
    required = ("event_id", "vehicle_id", "tenant_id", "event_ts", "speed_kmh", "engine_temp_c", "odometer_km")
    missing = [k for k in required if raw.get(k) is None]
    if missing:
        raise ValueError(f"missing required fields: {','.join(missing)}")
    if source not in {"oem-a", "oem-b", "oem-c"}:
        raise ValueError(f"unsupported source_oem: {source}")
    try:
        ts = datetime.fromisoformat(str(raw["event_ts"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("event_ts must be ISO 8601") from exc
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    out = dict(raw)
    out["event_ts"] = ts.astimezone(timezone.utc)
    out["dtc"] = list(raw.get("dtc") or [])[:32]
    out["harsh_brake"] = bool(raw.get("harsh_brake", False))
    bounds = {"speed_kmh": 300, "engine_temp_c": 250, "odometer_km": 1_000_000}
    for key, upper in bounds.items():
        out[key] = float(raw[key])
        if out[key] < 0 or out[key] > upper:
            raise ValueError(f"{key} outside accepted range")
    out["battery_soc_pct"] = float(raw["battery_soc_pct"]) if raw.get("battery_soc_pct") is not None else None
    out["latitude"] = float(raw["latitude"]) if raw.get("latitude") is not None else None
    out["longitude"] = float(raw["longitude"]) if raw.get("longitude") is not None else None
    if out["battery_soc_pct"] is not None and not 0 <= out["battery_soc_pct"] <= 100:
        raise ValueError("battery_soc_pct outside accepted range")
    if out["latitude"] is not None and not -90 <= out["latitude"] <= 90:
        raise ValueError("latitude outside accepted range")
    if out["longitude"] is not None and not -180 <= out["longitude"] <= 180:
        raise ValueError("longitude outside accepted range")
    out["source_oem"] = source
    return out
