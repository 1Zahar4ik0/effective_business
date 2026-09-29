import hashlib
import hmac
import secrets
from datetime import timedelta
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db, aware, utcnow
from .models import AuthSession, User


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: User, response: Response) -> dict:
    raw = secrets.token_urlsafe(48)
    csrf = secrets.token_urlsafe(32)
    session = AuthSession(
        token_hash=digest(raw),
        user_id=user.id,
        csrf=csrf,
        expires_at=utcnow() + timedelta(hours=settings().session_hours),
    )
    db.add(session)
    db.commit()
    response.set_cookie(
        "opora_session",
        raw,
        httponly=True,
        secure=settings().app_env == "production",
        samesite="none" if settings().app_env == "production" else "lax",
        max_age=settings().session_hours * 3600,
        path="/",
    )
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "demo": user.demo,
        },
        "csrf": csrf,
    }


def current_session(request: Request, db: Session = Depends(get_db)) -> AuthSession:
    raw = request.cookies.get("opora_session", "")
    session = db.get(AuthSession, digest(raw)) if raw else None
    if not session or aware(session.expires_at) <= utcnow():
        raise HTTPException(401, "Войдите в приложение заново")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if not hmac.compare_digest(
            request.headers.get("X-CSRF-Token", ""), session.csrf
        ):
            raise HTTPException(403, "Проверка запроса не пройдена")
    return session


def current_user(
    session: AuthSession = Depends(current_session), db: Session = Depends(get_db)
) -> User:
    user = db.get(User, session.user_id)
    if not user or (user.demo and settings().app_env == "production"):
        raise HTTPException(401, "Сессия недоступна")
    if not user.demo:

        admins = {
            value.strip()
            for value in settings().max_admin_ids.split(",")
            if value.strip()
        }
        user.role = "editor" if user.id.removeprefix("max:") in admins else "farmer"
    return user


def editor(user: User = Depends(current_user)) -> User:
    if user.role != "editor":
        raise HTTPException(403, "Доступ только для редактора")
    return user
