from copy import deepcopy
from datetime import timedelta
import pytest
from pydantic import ValidationError
from app.db import SessionLocal, utcnow
from app.matching import evaluate_documents
from app.models import Plan
from app.schemas import VersionData
from conftest import login


def condition(field="is_kfh", value=True):
    return dict(id="branch", label="СИНТЕТИЧЕСКОЕ условие документа", field=field,
                op="eq", value=value, source_ref="QA, пункт 1")


def payload(client):
    data = deepcopy(client.get('/api/measures/farm-growth').json()['data'])
    now = utcnow()
    data.update(verified_at=now.isoformat(), valid_from=(now-timedelta(days=1)).isoformat(),
                valid_until=(now+timedelta(days=10)).isoformat())
    data['documents'] = [
        dict(id="always", title="Общий документ", hint="QA"),
        dict(id="branch", title="Документ КФХ", hint="QA", condition=condition()),
        dict(id="manual", title="Документ по результату проверки", hint="QA",
             condition=dict(id="manual", label="Проверить основание по документам", op="manual", source_ref="QA, п. 2")),
        dict(id="year", title="Документ по году затрат", hint="QA", condition=condition("expense_year", 2026)),
    ]
    return data


@pytest.mark.parametrize('answer,expected', [(None,'unknown'), (True,'required'), (False,'not_applicable')])
def test_document_three_states_and_manual_never_proved(client, answer, expected):
    docs = evaluate_documents(payload(client), {'is_kfh':answer, 'expense_year':2026})
    assert [d['applicability'] for d in docs] == ['required',expected,'unknown','required']
    assert docs[2]['check']['status'] == 'UNKNOWN'
    assert docs[1]['check']['source_ref'] == 'QA, пункт 1'


def publish(client, data):
    login(client, 'editor')
    now = utcnow()
    r = dict(code='SYNTHETIC-CONDITIONAL', starts_at=(now-timedelta(days=1)).isoformat(),
             ends_at=(now+timedelta(days=2)).isoformat(), timezone='Europe/Moscow',
             application_url='https://example.invalid/official-route', channel='QA')
    response = client.post('/api/admin/measures', json=dict(title='СИНТЕТИЧЕСКИЕ условные документы',
                           synthetic=True, category='subsidy', data=data, rounds=[r]))
    assert response.status_code == 200, response.text
    measure = response.json()
    for action in ('review','publish'):
        response = client.post(f"/api/admin/versions/{measure['version_id']}/{action}", json={'revision':measure['revision']})
        assert response.status_code == 200, response.text
        measure = response.json()
    return measure


def test_conditional_plan_preserves_history_questions_and_owner(client):
    data = payload(client)
    data['rules'] = [dict(id='manual-rule',label='Документальная проверка',op='manual',source_ref='QA')]
    measure = publish(client, data)
    assert [q['field'] for q in client.get('/api/profile/questions').json()] == ['expense_year']
    login(client)
    client.put('/api/profile', json={'is_kfh':True,'legal_form':'ip','tax_regime':'usn','expense_year':2026})
    match = next(m for m in client.post('/api/matches').json()['results'] if m['measure']['id'] == measure['id'])
    assert match['status'] == 'UNKNOWN'
    body = {'round_id':measure['rounds'][0]['id']}
    plan = client.post('/api/preparation-plans', json=body).json()
    assert [{k:v for k,v in item.items() if k != 'done'} for item in plan['items']] == match['documents']
    assert plan['assessment']['engine_version'] == 'rules-20260928.1'
    assert plan['assessment']['availability'] == 'unknown'
    original = deepcopy(plan)
    client.put('/api/profile', json={'is_kfh':False,'legal_form':'cooperative','tax_regime':'eshn','expense_year':2025})
    repeat = client.post('/api/preparation-plans', json=body).json()
    assert repeat['profile_changed'] and repeat['items'] == original['items']
    assert repeat['assessment'] == original['assessment']
    match = next(m for m in client.post('/api/matches').json()['results'] if m['measure']['id'] == measure['id'])
    assert match['documents'][1]['applicability'] == 'not_applicable'
    marked = client.patch(f"/api/preparation-plans/{plan['id']}/items/manual", json={'revision':plan['revision'],'done':True}).json()
    assert marked['items'][2]['applicability'] == 'unknown'
    assert marked['assessment'] == original['assessment']
    assert client.patch(f"/api/preparation-plans/{plan['id']}/items/manual", json={'revision':plan['revision'],'done':False}).status_code == 409
    login(client,'second')
    assert client.get('/api/preparation-plans').json() == []
    assert client.patch(f"/api/preparation-plans/{plan['id']}/items/manual", json={'revision':marked['revision'],'done':False}).status_code == 404


def test_legacy_plan_json_is_not_backfilled(client):
    login(client)
    m = client.get('/api/measures/farm-growth').json()
    p = client.post('/api/preparation-plans',json={'round_id':m['rounds'][0]['id']}).json()
    with SessionLocal() as db:
        plan = db.get(Plan,p['id'])
        plan.items = [{k:v for k,v in d.items() if k not in ('condition','applicability','check')} for d in plan.items]
        old_items = deepcopy(plan.items)
        plan.assessment = {k:v for k,v in plan.assessment.items() if k != 'engine_version'}
        old_assessment = deepcopy(plan.assessment)
        db.commit()
    response = client.get('/api/preparation-plans').json()[0]
    assert response['items'][0]['applicability'] is None
    assert response['assessment']['engine_version'] is None
    with SessionLocal() as db:
        plan = db.get(Plan,p['id'])
        assert plan.items == old_items and plan.assessment == old_assessment


def test_nested_document_condition_truth_table_and_depth(client):
    data = payload(client)
    a = condition()
    b = dict(condition('legal_form','cooperative'), id='coop')
    data['documents'][1]['condition'] = dict(id='either',label='КФХ или кооператив',op='any',children=[a,b],source_ref='QA')
    for profile, expected in [({},'unknown'),({'is_kfh':False},'unknown'),
                              ({'is_kfh':False,'legal_form':'ip'},'not_applicable'),
                              ({'is_kfh':False,'legal_form':'cooperative'},'required')]:
        result = evaluate_documents(data,profile)[1]
        assert result['applicability'] == expected
        assert len(result['check']['children']) == 2
    for i in range(7):
        a = dict(id=f'level{i}',label='QA',op='all',children=[a],source_ref='QA')
    data['documents'][1]['condition'] = a
    with pytest.raises(ValidationError):
        VersionData.model_validate(data)


def test_draft_document_questions_not_exposed(client):
    data = payload(client)
    login(client,'editor')
    response = client.post('/api/admin/measures',json=dict(title='СИНТЕТИЧЕСКИЙ черновик',synthetic=True,category='grant',data=data,rounds=[]))
    assert response.status_code == 200
    assert client.get('/api/profile/questions').json() == []
