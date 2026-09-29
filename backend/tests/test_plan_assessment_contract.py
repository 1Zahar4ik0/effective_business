from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace
import pytest
from app.db import SessionLocal, utcnow
from app.matching import availability, evaluate
from app.models import Plan
from app.schemas import RoundInput
from conftest import login
from import_official import load_catalog


@pytest.mark.parametrize(
    "amount,lo,hi",
    [
        (None, "UNKNOWN", "UNKNOWN"),
        ("2999999.99", "FAIL", "PASS"),
        ("3000000.00", "PASS", "PASS"),
        ("10000000", "PASS", "PASS"),
        ("10000000.01", "PASS", "FAIL"),
    ],
)
def test_grant_limits_are_exact_but_finance_and_family_stay_manual(amount, lo, hi):
    data = next(
        e["payload"]["data"] for e in load_catalog() if e["id"] == "saratov-farm"
    )
    result = evaluate(
        data,
        {
            "requested_grant": amount,
            "own_funds": "999999999",
            "family_kfh_members": 2,
            "is_kfh": True,
            "legal_form": "ip",
            "registration_region": "64",
            "activity_region": "64",
        },
    )
    checks = {c["id"]: c["status"] for c in result["checks"]}
    assert checks["grant_min"] == lo and checks["grant_cap"] == hi
    assert all(
        checks[k] == "UNKNOWN"
        for k in (
            "finance",
            "family",
            "registration",
            "territory",
            "previous-support",
            "assets",
        )
    )
    assert result["status"] != "PASS"


def test_new_money_field_validation_and_numeric_profile_comparison(client):
    login(client)
    for value in ("NaN", "Infinity", "-0.01", "1.001", True):
        assert (
            client.put("/api/profile", json={"requested_grant": value}).status_code
            == 422
        )
    client.put(
        "/api/profile", json={"requested_grant": "3000000", "own_funds": "450000"}
    )
    m = client.get("/api/measures/farm-growth").json()
    p = client.post(
        "/api/preparation-plans", json={"round_id": m["rounds"][0]["id"]}
    ).json()
    client.put(
        "/api/profile", json={"requested_grant": "3000000.00", "own_funds": "450000.00"}
    )
    assert client.get("/api/preparation-plans").json()[0]["profile_changed"] is False
    client.put("/api/profile", json={"requested_grant": None, "own_funds": "450000"})
    assert client.get("/api/preparation-plans").json()[0]["profile_changed"] is True


def test_acceptance_and_condition_verification_are_independent(client):
    data = client.get("/api/catalog").json()[0]["data"]
    now = utcnow()
    data.update(
        verified_at=now.isoformat(),
        valid_from=(now - timedelta(days=2)).isoformat(),
        valid_until=(now + timedelta(days=20)).isoformat(),
    )
    r = SimpleNamespace(
        state="announced",
        starts_at=now,
        ends_at=now + timedelta(days=2),
        acceptance_status="unconfirmed",
        acceptance_checked_at=None,
    )
    assert availability(r, data, now) == "unknown"
    r.acceptance_status = "confirmed_open"
    r.acceptance_checked_at = now
    assert availability(r, data, now) == "open"
    for checked in (None, now - timedelta(days=8), now + timedelta(seconds=1)):
        r.acceptance_checked_at = checked
        assert availability(r, data, now) == "unknown"
    r.acceptance_checked_at = now
    assert (
        availability(r, {**data, "missing_evidence": ["Редакция не установлена"]}, now)
        == "unknown"
    )
    r.acceptance_status = "closed"
    assert availability(r, data, now) == "closed"
    r.acceptance_checked_at = now + timedelta(days=1)
    assert availability(r, data, now) == "unknown"
    r.acceptance_status = "confirmed_open"
    assert availability(r, data, r.ends_at) == "closed"


