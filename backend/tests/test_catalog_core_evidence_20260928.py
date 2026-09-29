from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.matching import availability
from app.schemas import NewMeasure
from conftest import login
from import_official import load_catalog


ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "data/official/sources/catalog-20260928"
KEYS = ("farm", "grain", "crop-insurance", "animal-insurance", "cooperative", "agroprogress", "agromotivator")


def entry(key):
    return next(x for x in load_catalog() if x["id"] == "saratov-" + key)


@pytest.mark.parametrize("key", KEYS)
def test_closed_core_round_matches_official_card(key):
    item = entry(key)
    evidence = item["evidence"]["catalog_review_20260928"]
    payload = NewMeasure.model_validate(item["payload"])
    rnd = payload.rounds[0]
    assert rnd.starts_at == datetime.fromisoformat(evidence["starts_at"])
    assert rnd.ends_at == datetime.fromisoformat(evidence["ends_at"])
    assert rnd.acceptance_status == "closed"
    assert not evidence["can_create_application"]
    assert availability(rnd, payload.data.model_dump(mode="json"), datetime(2026, 9, 28, 23, tzinfo=timezone.utc)) == "closed"
    assert str(rnd.application_url).endswith(evidence["competition_id"])


@pytest.mark.parametrize("key", KEYS)
def test_core_evidence_does_not_bypass_editorial_gate(client, key):
    login(client, "editor")
    item = entry(key)
    data = item["payload"]["data"]
    assert data["verified_at"] is None
    assert data["verification_status"] != "verified"
    assert data["missing_evidence"]
    assert not item["evidence"]["catalog_review_20260928"]["publication_ready"]
    created = client.post("/api/admin/measures", json=item["payload"])
    assert created.status_code == 200, created.text
    measure = created.json()
    reviewed = client.post(f"/api/admin/versions/{measure['version_id']}/review", json={"revision": measure["revision"]})
    assert reviewed.status_code == 200, reviewed.text
    measure = reviewed.json()
    result = client.post(f"/api/admin/versions/{measure['version_id']}/publish", json={"revision": measure["revision"]})
    assert result.status_code == 400
    assert client.get("/api/measures/" + measure["id"]).status_code == 404


def test_new_crop_round_is_separate_and_not_confirmed_open():
    item = entry("crop-insurance")
    payload = NewMeasure.model_validate(item["payload"])
    old, new = payload.rounds
    assert old.code == "26-009-R501П-2-0142"
    assert new.code == "26-009-R501П-2-0153"
    assert old.acceptance_status == "closed"
    assert new.starts_at == datetime.fromisoformat("2026-09-29T09:00:00+03:00")
    assert new.ends_at == datetime.fromisoformat("2026-10-09T09:00:00+03:00")
    assert new.acceptance_status == "unconfirmed"
    assert new.acceptance_checked_at is None
    data = payload.data.model_dump(mode="json")
    for date in ("2026-09-28T20:00:00+00:00", "2026-09-29T06:00:00+00:00", "2026-10-09T06:00:00+00:00"):
        assert availability(new, data, datetime.fromisoformat(date)) != "open"
    assert availability(new, data, new.ends_at) == "closed"


def test_amounts_have_distinct_purposes_and_zero_is_not_applicant_cap():
    expected = {"grain": "476821573.04", "crop-insurance": "103445251.28", "animal-insurance": "5303558.81", "cooperative": "24109550.57", "agromotivator": "13382022.48", "agroprogress": "16853932.59", "farm": "94292134.84"}
    for key, budget in expected.items():
        amounts = {x["kind"]: x for x in entry(key)["evidence"]["catalog_review_20260928"]["amounts"]}
        assert amounts["selection_budget"]["value"] == budget
        assert isinstance(amounts["selection_budget"]["value"], str)
        assert Decimal(budget) > 0
        if key in ("grain", "crop-insurance", "animal-insurance"):
            assert amounts["applicant_cap"]["value"] is None
            assert amounts["applicant_cap"]["status"] == "not_established"
    extra = entry("crop-insurance")["evidence"]["catalog_review_20260928"]["additional_rounds"][0]
    assert extra["budget"] == "94661130.72"
    assert extra["budget_kind"] == "selection_budget"


def test_evidence_hashes_and_retrievals_match_files():
    logs = [json.loads(line) for line in (SOURCES / "retrieval.jsonl").read_text(encoding="utf-8").splitlines()]
    for key in KEYS:
        for record in entry(key)["evidence"]["catalog_review_20260928"]["files"]:
            path = ROOT / record["path"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
            assert any(x["file"] == path.name and x["exit_code"] == 0 and x["attempted_at"] == record["retrieved_at"] for x in logs)
    assert any(x["exit_code"] != 0 and "announcement" in x["file"] for x in logs)


def test_insurance_categories_and_optional_documents_are_not_generic_rejections():
    for key in ("crop-insurance", "animal-insurance"):
        data = entry(key)["payload"]["data"]
        rules = {x["id"]: x for x in data["rules"]}
        assert rules["producer"]["op"] == "manual"
        assert rules["category-document"]["op"] == "manual"
        docs = {x["id"]: x for x in data["documents"]}
        assert "по инициативе" in docs["statistics"]["hint"]
        assert "межведомственный" in docs["statistics"]["hint"]
        assert "страховщику" in data["benefit"]


def test_agroprogress_outcome_and_cooperative_grant_not_conflated():
    progress = entry("agroprogress")
    assert progress["evidence"]["catalog_review_20260928"]["portal_status"] == "Не состоялся"
    assert progress["payload"]["rounds"][0]["starts_at"] == "2026-09-02T00:00:00+03:00"
    coop = entry("cooperative")
    assert [x["code"] for x in coop["payload"]["rounds"]] == ["26-009-R0162-2-0141"]
    assert any("0140" in x for x in coop["payload"]["data"]["missing_evidence"])
