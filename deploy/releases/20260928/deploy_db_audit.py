import hashlib
import json
import subprocess
import sys
from pathlib import Path

database, action, filename = sys.argv[1:]
assert database == 'navigator' or database.startswith('navigator_deploy_')
dc = ['/usr/local/sbin/opora-compose', 'exec', '-T', 'db', 'psql', '-X', '-q', '-A', '-t', '-v', 'ON_ERROR_STOP=1', '-U', 'navigator', '-d', database]
tables = ['users', 'profiles', 'preparation_plans', 'measures', 'measure_versions', 'selection_rounds', 'evaluations', 'audit_events']
result = {}
for table in tables:
    raw = subprocess.check_output(dc + ['-c', f"SELECT COALESCE(jsonb_agg(to_jsonb(t)), '[]'::jsonb) FROM {table} t"], text=True)
    rows = json.loads(raw)
    hashes = []
    for row in rows:
        if table == 'preparation_plans':
            row.setdefault('assessment', None)
        if table == 'selection_rounds':
            row.setdefault('acceptance_status', 'unconfirmed')
            row.setdefault('acceptance_checked_at', None)
        hashes.append(hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest())
    result[table] = sorted(hashes)
path = Path(filename)
if action == 'before':
    assert not path.exists()
    path.write_text(json.dumps(result, sort_keys=True))
else:
    old = json.loads(path.read_text())
    for table in tables:
        assert set(old[table]).issubset(result[table]), f'Old rows changed in {table}; stop and investigate'
        if action == 'exact':
            assert old[table] == result[table], f'Row count changed in {table}'
print(json.dumps({'mode': action, 'counts': {k: len(v) for k,v in result.items()}, 'sha256': hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()}))
