from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from sqlalchemy import select, func
from app.config import settings
from app.db import SessionLocal
from app.matching import evaluate_rule, availability
from app.models import BotEvent, Evaluation
from app.schemas import Rule
from conftest import login


@pytest.mark.parametrize(
    "actual,expected",
    [
        ("300000.00", "PASS"),
        ("300000", "PASS"),
        ("300000.01", "FAIL"),
        (None, "UNKNOWN"),
    ],
)
def test_money_equality_is_numeric(actual, expected):
    rule = Rule(
        id="money",
        label="Собственные средства",
        field="own_funds",
        op="eq",
        value=300000,
        source_ref="§1",
    )
    assert evaluate_rule(rule, {"own_funds": actual})["status"] == expected


def test_invalid_numeric_rule_cannot_be_saved():
    for value in ("NaN", "Infinity", "сто рублей", True):
        with pytest.raises(ValueError):
            Rule(
                id="money",
                label="Сумма",
                field="own_funds",
                op="eq",
                value=value,
                source_ref="§1",
            )


def test_deadline_same_instant_in_saratov_and_moscow(client):
    data = client.get("/api/catalog").json()[0]["data"]
    end = datetime.fromisoformat("2026-09-20T08:00:00+03:00")
    data.update(
        valid_from=(end - timedelta(days=5)).isoformat(),
        valid_until=(end + timedelta(days=1)).isoformat(),
        verified_at=(end - timedelta(days=1)).isoformat(),
        verification_status="verified",
        missing_evidence=[],
    )
    round_ = SimpleNamespace(
        state="announced",
        starts_at=end - timedelta(days=2),
        ends_at=end,
        acceptance_status="confirmed_open",
        acceptance_checked_at=end - timedelta(days=1),
    )
    assert (
        availability(round_, data, datetime.fromisoformat("2026-09-20T08:59:59+04:00"))
        == "open"
    )
    assert (
        availability(round_, data, datetime.fromisoformat("2026-09-20T09:00:00+04:00"))
        == "closed"
    )
    round_.state = "unknown"
    assert availability(round_, data, end - timedelta(seconds=1)) == "unknown"
    assert availability(round_, data, end) == "closed"


def launch(user_id, query_id):
    params = {
        "auth_date": str(int(time.time())),
        "query_id": query_id,
        "user": json.dumps(
            {"id": user_id, "first_name": "Синтетический MAX", "role": "editor"}
        ),
    }
    secret = hmac.new(b"WebAppData", b"release-test-only", hashlib.sha256).digest()
    params["hash"] = hmac.new(
        secret,
        "\n".join(f"{k}={params[k]}" for k in sorted(params)).encode(),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(params)


def test_max_profile_survives_reentry_and_editor_revocation(client, monkeypatch):
    monkeypatch.setattr(settings(), "max_bot_token", "release-test-only")
    monkeypatch.setattr(settings(), "max_admin_ids", "987")

    def enter(uid, nonce):
        result = client.post("/api/auth/max", json={"init_data": launch(uid, nonce)})
        assert result.status_code == 200
        client.headers["X-CSRF-Token"] = result.json()["csrf"]
        return result.json()

    assert enter(987, "first")["user"]["role"] == "editor"
    assert (
        client.put(
            "/api/profile", json={"is_kfh": True, "own_funds": "1200.01"}
        ).status_code
        == 200
    )
    monkeypatch.setattr(settings(), "max_admin_ids", "")
    assert client.get("/api/admin/versions").status_code == 403
    assert client.get("/api/auth/me").json()["user"]["role"] == "farmer"
    assert enter(988, "other")["user"]["role"] == "farmer"
    assert client.get("/api/profile").json()["is_kfh"] is None
    enter(987, "reopened")
    assert client.get("/api/profile").json()["own_funds"] == "1200.01"


def test_duplicate_max_message_keeps_one_reply_despite_envelope_change(
    client, monkeypatch
):
    monkeypatch.setattr(settings(), "max_webhook_secret", "synthetic-secret")
    monkeypatch.setattr(settings(), "max_app_url", "https://max.ru/synthetic_bot")
    for stamp in (100, 101):
        payload = {
            "update_type": "message_created",
            "timestamp": stamp,
            "message": {
                "recipient": {"chat_id": 1},
                "body": {"mid": "same-mid", "text": "/start"},
            },
        }
        response = client.post(
            "/api/max/webhook",
            json=payload,
            headers={"X-Max-Bot-Api-Secret": "synthetic-secret"},
        )
        assert response.status_code == 200
    with SessionLocal() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(BotEvent)
                .where(BotEvent.state == "pending")
            )
            == 1
        )


def test_matching_snapshot_survives_profile_edit(client):
    login(client)
    client.put(
        "/api/profile",
        json={
            "registration_region": "64",
            "is_kfh": True,
            "goal": "equipment",
            "own_funds": "450000",
        },
    )
    result = client.post("/api/matches").json()
    client.put("/api/profile", json={"registration_region": "other", "is_kfh": False})
    with SessionLocal() as db:
        snapshot = db.get(Evaluation, result["evaluation_id"])
        assert snapshot.profile["registration_region"] == "64"
        assert snapshot.results == result["results"]
        assert snapshot.created_at.tzinfo is not None
