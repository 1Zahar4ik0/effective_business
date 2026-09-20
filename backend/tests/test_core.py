from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode
import pytest
from sqlalchemy import select, func
from app.db import SessionLocal, utcnow
from app.models import BotEvent, Version, Plan, AuthSession
from app.config import Settings, settings
from app.matching import evaluate_rule, combine, availability
from app.schemas import Rule, RoundInput
from app.max_adapter import validate_launch
from conftest import login


@pytest.mark.parametrize('value,status', [(None,'UNKNOWN'),(True,'PASS'),(False,'FAIL')])
def test_tri_state(value,status):
    rule=Rule(id='kfh',label='КФХ',field='is_kfh',op='eq',value=True,source_ref='§1')
    assert evaluate_rule(rule,{'is_kfh':value})['status']==status


@pytest.mark.parametrize('statuses,op,result', [(['PASS','UNKNOWN'],'all','UNKNOWN'),(['FAIL','UNKNOWN'],'all','FAIL'),(['FAIL','UNKNOWN'],'any','UNKNOWN'),(['PASS','UNKNOWN'],'any','PASS'),(['FAIL','FAIL'],'any','FAIL')])
def test_group_logic(statuses,op,result):
    assert combine(statuses,op)==result


def test_decimal_boundary():
    rule=Rule(id='money',label='Сумма',field='own_funds',op='gte',value='300000.01',source_ref='§2')
    assert evaluate_rule(rule,{'own_funds':'300000.00'})['status']=='FAIL'
    assert evaluate_rule(rule,{'own_funds':'300000.01'})['status']=='PASS'


def test_round_dates_and_stale_source(client):
    m=client.get('/api/catalog').json()[0]
    data=m['data']; now=utcnow()
    data.update(verified_at=now.isoformat(),valid_from=(now-timedelta(days=2)).isoformat(),valid_until=(now+timedelta(days=20)).isoformat())
    r=SimpleNamespace(state='announced',starts_at=now,ends_at=now+timedelta(hours=1))
    assert availability(r,data,now)=='open'
    assert availability(r,data,now-timedelta(seconds=1))=='unknown' # будущая дата проверки
    assert availability(r,data,r.ends_at)=='closed'
    data['verified_at']=(now-timedelta(days=8)).isoformat()
    assert availability(r,data,now)=='unknown'
    assert availability(r,data,r.ends_at)=='closed'
    data['verified_at']=now.isoformat();data['verification_status']='conflict'
    assert availability(r,data,now)=='unknown'


def test_round_timezone():
    r=RoundInput(code='test',starts_at='2026-09-18T12:00:00+04:00',ends_at='2026-09-18T13:00:00+04:00',timezone='Europe/Saratov',application_url='https://example.org',channel='test')
    assert r.ends_at.astimezone(timezone.utc).hour==9
    with pytest.raises(ValueError):
        RoundInput(**{**r.model_dump(),'ends_at':'2026-09-18T13:00:00'})


def test_api_scenario_and_persistence(client):
    login(client)
    response=client.put('/api/profile',json={'registration_region':'64','is_kfh':True,'goal':'equipment','own_funds':'450000'})
    assert response.status_code==200
    matches=client.post('/api/matches').json()['results']
    farm=next(m for m in matches if m['measure']['id']=='farm-growth')
    assert farm['status']=='PASS'
    assert all(c['status']=='PASS' for c in farm['checks'])
    body={'round_id':farm['measure']['rounds'][0]['id']}
    plan=client.post('/api/preparation-plans',json=body).json()
    assert client.post('/api/preparation-plans',json=body).json()['id']==plan['id']
    url=f"/api/preparation-plans/{plan['id']}/items/{plan['items'][0]['id']}"
    assert client.patch(url,json={'revision':plan['revision'],'done':True}).status_code==200
    assert client.patch(url,json={'revision':plan['revision'],'done':False}).status_code==409
    login(client)
    assert client.get('/api/preparation-plans').json()[0]['items'][0]['done'] is True
    assert client.get('/api/profile').json()['own_funds']=='450000'


def test_region_and_special_category(client):
    login(client)
    client.put('/api/profile',json={'registration_region':'other','special_category':False,'activity_region':'64'})
    matches=client.post('/api/matches').json()['results']
    by_id={m['measure']['id']:m for m in matches}
    assert by_id['farm-growth']['status']=='FAIL'
    assert by_id['special-farmer']['status']=='FAIL'
    assert by_id['special-farmer']['measure']['rounds'][0]['availability']=='closed'
    client.put('/api/profile',json={})
    assert all(m['status']=='UNKNOWN' for m in client.post('/api/matches').json()['results'])


def test_owner_role_and_csrf(client):
    assert client.get('/api/profile').status_code==401
    login(client)
    assert client.get('/api/admin/versions').status_code==403
    m=client.get('/api/catalog').json()[0]
    p=client.post('/api/preparation-plans',json={'round_id':m['rounds'][0]['id']}).json()
    login(client,'second')
    assert client.get('/api/preparation-plans').json()==[]
    assert client.patch(f"/api/preparation-plans/{p['id']}/items/{p['items'][0]['id']}",json={'revision':1,'done':True}).status_code==404
    assert client.put('/api/profile',json={},headers={'X-CSRF-Token':'wrong'}).status_code==403
    assert client.put('/api/profile',json={},headers={'Origin':'https://attacker.invalid'}).status_code==403
    with SessionLocal() as db:
        for s in db.scalars(select(AuthSession)):
            s.expires_at=utcnow()-timedelta(seconds=1)
        db.commit()
    assert client.get('/api/profile').status_code==401


