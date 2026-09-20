from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace
import json
import httpx
import pytest
from sqlalchemy import select
from app.catalog import publication_checks
from app.db import SessionLocal
from app.matching import evaluate, evaluate_rule, availability
from app.models import Version, Measure
from app.schemas import Rule, VersionData
from import_official import load_catalog, import_catalog
from max_preflight import check
from conftest import login


def test_import_preserves_edits_and_never_publishes(client):
    entries=load_catalog()
    with SessionLocal() as db:
        assert len(import_catalog(db,entries)['created'])==10
        db.commit()
        v=db.scalar(select(Version).where(Version.measure_id==entries[0]['id']))
        v.data={**v.data,'summary':'Исправление редактора, которое импорт не должен перезаписать.'}
        db.commit()
        assert len(import_catalog(db,entries)['preserved'])==10
        db.commit()
        db.refresh(v)
        assert v.data['summary'].startswith('Исправление редактора')
        assert v.state=='draft'
    assert all(m['synthetic'] for m in client.get('/api/catalog').json())
    login(client,'editor')
    assert len([m for m in client.get('/api/admin/versions').json() if not m['synthetic']])==10


def test_unknown_draft_and_manual_rules_cannot_pass():
    d=load_catalog()[0]['payload']['data']
    assert evaluate({**d,'rules':[]},{})['status']=='UNKNOWN'
    r=Rule(id='manual',label='Проверить документы',op='manual',source_ref='§1')
    assert evaluate_rule(r,{'special_category':True})['status']=='UNKNOWN'
    with pytest.raises(ValueError):
        Rule(id='manual',label='Invalid',op='manual',field='is_kfh',value=True,source_ref='§1')


def test_actual_agroprogress_exclusion_and_agromotivator_category():
    entries={e['id']:e['payload']['data'] for e in load_catalog()}
    assert evaluate(entries['saratov-agroprogress'],{'is_kfh':True,'legal_form':'ip'})['status']=='FAIL'
    assert evaluate(entries['saratov-agroprogress'],{'is_kfh':False,'legal_form':'company'})['status']=='UNKNOWN'
    a=entries['saratov-agromotivator']
    assert all(r.get('field')!='special_category' for r in a['rules'])
    assert evaluate(a,{'special_category':True,'is_kfh':True})['status']=='UNKNOWN'


def test_real_deadlines_and_incomplete_evidence():
    entries={e['id']:e['payload'] for e in load_catalog()}
    now=datetime(2026,9,18,12,tzinfo=timezone.utc)
    for key in ('cooperative','grain','classes'):
        p=entries['saratov-'+key]; r=SimpleNamespace(**p['rounds'][0])
        r.starts_at=datetime.fromisoformat(r.starts_at);r.ends_at=datetime.fromisoformat(r.ends_at)
        assert availability(r,p['data'],now)=='closed'
    p=entries['saratov-students'];r=SimpleNamespace(**p['rounds'][0])
    r.starts_at=datetime.fromisoformat(r.starts_at);r.ends_at=datetime.fromisoformat(r.ends_at)
    assert availability(r,p['data'],now)=='unknown'
    p['data'].update(verification_status='verified',verified_at=now.isoformat(),valid_from=r.starts_at.isoformat(),valid_until=r.ends_at.isoformat())
    assert availability(r,p['data'],now)=='unknown' # unresolved evidence still blocks open


def test_editor_cannot_publish_incomplete_real_data(client):
    login(client,'editor')
    payload=deepcopy(load_catalog()[0]['payload'])
    created=client.post('/api/admin/measures',json=payload)
    assert created.status_code==200,created.text
    m=created.json()
    m=client.post(f"/api/admin/versions/{m['version_id']}/review",json={'revision':m['revision']}).json()
    assert client.post(f"/api/admin/versions/{m['version_id']}/publish",json={'revision':m['revision']}).status_code==400
    assert client.get('/api/measures/'+m['id']).status_code==404


def test_safe_max_preflight_does_not_leak_or_send():
    cfg=SimpleNamespace(max_bot_token='private-test-token',max_webhook_secret='private-secret',max_app_url='https://max.ru/test',
                        max_admin_ids='1',public_origin='https://apk.example.org',max_api_base='https://platform-api2.max.ru',max_ca_bundle='')
    calls=[]
    def handler(request):
        calls.append((request.method,request.url.path))
        assert request.headers['Authorization']=='private-test-token'
        return httpx.Response(200,json={'is_bot':True} if request.url.path=='/me' else {'subscriptions':[{'url':'https://apk.example.org/api/max/webhook','secret':'private-secret'}]})
    result=check(cfg,httpx.MockTransport(handler))
    assert result['bot_api']=='authenticated' and result['webhook_registered']
    assert calls==[('GET','/me'),('GET','/subscriptions')]
    assert 'private-' not in json.dumps(result)
    cfg.max_bot_token=''
    assert check(cfg,httpx.MockTransport(handler))['bot_api']=='not_configured'
    assert len(calls)==2


def test_max_token_never_follows_redirect_or_unreviewed_origin():
    from app.max_adapter import MaxClient
    cfg=SimpleNamespace(max_bot_token='private-test-token',max_webhook_secret='',max_app_url='',
                        max_admin_ids='',public_origin='http://localhost:8000',
                        max_api_base='https://platform-api2.max.ru',max_ca_bundle='')
    calls=[]
    def redirect(request):
        calls.append(str(request.url))
        return httpx.Response(302,headers={'Location':'https://third-party.example.org/capture'})
    report=check(cfg,httpx.MockTransport(redirect))
    assert report['bot_api']=='http_302'
    assert calls==['https://platform-api2.max.ru/me']
    cfg.max_api_base='https://third-party.example.org'
    assert check(cfg,httpx.MockTransport(redirect))['bot_api']=='blocked_unreviewed_api_origin'
    with pytest.raises(ValueError):
        MaxClient(cfg)
    assert len(calls)==1
