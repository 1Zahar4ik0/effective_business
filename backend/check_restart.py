"""Before/after check for the isolated release Compose only, never production."""
import argparse
import hashlib
import json
from pathlib import Path
import httpx

parser = argparse.ArgumentParser()
parser.add_argument('stage', choices=['before', 'after'])
args = parser.parse_args()
path = Path(__file__).resolve().parents[1] / 'tmp/release-persistence.json'
with httpx.Client(base_url='http://localhost:8001', trust_env=False, timeout=20,
                  headers={'X-App-Request': '1'}) as client:
    config = client.get('/api/config').json()
    assert config['demo'] is True
    response = client.post('/api/auth/demo', json={'persona': 'farmer'})
    response.raise_for_status()
    client.headers['X-CSRF-Token'] = response.json()['csrf']
    if args.stage == 'before':
        client.put('/api/profile', json={'registration_region': '64', 'is_kfh': True,
                                         'goal': 'equipment', 'own_funds': '450000.01'}).raise_for_status()
        measure = client.get('/api/measures/farm-growth').json()
        plan = client.post('/api/preparation-plans', json={'round_id': measure['rounds'][0]['id']}).json()
        client.patch(f"/api/preparation-plans/{plan['id']}/items/{plan['items'][0]['id']}",
                     json={'revision': plan['revision'], 'done': True}).raise_for_status()
    profile = client.get('/api/profile').json()
    plans = client.get('/api/preparation-plans').json()
    assert plans[0]['items'][0]['done'] is True
    snapshot = {'profile': profile, 'plans': plans}
    checksum = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
    if args.stage == 'before':
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps({'sha256': checksum}), encoding='utf-8')
    else:
        assert json.loads(path.read_text())['sha256'] == checksum, 'Profile / plan / version changed after restart'
    print(f'{args.stage}: profile, plan, document mark, version and IDs verified')
