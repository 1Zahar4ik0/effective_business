from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from .db import aware, utcnow
from .schemas import Rule, VersionData


def combine(statuses: list[str], op: str = "all") -> str:
    if op == "any":
        return "PASS" if "PASS" in statuses else "UNKNOWN" if "UNKNOWN" in statuses else "FAIL"
    return "FAIL" if "FAIL" in statuses else "UNKNOWN" if "UNKNOWN" in statuses else "PASS"


def evaluate_rule(rule: Rule, profile: dict) -> dict:
    children = [evaluate_rule(child, profile) for child in rule.children]
    if rule.op == "manual":
        status = "UNKNOWN"
    elif rule.op in ("all", "any"):
        status = combine([child["status"] for child in children], rule.op)
    else:
        actual = profile.get(rule.field)
        if actual is None or actual == "":
            status = "UNKNOWN"
        else:
            if rule.field in ("own_funds", "years_active") and rule.op in ("eq", "gte", "lte"):
                try:
                    a, b = Decimal(str(actual)), Decimal(str(rule.value))
                    if not a.is_finite() or not b.is_finite():
                        raise ValueError()
                    match = a == b if rule.op == "eq" else a >= b if rule.op == "gte" else a <= b
                except (InvalidOperation, ValueError):
                    return {"id": rule.id, "label": rule.label, "status": "UNKNOWN", "field": rule.field,
                            "source_ref": rule.source_ref, "children": children}
            elif rule.op == "eq":
                match = actual == rule.value
            elif rule.op == "in":
                match = actual in rule.value
            else:
                try:
                    a, b = Decimal(str(actual)), Decimal(str(rule.value))
                    match = a >= b if rule.op == "gte" else a <= b
                except (InvalidOperation, ValueError):
                    return {"id": rule.id, "label": rule.label, "status": "UNKNOWN", "field": rule.field,
                            "source_ref": rule.source_ref, "children": children}
            status = "PASS" if match else "FAIL"
    return {"id": rule.id, "label": rule.label, "status": status, "field": rule.field,
            "source_ref": rule.source_ref, "children": children}


def evaluate(data: dict, profile: dict) -> dict:
    version = VersionData.model_validate(data)
    checks = [evaluate_rule(rule, profile) for rule in version.rules]
    return {"status": combine([c["status"] for c in checks]) if checks else "UNKNOWN", "checks": checks}


def availability(round_, data: dict, now: datetime | None = None, fresh_days: int = 7) -> str:
    now = now or utcnow()
    if round_.state in ("cancelled", "suspended"):
        return round_.state
    # Дата закрытия имеет приоритет над устареванием сведений.
    if now >= aware(round_.ends_at):
        return "closed"
    if round_.state == "unknown":
        return "unknown"
    version = VersionData.model_validate(data)
    if not version.valid_from or not version.valid_until or version.missing_evidence:
        return "unknown"
    if now >= version.valid_until or now < version.valid_from:
        return "unknown"
    if (version.verification_status != "verified" or not version.verified_at
            or version.verified_at > now
            or now - version.verified_at > timedelta(days=fresh_days)):
        return "unknown"
    if now < aware(round_.starts_at):
        return "scheduled"
    return "open"
