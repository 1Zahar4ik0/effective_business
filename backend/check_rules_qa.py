import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import httpx

parser = argparse.ArgumentParser(
    description="Explicitly synthetic QA on a dedicated Compose environment, via editorial API."
)
parser.add_argument(
    "--base-url",
    choices=["http://localhost:8002", "http://localhost:8003", "http://localhost:8000"],
    default="http://localhost:8002",
)
parser.add_argument("--snapshot", type=Path, default=Path("/tmp/rules-qa.json"))
parser.add_argument("--verify", action="store_true")
args = parser.parse_args()
with httpx.Client(
    base_url=args.base_url, headers={"X-App-Request": "1"}, trust_env=False, timeout=20
) as c:

    def call(method, path, body=None):
        r = c.request(method, path, json=body)
        r.raise_for_status()
        return r.json()

    def login(persona):
        s = call("POST", "/api/auth/demo", {"persona": persona})
        c.headers["X-CSRF-Token"] = s["csrf"]

    assert call("GET", "/api/config")["demo"] is True
    if args.verify:
        saved = json.loads(args.snapshot.read_text())
        login("farmer")
        plans = call("GET", "/api/preparation-plans")
        actual = next(p for p in plans if p["id"] == saved["plan"]["id"])
        assert actual == saved["plan"]
        assert call("GET", "/api/profile") == saved["profile"]
        print(
            "PASS restart: complete plan, snapshot, profile, marks, version, round and route unchanged"
        )
    else:
        login("editor")
        now = datetime.now(timezone.utc)
        existing = call("GET", "/api/admin/versions")
        title = "СИНТЕТИЧЕСКИЙ QA — анкета и сохранённый план"
        assert not any(
            m["title"] == title for m in existing
        ), "QA fixture exists: use --verify or a new isolated volume; never overwrite it"
        data = dict(
            summary="Полностью вымышленная мера для проверки анкеты, снимка и второго отбора. Не реальная поддержка.",
            benefit="Учебные пределы: 3–10 млн ₽; выплаты нет.",
            operator="СИНТЕТИЧЕСКИЙ QA",
            obligations="Учебный сценарий; документы никуда не отправляются.",
            contact="",
            rules=[
                dict(
                    id="year",
                    label="Учебный год расходов — 2026",
                    field="expense_year",
                    op="eq",
                    value=2026,
                    source_ref="СИНТЕТИЧЕСКИЙ QA, п. 1",
                ),
                dict(
                    id="family",
                    label="Учебный состав проекта — минимум 2",
                    field="family_kfh_members",
                    op="gte",
                    value=2,
                    source_ref="СИНТЕТИЧЕСКИЙ QA, п. 2",
                ),
                dict(
                    id="amount",
                    label="Учебная сумма — до 10 млн",
                    field="requested_grant",
                    op="lte",
                    value="10000000",
                    source_ref="СИНТЕТИЧЕСКИЙ QA, п. 3",
                ),
                dict(
                    id="documents",
                    label="Родство и документы требуют отдельной проверки",
                    op="manual",
                    source_ref="СИНТЕТИЧЕСКИЙ QA, п. 4",
                ),
            ],
            documents=[
                dict(
                    id="proof",
                    title="Учебное подтверждение — не загружать",
                    hint="Отметка готовности не подтверждает условие; при применимости нужны документы.",
                    condition=dict(id="conditional-year", label="Учебные расходы 2026 года", field="expense_year", op="eq", value=2026, source_ref="СИНТЕТИЧЕСКИЙ QA, п. 5"),
                )
            ],
            sources=[
                dict(
                    title="СИНТЕТИЧЕСКИЙ источник",
                    url="https://example.invalid/qa",
                    reference="Вымышленный набор",
                    published_on=now.date().isoformat(),
                )
            ],
            verification_status="verified",
            verified_at=now.isoformat(),
            valid_from=(now - timedelta(days=2)).isoformat(),
            valid_until=(now + timedelta(days=30)).isoformat(),
            legal_edition="СИНТЕТИЧЕСКАЯ редакция QA 1",
        )
        common = dict(
            starts_at=(now - timedelta(days=1)).isoformat(),
            ends_at=(now + timedelta(days=10)).isoformat(),
            timezone="Europe/Moscow",
            state="announced",
            acceptance_status="unconfirmed",
            channel="Учебный переход на главную портала; реального отбора нет",
        )
        rounds = [
            dict(
                common,
                code="SYNTHETIC-FIRST",
                application_url="https://minagro.saratov.gov.ru/",
            ),
            dict(
                common,
                code="SYNTHETIC-SECOND",
                application_url="https://promote.budget.gov.ru/",
            ),
        ]
        m = call(
            "POST",
            "/api/admin/measures",
            dict(
                title=title, synthetic=True, category="grant", data=data, rounds=rounds
            ),
        )
        m = call(
            "POST",
            f"/api/admin/versions/{m['version_id']}/review",
            {"revision": m["revision"]},
        )
        m = call(
            "POST",
            f"/api/admin/versions/{m['version_id']}/publish",
            {"revision": m["revision"]},
        )
        login("farmer")
        q = call("GET", "/api/profile/questions")
        assert {x["field"] for x in q} == {
            "expense_year",
            "family_kfh_members",
            "requested_grant",
        }
        for year, status in [(None, "UNKNOWN"), (2025, "FAIL"), (2026, "PASS")]:
            call(
                "PUT",
                "/api/profile",
                {
                    "expense_year": year,
                    "family_kfh_members": 2,
                    "requested_grant": "3000000.01",
                },
            )
            results = call("POST", "/api/matches")["results"]
            match = next(x for x in results if x["measure"]["id"] == m["id"])
            assert (
                next(x for x in match["checks"] if x["id"] == "year")["status"]
                == status
            )
            assert (
                next(x for x in match["checks"] if x["id"] == "documents")["status"]
                == "UNKNOWN"
            )
            assert match["status"] != "PASS"
        rnd = next(r for r in m["rounds"] if r["code"] == "SYNTHETIC-SECOND")
        assert rnd["availability"] == "unknown"
        p = call("POST", "/api/preparation-plans", {"round_id": rnd["id"]})
        assert p["items"][0]["applicability"] == "required"
        assert p["items"][0]["check"]["status"] == "PASS"
        saved_items = p["items"]
        snapshot = p["assessment"]
        assert snapshot["engine_version"] == "rules-20260928.1"
        assert (
            snapshot["round"]["code"] == "SYNTHETIC-SECOND"
            and snapshot["round"]["application_url"] == "https://promote.budget.gov.ru/"
        )
        call(
            "PUT",
            "/api/profile",
            {
                "expense_year": 2025,
                "family_kfh_members": 1,
                "requested_grant": "3000000.01",
            },
        )
        p = call("POST", "/api/preparation-plans", {"round_id": rnd["id"]})
        assert p["assessment"] == snapshot and p["profile_changed"]
        assert p["items"] == saved_items
        current_match = next(x for x in call("POST", "/api/matches")["results"] if x["measure"]["id"] == m["id"])
        assert current_match["documents"][0]["applicability"] == "not_applicable"
        p = call(
            "PATCH",
            f"/api/preparation-plans/{p['id']}/items/proof",
            {"revision": p["revision"], "done": True},
        )
        assert p["assessment"] == snapshot
        login("second")
        assert not any(
            x["id"] == p["id"] for x in call("GET", "/api/preparation-plans")
        )
        assert (
            c.patch(
                f"/api/preparation-plans/{p['id']}/items/proof",
                json={"revision": p["revision"], "done": False},
            ).status_code
            == 404
        )
        login("farmer")
        args.snapshot.write_text(
            json.dumps(
                {"plan": p, "profile": call("GET", "/api/profile")},
                ensure_ascii=False,
                indent=2,
            )
        )
        print(
            "PASS synthetic editorial publication, dynamic questions, UNKNOWN/FAIL/PASS, manual UNKNOWN, second round/route, immutable assessment, profile_changed, owner isolation"
        )
