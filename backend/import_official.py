"""Import prepared sources as drafts only; existing editor work is never replaced."""
import argparse
import json
from pathlib import Path
from uuid import uuid4
from sqlalchemy import select, text
from app.db import SessionLocal
from app.models import Measure, Version
from app.catalog import add_rounds
from app.schemas import NewMeasure

CATALOG = Path(__file__).resolve().parents[1] / 'data/official/catalog.json'

def load_catalog(path=CATALOG):
    entries = json.loads(Path(path).read_text(encoding='utf-8'))['measures']
    ids = [e['id'] for e in entries]
    if len(ids) != len(set(ids)):
        raise ValueError('Повтор ID меры')
    for entry in entries:
        if not entry['id'].startswith('saratov-') or entry['payload'].get('synthetic') is not False:
            raise ValueError('Ожидаются только реальные меры Саратовской области')
        NewMeasure.model_validate(entry['payload'])
    return entries

def import_catalog(db, entries):
    # Serialize concurrent CLI imports without changing existing records.
    db.execute(text('SELECT pg_advisory_xact_lock(6409182026)'))
    created, skipped = [], []
    for entry in entries:
        if db.get(Measure, entry['id']):
            skipped.append(entry['id'])
            continue
        payload = NewMeasure.model_validate(entry['payload'])
        measure = Measure(id=entry['id'], title=payload.title, category=payload.category, synthetic=False)
        db.add(measure)
        db.flush()
        version = Version(id=str(uuid4()), measure_id=measure.id, number=1, state='draft',
                          data=payload.data.model_dump(mode='json'))
        db.add(version)
        db.flush()
        add_rounds(db, version.id, payload.rounds)
        created.append(entry['id'])
    return {'created': created, 'preserved': skipped}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Сохранить только новые черновики в БД')
    args = parser.parse_args()
    entries = load_catalog()
    if args.apply:
        with SessionLocal() as db:
            result = import_catalog(db, entries)
            db.commit()
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f'Проверено {len(entries)} реальных черновиков. БД не изменена. Для импорта: --apply')
