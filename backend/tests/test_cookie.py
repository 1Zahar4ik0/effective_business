from fastapi import Response
from app.auth import create_session
from app.config import settings
from app.db import SessionLocal
from app.models import User


def test_production_cookie_for_embedded_max(client, monkeypatch):
    with SessionLocal() as db:
        user = User(
            id="max:synthetic-test",
            name="Синтетический тест",
            role="farmer",
            demo=False,
        )
        db.add(user)
        db.flush()
        monkeypatch.setattr(settings(), "app_env", "production")
        response = Response()
        create_session(db, user, response)
        cookie = response.headers["set-cookie"]
        assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=none" in cookie
