import hashlib,json,re
import httpx
base='https://opora-apk.159-194-249-97.sslip.io'
with httpx.Client(base_url=base,trust_env=False,follow_redirects=False,timeout=25) as c:
    h=c.get('/health');assert h.status_code==200 and h.json()['environment']=='production'
    assert 'max-age=' in h.headers['strict-transport-security']
    cfg=c.get('/api/config');assert cfg.status_code==200 and cfg.json()['demo'] is False
    assert c.get('/api/catalog').json()==[]
    assert c.post('/api/auth/demo',json={'persona':'editor'},headers={'X-App-Request':'1'}).status_code==404
    assert c.get('/api/profile').status_code==401
    assert c.get('/api/admin/versions').status_code==401
    assert c.post('/api/max/webhook',json={}).status_code==403
    notices=c.get('/api/official-announcements');assert notices.status_code==200
    root=c.get('/');assert root.status_code==200
    asset=re.search(r'src="([^"]+\.js)"',root.text).group(1)
    js=c.get(asset);assert js.status_code==200
    assert 'index-YYOZFh4d.js' in asset
    print(json.dumps({'https':'PASS','demo_disabled':True,'anonymous_editor_denied':True,'webhook_secret_required':True,'frontend_asset':asset,'frontend_sha256':hashlib.sha256(js.content).hexdigest()}))
with httpx.Client(trust_env=False,follow_redirects=False,timeout=20) as c:
    redirect=c.get(base.replace('https:','http:')+'/health');assert redirect.status_code==308 and redirect.headers['location']==base+'/health'
print('HTTP to HTTPS redirect PASS; TLS validation enabled')
