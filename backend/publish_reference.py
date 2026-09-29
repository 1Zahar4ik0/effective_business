import argparse
from copy import deepcopy
from sqlalchemy import select
from app.api import transition
from app.catalog import publication_checks
from app.config import settings
from app.db import SessionLocal
from app.models import User, Version
from app.schemas import RevisionInput
from import_official import load_catalog, import_catalog, stage_revisions


def main():
    parser = argparse.ArgumentParser(description='Публикация справочных карточек без подтверждения права участия')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--actor-max-id')
    args = parser.parse_args()
    entries = deepcopy(load_catalog())
    for entry in entries:
        entry['payload']['data']['publication_scope'] = 'reference'
        entry['payload']['data']['reference_rule_ids'] = {
            'saratov-agroprogress': ['not-kfh', 'grant_cap_186'],
            'saratov-agromotivator': ['grant_cap_186'],
        }.get(entry['id'], [])
    if not args.apply:
        print(f'Reference release prepared: {len(entries)} real measures. No changes.')
        return
    allowed = {item.strip() for item in settings().max_admin_ids.split(',') if item.strip()}
    if not args.actor_max_id or args.actor_max_id not in allowed:
        raise RuntimeError('Нужен подтверждённый MAX-редактор из конфигурации')
    with SessionLocal() as db:
        actor = db.get(User, 'max:' + args.actor_max_id)
        if not actor or actor.demo:
            raise RuntimeError('Подтверждённый аккаунт редактора не найден')
        existing_full = {
            version.measure_id for version in db.scalars(select(Version).where(Version.state == 'published'))
            if version.data.get('publication_scope', 'full') == 'full'
        }
        entries = [entry for entry in entries if entry['id'] not in existing_full]
        import_catalog(db, entries)
        prepared = stage_revisions(db, entries, [entry['id'] for entry in entries]) if entries else {'created': [], 'reused': []}
        selected = prepared['created'] + prepared['reused']
        for item in selected:
            publication_checks(db, db.get(Version, item['version_id']))
        db.commit()
        published = 0
        for item in selected:
            version = db.get(Version, item['version_id'])
            if version.state == 'published':
                continue
            if version.state == 'draft':
                transition(version.id, 'review', RevisionInput(revision=version.revision), actor, db)
            if version.state != 'review':
                raise RuntimeError('Требуется новая версия для архивной карточки')
            transition(version.id, 'publish', RevisionInput(revision=version.revision), actor, db)
            published += 1
        print(f'Reference published: {published}; already published: {len(selected)-published}; full publications preserved: {len(existing_full)}')


if __name__ == '__main__':
    main()
