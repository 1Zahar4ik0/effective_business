import os
import sys
from sqlalchemy.engine import make_url

name = sys.argv[1]
assert name.startswith('navigator_deploy_')
os.environ['DATABASE_URL'] = make_url(os.environ['DATABASE_URL']).set(database=name).render_as_string(hide_password=False)
from app.db import SessionLocal
from app.models import Profile, Plan, Version, SelectionRound
from sqlalchemy import select
from app.schemas import BusinessProfile, VersionData
from app.main import app
from fastapi.testclient import TestClient
with SessionLocal() as db:
    for p in db.scalars(select(Profile)):
        BusinessProfile.model_validate(p.data)
    for v in db.scalars(select(Version)):
        VersionData.model_validate(v.data)
    list(db.scalars(select(Plan)))
    list(db.scalars(select(SelectionRound)))
with TestClient(app, base_url=os.environ['PUBLIC_ORIGIN']) as client:
    assert client.get('/health').status_code == 200
    assert client.get('/api/config').json()['demo'] is False
    assert client.get('/api/catalog').status_code == 200
    assert client.get('/api/profile').status_code == 401
print('Old-image read compatibility with migrated production copy: PASS')
