import unittest

from fleetguard.events import normalize
from fleetguard.risk import evaluate
from fleetguard.security import decode_token, issue_token, password_hash, password_matches


class EventNormalizationTests(unittest.TestCase):
    def test_oem_a_canonical_event(self):
        event = normalize({
            "event_id": "evt-a", "tenant_id": "tenant-a", "vehicle_id": "FG-000001",
            "source_oem": "oem-a", "event_ts": "2026-10-01T10:00:00Z", "speed_kmh": 42,
            "engine_temp_c": 90, "odometer_km": 1234, "dtc": [], "harsh_brake": False,
        })
        self.assertEqual(event["event_ts"].tzinfo is not None, True)
        self.assertEqual(event["vehicle_id"], "FG-000001")

    def test_oem_b_adapter(self):
        event = normalize({
            "id": "evt-b", "tenant_id": "tenant-a", "vehicle": "FG-000002", "source_oem": "OEM-B",
            "time": "2026-10-01T10:00:00Z", "speed": 30, "temp_c": 88, "odometer": 12,
            "faults": ["P0301"], "brake_hard": False,
        })
        self.assertEqual(event["source_oem"], "oem-b")
        self.assertEqual(event["dtc"], ["P0301"])

    def test_oem_c_adapter(self):
        event = normalize({
            "eventId": "evt-c", "tenant_id": "tenant-a", "vin_ref": "FG-000003", "source_oem": "oem-c",
            "ts_utc": "2026-10-01T10:00:00Z", "velocity": 30, "coolant": 88, "odo": 12,
            "gps": {"lat": 13.08, "lng": 80.2}, "dtc_codes": [], "event": "TELEMETRY",
        })
        self.assertAlmostEqual(event["latitude"], 13.08)
        self.assertFalse(event["harsh_brake"])

    def test_rejects_missing_fields_and_bad_ranges(self):
        with self.assertRaisesRegex(ValueError, "missing required"):
            normalize({"source_oem": "oem-a"})
        raw = {"event_id": "x", "tenant_id": "t", "vehicle_id": "v", "source_oem": "oem-a",
               "event_ts": "2026-10-01T10:00:00Z", "speed_kmh": 301, "engine_temp_c": 90,
               "odometer_km": 10}
        with self.assertRaisesRegex(ValueError, "speed_kmh"):
            normalize(raw)

    def test_rejects_unknown_oem_and_invalid_soc(self):
        base = {"event_id": "x", "tenant_id": "t", "vehicle_id": "v", "source_oem": "oem-z",
                "event_ts": "2026-10-01T10:00:00Z", "speed_kmh": 30, "engine_temp_c": 90,
                "odometer_km": 10}
        with self.assertRaisesRegex(ValueError, "unsupported source_oem"):
            normalize(base)
        base["source_oem"] = "oem-a"
        base["battery_soc_pct"] = 120
        with self.assertRaisesRegex(ValueError, "battery_soc_pct"):
            normalize(base)


class RiskRuleTests(unittest.TestCase):
    def test_clean_event_has_zero_risk(self):
        score, alerts = evaluate({"event_id": "evt", "dtc": [], "engine_temp_c": 90, "harsh_brake": False})
        self.assertEqual((score, alerts), (0, []))

    def test_faults_create_explainable_alerts(self):
        event = {"event_id": "evt-risk", "dtc": ["P0301"], "engine_temp_c": 115, "harsh_brake": True}
        score, alerts = evaluate(event)
        self.assertEqual(score, 100)
        self.assertEqual({a["code"] for a in alerts}, {"diagnostic_code", "high_engine_temp", "harsh_braking"})
        self.assertEqual(alerts, evaluate(event)[1])


class SecurityTests(unittest.TestCase):
    def test_password_hash_and_jwt_round_trip(self):
        salt, hashed = password_hash("sample-password")
        self.assertTrue(password_matches("sample-password", salt, hashed))
        self.assertFalse(password_matches("wrong-password", salt, hashed))
        token = issue_token("manager@example.test", "tenant-a", "manager", "unit-test-secret")
        claims = decode_token(token, "unit-test-secret")
        self.assertEqual((claims["sub"], claims["tenant"], claims["role"]),
                         ("manager@example.test", "tenant-a", "manager"))

    def test_jwt_rejects_tampering_and_wrong_key(self):
        token = issue_token("user", "tenant-a", "viewer", "unit-test-secret")
        with self.assertRaisesRegex(ValueError, "invalid token"):
            decode_token(token[:-1] + ("x" if token[-1] != "x" else "y"), "unit-test-secret")
        with self.assertRaisesRegex(ValueError, "invalid token"):
            decode_token(token, "another-secret")


if __name__ == "__main__":
    unittest.main()
