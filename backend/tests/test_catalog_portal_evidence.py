from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json

from app.matching import availability
from import_official import load_catalog
from conftest import login


def test_portal_deadlines_match_catalog_and_remain_closed():
    entries = {e["id"]: e for e in load_catalog()}
    now = datetime(2026, 9, 27, 18, tzinfo=timezone.utc)
    for key in ("students", "farm"):
        entry = entries["saratov-" + key]
        evidence = entry["evidence"]["portal_review"]
        payload = entry["payload"]
        rnd = SimpleNamespace(**payload["rounds"][0])
        rnd.starts_at = datetime.fromisoformat(rnd.starts_at)
        rnd.ends_at = datetime.fromisoformat(rnd.ends_at)
        assert rnd.starts_at == datetime.fromisoformat(evidence["starts_at"])
        assert rnd.ends_at == datetime.fromisoformat(evidence["ends_at"])
        assert rnd.application_url.endswith(evidence["competition_id"])
        assert not evidence["can_create_application"]
        assert availability(rnd, payload["data"], now) == "closed"


def test_portal_confirmation_does_not_allow_publication(client):
    login(client, "editor")
    entries = {e["id"]: e for e in load_catalog()}
    for key in ("students", "farm"):
        entry = entries["saratov-" + key]
        assert entry["payload"]["data"]["verification_status"] == "conflict"
        assert entry["payload"]["data"]["verified_at"] is None
        created = client.post("/api/admin/measures", json=entry["payload"])
        assert created.status_code == 200, created.text
        measure = created.json()
        reviewed = client.post(
            f"/api/admin/versions/{measure['version_id']}/review",
            json={"revision": measure["revision"]},
        )
        assert reviewed.status_code == 200, reviewed.text
        measure = reviewed.json()
        published = client.post(
            f"/api/admin/versions/{measure['version_id']}/publish",
            json={"revision": measure["revision"]},
        )
        assert published.status_code == 400
        assert client.get("/api/measures/" + measure["id"]).status_code == 404


def test_catalog_source_claims_and_amount_types():
    entries = {e["id"]: e for e in load_catalog()}
    for key in ("students", "farm"):
        evidence = entries["saratov-" + key]["evidence"]["portal_review"]
        amounts = {x["kind"]: x for x in evidence["amounts"]}
        assert isinstance(amounts["selection_budget"]["value"], str)
        assert amounts["applicant_cap"]["value"] == (
            "10000000.00" if key == "farm" else None
        )
        assert evidence["publication_ready"] is False
    students = entries["saratov-students"]["payload"]["data"]
    employment = next(d for d in students["documents"] if d["id"] == "employment")
    assert "23.09.2026" in employment["hint"] and "Конфликт" in employment["hint"]
    farm = entries["saratov-farm"]["payload"]["data"]
    expense_plan = next(d for d in farm["documents"] if d["id"] == "expense-plan")
    assert (
        "обязательном" in expense_plan["hint"]
        and "межведомственном" in expense_plan["hint"]
    )
