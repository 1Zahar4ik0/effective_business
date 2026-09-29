import os
import subprocess
import sys
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.engine import make_url

if (
    os.environ.get("APP_ENV") != "test"
    or make_url(os.environ["DATABASE_URL"]).database != "navigator_test"
):
    raise RuntimeError("Only isolated navigator_test with APP_ENV=test is allowed")
from app.db import engine


def migrate(*args):
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", *args],
        check=True,
    )


migrate("downgrade", "20260918_one_published")
try:

    uid = "qa-migration-" + str(uuid4())
    mid = "qa-migration-" + str(uuid4())
    vid = str(uuid4())
    rid = str(uuid4())
    pid = str(uuid4())
    with engine.begin() as c:
        c.execute(
            text(
                "INSERT INTO users (id,name,role,demo) VALUES (:id,'SYNTHETIC migration QA','farmer',true)"
            ),
            {"id": uid},
        )
        c.execute(
            text(
                "INSERT INTO profiles (user_id,data,updated_at) VALUES (:id,CAST(:data AS json),now())"
            ),
            {"id": uid, "data": '{"expense_year":2026}'},
        )
        c.execute(
            text(
                "INSERT INTO measures (id,title,category,synthetic) VALUES (:id,'SYNTHETIC migration QA','grant',true)"
            ),
            {"id": mid},
        )
        c.execute(
            text(
                "INSERT INTO measure_versions (id,measure_id,number,state,revision,data,created_at) VALUES (:id,:mid,1,'archived',1,'{}',now())"
            ),
            {"id": vid, "mid": mid},
        )
        c.execute(
            text(
                "INSERT INTO selection_rounds (id,version_id,code,starts_at,ends_at,timezone,state,application_url,channel) VALUES (:id,:vid,'SYNTHETIC',now(),now()+interval '1 day','Europe/Moscow','announced','https://example.invalid','QA')"
            ),
            {"id": rid, "vid": vid},
        )
        c.execute(
            text(
                "INSERT INTO preparation_plans (id,user_id,version_id,round_id,items,revision,created_at) VALUES (:id,:uid,:vid,:rid,CAST(:items AS json),3,now())"
            ),
            {
                "id": pid,
                "uid": uid,
                "vid": vid,
                "rid": rid,
                "items": '[{"id":"proof","title":"QA","hint":"QA","done":true}]',
            },
        )
        before = dict(
            c.execute(text("SELECT * FROM preparation_plans WHERE id=:id"), {"id": pid})
            .mappings()
            .one()
        )
        profile = dict(
            c.execute(text("SELECT * FROM profiles WHERE user_id=:id"), {"id": uid})
            .mappings()
            .one()
        )
    migrate("upgrade", "head")
    with engine.connect() as c:
        after = dict(
            c.execute(text("SELECT * FROM preparation_plans WHERE id=:id"), {"id": pid})
            .mappings()
            .one()
        )
        assert after.pop("assessment") is None and after == before
        assert (
            dict(
                c.execute(text("SELECT * FROM profiles WHERE user_id=:id"), {"id": uid})
                .mappings()
                .one()
            )
            == profile
        )
        row = c.execute(
            text(
                "SELECT acceptance_status,acceptance_checked_at FROM selection_rounds WHERE id=:id"
            ),
            {"id": rid},
        ).one()
        assert tuple(row) == ("unconfirmed", None)
    migrate("check")
    print(
        "PASS old-schema migration: profile, owner, plan IDs, version, archived round, revision and document marks retained; no invented assessment/acceptance"
    )
finally:
    migrate("upgrade", "head")