def test_second_round_and_archived_version_keep_exact_snapshot(client):
    login(client, "editor")
    original = client.get("/api/measures/farm-growth").json()
    draft = client.post(f"/api/admin/versions/{original['version_id']}/clone").json()
    data = deepcopy(draft["data"])
    now = utcnow()
    data.update(
        verification_status="verified",
        verified_at=now.isoformat(),
        legal_edition="СИНТЕТИЧЕСКАЯ редакция QA",
    )
    first = {
        k: v for k, v in draft["rounds"][0].items() if k not in ("id", "availability")
    }
    second = {
        **first,
        "code": "SYNTHETIC-SECOND",
        "application_url": "https://example.invalid/qa-second",
    }
    draft = client.put(
        f"/api/admin/versions/{draft['version_id']}",
        json={"revision": draft["revision"], "data": data, "rounds": [first, second]},
    ).json()
    draft = client.post(
        f"/api/admin/versions/{draft['version_id']}/review",
        json={"revision": draft["revision"]},
    ).json()
    published = client.post(
        f"/api/admin/versions/{draft['version_id']}/publish",
        json={"revision": draft["revision"]},
    ).json()
    login(client)
    client.put("/api/profile", json={"registration_region": "64", "expense_year": 2026})
    rnd = next(r for r in published["rounds"] if r["code"] == "SYNTHETIC-SECOND")
    p = client.post("/api/preparation-plans", json={"round_id": rnd["id"]}).json()
    a = p["assessment"]
    assert a["version_id"] == published["version_id"] and a["version"] == 2
    assert a["legal_edition"] == data["legal_edition"]
    assert a["round"] == rnd and a["round"]["id"] == p["round_id"]
    assert a["assessed_at"] and a["checks"] and a["profile"]["expense_year"] == 2026
    login(client, "editor")
    client.post(
        f"/api/admin/versions/{published['version_id']}/unpublish",
        json={"revision": published["revision"]},
    )
    login(client)
    saved = client.get("/api/preparation-plans").json()[0]
    assert saved["needs_review"] and saved["assessment"] == a
    assert saved["measure"]["version_id"] == published["version_id"]
    login(client, "second")
    assert client.get("/api/preparation-plans").json() == []
    assert (
        client.post("/api/preparation-plans", json={"round_id": rnd["id"]}).status_code
        == 409
    )


def test_early_assessment_json_remains_readable_without_backfill(client):
    login(client)
    m = client.get("/api/measures/farm-growth").json()
    p = client.post(
        "/api/preparation-plans", json={"round_id": m["rounds"][0]["id"]}
    ).json()
    with SessionLocal() as db:
        row = db.get(Plan, p["id"])
        row.assessment = {
            k: v
            for k, v in row.assessment.items()
            if k not in ("round", "version", "version_id", "legal_edition")
        }
        original = deepcopy(row.assessment)
        db.commit()
    saved = client.get("/api/preparation-plans").json()[0]
    assert (
        saved["assessment"]["round"] is None
        and saved["assessment"]["version_id"] is None
    )
    assert saved["assessment"]["checks"] == original["checks"]
    with SessionLocal() as db:
        assert db.get(Plan, p["id"]).assessment == original


def test_acceptance_requires_aware_check_time():
    args = dict(
        code="SYNTHETIC",
        starts_at="2026-09-01T00:00:00+03:00",
        ends_at="2026-09-30T00:00:00+03:00",
        application_url="https://example.invalid",
        channel="QA",
        acceptance_status="confirmed_open",
    )
    with pytest.raises(ValueError):
        RoundInput(**args)
    with pytest.raises(ValueError):
        RoundInput(**args, acceptance_checked_at="2026-09-20T00:00:00")


def test_import_acceptance_timestamp_offset_does_not_create_duplicate_revision():
    from import_official import canonical_rounds

    r = dict(
        code="QA",
        starts_at="2026-09-01T00:00:00+03:00",
        ends_at="2026-09-30T00:00:00+03:00",
        application_url="https://example.invalid",
        channel="QA",
        acceptance_status="closed",
        acceptance_checked_at="2026-09-27T20:00:00+03:00",
    )
    assert canonical_rounds([r]) == canonical_rounds(
        [{**r, "acceptance_checked_at": "2026-09-27T17:00:00Z"}]
    )
