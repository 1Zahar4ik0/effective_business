from pathlib import Path
from alembic import command
from alembic.config import Config
import uvicorn
from .config import settings
from .db import SessionLocal
from .seed import seed_demo


def main():
    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    if settings().seed_demo:
        with SessionLocal() as db:
            seed_demo(db)
    # Proxy logs only sanitized paths; uvicorn's access log includes query strings.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, access_log=False)


if __name__ == "__main__":
    main()
