from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from app.matching import availability, evaluate
from app.schemas import VersionData
from import_official import load_catalog
from conftest import login


def data_for_test():

    data = deepcopy(load_catalog()[0]["payload"]["data"])
    data.update(
        valid_from="2026-01-01T00:00:00+03:00",
        valid_until=None,
        validity_open_ended=True,
        validity_reference="Учебный акт, п. 2: конечная дата не установлена",
        verified_at="2026-09-19T12:00:00+03:00",
        verification_status="verified",
        missing_evidence=[],
    )
    return data


def test_open_ended_conditions_keep_precise_selection_boundaries_and_freshness():
    data = data_for_test()
    end = datetime.fromisoformat("2026-09-20T08:00:00+03:00")
    r = SimpleNamespace(
        state="announced",
        starts_at=end - timedelta(days=10),
        ends_at=end,
        acceptance_status="confirmed_open",
        acceptance_checked_at=end - timedelta(days=1),
    )
    assert availability(r, data, end - timedelta(microseconds=1)) == "open"
    assert (
        availability(r, data, end.astimezone(timezone(timedelta(hours=4)))) == "closed"
    )
    r.starts_at = end + timedelta(days=1)
    r.ends_at = end + timedelta(days=20)
    assert availability(r, data, end) == "scheduled"
    assert availability(r, data, end + timedelta(days=8)) == "unknown"
    data["verified_at"] = (end + timedelta(days=1)).isoformat()
    assert availability(r, data, end) == "unknown"


@pytest.mark.parametrize(
    "patch",
    [
        {"validity_open_ended": False},
        {"validity_reference": "  "},
        {"valid_from": None},
        {"valid_from": "2027-01-01T00:00:00+03:00"},
        {"missing_evidence": ["Нет первичного документа"]},
        {"verification_status": "conflict"},
    ],
)
def test_unknown_validity_and_evidence_never_become_open(patch):
    data = {**data_for_test(), **patch}
    now = datetime.fromisoformat("2026-09-19T13:00:00+03:00")
    r = SimpleNamespace(
        state="announced",
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
    )
    assert availability(r, data, now) == "unknown"
    assert availability(r, data, r.ends_at) == "closed"


def test_conflicting_period_is_rejected_and_legacy_period_is_unchanged():
    data = data_for_test()
    with pytest.raises(ValidationError):
        VersionData.model_validate({**data, "valid_until": "2026-12-31T00:00:00+03:00"})
    data.pop("validity_open_ended")
    data.pop("validity_reference")
    assert not VersionData.model_validate(data).has_validity_period
    data["valid_until"] = "2026-12-31T00:00:00+03:00"
    model = VersionData.model_validate(data)
    assert model.has_validity_period and model.validity_open_ended is False


@pytest.mark.parametrize(
    "patch,expected",
    [
        ({}, 200),
        ({"validity_reference": " "}, 400),
        ({"validity_open_ended": False}, 400),
        ({"valid_from": None}, 400),
    ],
)
def test_editor_publication_requires_explicit_supported_open_end(
    client, patch, expected
):
    login(client, "editor")
    payload = deepcopy(load_catalog()[0]["payload"])
    payload.update(title="Учебная проверка бессрочной редакции", synthetic=True)
    payload["data"] = {**data_for_test(), **patch}
    created = client.post("/api/admin/measures", json=payload)
    assert created.status_code == 200, created.text
    m = created.json()
    review = client.post(
        f"/api/admin/versions/{m['version_id']}/review",
        json={"revision": m["revision"]},
    )
    assert review.status_code == 200
    m = review.json()
    response = client.post(
        f"/api/admin/versions/{m['version_id']}/publish",
        json={"revision": m["revision"]},
    )
    assert response.status_code == expected, response.text
    public = client.get("/api/measures/" + m["id"])
    assert public.status_code == (200 if expected == 200 else 404)


def test_student_conditions_do_not_confuse_categories_or_unknown_answers():
    payload = next(
        e["payload"] for e in load_catalog() if e["id"] == "saratov-students"
    )
    data = payload["data"]
    profile = {
        "legal_form": "ip",
        "activity_region": "64",
        "expense_stage": "incurred",
        "is_kfh": False,
        "is_sme": False,
    }
    assert evaluate(data, profile)["status"] == "UNKNOWN"
    assert (
        evaluate(data, {**profile, "legal_form": "cooperative"})["status"] == "UNKNOWN"
    )
    for patch in (
        {"legal_form": "individual"},
        {"activity_region": "other"},
        {"expense_stage": "planned"},
    ):
        assert evaluate(data, {**profile, **patch})["status"] == "FAIL"
    assert evaluate(data, {"legal_form": "ip"})["status"] == "UNKNOWN"
    assert all(r.get("field") not in ("is_kfh", "is_sme") for r in data["rules"])
    r = SimpleNamespace(**payload["rounds"][0])
    r.starts_at = datetime.fromisoformat(r.starts_at)
    r.ends_at = datetime.fromisoformat(r.ends_at)
    assert availability(r, data, datetime(2026, 9, 27, tzinfo=timezone.utc)) == "closed"
