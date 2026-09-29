from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .db import aware, utcnow
from .matching import availability
from .models import AuditEvent, Measure, Plan, Profile, SelectionRound, Version
from .schemas import BusinessProfile, RoundInput, VersionData


def audit(db: Session, actor: str, action: str, entity: str):
    db.add(AuditEvent(id=str(uuid4()), actor_id=actor, action=action, entity_id=entity))


def visible_versions(db: Session):
    query = select(Version).join(Measure).where(Version.state == "published")
    if settings().app_env == "production":
        query = query.where(Measure.synthetic.is_(False))
    return db.scalars(query.order_by(Measure.title)).all()


def current_version(db: Session, measure_id: str):
    return db.scalar(
        select(Version).where(
            Version.measure_id == measure_id, Version.state == "published"
        )
    )


def serialize_measure(db: Session, version: Version):
    measure = db.get(Measure, version.measure_id)
    rounds = db.scalars(
        select(SelectionRound)
        .where(SelectionRound.version_id == version.id)
        .order_by(SelectionRound.ends_at)
    ).all()
    return {
        "id": measure.id,
        "title": measure.title,
        "category": measure.category,
        "synthetic": measure.synthetic,
        "version_id": version.id,
        "version": version.number,
        "state": version.state,
        "revision": version.revision,
        "data": version.data,
        "rounds": [
            {
                "id": r.id,
                "code": r.code,
                "starts_at": aware(r.starts_at),
                "ends_at": aware(r.ends_at),
                "timezone": r.timezone,
                "state": r.state,
                "application_url": r.application_url,
                "channel": r.channel,
                "acceptance_status": r.acceptance_status,
                "acceptance_checked_at": (
                    aware(r.acceptance_checked_at) if r.acceptance_checked_at else None
                ),
                "availability": availability(
                    r, version.data, fresh_days=settings().source_fresh_days
                ),
            }
            for r in rounds
        ],
    }


def serialize_plan(db: Session, plan: Plan):
    version = db.get(Version, plan.version_id)
    current = current_version(db, version.measure_id)
    profile = db.get(Profile, plan.user_id)
    current_profile = BusinessProfile.model_validate(
        profile.data if profile else {}
    ).model_dump()
    saved_profile = (
        BusinessProfile.model_validate(plan.assessment["profile"]).model_dump()
        if plan.assessment
        else None
    )
    return {
        "id": plan.id,
        "revision": plan.revision,
        "created_at": aware(plan.created_at),
        "items": plan.items,
        "measure": serialize_measure(db, version),
        "round_id": plan.round_id,
        "needs_review": current is None or current.id != version.id,
        "current_version_id": current.id if current else None,
        "assessment": plan.assessment,
        "profile_changed": saved_profile is not None
        and current_profile != saved_profile,
    }


def add_rounds(db: Session, version_id: str, rounds: list[RoundInput]):
    for round_ in rounds:
        values = round_.model_dump()
        values["application_url"] = str(round_.application_url)
        db.add(SelectionRound(id=str(uuid4()), version_id=version_id, **values))


def lock_version(db: Session, version_id: str, revision: int):
    version = db.scalar(
        select(Version).where(Version.id == version_id).with_for_update()
    )
    if not version:
        raise HTTPException(404, "Версия не найдена")
    if version.revision != revision:
        raise HTTPException(409, "Версия уже изменена. Обновите страницу")
    return version


def publication_checks(db: Session, version: Version):
    measure = db.get(Measure, version.measure_id)
    data = VersionData.model_validate(version.data)
    if data.publication_scope == "reference":
        if measure.synthetic:
            raise HTTPException(400, "Справочная публикация предназначена для реальных источников")
        if not data.research_checked_at or data.research_checked_at > utcnow():
            raise HTTPException(400, "Нужна фактическая дата исследования источников")
        if not data.documents or not data.legal_edition:
            raise HTTPException(400, "Нужны перечень документов и описание редакции")
        if any("example." in str(source.url) for source in data.sources):
            raise HTTPException(400, "Нужны реальные источники")
        if not db.scalar(select(SelectionRound).where(SelectionRound.version_id == version.id)):
            raise HTTPException(400, "Добавьте отбор и канал подачи")
        return
    if (
        data.missing_evidence
        or not data.rules
        or not data.documents
        or not data.has_validity_period
    ):
        raise HTTPException(
            400,
            "Не завершена проверка: заполните условия, документы, начало и конец периода (либо подтвердите отсутствие конечной даты ссылкой на источник) и устраните пробелы доказательств",
        )
    if not measure.synthetic and not data.legal_edition:
        raise HTTPException(400, "Укажите применимую редакцию нормативных документов")
    if measure.synthetic and settings().app_env == "production":
        raise HTTPException(400, "Синтетические данные запрещены")
    if (
        data.verification_status != "verified"
        or not data.verified_at
        or data.verified_at > utcnow()
    ):
        raise HTTPException(400, "Подтвердите источники и корректную дату проверки")
    if not db.scalar(
        select(SelectionRound).where(SelectionRound.version_id == version.id)
    ):
        raise HTTPException(400, "Добавьте отбор и канал подачи")
    if not measure.synthetic and any("example." in str(s.url) for s in data.sources):
        raise HTTPException(400, "Для реальной меры укажите реальные источники")
