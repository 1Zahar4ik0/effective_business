from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace
from conftest import login
from import_official import load_catalog
from app.db import utcnow
from app.matching import evaluate, evaluate_documents, availability


def payload():
    entry = next(entry for entry in load_catalog() if entry['id'] == 'saratov-farm')
    value = deepcopy(entry['payload'])
    value['data']['publication_scope'] = 'reference'
    return value


def test_reference_never_claims_eligibility_or_document_requirement():
    data = payload()['data']
    for profile in ({}, {'registration_region': 'other'}, {'is_kfh': True, 'own_funds': '999999'}):
        assert evaluate(data, profile)['status'] == 'UNKNOWN'
        assert all(document['applicability'] == 'unknown' for document in evaluate_documents(data, profile))
    now = utcnow()
    round_ = SimpleNamespace(state='announced', starts_at=now-timedelta(days=1), ends_at=now+timedelta(days=1), acceptance_status='confirmed_open', acceptance_checked_at=now)
    assert availability(round_, data, now) == 'unknown'
    round_.ends_at = now
    assert availability(round_, data, now) == 'closed'


def test_reference_workflow_plan_and_access(client):
    login(client, 'editor')
    response = client.post('/api/admin/measures', json=payload())
    assert response.status_code == 200, response.text
    card = response.json()
    measure_id = card['id']
    version_id = card['version_id']
    assert not any(item['id'] == measure_id for item in client.get('/api/catalog').json())
    for action in ('review', 'publish'):
        response = client.post(f'/api/admin/versions/{version_id}/{action}', json={'revision': card['revision']})
        assert response.status_code == 200, response.text
        card = response.json()
    login(client, 'farmer')
    assert any(item['id'] == measure_id for item in client.get('/api/catalog').json())
    assert client.put('/api/profile', json={'is_kfh': True}).status_code == 200
    match = next(item for item in client.post('/api/matches').json()['results'] if item['measure']['id'] == measure_id)
    assert match['status'] == 'UNKNOWN'
    plan = client.post('/api/preparation-plans', json={'round_id': card['rounds'][0]['id']})
    assert plan.status_code == 200, plan.text
    plan = plan.json()
    assert plan['assessment']['status'] == 'UNKNOWN'
    assert plan['measure']['data']['publication_scope'] == 'reference'
    assert all(item['applicability'] == 'unknown' for item in plan['items'])
    login(client, 'second')
    assert plan['id'] not in [item['id'] for item in client.get('/api/preparation-plans').json()]
    assert client.patch(f"/api/preparation-plans/{plan['id']}/items/{plan['items'][0]['id']}", json={'done': True, 'revision': plan['revision']}).status_code == 404
    assert client.post(f'/api/admin/versions/{version_id}/unpublish', json={'revision': card['revision']}).status_code == 403
    login(client, 'editor')
    assert client.post(f'/api/admin/versions/{version_id}/unpublish', json={'revision': card['revision']}).status_code == 200
    assert not any(item['id'] == measure_id for item in client.get('/api/catalog').json())
    login(client, 'farmer')
    saved = next(item for item in client.get('/api/preparation-plans').json() if item['id'] == plan['id'])
    assert saved['needs_review'] is True
    assert saved['assessment']['status'] == 'UNKNOWN'


def test_reference_does_not_relax_full_publication(client):
    login(client, 'editor')
    value = payload()
    value['data']['publication_scope'] = 'full'
    card = client.post('/api/admin/measures', json=value).json()
    version_id = card['version_id']
    card = client.post(f'/api/admin/versions/{version_id}/review', json={'revision': card['revision']}).json()
    assert client.post(f'/api/admin/versions/{version_id}/publish', json={'revision': card['revision']}).status_code == 400


def test_reference_requires_provenance(client):
    login(client, 'editor')
    value = payload()
    value['data']['research_checked_at'] = None
    card = client.post('/api/admin/measures', json=value).json()
    version_id = card['version_id']
    card = client.post(f'/api/admin/versions/{version_id}/review', json={'revision': card['revision']}).json()
    assert client.post(f'/api/admin/versions/{version_id}/publish', json={'revision': card['revision']}).status_code == 400


def test_reference_release_command_is_idempotent(client, monkeypatch):
    import sys
    from sqlalchemy import select, func
    from app.config import settings
    from app.db import SessionLocal
    from app.models import User, Version, AuditEvent
    from publish_reference import main
    monkeypatch.setattr(settings(), 'max_admin_ids', '900000001')
    monkeypatch.setattr(sys, 'argv', ['publish_reference.py', '--apply', '--actor-max-id', '900000001'])
    with SessionLocal() as db:
        db.add(User(id='max:900000001', name='Isolated test editor', role='editor', demo=False))
        db.commit()
    main()
    with SessionLocal() as db:
        versions = db.scalars(select(Version).where(Version.state == 'published')).all()
        assert len([v for v in versions if v.data.get('publication_scope') == 'reference']) == 10
        count = db.scalar(select(func.count()).select_from(Version))
        audit_count = db.scalar(select(func.count()).select_from(AuditEvent))
    main()
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Version)) == count
        assert db.scalar(select(func.count()).select_from(AuditEvent)) == audit_count


def test_confirmed_reference_exclusion_and_cap():
    for entry in load_catalog():
        if entry['id'] != 'saratov-agroprogress':
            continue
        data = deepcopy(entry['payload']['data'])
        data['publication_scope'] = 'reference'
        data['reference_rule_ids'] = ['not-kfh', 'grant_cap_186']
        assert evaluate(data, {'is_kfh': True})['status'] == 'FAIL'
        assert evaluate(data, {'is_kfh': False, 'requested_grant': '16853932.60'})['status'] == 'FAIL'
        assert evaluate(data, {'is_kfh': False, 'requested_grant': '16853932.59'})['status'] == 'UNKNOWN'
        assert evaluate(data, {})['status'] == 'UNKNOWN'
