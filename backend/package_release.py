"""Freeze the navigator manifest into a source archive; no environment/database export."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'output/submission'
VERSION = 'opora-apk-20260918-local-r1'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    subprocess.run([sys.executable, str(ROOT/'backend/hash_sources.py')], cwd=ROOT, check=True)
    manifest = ROOT/'docs/SOURCE-SHA256.txt'
    entries = [line.split('  ',1) for line in manifest.read_text(encoding='utf-8').splitlines()]
    files = [ROOT/name for _,name in entries] + [manifest]
    patterns = [re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
                re.compile(r'\bAKIA[A-Z0-9]{16}\b'),
                re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b'),
                re.compile(r'\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{20,}\b')]
    known_secrets = []
    env = ROOT/'.env'
    if env.exists():
        for line in env.read_text(encoding='utf-8-sig').splitlines():
            key, sep, value = line.partition('=')
            if sep and key.strip() in ('MAX_BOT_TOKEN','MAX_WEBHOOK_SECRET'):
                value = value.strip().strip('\"\'')
                if len(value) >= 8:
                    known_secrets.append(value)
    findings = []
    text_count = 0
    for file in files:
        rel = file.relative_to(ROOT)
        assert '..' not in rel.parts and not file.is_symlink()
        assert file.name != '.env' and file.suffix.lower() not in ('.pem','.key','.sqlite','.db')
        assert not any(part in ('tmp','node_modules','.venv','backups') or part.startswith('_qa_') for part in rel.parts)
        if file.stat().st_size > 5_000_000 or file.suffix.lower() in ('.zip','.pdf','.png','.jpg','.webp'):
            continue
        content = file.read_text(encoding='utf-8', errors='replace')
        text_count += 1
        if any(p.search(content) for p in patterns) or any(secret in content for secret in known_secrets):
            findings.append(rel.as_posix())
    if findings:
        # Only names, never the matched sensitive strings.
        raise RuntimeError('Inspect potentially sensitive files: '+', '.join(findings))
    DEST.mkdir(parents=True, exist_ok=True)
    archive = DEST/'source.zip'
    if archive.exists():
        raise RuntimeError('Source archive already frozen; choose a new release directory')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for file in sorted(files):
            info = zipfile.ZipInfo(file.relative_to(ROOT).as_posix(), date_time=(2026,9,18,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info,file.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(files)
        for checksum,name in entries:
            assert sha(z.read(name)) == checksum
    info = {'version': VERSION, 'source_archive': 'source.zip', 'source_sha256':sha(archive.read_bytes()),
            'source_manifest_sha256':sha(manifest.read_bytes()), 'source_files':len(files),
            'secret_scan':{'text_files_checked':text_count,'findings':0,'scope':'Known local MAX secrets and selected private-key/token patterns; not a full security audit'},
            'status':'local-demo; MAX and public HTTPS acceptance blocked'}
    (DEST/'VERSION.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'version': VERSION, 'source_files':len(files), 'secret_findings':0,'source_sha256':info['source_sha256']}))

if __name__=='__main__':main()
