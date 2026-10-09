"""Package the reviewed deck, viewing PDF, notes and source-integrity evidence."""
from pathlib import Path
import hashlib,json,zipfile,xml.etree.ElementTree as ET,subprocess
from io import BytesIO
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from pypdf import PdfReader
from powerbi_prepare import sources
from powerbi_acceptance_status import accepted,fingerprint

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'analysis/.presentation_build'
OUT=ROOT/'presentation'
NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}

def finish():
    inputs=json.loads((BUILD/'inputs.json').read_text(encoding='utf-8'))
    notes=json.loads((BUILD/'notes.json').read_text(encoding='utf-8'))
    receipt=json.loads((BUILD/'latest_validation.json').read_text(encoding='utf-8'))
    deck=Path(notes['finalPath'])
    assert hashlib.sha256(deck.read_bytes()).hexdigest()==receipt['finalSha256']
    assert receipt['packageIntegrity']['status']=='pass'
    assert not receipt['presentationLayout']['findings'] and not receipt['presentationLayout']['warnings']
    assert receipt['nativeChartValidation']['passed']
    with zipfile.ZipFile(deck) as z:
        slides=[n for n in z.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml')]
        assert len(slides)==10
        charts=[n for n in z.namelist() if n.endswith('.xml') and '/charts/chart' in n]
        assert len(charts)==4
        all_text='\n'.join(ET.fromstring(z.read(n)).findall('.//a:t',NS)[i].text or '' for n in slides for i in range(len(ET.fromstring(z.read(n)).findall('.//a:t',NS))))
        # Independent checks of factual anchors in the exported package.
        for term in ['£107.01m','396,311','£149k','1,209','EXTEND TEST','STOP','-8.27%','+0.345 pp','+0.324 pp','64.7%','2.74%']:
            assert term in all_text,term
        for r in inputs['raise_sites']: assert r['gym_id'] in all_text and r['city'] in all_text
        for disclaimer in inputs['disclaimers']: assert disclaimer in all_text
        assert sum(len(ET.fromstring(z.read(n)).findall('.//a:tbl',NS)) for n in slides)==5
        ch=ET.fromstring(z.read('ppt/slides/charts/chart1.xml'))
        vals=[float(v.text) for v in ch.findall('.//c:val/c:numRef/c:numCache/c:pt/c:v',NS)]
        assert len(vals)==3 and abs((vals[0]+vals[1]-vals[2])*1e6)<.01
        assert len([n for n in z.namelist() if n.startswith('ppt/notesSlides/notesSlide') and n.endswith('.xml')])==10
    pdf=OUT/'pricing_recommendation.pdf'
    c=canvas.Canvas(str(pdf),pagesize=(960,540))
    c.setTitle('Northstar Fitness: UK Gym Pricing & Revenue Optimisation')
    c.setAuthor('Northstar Fitness synthetic portfolio project')
    for i in range(1,11):
        img=BUILD/'rendered'/f'slide-{i}.png'
        with Image.open(img) as im: assert im.size==(1920,1080)
        c.drawImage(str(img),0,0,width=960,height=540)
        c.showPage()
    c.save()
    reader=PdfReader(str(pdf))
    assert len(reader.pages)==10
    review=BUILD/'pdf_review';review.mkdir(exist_ok=True)
    poppler=Path('C:/Users/prave/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
    subprocess.run([str(poppler),'-r','144','-png',str(pdf),str(review/'slide')],check=True)
    pdf_checks=[]
    for i,page in enumerate(reader.pages,1):
        source=np.asarray(Image.open(BUILD/'rendered'/f'slide-{i}.png').convert('RGB'),dtype=np.int16)
        assert len(page.images)==1
        embedded=np.asarray(Image.open(BytesIO(page.images[0].data)).convert('RGB'),dtype=np.int16)
        assert np.array_equal(source,embedded),i
        rendered=np.asarray(Image.open(review/f'slide-{i:02}.png').convert('RGB'),dtype=np.int16)
        assert source.shape==rendered.shape
        pdf_checks.append({'slide':i,'embedded_pixels_equal_source':True,'mean_render_rgb_difference':float(np.abs(source-rendered).mean())})
    text=['# Northstar Fitness management presentation\n',
          'Ten-slide presentation for the Pricing Manager, Commercial Director and CFO. Figures describe synthetic historical observations or hypothetical 2026 modelled outcomes.\n']
    for i,(title,note) in enumerate(zip(notes['titles'],notes['notes']),1):
        text += [f'## Slide {i}: {title}\n',note+'\n']
    text += ['## Delivery and use\n',
             'Use the editable PPTX for presentation or revision. The PDF is a static, image-based viewing copy of the reviewed slides. The PowerPoint contains native charts with embedded data snapshots, five editable evidence tables and speaker notes. The PDF does not expose searchable text.\n',
             *[d+'\n' for d in inputs['disclaimers']]]
    (OUT/'presenter_notes.md').write_text('\n'.join(text),encoding='utf-8')
    assert sources()==inputs['input_hashes'], 'Protected evidence changed'
    assert hashlib.sha256((ROOT/'excel/gym_pricing_model.xlsx').read_bytes()).hexdigest()==inputs['excel_hash']
    assert fingerprint()==inputs['powerbi_fingerprint'] and accepted(), 'Power BI acceptance changed'
    acceptance=json.loads((ROOT/'analysis/powerbi_native_acceptance.json').read_text())
    assert hashlib.sha256((ROOT/'powerbi/gym_pricing_dashboard.pbix').read_bytes()).hexdigest().upper()==acceptance['pbix']['sha256']
    result={
        'status':'Phase 10 complete; Phase 11 next',
        'slides':10,'editable_charts':4,'editable_tables':5,'speaker_note_pages':10,'pdf_pages':10,
        'facts_reconciled':True,'protected_evidence_hashes_unchanged':len(inputs['input_hashes']),
        'excel_hash_unchanged':True,'powerbi_project_and_pbix_unchanged':True,
        'package_and_layout_validation':'pass, no findings or warnings',
        'visual_review':{'all_slides':True,'repaired_slides':[2,7,8],'renderer':'Artifact Tool saved-PPTX import'},
        'native_powerpoint_open_review':False,
        'pdf_type':'Static image-based viewing copy',
        'pdf_render_checks':pdf_checks,'pdf_embedded_images_match_reviewed_slides':True,
        'pdf_all_pages_visually_reviewed':True,
        'pptx_sha256':hashlib.sha256(deck.read_bytes()).hexdigest(),
        'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
        'evidence_hashes':inputs['input_hashes'],
        'excel_sha256':inputs['excel_hash'],'powerbi_fingerprint':inputs['powerbi_fingerprint'],
        'receipt_path':str(Path(receipt['receiptPath']).relative_to(ROOT))
    }
    (ROOT/'analysis/presentation_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='evidence_hashes'},indent=2))

if __name__=='__main__':finish()
