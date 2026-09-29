from pathlib import Path
import hashlib
import json
import shutil
import tarfile
import os

root=Path('/opt/opora-apk')
stage=Path('/opt/opora-apk-release-20260928')
ops=Path('/etc/opora-apk/deploy-20260928')
def manifest(path):
    return dict((name, sha) for sha,name in (l.split('  ',1) for l in path.read_text(encoding='utf-8-sig').splitlines()))
old=manifest(Path('/tmp/r3-SHA256.txt'))
new=manifest(Path('/tmp/SOURCE-SHA256.txt'))
for name,sha in old.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha, f'Existing server change: {name}'
for name,sha in new.items():
    assert '..' not in Path(name).parts and not Path(name).is_absolute()
    assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==sha
    if (root/name).exists() and name not in old:
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha, f'Unmanifested server file: {name}'
with tarfile.open(ops/'r3-source.tar.gz','w:gz') as arc:
    for name in old:
        assert Path(name).name not in ['.env','production.env']
        arc.add(root/name,arcname=name,recursive=False)
for name in new:
    dest=root/name
    dest.parent.mkdir(parents=True,exist_ok=True)
    temporary=dest.with_name(dest.name+'.deploy-new')
    shutil.copy2(stage/name,temporary)
    os.replace(temporary,dest)
shutil.copy2('/tmp/SOURCE-SHA256.txt',ops/'SOURCE-SHA256.txt')
print(json.dumps({'old_manifest_verified':len(old),'new_source_files':len(new),'foreign_changes':0}))