def test_version_workflow_preserves_plan(client):
    login(client)
    original=client.get('/api/measures/farm-growth').json()
    plan=client.post('/api/preparation-plans',json={'round_id':original['rounds'][0]['id']}).json()
    login(client,'editor')
    draft=client.post(f"/api/admin/versions/{original['version_id']}/clone").json()
    assert draft['version']==2 and draft['state']=='draft'
    base=f"/api/admin/versions/{draft['version_id']}"
    payload={'revision':draft['revision'],'data':draft['data'],'rounds':[{k:v for k,v in r.items() if k not in ('id','availability')} for r in draft['rounds']]}
    payload['data'].update(summary='Новая редакция учебной меры поддержки.',verification_status='verified',verified_at=utcnow().isoformat())
    changed=client.put(base,json=payload)
    assert changed.status_code==200,changed.text
    assert client.put(base,json=payload).status_code==409
    review=client.post(base+'/review',json={'revision':changed.json()['revision']}).json()
    published=client.post(base+'/publish',json={'revision':review['revision']})
    assert published.status_code==200,published.text
    assert client.get('/api/measures/farm-growth').json()['version']==2
    assert client.put(base,json={**payload,'revision':published.json()['revision']}).status_code==409
    login(client)
    saved=client.get('/api/preparation-plans').json()[0]
    assert saved['id']==plan['id'] and saved['measure']['version']==1 and saved['needs_review']
    assert saved['measure']['data']['summary']==original['data']['summary']
    login(client,'editor')
    withdrawn=client.post(base+'/unpublish',json={'revision':published.json()['revision']})
    assert withdrawn.status_code==200
    assert client.get('/api/measures/farm-growth').status_code==404
    login(client)
    assert client.get('/api/preparation-plans').json()[0]['current_version_id'] is None


def test_unverified_publication_rejected(client):
    login(client,'editor')
    m=client.get('/api/catalog').json()[0]
    draft=client.post(f"/api/admin/versions/{m['version_id']}/clone").json()
    base=f"/api/admin/versions/{draft['version_id']}"
    review=client.post(base+'/review',json={'revision':draft['revision']}).json()
    assert client.post(base+'/publish',json={'revision':review['revision']}).status_code==400


def signed_launch(token,auth_date=None):
    params={'auth_date':str(auth_date or int(time.time())),'user':json.dumps({'id':123,'first_name':'Тест'},ensure_ascii=False)}
    secret=hmac.new(b'WebAppData',token.encode(),hashlib.sha256).digest()
    params['hash']=hmac.new(secret,'\n'.join(f'{k}={params[k]}' for k in sorted(params)).encode(),hashlib.sha256).hexdigest()
    return urlencode(params)


def test_max_signature_expiry_and_duplicate_keys():
    raw=signed_launch('token')
    assert validate_launch(raw,'token')['id']==123
    for bad in [raw+'&auth_date=1',raw.replace('hash=','hash=0'),signed_launch('token',int(time.time())-601)]:
        with pytest.raises(ValueError):validate_launch(bad,'token')


def test_max_replay_and_role_assignment(client,monkeypatch):
    monkeypatch.setattr(settings(),'max_bot_token','test-token')
    raw = signed_launch('test-token')
    response=client.post('/api/auth/max',json={'init_data':raw})
    assert response.status_code==200,response.text
    assert response.json()['user']['role']=='farmer'
    assert client.post('/api/auth/max',json={'init_data':raw}).status_code==401


def test_outbox_bounded_retries(client,monkeypatch):
    import asyncio
    from app.jobs import deliver_once
    from app.max_adapter import MaxClient
    monkeypatch.setattr(settings(),'max_bot_token','unit-test')
    async def failure(self, **kwargs):
        raise TimeoutError('test')
    monkeypatch.setattr(MaxClient,'send',failure)
    with SessionLocal() as db:
        db.add(BotEvent(key='retry-test',reply={'chat_id':1,'text':'test'}));db.commit()
    for attempt in range(5):
        assert asyncio.run(deliver_once())==0
        with SessionLocal() as db:
            event=db.get(BotEvent,'retry-test')
            assert event.attempts==attempt+1
            assert event.state==('failed' if attempt==4 else 'pending')
            event.next_attempt=utcnow()-timedelta(seconds=1);db.commit()
    assert asyncio.run(deliver_once())==0
    with SessionLocal() as db:assert db.get(BotEvent,'retry-test').attempts==5


def test_openapi_contract_snapshot():
    from pathlib import Path
    from app.main import app
    stored=json.loads((Path(__file__).resolve().parents[2]/'docs/openapi.json').read_text(encoding='utf-8'))
    assert stored==app.openapi()


def test_webhook_secret_and_dedup(client,monkeypatch):
    monkeypatch.setattr(settings(),'max_webhook_secret','unit-test-secret')
    monkeypatch.setattr(settings(),'max_app_url','https://example.org/app')
    payload={'update_type':'message_created','message':{'recipient':{'chat_id':100},'body':{'mid':'unique-message','text':'/start'}}}
    assert client.post('/api/max/webhook',json=payload).status_code==403
    for _ in range(2):
        assert client.post('/api/max/webhook',json=payload,headers={'X-Max-Bot-Api-Secret':'unit-test-secret'}).status_code==200
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(BotEvent))==1


def test_production_guards(client,monkeypatch):
    with pytest.raises(ValueError):Settings(app_env='production',seed_demo=True,public_origin='https://example.org')
    monkeypatch.setattr(settings(),'app_env','production')
    assert client.post('/api/auth/demo',json={'persona':'editor'}).status_code==404
    assert client.get('/api/catalog').json()==[]
    from app.main import create_app
    from fastapi.testclient import TestClient
    with pytest.raises(RuntimeError,match='демонстрационную'):
        with TestClient(create_app()):pass
