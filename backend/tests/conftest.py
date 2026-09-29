import os
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["APP_ENV"] = "test"
os.environ["SEED_DEMO"] = "false"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://navigator:local-demo-only@localhost:55432/navigator_test",
)
if not os.environ["DATABASE_URL"].endswith("/navigator_test"):
    raise RuntimeError("Тесты разрешены только в отдельной базе navigator_test")
from app.db import Base, engine, SessionLocal
from app.main import app
from app.seed import seed_demo
from fastapi.testclient import TestClient


@pytest.fixture
def client():

    from sqlalchemy import text

    with engine.begin() as connection:
        tables = ", ".join('"' + t.name + '"' for t in Base.metadata.sorted_tables)
        connection.execute(text("TRUNCATE " + tables + " CASCADE"))
    with SessionLocal() as db:
        seed_demo(db)
    with TestClient(app, headers={"X-App-Request": "1"}) as client:
        yield client


def login(client, persona="farmer"):
    response = client.post("/api/auth/demo", json={"persona": persona})
    assert response.status_code == 200, response.text
    client.headers["X-CSRF-Token"] = response.json()["csrf"]
    return response.json()
