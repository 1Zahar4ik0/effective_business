from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, text
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .api import router
from .config import settings
from .db import SessionLocal
from .models import Measure, User


@asynccontextmanager
async def lifespan(app):
    if settings().app_env == "production":
        with SessionLocal() as db:
            if db.scalar(
                select(Measure.id).where(Measure.synthetic.is_(True)).limit(1)
            ) or db.scalar(select(User.id).where(User.demo.is_(True)).limit(1)):
                raise RuntimeError(
                    "Рабочее окружение не должно использовать демонстрационную базу"
                )
    yield


def create_app():
    config = settings()
    app = FastAPI(
        title="Опора АПК",
        version="0.1.0",
        lifespan=lifespan,
        description="Навигатор поддержки. Подбор предварительный. Локальный набор — синтетический.",
    )
    hosts = [urlparse(config.public_origin).hostname or "localhost"]
    if config.app_env in ("demo", "test"):
        hosts += ["localhost", "127.0.0.1", "testserver"]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

    @app.middleware("http")
    async def guard(request: Request, call_next):
        try:
            length = int(request.headers.get("content-length", "0") or 0)
        except ValueError:
            return JSONResponse({"detail": "Неверная длина запроса"}, status_code=400)
        if length > 262144:
            return JSONResponse({"detail": "Запрос слишком большой"}, status_code=413)
        if (
            request.method not in ("GET", "HEAD", "OPTIONS")
            and request.url.path != "/api/max/webhook"
        ):
            origins = {config.public_origin.rstrip("/")}
            if config.app_env in ("demo", "test"):
                origins |= {
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                    "http://localhost:8000",
                    "http://127.0.0.1:8000",
                }
            origin = request.headers.get("origin")
            if request.headers.get("X-App-Request") != "1" or (
                origin and origin not in origins
            ):
                return JSONResponse(
                    {"detail": "Недопустимый источник запроса"}, status_code=403
                )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):

        errors = [
            {"field": ".".join(str(x) for x in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            {"detail": "Проверьте заполненные поля", "errors": errors}, status_code=422
        )

    @app.get("/health")
    def health():
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "environment": config.app_env}

    app.include_router(router)

    def documented_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        schema["servers"] = [{"url": "/", "description": "Текущий сервер"}]
        schema.setdefault("components", {})["securitySchemes"] = {
            "sessionCookie": {
                "type": "apiKey",
                "in": "cookie",
                "name": "opora_session",
                "description": "HttpOnly cookie после /api/auth/max; /api/auth/demo только локально",
            },
            "csrfHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "X-CSRF-Token",
                "description": "Значение csrf из входа или /api/auth/me",
            },
            "maxWebhookSecret": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Max-Bot-Api-Secret",
            },
        }
        for path, methods in schema["paths"].items():
            for method, operation in methods.items():
                if method not in ("get", "post", "put", "patch", "delete"):
                    continue
                public = path in (
                    "/health",
                    "/api/config",
                    "/api/catalog",
                    "/api/official-announcements",
                    "/api/auth/demo",
                    "/api/auth/max",
                ) or path.startswith("/api/measures/")
                if path == "/api/max/webhook":
                    operation["security"] = [{"maxWebhookSecret": []}]
                elif not public:
                    operation["security"] = [
                        {
                            "sessionCookie": [],
                            **({"csrfHeader": []} if method != "get" else {}),
                        }
                    ]
                    operation["responses"]["401"] = {
                        "description": "Нет действующей сессии"
                    }
                if method != "get" and path != "/api/max/webhook":
                    operation.setdefault("parameters", []).append(
                        {
                            "name": "X-App-Request",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string", "const": "1"},
                            "description": "Защита запросов приложения. Origin должен соответствовать PUBLIC_ORIGIN.",
                        }
                    )
                if not public or method != "get":
                    operation["responses"]["403"] = {
                        "description": "Недостаточно прав или запрос не прошёл проверку защиты"
                    }
        app.openapi_schema = schema
        return schema

    app.openapi = documented_openapi
    if Path(config.static_dir).is_dir():
        app.mount(
            "/", StaticFiles(directory=config.static_dir, html=True), name="frontend"
        )
    return app


app = create_app()
