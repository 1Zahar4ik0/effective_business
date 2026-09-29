from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from .db import aware, utcnow
from .schemas import NUMERIC_PROFILE_FIELDS, Rule, VersionData


def combine(statuses: list[str], op: str = "all") -> str:
    if op == "any":
        if "PASS" in statuses:
            return "PASS"
        if "UNKNOWN" in statuses:
            return "UNKNOWN"
        return "FAIL"

    if "FAIL" in statuses:
        return "FAIL"
    if "UNKNOWN" in statuses:
        return "UNKNOWN"
    return "PASS"


def answer_status(rule: Rule, actual) -> str:
    if actual is None or actual == "":
        return "UNKNOWN"

    if rule.field in NUMERIC_PROFILE_FIELDS:
        try:
            actual_number = Decimal(str(actual))
            required_number = Decimal(str(rule.value))
        except (InvalidOperation, ValueError):
            return "UNKNOWN"

        if not actual_number.is_finite() or not required_number.is_finite():
            return "UNKNOWN"

        if rule.op == "eq":
            matches = actual_number == required_number
        elif rule.op == "gte":
            matches = actual_number >= required_number
        else:
            matches = actual_number <= required_number
    elif rule.op == "in":
        matches = actual in rule.value
    else:
        matches = actual == rule.value

    return "PASS" if matches else "FAIL"


def evaluate_rule(rule: Rule, profile: dict) -> dict:
    children = [evaluate_rule(child, profile) for child in rule.children]

    if rule.op == "manual":
        status = "UNKNOWN"
    elif rule.op in ("all", "any"):
        status = combine([child["status"] for child in children], rule.op)
    else:
        status = answer_status(rule, profile.get(rule.field))

    return {
        "id": rule.id,
        "label": rule.label,
        "status": status,
        "field": rule.field,
        "source_ref": rule.source_ref,
        "children": children,
    }


def evaluate(data: dict, profile: dict) -> dict:
    version = VersionData.model_validate(data)
    if version.publication_scope == "reference":
        checks = [evaluate_rule(rule, profile) for rule in version.rules if rule.id in version.reference_rule_ids]
        checks.append({
                "id": "reference-review",
                "label": "Справочная карточка: применимость условий к хозяйству требует проверки по документам",
                "status": "UNKNOWN",
                "field": None,
                "source_ref": version.sources[0].reference,
                "children": [],
            })
        return {"status": combine([check["status"] for check in checks]), "checks": checks}
    checks = [evaluate_rule(rule, profile) for rule in version.rules]
    status = combine([check["status"] for check in checks]) if checks else "UNKNOWN"
    return {"status": status, "checks": checks}


def evaluate_documents(data: dict, profile: dict) -> list[dict]:
    version = VersionData.model_validate(data)
    documents = version.documents
    if version.publication_scope == "reference":
        return [
            {**document.model_dump(mode="json"), "applicability": "unknown", "check": None}
            for document in documents
        ]
    results = []
    for document in documents:
        check = None
        applicability = "required"
        if document.condition:
            check = evaluate_rule(document.condition, profile)
            if check["status"] == "FAIL":
                applicability = "not_applicable"
            elif check["status"] == "UNKNOWN":
                applicability = "unknown"

        result = document.model_dump(mode="json")
        result["applicability"] = applicability
        result["check"] = check
        results.append(result)
    return results


def availability(
    round_, data: dict, now: datetime | None = None, fresh_days: int = 7
) -> str:
    now = now or utcnow()
    if round_.state in ("cancelled", "suspended"):
        return round_.state
    if now >= aware(round_.ends_at):
        return "closed"

    acceptance_status = getattr(round_, "acceptance_status", "unconfirmed")
    checked_at = getattr(round_, "acceptance_checked_at", None)
    if acceptance_status == "closed" and checked_at and aware(checked_at) <= now:
        return "closed"
    if round_.state == "unknown":
        return "unknown"

    version = VersionData.model_validate(data)
    if version.publication_scope == "reference" or not version.has_validity_period or version.missing_evidence:
        return "unknown"
    if now < version.valid_from:
        return "unknown"
    if version.valid_until is not None and now >= version.valid_until:
        return "unknown"

    freshness_limit = timedelta(days=fresh_days)
    if (
        version.verification_status != "verified"
        or not version.verified_at
        or version.verified_at > now
        or now - version.verified_at > freshness_limit
    ):
        return "unknown"
    if now < aware(round_.starts_at):
        return "scheduled"

    if acceptance_status != "confirmed_open" or not checked_at:
        return "unknown"
    checked_at = aware(checked_at)
    if checked_at > now or now - checked_at > freshness_limit:
        return "unknown"
    return "open"
