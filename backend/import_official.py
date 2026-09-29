import argparse
import json
from pathlib import Path
from uuid import uuid4
from datetime import timezone
from sqlalchemy import select, text
from app.db import SessionLocal
from app.models import Measure, Version, SelectionRound
from app.catalog import add_rounds
from app.schemas import NewMeasure, RoundInput, VersionData

CATALOG = Path(__file__).resolve().parents[1] / "data/official/catalog.json"


def load_catalog(path=CATALOG):
    entries = json.loads(Path(path).read_text(encoding="utf-8"))["measures"]
    ids = [e["id"] for e in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("Повтор ID меры")
    for entry in entries:
        if (
            not entry["id"].startswith("saratov-")
            or entry["payload"].get("synthetic") is not False
        ):
            raise ValueError("Ожидаются только реальные меры Саратовской области")
        NewMeasure.model_validate(entry["payload"])
    return entries


def import_catalog(db, entries):

    db.execute(text("SELECT pg_advisory_xact_lock(6409182026)"))
    created, skipped = [], []
    for entry in entries:
        if db.get(Measure, entry["id"]):
            skipped.append(entry["id"])
            continue
        payload = NewMeasure.model_validate(entry["payload"])
        measure = Measure(
            id=entry["id"],
            title=payload.title,
            category=payload.category,
            synthetic=False,
        )
        db.add(measure)
        db.flush()
        version = Version(
            id=str(uuid4()),
            measure_id=measure.id,
            number=1,
            state="draft",
            data=payload.data.model_dump(mode="json"),
        )
        db.add(version)
        db.flush()
        add_rounds(db, version.id, payload.rounds)
        created.append(entry["id"])
    return {"created": created, "preserved": skipped}


def canonical_rounds(rounds):

    normalized = []
    for values in rounds:
        item = RoundInput.model_validate(values).model_dump(mode="json")
        parsed = RoundInput.model_validate(values)
        for key in ("starts_at", "ends_at", "acceptance_checked_at"):
            value = getattr(parsed, key)
            item[key] = value.astimezone(timezone.utc).isoformat() if value else None
        normalized.append(item)
    return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True))


def stage_revisions(db, entries, measure_ids):
    by_id = {e["id"]: e for e in entries}
    selected = sorted(set(measure_ids))
    if not selected or any(key not in by_id for key in selected):
        raise ValueError("Укажите существующие ID из официального каталога")
    db.execute(text("SELECT pg_advisory_xact_lock(6409182026)"))
    prepared = []
    for key in selected:
        measure = db.scalar(select(Measure).where(Measure.id == key).with_for_update())
        payload = NewMeasure.model_validate(by_id[key]["payload"])
        if not measure or measure.synthetic or payload.synthetic:
            raise ValueError("Для новой версии нужна существующая реальная мера")
        if (measure.title, measure.category) != (payload.title, payload.category):
            raise ValueError(
                "Название или категория изменены редактором: требуется ручное сопоставление"
            )
        data = payload.data.model_dump(mode="json")
        data["verified_at"] = None
        if data["verification_status"] != "conflict":
            data["verification_status"] = "unverified"
        prepared.append((measure, payload, data))
    created, reused = [], []
    for measure, payload, data in prepared:
        versions = db.scalars(
            select(Version)
            .where(Version.measure_id == measure.id)
            .order_by(Version.number.desc())
        ).all()
        candidate_rounds = canonical_rounds([r.model_dump() for r in payload.rounds])
        existing = None
        for version in versions:
            if VersionData.model_validate(version.data).model_dump(mode="json") != data:
                continue
            rows = db.scalars(
                select(SelectionRound).where(SelectionRound.version_id == version.id)
            ).all()
            actual_rounds = [
                {key: getattr(r, key) for key in RoundInput.model_fields} for r in rows
            ]
            if canonical_rounds(actual_rounds) == candidate_rounds:
                existing = version
                break
        if existing:
            reused.append(
                {
                    "measure_id": measure.id,
                    "version_id": existing.id,
                    "number": existing.number,
                }
            )
            continue
        version = Version(
            id=str(uuid4()),
            measure_id=measure.id,
            number=max((v.number for v in versions), default=0) + 1,
            state="draft",
            data=data,
        )
        db.add(version)
        db.flush()
        add_rounds(db, version.id, payload.rounds)
        db.flush()
        created.append(
            {
                "measure_id": measure.id,
                "version_id": version.id,
                "number": version.number,
            }
        )
    return {"created": created, "reused": reused}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import prepared sources as drafts only; existing editor work is never replaced."
    )
    parser.add_argument(
        "--apply", action="store_true", help="Сохранить только новые черновики в БД"
    )
    parser.add_argument(
        "--stage-revision",
        action="append",
        default=[],
        metavar="MEASURE_ID",
        help="Создать отдельную новую версию выбранной существующей меры, не изменяя старую",
    )
    args = parser.parse_args()
    if args.stage_revision and not args.apply:
        parser.error("--stage-revision требует явного --apply")
    entries = load_catalog()
    if args.apply:
        with SessionLocal() as db:
            result = (
                stage_revisions(db, entries, args.stage_revision)
                if args.stage_revision
                else import_catalog(db, entries)
            )
            db.commit()
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(
            f"Проверено {len(entries)} реальных черновиков. БД не изменена. Для импорта: --apply"
        )
