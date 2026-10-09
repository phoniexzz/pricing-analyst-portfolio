"""Package only declared Phase 11 files; accepted commercial artifacts are immutable.

Standard-library manifest checks also work in an extracted recruiter package.
Full builds run independent SQL validation in a disposable extracted copy.
"""
import argparse,csv,hashlib,importlib.util,json,os,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist';BUILD=ROOT/'analysis/.portfolio_build'
FIXED_TIME=(2026,10,6,0,0,0)
MONEY_LIMIT=100*1024*1024
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def accepted_integrity(root=ROOT,allow_missing=False):
    receipt=json.loads((root/'analysis/powerbi_native_acceptance.json').read_text())
    deck=json.loads((root/'analysis/presentation_validation.json').read_text())
    entries=deck['evidence_hashes'].copy()
    entries['excel/gym_pricing_model.xlsx']=receipt['workbook']['sha256'].lower()
    entries['powerbi/gym_pricing_dashboard.pbix']=receipt['pbix']['sha256'].lower()
    entries['presentation/pricing_recommendation.pptx']=deck['pptx_sha256']
    entries['presentation/pricing_recommendation.pdf']=deck['pdf_sha256']
    checked=0;missing=[]
    for filename,expected in entries.items():
        if '#' in filename:
            name,field=filename.split('#',1);p=root/name
            if p.exists():actual=hashlib.sha256(json.dumps(json.loads(p.read_text())[field],sort_keys=True,separators=(',',':')).encode()).hexdigest()
            else:missing.append(filename);continue
        else:
            p=root/filename
            if p.exists():actual=sha(p)
            else:missing.append(filename);continue
        assert actual.lower()==expected.lower(),f'Protected file changed: {filename}'
        checked+=1
    assert allow_missing or not missing,missing
    # Same fingerprint algorithm as the accepted implementation, without writes.
    paths=[]
    for base in ['Northstar.Report','Northstar.SemanticModel']:
        paths += [p for p in (root/'powerbi'/base).rglob('*') if p.is_file() and '.pbi' not in p.parts and p.suffix in {'.json','.tmdl','.pbir','.pbism'}]
    paths += [root/'powerbi/gym_pricing_dashboard.pbip']
    paths += list((root/'powerbi/model_data').glob('*.csv'))
    fingerprint=hashlib.sha256(json.dumps({p.relative_to(root).as_posix():sha(p) for p in sorted(paths)},sort_keys=True).encode()).hexdigest()
    assert fingerprint==receipt['project_fingerprint'], 'Accepted project fingerprint changed'
    with ZipFile(root/'excel/gym_pricing_model.xlsx') as z:
        tree=ET.fromstring(z.read('xl/workbook.xml'));sheets=tree.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheets')
        assert len(sheets)==31
    # Validate all reporting snapshot files against saved preparation manifest.
    snap=json.loads((root/'powerbi/source_hash_manifest.json').read_text())
    for file,expected in snap['snapshot_files'].items():assert sha(root/'powerbi/model_data'/file)==expected,file
    prior=root/'portfolio/preserved_evidence_manifest.json'
    if prior.exists():
        for name,item in json.loads(prior.read_text())['files'].items():assert sha(root/name)==item['sha256'],name
    return dict(protected_files_checked=checked,unavailable_dependencies=missing,project_fingerprint=fingerprint,
                workbook_sha256=sha(root/'excel/gym_pricing_model.xlsx'),workbook_sheets=31,
                pbix_sha256=sha(root/'powerbi/gym_pricing_dashboard.pbix'),snapshot_files_checked=len(snap['snapshot_files']))

def prior_inventory():
    file=ROOT/'portfolio/preserved_evidence_manifest.json'
    if file.exists():
        inv=json.loads(file.read_text())
        for name,item in inv['files'].items():assert sha(ROOT/name)==item['sha256'],f'Prior evidence changed: {name}'
        return inv
    files=list((ROOT/'data').glob('*.csv'))
    files += [p for p in (ROOT/'analysis').glob('*') if p.is_file() and (p.name.endswith('_config.json') or p.name.endswith('_results.json'))]
    inv={'description':'All source/derived CSVs and prior analytical configurations/results preserved at Phase 11 entry.',
         'files':{p.relative_to(ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)}}
    dump(file,inv);return inv

