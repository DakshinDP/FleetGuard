"""Deterministic, interpretable fault triage; scores are prioritization hints."""
from uuid import NAMESPACE_URL, uuid5


def evaluate(event: dict) -> tuple[int, list[dict]]:
    score = 0
    findings: list[tuple[str, str, str, int]] = []
    if event.get("dtc"):
        score += 55
        findings.append(("diagnostic_code", "warning", "Vehicle reported diagnostic code(s)", 55))
    if event.get("engine_temp_c", 0) >= 110:
        score += 40
        findings.append(("high_engine_temp", "critical", "Engine temperature is at least 110 C", 90))
    if event.get("harsh_brake"):
        score += 18
        findings.append(("harsh_braking", "info", "Harsh braking event detected", 18))
    score = min(score, 100)
    alerts = [{"alert_id": str(uuid5(NAMESPACE_URL, f"{event['event_id']}:{code}")),
               "code": code, "severity": severity, "title": title,
               "detail": title, "risk_score": risk}
              for code, severity, title, risk in findings]
    return score, alerts
