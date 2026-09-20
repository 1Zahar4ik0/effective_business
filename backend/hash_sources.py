"""Manifest only for navigator project files; never includes .env or lab work."""
from pathlib import Path
import hashlib

root=Path(__file__).resolve().parents[1]
files=[]
for folder in ('backend','frontend','data','docs','deploy'):
    for path in (root/folder).rglob('*'):
        # Skip caches before stat: Linux-created npm links may be unreadable on Windows.
        if any(p in ('node_modules','dist','__pycache__','.pytest_cache') for p in path.parts):continue
        if not path.is_file():continue
        if path.suffix in ('.pyc','.tsbuildinfo') or path.name=='SOURCE-SHA256.txt':continue
        files.append(path)
for name in ('README.md','AGENTS.md','ARCHITECTURE.md','Dockerfile','compose.yaml','compose.max.yaml','compose.max-ca.yaml','compose.local-max-ca.yaml','compose.test.yaml','compose.production.yaml','compose.release-check.yaml','.env.example','.dockerignore','.gitignore','DATA-API.yaml'):
    files.append(root/name)
lines=[hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(root).as_posix() for p in sorted(files)]
(root/'docs/SOURCE-SHA256.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f'{len(lines)} project files hashed')
