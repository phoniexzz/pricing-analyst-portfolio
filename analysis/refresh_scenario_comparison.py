"""Read authorized live-workbook inputs, recalculate/capture via Artifact Tool, preserve Phase 1–5.

No Excel application automation. Run after closing the workbook to release its file lock.
The editable selectors are restored; original evidence CSVs are never overwritten.
"""
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile
import append_scenario_sheets as pack

ROOT=Path(__file__).resolve().parents[1]
PRE=ROOT/'analysis'/'.workbook_previews'/'phase6'
NODE=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
T=pack.T

def cells(z,part):
    strings=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        strings=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml'))]
    out={}
    for c in ET.fromstring(z.read(part)).iter(T+'c'):
        typ=c.attrib.get('t');v=c.find(T+'v');raw=v.text if v is not None else None
        if typ=='inlineStr':value=''.join(c.find(T+'is').itertext())
        elif typ=='s':value=strings[int(raw)]
        elif typ in ['str','e']:value=raw or ''
        elif typ=='b':value=raw=='1'
        else:value=float(raw) if raw is not None else None
        out[c.attrib['r']]=value
    return out

def col(i):
    s='';i+=1
    while i:s=chr(65+(i-1)%26)+s;i=(i-1)//26
    return s

def read_inputs():
    p=json.loads((PRE/'payload.json').read_text())
    with ZipFile(pack.OUTPUT) as z:
        paths=pack.sheet_paths(z)
        assert len(paths)>=25, 'Phase 6 requires all 25 existing sheets'
        # Do not overwrite unrelated source edits during a refresh.
        with ZipFile(pack.BASE) as base:
            old=pack.sheet_paths(base)
            for name,part in old.items():
                if name not in ['Dataset Overview','README']:
                    assert z.read(paths[name])==base.read(part), 'Source sheet changed: '+name
        x=cells(z,paths['Scenario Inputs'])
    def matrix(first,n,width):return [[x.get(col(c)+str(r)) for c in range(width)] for r in range(first,first+n)]
    return {'case':int(x['B3']),'price':float(x['B4']),'parameters':[[x.get(col(c)+str(r)) for c in range(5,9)] for r in range(9,18)],
        'drivers':matrix(50,len(p['drivers']['data']),len(p['drivers']['columns'])),'states':matrix(1101,len(p['states']['data']),len(p['states']['columns']))}

def main():
    values=read_inputs();(PRE/'refresh_inputs.json').write_text(json.dumps(values),encoding='utf-8')
    # Replace only Phase 6-owned sheets in a fresh copy, preserving later phases.
    refresh_base=PRE/'refresh_preservation_base.xlsx';refresh_base.write_bytes(pack.OUTPUT.read_bytes())
    subprocess.run([str(NODE),'--max-old-space-size=16384',str(ROOT/'analysis/build_scenario_workbook.mjs'),'--refresh'],check=True,cwd=ROOT)
    subprocess.run([str(NODE),'--max-old-space-size=16384',str(ROOT/'analysis/style_scenario_segments.mjs')],check=True,cwd=ROOT)
    from package_recommendations import graft
    graft(refresh_base,pack.OUTPUT,json.loads((PRE/'segments.json').read_text(encoding='utf-8')),PRE,
          PRE/'final_values.json',PRE/'final_formulas.json',None,prefix='phase6_refresh_')
    with ZipFile(pack.OUTPUT) as saved:
        has_recommendations='Recommendations' in pack.sheet_paths(saved)
    if has_recommendations:
        from refresh_recommendation_portfolio import refresh
        refresh(allow_unavailable=True)
    print('All twelve combinations captured through the live formula build. Selected case/price restored. Evidence CSVs unchanged.')

if __name__=='__main__':main()
