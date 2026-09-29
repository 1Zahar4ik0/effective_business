import json
from datetime import timedelta
from pathlib import Path
from uuid import uuid4
from sqlalchemy import select
from .catalog import add_rounds
from .config import settings
from .db import SessionLocal, utcnow
from .models import Measure, Version
from .schemas import RoundInput, VersionData


def seed_demo(db):
    if settings().app_env not in ("demo", "test"):
        raise RuntimeError("Загрузка демоданных запрещена")
    if db.scalar(select(Measure.id).limit(1)):
        return
    path = Path(__file__).resolve().parents[2] / "data" / "demo" / "catalog.json"
    now = utcnow()
    for entry in json.loads(path.read_text(encoding="utf-8")):
        data = {
            "summary": entry["summary"],
            "benefit": entry["benefit"],
            "operator": "Учебный оператор — вымышленная организация",
            "obligations": "Учебный пример: подтвердить целевое использование средств и представить отчёт. Реальные обязательства определяет положение конкретной меры.",
            "contact": "Для реальной консультации найдите контакты на официальном сайте ведомства.",
            "rules": entry["rules"],
            "documents": [
                {
                    "id": "application",
                    "title": "Заявление на участие",
                    "hint": "Учебный пункт. В реальном отборе скачайте действующую форму.",
                },
                {
                    "id": "registration",
                    "title": "Сведения о хозяйстве",
                    "hint": "Проверьте регистрационные сведения и категорию заявителя.",
                },
                {
                    "id": "budget",
                    "title": "План расходов",
                    "hint": "Укажите затраты и собственные средства. Суммы в демо вымышлены.",
                },
                {
                    "id": "business-plan",
                    "title": "Описание проекта",
                    "hint": "Опишите цель и ожидаемый результат проекта.",
                },
            ],
            "sources": [
                {
                    "title": "Синтетический набор Опора АПК",
                    "url": "https://example.invalid/opora-demo",
                    "reference": "data/demo/catalog.json — не нормативный акт",
                    "published_on": now.date().isoformat(),
                }
            ],
            "verified_at": (
                now - timedelta(days=30 if entry.get("stale") else 0)
            ).isoformat(),
            "verification_status": "verified",
            "valid_from": (now - timedelta(days=365)).isoformat(),
            "valid_until": (now + timedelta(days=365)).isoformat(),
        }
        validated = VersionData.model_validate(data)
        measure = Measure(
            id=entry["id"],
            title=entry["title"],
            category=entry["category"],
            synthetic=True,
        )
        db.add(measure)
        db.flush()
        version = Version(
            id=str(uuid4()),
            measure_id=measure.id,
            number=1,
            state="published",
            data=validated.model_dump(mode="json"),
        )
        db.add(version)
        db.flush()
        starts, ends = (
            (-60, -10)
            if entry.get("closed")
            else (10, 40) if entry.get("scheduled") else (-10, 30)
        )
        add_rounds(
            db,
            version.id,
            [
                RoundInput(
                    code="DEMO-" + entry["id"].upper(),
                    starts_at=now + timedelta(days=starts),
                    ends_at=now + timedelta(days=ends),
                    acceptance_status="confirmed_open",
                    acceptance_checked_at=now,
                    application_url="https://promote.budget.gov.ru/",
                    channel="Официальный портал — только ознакомление в демо",
                )
            ],
        )
    db.commit()


if __name__ == "__main__":
    with SessionLocal() as db:
        seed_demo(db)
