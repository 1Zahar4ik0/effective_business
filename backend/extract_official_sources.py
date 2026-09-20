"""Read-only extraction of downloaded official documents; never executes attachments."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import json
import hashlib
from pypdf import PdfReader
from xml.etree import ElementTree

root = Path(__file__).resolve().parents[1] / "data/official/sources"
out = root / "text"
out.mkdir(exist_ok=True)
manifest = []

def extract(name, content, origin):
    suffix = Path(name).suffix.lower()
    text = ""
    if suffix == ".pdf":
        reader = PdfReader(BytesIO(content))
        text = "\n".join(f"\n--- PAGE {i+1} ---\n" + (p.extract_text() or "") for i, p in enumerate(reader.pages))
    elif suffix == ".docx":
        with ZipFile(BytesIO(content)) as doc:
            tree = ElementTree.fromstring(doc.read("word/document.xml"))
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            text = "\n".join("".join(p.itertext()) for p in tree.findall(".//w:p", ns))
    output = f"{len(manifest)+1:02d}.txt"
    if text:
        (out / output).write_text(text, encoding="utf-8")
    manifest.append({"archive": origin, "document": name, "sha256": hashlib.sha256(content).hexdigest(),
                     "text": output if text else None, "characters": len(text)})

for path in sorted(root.glob("source-*")):
    if path.suffix == ".zip":
        with ZipFile(path) as archive:
            for member in archive.infolist():
                if not member.is_dir():
                    extract(member.filename, archive.read(member), path.name)
    else:
        extract(path.name, path.read_bytes(), path.name)
(out / "index.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
