from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select
from app.db import SessionLocal
from app.models import Evaluation, Measure, Plan, Profile, SelectionRound, Version
from app.matching import availability, evaluate
from import_official import import_catalog, load_catalog, stage_revisions
from conftest import login


def farm_entry():
    return deepcopy(next(e for e in load_catalog() if e["id"] == "saratov-farm"))


def test_farm_new_applicant_is_not_rejected_and_closed_round_is_closed():
    entry = farm_entry()
    data = entry["payload"]["data"]
    for profile in (
        {},
        {"legal_form": "individual", "is_kfh": False},
        {"legal_form": "ip", "is_kfh": True},
    ):
        result = evaluate(data, profile)
        assert result["status"] == "UNKNOWN"
        assert not any(check["status"] == "FAIL" for check in result["checks"])
    assert (
        evaluate(data, {"legal_form": "cooperative", "is_kfh": False})["status"]
        == "FAIL"
    )
    r = entry["payload"]["rounds"][0]
    round_ = SimpleNamespace(
        **{
            **r,
            "starts_at": datetime.fromisoformat(r["starts_at"]),
            "ends_at": datetime.fromisoformat(r["ends_at"]),
        }
    )
    assert (
        availability(round_, data, datetime(2026, 9, 27, tzinfo=timezone.utc))
        == "closed"
    )
    assert data["verification_status"] == "conflict" and data["verified_at"] is None
    assert len(data["documents"]) == 20
    assert "инициативе" in next(
        d["hint"] for d in data["documents"] if d["id"] == "register"
    )


def test_new_revision_keeps_editor_work_and_does_not_publish(client):
    entry = farm_entry()
    with SessionLocal() as db:
        import_catalog(db, [entry])
        db.commit()
        old = db.scalar(select(Version).where(Version.measure_id == entry["id"]))
        old.data = {
            **old.data,
            "summary": "Существующая пользовательская правка. Сохранить дословно.",
        }

        old.state = "published"
        db.commit()
        previous = deepcopy(old.data)
        old_round_ids = list(
            db.scalars(
                select(SelectionRound.id).where(SelectionRound.version_id == old.id)
            )
        )
        report = stage_revisions(db, [entry], [entry["id"]])
        db.commit()
        assert len(report["created"]) == 1
        new_id = report["created"][0]["version_id"]
        new = db.get(Version, new_id)
        assert new.number == 2 and new.state == "draft"
        db.refresh(old)
        assert old.data == previous and old.state == "published" and old.revision == 1
        assert old_round_ids == list(
            db.scalars(
                select(SelectionRound.id).where(SelectionRound.version_id == old.id)
            )
        )

        again = stage_revisions(db, [entry], [entry["id"]])
        db.commit()
        assert not again["created"] and again["reused"][0]["version_id"] == new_id
        new.data = {
            **new.data,
            "summary": "Редактор уточнил новый черновик; импорт сохраняет и эту правку.",
        }
        db.commit()
        third = stage_revisions(db, [entry], [entry["id"]])
        db.commit()
        assert third["created"][0]["number"] == 3
        db.refresh(new)
        assert new.data["summary"].startswith("Редактор уточнил")
        measure = db.get(Measure, entry["id"])
        measure.title = "Переименовано пользователем"
        db.commit()
        with pytest.raises(ValueError, match="Название"):
            stage_revisions(db, [entry], [entry["id"]])
        db.rollback()
    assert all(m["version_id"] != new_id for m in client.get("/api/catalog").json())


def test_concurrent_research_import_creates_only_one_candidate(client):
    entry = farm_entry()
    with SessionLocal() as db:
        import_catalog(db, [entry])
        db.commit()
    entry["payload"]["data"]["summary"] += " Повторная редакторская сверка."

    def apply():
        with SessionLocal() as db:
            result = stage_revisions(db, [entry], [entry["id"]])
            db.commit()
            return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(lambda _: apply(), range(2)))
    assert sum(len(r["created"]) for r in reports) == 1
    assert sum(len(r["reused"]) for r in reports) == 1


def test_preview_permissions_unknowns_unsaved_rules_and_no_profile_write(client):
    data = farm_entry()["payload"]["data"]
    body = {"data": data, "profile": {"legal_form": "individual", "is_kfh": False}}
    assert client.post("/api/admin/preview", json=body).status_code == 401
    login(client, "farmer")
    assert client.post("/api/admin/preview", json=body).status_code == 403
    login(client, "editor")
    csrf = client.headers.pop("X-CSRF-Token")
    assert client.post("/api/admin/preview", json=body).status_code == 403
    client.headers["X-CSRF-Token"] = csrf
    with SessionLocal() as db:
        before = {
            model.__name__: db.scalar(select(func.count()).select_from(model))
            for model in (Profile, Evaluation, Plan, Version)
        }
    response = client.post("/api/admin/preview", json=body)
    assert response.status_code == 200, response.text
    assert response.json() == evaluate(data, body["profile"])
    body["data"]["rules"] = [
        {
            "id": "form",
            "label": "Тест изменённого правила",
            "field": "legal_form",
            "op": "eq",
            "value": "ip",
            "source_ref": "Тест",
        }
    ]
    assert client.post("/api/admin/preview", json=body).json()["status"] == "FAIL"
    body["profile"]["legal_form"] = "ip"
    assert client.post("/api/admin/preview", json=body).json()["status"] == "PASS"
    body["profile"] = {}
    assert client.post("/api/admin/preview", json=body).json()["status"] == "UNKNOWN"
    body["data"]["rules"][0]["op"] = "exec"
    assert client.post("/api/admin/preview", json=body).status_code == 422
    with SessionLocal() as db:
        after = {
            model.__name__: db.scalar(select(func.count()).select_from(model))
            for model in (Profile, Evaluation, Plan, Version)
        }
    assert before == after
