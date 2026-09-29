import os
import subprocess
import sys
from sqlalchemy.engine import make_url

name = sys.argv[1]
assert name.startswith('navigator_deploy_')
os.environ['DATABASE_URL'] = make_url(os.environ['DATABASE_URL']).set(database=name).render_as_string(hide_password=False)
subprocess.run(['alembic','-c','backend/alembic.ini','upgrade','head'],check=True)
subprocess.run(['alembic','-c','backend/alembic.ini','check'],check=True)
from app.db import SessionLocal
from app.models import Profile, Plan
from sqlalchemy import select
from app.schemas import BusinessProfile, PlanAssessment
with SessionLocal() as db:
    profiles = db.scalars(select(Profile)).all()
    plans = db.scalars(select(Plan)).all()
    for p in profiles:
        BusinessProfile.model_validate(p.data)
    for p in plans:
        if p.assessment is not None:
            PlanAssessment.model_validate(p.assessment)
    print(f'Production-copy validation PASS: profiles={len(profiles)}, plans={len(plans)}, nullable assessment respected')
