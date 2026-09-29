from pathlib import Path
import subprocess, json, hashlib, sys
from datetime import datetime, timezone
root=Path('C:/EffectiveBusiness/data/official/sources/catalog-20260927')
root.mkdir(parents=True,exist_ok=True)
name,url=sys.argv[1:3]
assert url.startswith(('https://promote.budget.gov.ru/','https://minagro.saratov.gov.ru/','https://publication.pravo.gov.ru/'))
assert '/' not in name and '\\' not in name
args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','effectivebusiness','curl','--fail','--max-time','35','--silent','--show-error',"'"+url+"'"]
body=None
if len(sys.argv)>3:
    body=Path(sys.argv[3]).read_bytes()
    args+=['-H',"'Content-Type: application/json'",'--data-binary','@-']
proc=subprocess.run(args,input=body,capture_output=True)
row={'url':url,'attempted_at':datetime.now(timezone.utc).isoformat(),'transport':'public GET via existing VPS; no cookies/auth; TLS verification enabled','exit_code':proc.returncode}
if body is not None:row.update(transport='public search POST (read-only), no auth; TLS verified',request=json.loads(body))
if proc.returncode==0:
    (root/name).write_bytes(proc.stdout)
    row.update(file=name,bytes=len(proc.stdout),sha256=hashlib.sha256(proc.stdout).hexdigest())
else: row['error']=proc.stderr.decode(errors='replace')[-1200:]
with (root/'retrieval.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
print(json.dumps(row,ensure_ascii=False))
