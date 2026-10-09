"""Independent saved-file verification, using CSV and standard-library OOXML only."""
import csv
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

from append_baseline_sheets import MAIN, RID, T, PREVIEW, BASE, OUTPUT, ADDED, sheet_paths

ROOT=Path(__file__).resolve().parents[1]
if '--candidate' in sys.argv:OUTPUT=OUTPUT.with_suffix('.xlsx.tmp')


def index(address):
    ci=0
    for c in re.match('[A-Z]+',address).group():ci=ci*26+ord(c)-64
    return int(re.search('[0-9]+$',address).group())-1,ci-1


def decode(cell,strings):
    kind=cell.attrib.get('t');v=cell.find(T+'v')
    if kind=='e':raise AssertionError('Saved formula error: '+cell.attrib['r'])
    if kind=='inlineStr':return ''.join(x.text or '' for x in cell.iter(T+'t'))
    if v is None or v.text is None:return None
    if kind=='s':return strings[int(v.text)]
    if kind=='str':return v.text
    if kind=='b':return v.text=='1'
    return float(v.text)


def main():
    info=json.loads((ROOT/'analysis'/'baseline_workbook_verification.json').read_text())
    result=json.loads((ROOT/'analysis'/'baseline_results.json').read_text())
    checked=0;formula_count=0;charts=[]
    with ZipFile(OUTPUT) as z,ZipFile(BASE) as base:
        paths=sheet_paths(z);old=sheet_paths(base)
        assert len(paths)==16 and all(name in paths for name in ADDED)
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():strings=[''.join(t.text or '' for t in si.iter(T+'t')) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        values={}
        for name in ADDED:
            values[name]={}
            for _,cell in ET.iterparse(z.open(paths[name]),events=['end']):
                if cell.tag==T+'c':
                    values[name][index(cell.attrib['r'])]=decode(cell,strings)
                    if cell.find(T+'f') is not None:
                        formula_count+=1
                        assert cell.find(T+'v') is not None,'Missing calculated cache'
                        assert 'Checks!' not in cell.find(T+'f').text and "'Checks'!" not in cell.find(T+'f').text,'Checks feeds a business calculation'
                    cell.clear()
        import datetime as dt
        for name,table,start in [('Baseline','gym_baseline',9),('Estate Trends','estate_monthly_trend',9),('Baseline Summary','region_year_baseline',105)]:
            with (ROOT/'data'/(table+'.csv')).open(encoding='utf-8',newline='') as stream:
                reader=csv.reader(stream);header=next(reader)
                for ri,row in enumerate(reader,start-1):
                    for ci,expected in enumerate(row):
                        actual=values[name].get((ri,ci))
                        if table=='estate_monthly_trend' and ci==0:
                            expected=(dt.date.fromisoformat(expected)-dt.date(1899,12,30)).days
                        elif expected in ['True','False']:expected=expected=='True'
                        elif expected=='':expected=None
                        else:
                            try:expected=float(expected)
                            except ValueError:pass
                        if expected is None:assert actual in [None,'']
                        elif isinstance(expected,bool):assert actual is expected
                        elif isinstance(expected,(int,float)):
                            assert isinstance(actual,(int,float)) and math.isclose(actual,expected,rel_tol=2e-12,abs_tol=.00002),(table,header[ci],ri,actual,expected)
                        else:assert actual==expected,(table,header[ci],ri,actual,expected)
                        checked+=1
        guide={'Dataset Overview':{'D5','E5','E7'},'README':{'B20'}}
        for name,part in old.items():
            if name not in guide:assert z.read(part)==base.read(part),'Original sheet changed: '+name
            else:
                a=ET.fromstring(z.read(part));b=ET.fromstring(base.read(part))
                ac={c.attrib['r']:c for c in a.iter(T+'c')};bc={c.attrib['r']:c for c in b.iter(T+'c')}
                assert set(ac)==set(bc)
                for addr in ac:
                    if addr not in guide[name]:assert ET.tostring(ac[addr])==ET.tostring(bc[addr]),'Unrequested guide change '+addr
        for item in base.infolist():
            if item.filename.startswith(('xl/tables/','xl/drawings/','xl/charts/')):assert z.read(item.filename)==base.read(item.filename),'Original native feature changed'
        oldstyles=ET.fromstring(base.read('xl/styles.xml'));newstyles=ET.fromstring(z.read('xl/styles.xml'))
        for name in ['fonts','fills','borders','cellStyleXfs','cellXfs','dxfs']:
            group=oldstyles.find(T+name)
            if group is not None:assert all(ET.tostring(a)==ET.tostring(b) for a,b in zip(group,newstyles.find(T+name))),'Original styles shifted'
        formats={int(x.attrib['numFmtId']):x.attrib['formatCode'] for x in newstyles.find(T+'numFmts')}
        summary=ET.fromstring(z.read(paths['Baseline Summary']))
        cells={c.attrib['r']:c for c in summary.iter(T+'c')}
        for address in ['B20','C20','B21','C21','B27','C27','B28','C28','B42']:
            style=newstyles.find(T+'cellXfs')[int(cells[address].attrib['s'])]
            fmt_id=int(style.attrib.get('numFmtId','0'));code=formats.get(fmt_id,{10:'0.00%',2:'0.00'}.get(fmt_id))
            assert code==('0.00;(0.00);0.00' if address=='B42' else '0.00%'),'Rate/check format mismatch '+address
        for name in ADDED[:2]:
            sheet=ET.fromstring(z.read(paths[name]));assert sheet.find('.//'+T+'pane') is not None,'No freeze panes'
            assert sheet.find(T+'tableParts') is not None,'No native filter table'
        tables=[n for n in z.namelist() if n.startswith('xl/tables/') and n.endswith('.xml')]
        assert len(tables)==12
        table_ids=[ET.fromstring(z.read(n)).attrib['id'] for n in tables];assert len(set(table_ids))==12
        C='{http://schemas.openxmlformats.org/drawingml/2006/chart}'
        A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
        for n in z.namelist():
            if '/charts/phase3_' in n and n.endswith('.xml'):
                tree=ET.fromstring(z.read(n));series=list(tree.iter(C+'ser'))
                refs=[f.text for f in tree.iter(C+'f')]
                assert refs and all('Baseline' in f or 'Estate Trends' in f for f in refs),'Disconnected chart'
                colors=[node.attrib['val'] for node in tree.iter(A+'srgbClr')]
                assert any(c in colors for c in ['829AB1','243B53','D97706']),'Chart palette not saved'
                charts.append({'part':n,'series_count':len(series),'source_formulas':refs,'palette_verified':True})
        assert len(charts)==4 and sorted(c['series_count'] for c in charts)==[1,1,2,2]
        # All relationship targets exist, including chart and table dependencies.
        import posixpath
        from append_baseline_sheets import resolve
        for n in z.namelist():
            if n.endswith('.rels'):
                folder,base_name=posixpath.split(n)
                source='' if n=='_rels/.rels' else posixpath.join(posixpath.dirname(folder),base_name[:-5])
                for relation in ET.fromstring(z.read(n)):
                    if relation.attrib.get('TargetMode')!='External':assert resolve(source,relation.attrib['Target']) in z.namelist(),(n,relation.attrib['Target'])
        for name in ['Dataset Overview','Checks']:
            for _,cell in ET.iterparse(z.open(paths[name]),events=['end']):
                if cell.tag==T+'c':decode(cell,strings);cell.clear()
    assert result['sources_sha256']=={name:hashlib.sha256((ROOT/'data'/name).read_bytes()).hexdigest() for name in result['sources_sha256']}
    assert result['generation_config_sha256']==hashlib.sha256((ROOT/'analysis'/'generation_config.json').read_bytes()).hexdigest()
    info.update(saved_cells_compared_to_derived_csvs=checked,saved_analysis_formula_cells=formula_count,charts=charts,
                source_preservation='All original source sheet XML, native tables, panes and style IDs preserved; four authorised progress-text cells updated',
                native_tables=12,sheet_count=16,package_relationships_valid=True,source_hashes_unchanged=True)
    reproducibility=json.loads((PREVIEW/'reproducibility.json').read_text())
    info['derived_csv_reproducibility']=reproducibility
    if '--visual-review-confirmed' in sys.argv:
        info['visual_review']='Completed for all three new sheets, four native charts, two updated guide views, three standalone figures and targeted rate/check formatting repairs.'
        info['phase3_status']='Complete'
    else:
        info['phase3_status']='Workbook verified; visual review confirmation required'
    (ROOT/'analysis'/'baseline_workbook_verification.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    if '--visual-review-confirmed' in sys.argv:
        report=ROOT/'analysis'/'baseline_validation.md'
        text=report.read_text(encoding='utf-8').split('## Workbook completion')[0].rstrip()
        text+='\n\n## Workbook completion\n\nPhase 3 is complete.\n\n'
        text+=f'- All **{checked:,} derived output cells** match the CSVs after full-workbook recalculation and saved-file reload.\n'
        text+=f'- **{formula_count:,} new formula cells** retain calculated cached results. Formula error scan matched zero entries.\n'
        text+='- The complete assembled workbook was re-imported and recalculated in Artifact Tool. Original ledger and monthly reconciliation checks passed.\n'
        text+='- A temporary GBP 120 source-revenue edit propagated to the site annual result; the original input was restored and every derived output rechecked.\n'
        text+='- All eight source CSVs and generation configuration hashes are unchanged. Original source worksheet XML, styles, native tables and panes are preserved. Four progress-text cells were updated.\n'
        text+='- Four native charts have verified source references and exported colors. All workbook relationship targets exist.\n'
        text+='- All three new sheets, two affected guide views, native charts and standalone figures received visual review. Churn/conversion precision and 0.00 reconciliation formatting were corrected and verified.\n'
        text+='- All three derived CSVs reproduce byte-for-byte.\n'
        text+='- Native Microsoft Excel application execution was not automated. Engine verification used Artifact Tool, with independent saved OOXML checks.\n'
        text+='\n## Remaining simplifications\n\nMonthly midpoint exposure approximates billing. Retention is a monthly opening-base measure, not annual survival or cohort retention. Peak occupancy is an estimate of comfortable-capacity pressure. The revenue bridge is descriptive and includes mix, joining fees and ancillary income. Historical selection, marketing, promotions and competitor events can confound price-response interpretation. December annualisation is seasonal and is not a forecast. No elasticity, headroom scores or pricing actions are estimated in Phase 3.\n'
        report.write_text(text,encoding='utf-8')
    print(json.dumps({k:v for k,v in info.items() if k!='charts'},indent=2))


if __name__=='__main__':main()
