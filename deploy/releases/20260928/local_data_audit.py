import hashlib,json,sys
from pathlib import Path
from sqlalchemy import create_engine,text
import os
from sqlalchemy.engine import make_url

action,filename,*database=sys.argv[1:]
url=make_url(os.environ['DATABASE_URL'])
if database:
    assert database[0].startswith('navigator_deploy_')
    url=url.set(database=database[0])
engine=create_engine(url)
result={}
with engine.connect() as connection:
    for table in ['users','profiles','preparation_plans','measures','measure_versions','selection_rounds','evaluations','audit_events']:
        rows=connection.execute(text(f'SELECT to_jsonb(t) FROM {table} t')).scalars().all()
        hashes=[]
        for row in rows:
            if table=='preparation_plans':row.setdefault('assessment',None)
            if table=='selection_rounds':
                row.setdefault('acceptance_status','unconfirmed');row.setdefault('acceptance_checked_at',None)
            hashes.append(hashlib.sha256(json.dumps(row,sort_keys=True,ensure_ascii=False).encode()).hexdigest())
        result[table]=sorted(hashes)
path=Path(filename)
if action=='before':
    assert not path.exists();path.write_text(json.dumps(result,sort_keys=True))
else:
    old=json.loads(path.read_text())
    for table in result:
        assert set(old[table]).issubset(result[table]),f'Changed old rows in {table}'
        if action=='exact':assert old[table]==result[table],f'Count changed in {table}'
print(json.dumps({'mode':action,'counts':{k:len(v) for k,v in result.items()},'sha256':hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()}))
