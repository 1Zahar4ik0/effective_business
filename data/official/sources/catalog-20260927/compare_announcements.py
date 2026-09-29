from pathlib import Path
from pypdf import PdfReader
import pypdfium2 as pdf
import re,difflib
r=Path('C:/EffectiveBusiness/data/official/sources/catalog-20260927')
for key,old in [('farm-announcement-current','13'),('students-announcement','09')]:
    pages=[p.extract_text() or '' for p in PdfReader(r/(key+'.pdf')).pages]
    text='\n'.join(f'\n--- PAGE {i+1} ---\n'+p for i,p in enumerate(pages))
    (r/(key+'.txt')).write_text(text,encoding='utf-8')
    before=(r.parent/'text'/(old+'.txt')).read_text(encoding='utf-8')
    a=re.sub(r'\s+',' ',before).split();b=re.sub(r'\s+',' ',text).split()
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    changes=[{'old':' '.join(a[i:j]),'new':' '.join(b[k:l])} for tag,i,j,k,l in sm.get_opcodes() if tag!='equal']
    (r/(key+'-diff.json')).write_text(__import__('json').dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
    print(key,'pages',len(pages),'changes',len(changes));print(__import__('json').dumps(changes,ensure_ascii=False)[:10000])
doc=pdf.PdfDocument(r/'students-result.pdf')
for n in [1,2]:doc[n].render(scale=1.6).to_pil().save(r/f'students-result-p{n+1}.png')
doc=pdf.PdfDocument(r/'farm-announcement-current.pdf')
for n in [5,8,9,21]:doc[n].render(scale=1.6).to_pil().save(r/f'farm-current-p{n+1}.png')
