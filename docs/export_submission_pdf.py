"""PDF copies of the individually reviewed final PPTX slide renders.

Requires the authoring runtime: reportlab, pypdf, pypdfium2, Pillow.
Application runtime does not depend on these packages. PPTX remains editable.
"""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image, ImageChops, ImageStat

root = Path(__file__).resolve().parents[1]
report = {}
for audience, expected in [('public', 12), ('jury', 13)]:
    slides = sorted((root / 'tmp/presentation' / audience).glob('slide-*.png'))
    assert len(slides) == expected
    output = root / 'output/pdf' / f'opora-apk-{audience}.pdf'
    output.parent.mkdir(exist_ok=True)
    doc = canvas.Canvas(str(output), pagesize=(960, 540), pageCompression=1)
    doc.setTitle('Опора АПК — публичная презентация' if audience == 'public' else 'Опора АПК — комплект для жюри')
    doc.setAuthor('Опора АПК')
    for i, picture in enumerate(slides):
        doc.drawImage(ImageReader(str(picture)), 0, 0, width=960, height=540)
        if i == len(slides)-1:
            for y, link in [(294,'https://minagro.saratov.gov.ru/subsidii/'),
                            (235,'https://dev.max.ru/docs/webapps/validation'),
                            (176,'https://dev.max.ru/docs-api/changelog-api')]:
                doc.linkURL(link,(48,y,912,y+50),relative=0,thickness=0)
        doc.showPage()
    doc.save()
    assert len(PdfReader(output).pages) == expected
    rendered = pdfium.PdfDocument(output)
    differences = []
    for i, original in enumerate(slides):
        actual = rendered[i].render(scale=2).to_pil().convert('RGB')
        expected_image = Image.open(original).convert('RGB')
        assert actual.size == expected_image.size
        difference = sum(ImageStat.Stat(ImageChops.difference(actual, expected_image)).mean)/3
        assert difference < 0.1, (i, difference)
        differences.append(round(difference,6))
        actual.save(root / 'tmp/presentation' / audience / f'pdf-page-{i+1:02d}.png')
    target = root / 'output/submission' / audience / output.name
    target.write_bytes(output.read_bytes())
    report[audience] = {'pages': expected, 'all_pages_rendered': True, 'pixel_mean_errors': differences,
                        'pdf_text':'rasterized verified slides; editable original is PPTX'}
(root / 'tmp/presentation/pdf-validation.json').write_text(json.dumps(report, indent=2),encoding='utf-8')
print('Public and jury PDFs: all 25 pages match reviewed PPTX renders')
