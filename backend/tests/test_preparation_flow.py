from copy import deepcopy
from datetime import timedelta
import pytest
from sqlalchemy import select
from app.db import SessionLocal, utcnow
from app.models import Plan
from app.matching import evaluate
from import_official import load_catalog
from conftest import login


def test_questions_do_not_disclose_draft_conditions(client):
    login(client, "editor")
    payload = deepcopy(
        next(e["payload"] for e in load_catalog() if e["id"] == "saratov-students")
    )

    payload.update(title="Учебная проверка годовых расходов", synthetic=True)
    now = utcnow()
    payload["data"].update(
        missing_evidence=[],
        verification_status="verified",
        verified_at=now.isoformat(),
        valid_from=(now - timedelta(days=1)).isoformat(),
        valid_until=(now + timedelta(days=30)).isoformat(),
    )
    created = client.post("/api/admin/measures", json=payload)
    assert created.status_code == 200, created.text
    m = created.json()
    assert client.get("/api/profile/questions").json() == []
    m = client.post(
        f"/api/admin/versions/{m['version_id']}/review",
        json={"revision": m["revision"]},
    ).json()
    assert client.get("/api/profile/questions").json() == []
    published = client.post(
        f"/api/admin/versions/{m['version_id']}/publish",
        json={"revision": m["revision"]},
    )
    assert published.status_code == 200, published.text
    questions = client.get("/api/profile/questions").json()
    assert [q["field"] for q in questions] == ["expense_year"]
    assert questions[0]["source_refs"] and questions[0]["minimum"] == 2000


def test_actual_expense_year_and_family_boundaries():
    entries = {e["id"]: e["payload"]["data"] for e in load_catalog()}
    for value, status in (
        (None, "UNKNOWN"),
        (2025, "FAIL"),
        (2026, "PASS"),
        (2027, "FAIL"),
    ):
        checks = evaluate(entries["saratov-students"], {"expense_year": value})[
            "checks"
        ]
        assert next(c for c in checks if c["id"] == "year")["status"] == status
    for value, status in ((None, "UNKNOWN"), (1, "FAIL"), (2, "PASS")):
        checks = evaluate(entries["saratov-farm"], {"family_kfh_members": value})[
            "checks"
        ]
        assert next(c for c in checks if c["id"] == "family_count")["status"] == status


@pytest.mark.parametrize(
    "body",
    [
        {"expense_year": 1999},
        {"expense_year": 2026.5},
        {"family_kfh_members": -1},
        {"family_kfh_members": 101},
    ],
)
def test_invalid_additional_answers_are_rejected(client, body):
    login(client)
    assert client.put("/api/profile", json=body).status_code == 422


def test_plan_keeps_unknown_reasons_and_detects_profile_changes(client):
    login(client)
    client.put("/api/profile", json={"registration_region": "64", "expense_year": 2026})
    m = client.get("/api/measures/farm-growth").json()
    body = {"round_id": m["rounds"][0]["id"]}
    saved = client.post("/api/preparation-plans", json=body)
    assert saved.status_code == 200, saved.text
    p = saved.json()
    snapshot = deepcopy(p["assessment"])
    assert snapshot["status"] == "UNKNOWN"
    assert any(c["status"] == "UNKNOWN" for c in snapshot["checks"])
    assert snapshot["profile"]["expense_year"] == 2026
    assert p["profile_changed"] is False
    client.put(
        "/api/profile", json={"registration_region": "other", "expense_year": 2025}
    )
    repeated = client.post("/api/preparation-plans", json=body).json()
    assert repeated["id"] == p["id"] and repeated["assessment"] == snapshot
    assert repeated["profile_changed"] is True
    changed = client.patch(
        f"/api/preparation-plans/{p['id']}/items/{p['items'][0]['id']}",
        json={"revision": p["revision"], "done": True},
    ).json()
    assert changed["assessment"] == snapshot and changed["items"][0]["done"] is True
    login(client, "second")
    assert client.get("/api/preparation-plans").json() == []
    assert (
        client.patch(
            f"/api/preparation-plans/{p['id']}/items/{p['items'][0]['id']}",
            json={"revision": changed["revision"], "done": False},
        ).status_code
        == 404
    )
    login(client)
    assert client.get("/api/preparation-plans").json()[0]["assessment"] == snapshot


def test_legacy_plan_is_preserved_without_inventing_historical_assessment(client):
    login(client)
    m = client.get("/api/measures/farm-growth").json()
    p = client.post(
        "/api/preparation-plans", json={"round_id": m["rounds"][0]["id"]}
    ).json()
    with SessionLocal() as db:
        stored = db.get(Plan, p["id"])
        stored.assessment = None
        db.commit()
    response = client.get("/api/preparation-plans").json()[0]
    assert response["assessment"] is None
    assert response["items"] == p["items"] and response["id"] == p["id"]