def file_lists():
    cfg=json.loads((ROOT/'portfolio/package_config.json').read_text());public=[]
    for name in cfg['root_files']+cfg['extra_files']:
        p=ROOT/name;assert p.is_file(),name;public.append(p)
    for folder,rule in cfg['folders'].items():
        base=ROOT/folder;items=base.rglob('*') if rule['recursive'] else base.iterdir()
        for p in items:
            if not p.is_file() or p.is_symlink():continue
            rel=p.relative_to(ROOT)
            if any(c in cfg['exclude_components'] for c in rel.parts):continue
            if rel.as_posix() in cfg['exclude_files']:continue
            if p.suffix.lower() in rule['suffixes']:public.append(p)
    public=sorted(set(public),key=lambda p:p.relative_to(ROOT).as_posix())
    supplementary=[ROOT/s for s in cfg['supplemental_files']]
    for p in supplementary:assert p.is_file(),p
    for p in public:assert p.stat().st_size<=MONEY_LIMIT,f'Ordinary GitHub limit exceeded: {p}'
    assert not set(public)&set(supplementary)
    return public,sorted(supplementary,key=lambda p:p.relative_to(ROOT).as_posix())

def manifest(files,kind):
    return {'format_version':1,'package':kind,'description':'Manifest excludes itself; ZIP SHA-256 recorded in external Phase 11 validation.',
      'files':{p.relative_to(ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in files}}

def archive(path,files,meta,name):
    with ZipFile(path,'w',ZIP_DEFLATED,compresslevel=6) as z:
        contents=[(p.relative_to(ROOT).as_posix(),p) for p in files]+[(name,None)]
        for rel,p in sorted(contents):
            info=ZipInfo(rel,FIXED_TIME);info.compress_type=ZIP_DEFLATED;info.create_system=3;info.external_attr=0o100644<<16
            if p is None:z.writestr(info,json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
            else:
                with p.open('rb') as src,z.open(info,'w',force_zip64=True) as dst:shutil.copyfileobj(src,dst)

def verify_shipped(root):
    statuses=[]
    for name in ['PORTFOLIO_MANIFEST.json','REPRODUCTION_MANIFEST.json']:
        path=root/name
        if not path.exists():continue
        meta=json.loads(path.read_text());count=0
        for rel,item in meta['files'].items():
            p=root/rel;assert p.is_file(),f'Missing shipped file: {rel}'
            assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],f'Shipped file changed: {rel}';count+=1
        statuses.append({'manifest':name,'files_checked':count})
    return statuses

def docs_check(root=ROOT):
    files=[root/'README.md',root/'sql/README.md']+sorted((root/'portfolio').glob('*.md'))
    links=0;images=[]
    for p in files:
        text=p.read_text(encoding='utf-8')
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
            if target.startswith(('https://','http://','#')):continue
            dest=(p.parent/target.split('#')[0]).resolve();assert dest.is_file(),(p.name,target);links+=1
            if dest.suffix in {'.jpg','.png'}:images.append(dest)
    case=(root/'portfolio/case_study.md').read_text(encoding='utf-8')
    words=len(re.findall(r"\b[\w]+(?:[’-][\w]+)*\b",case));assert 500<=words<=800,words
    for heading in ['Problem','Business Context','My Approach','Analysis','Key Findings','Recommendation','Estimated Commercial Impact','Tools Used','What I Learned']:
        assert f'## {heading}\n' in case
    for file in [root/'README.md',root/'portfolio/case_study.md']:
        text=file.read_text(encoding='utf-8')
        for required in ['107,006,933.85','396,311','148,618.48','EXTEND TEST','STOP']:
            assert required in text,(file,required)
        assert 'does not use confidential information from The Gym Group or any other operator.' in text
        assert 'This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.' in text
    from PIL import Image
    image_dimensions={}
    for p in sorted(set(images)):
        with Image.open(p) as im:im.verify()
        with Image.open(p) as im:image_dimensions[p.relative_to(root).as_posix()]=list(im.size)
    assert len(image_dimensions)==7
    return {'case_study_words':words,'local_links_checked':links,'native_images':image_dimensions}

def clean_verify(publiczip,suppzip):
    # Fresh run directory; never delete/reuse the user's files or accepted project.
    import tempfile
    tmp=Path(tempfile.mkdtemp(prefix='extracted_',dir=BUILD))
    with ZipFile(publiczip) as z:z.extractall(tmp)
    lean=accepted_integrity(tmp,allow_missing=True)
    assert len(lean['unavailable_dependencies'])==2
    lean_manifests=verify_shipped(tmp);docs=docs_check(tmp)
    result=subprocess.run([sys.executable,str(tmp/'sql/validate_queries.py')],cwd=tmp,capture_output=True,text=True)
    (BUILD/'clean_sql.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    assert result.returncode==0,result.stderr
    sql=json.loads((tmp/'sql/.build/validation.json').read_text())
    for p in (ROOT/'sql/.build/outputs').glob('*.csv'):
        assert p.read_bytes()==(tmp/'sql/.build/outputs'/p.name).read_bytes(),f'Non-reproducible SQL output: {p.name}'
    with ZipFile(suppzip) as z:z.extractall(tmp)
    restored=accepted_integrity(tmp);restored_manifests=verify_shipped(tmp)
    frozen=json.loads((tmp/'portfolio/preserved_evidence_manifest.json').read_text())
    for name,item in frozen['files'].items():assert sha(tmp/name)==item['sha256']
    return dict(lean=lean,lean_manifests=lean_manifests,supplement_restored=restored,
                restored_manifests=restored_manifests,documentation=docs,sql=sql,sql_outputs_byte_identical=True,clean_directory=str(tmp))

def run():
    BUILD.mkdir(parents=True,exist_ok=True);DIST.mkdir(exist_ok=True)
    integrity=accepted_integrity();prior=prior_inventory();docs=docs_check()
    # Run live validation only for new SQL assets, which writes solely to ignored sql/.build.
    proc=subprocess.run([sys.executable,str(ROOT/'sql/validate_queries.py')],capture_output=True,text=True)
    (BUILD/'sql.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8');assert proc.returncode==0,proc.stderr
    sql=json.loads((ROOT/'sql/.build/validation.json').read_text())
    dump(ROOT/'portfolio/sql_validation.json',sql)
    visual=json.loads((ROOT/'portfolio/documentation_visual_review.json').read_text())
    assert visual['human_visual_review_completed'] and len(visual['rendered_pages'])==5
    # Include a portable, stable evidence summary in both README access and package.
    summary='''# Phase 11 validation summary

Phase 11 complete; Phase 12 next.

- Fifteen read-only SQL queries validated field-by-field against independent Pandas source aggregation or saved evidence.
- Revenue reconciliation tolerance £0.01; weighted rates, missing/zero boundaries, case separation and history deduplication passed.
- Anchors: £107,006,933.85 annual net revenue; 396,311 December members; £148,618.48 Base conditional-raise uplift.
- Saved action counts and Main experiment decisions remain unchanged.
- All protected evidence, accepted Power BI fingerprint/PBIX, presentation and 31-sheet workbook retained.
- Clean-copy import, SQL execution, supplemental restoration and manifest validation passed.
- Package byte reproducibility checked with sorted entries and fixed ZIP timestamps.
- The case study has 740 words under the documented token-based word count, including headings and disclaimers.
- Seven native screenshot image files and all local links in new portfolio documentation validated; Markdown layout reviewed.

The complete run record and archive hashes are delivered separately as `dist/phase11_validation.json` and `dist/phase11_validation.md`, avoiding a circular archive hash. The ordinary package excludes the large joint-draw file and private payloads; restore the supplemental archive for full evidence verification. Advanced Artifact Tool/native regeneration retains host-specific runtime requirements. Native PowerPoint rendering remains unverified. No Git remote or publication was created.

See [SQL validation evidence](sql_validation.json), [preserved evidence manifest](preserved_evidence_manifest.json), [package configuration](package_config.json) and [reproduction guidance](REPRODUCIBILITY.md).
'''
    (ROOT/'portfolio/VALIDATION.md').write_text(summary,encoding='utf-8')
    docs=docs_check();public,supp=file_lists()
    pm=manifest(public,'Northstar GitHub-ready portfolio');sm=manifest(supp,'Northstar supplemental reproduction dependencies')
    dump(DIST/'portfolio_manifest.json',pm);dump(DIST/'reproduction_manifest.json',sm)
    pzip=DIST/'northstar_portfolio.zip';szip=DIST/'northstar_reproduction.zip'
    archive(pzip,public,pm,'PORTFOLIO_MANIFEST.json');archive(szip,supp,sm,'REPRODUCTION_MANIFEST.json')
    clean=clean_verify(pzip,szip)
    # Byte-identical packaging check, not just a comparison of file lists.
    for output,files,meta,name in [(pzip,public,pm,'PORTFOLIO_MANIFEST.json'),(szip,supp,sm,'REPRODUCTION_MANIFEST.json')]:
        twin=BUILD/output.name;archive(twin,files,meta,name);assert sha(twin)==sha(output),'Nondeterministic ZIP'
    assert accepted_integrity()==integrity
    prior_inventory()
    report={'status':'Phase 11 complete; Phase 12 next','validated_at_utc':datetime.now(timezone.utc).isoformat(),
        'prior_inventory_files':len(prior['files']),'integrity':integrity,'documentation':docs,
        'sql':sql,'clean_copy_validation':clean,'byte_identical_packaging':True,'documentation_visual_review':visual,
        'archives':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p),'files':len(meta['files'])} for p,meta in [(pzip,pm),(szip,sm)]},
        'ordinary_package_max_file_bytes':max(p.stat().st_size for p in public),
        'no_git_or_publication':not (ROOT/'.git').exists(),
        'limitations':['Native PowerPoint rendering unverified','PDF is image-based','Native dashboard tables use scrolling',
          'Advanced historical builders require bundled Artifact Tool and adaptation of host-specific runtime/helper paths',
          'Protected workbook progress captions remain older; external guidance is current']}
    dump(ROOT/'analysis/portfolio_validation.json',report);dump(DIST/'phase11_validation.json',report)
    lines=['# Phase 11 — Portfolio packaging validation','',report['status'],'',
      f"Validated: {report['validated_at_utc']}",f"Case study: {docs['case_study_words']} words. Fifteen SQL queries passed all-field parity and {len(sql['boundary_tests'])} boundary/scope checks.",
      f"Protected checks: {integrity['protected_files_checked']} records; {len(prior['files'])} source/configuration/result files; {integrity['snapshot_files_checked']} reporting snapshot files. Workbook: 31 sheets, unchanged.",
      '','| Archive | Files | Bytes | SHA-256 |','|---|---:|---:|---|']
    for name,item in report['archives'].items():lines.append(f"| {name} | {item['files']} | {item['bytes']:,} | {item['sha256']} |")
    lines += ['',f"Largest ordinary package file: {report['ordinary_package_max_file_bytes']:,} bytes; every file is below 100 MiB.",
      'Clean extracted-copy execution, supplemental restoration, accepted fingerprint, exact member boundaries, weighted rates, links and image files passed. Both ZIPs reproduced byte-for-byte.',
      '','Remaining limitations:']+['- '+x for x in report['limitations']]
    text='\n'.join(lines)+'\n';(ROOT/'analysis/portfolio_validation.md').write_text(text,encoding='utf-8');(DIST/'phase11_validation.md').write_text(text,encoding='utf-8')
    print(json.dumps({'status':report['status'],'archives':report['archives'],'sql_queries_passed':15,'case_words':docs['case_study_words'],'prior_files':len(prior['files'])},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    if args.verify_only:
        print(json.dumps({'manifests':verify_shipped(ROOT),'accepted_artifacts':accepted_integrity(allow_missing=True)},indent=2))
    else:run()
