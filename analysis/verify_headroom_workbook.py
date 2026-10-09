"""Verify delivered Phase 4 workbook independently from CSV and OOXML."""
import csv
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
import pandas as pd
from zipfile import ZipFile
from pathlib import Path
from append_headroom_sheets import sheet_paths, resolve, MAIN, T

ROOT=Path(__file__).resolve().parents[1]
AN=ROOT/'analysis'
PRE=AN/'.workbook_previews'/'phase4'

def index(address):
    ci=0
    for c in re.match('[A-Z]+',address).group():ci=ci*26+ord(c)-64
    return int(re.search('[0-9]+$',address).group())-1,ci-1

def decode(cell,strings):
    typ=cell.attrib.get('t');v=cell.find(T+'v')
    assert typ!='e','Saved formula error '+cell.attrib['r']
    if typ=='inlineStr':return ''.join(x.text or '' for x in cell.iter(T+'t'))
    if v is None or v.text is None:return None
    if typ=='s':return strings[int(v.text)]
    if typ=='str':return v.text
    if typ=='b':return v.text=='1'
    return float(v.text)

def main():
    info=json.loads((AN/'headroom_workbook_verification.json').read_text())
    result=json.loads((AN/'headroom_results.json').read_text())
    for name,expected in result['input_hashes'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,'Input changed: '+name
    checked=formulas=0
    with ZipFile(ROOT/'excel'/'gym_pricing_model.xlsx') as z, ZipFile(PRE/'input_workbook.xlsx') as old:
        paths=sheet_paths(z);original=sheet_paths(old)
        assert len(original)==16 and len(paths)==18
        assert all(name in paths for name in original)
        allowed={'xl/styles.xml','xl/workbook.xml','xl/_rels/workbook.xml.rels','[Content_Types].xml','docProps/app.xml',original['Dataset Overview'],original['README']}
        for item in old.infolist():
            if item.filename not in allowed:assert old.read(item.filename)==z.read(item.filename),'Unintended original feature change: '+item.filename
        prior_styles=ET.fromstring(old.read('xl/styles.xml'));current_styles=ET.fromstring(z.read('xl/styles.xml'))
        for group in prior_styles:
            newer=current_styles.find(group.tag)
            assert newer is not None
            for i,entry in enumerate(group):assert ET.tostring(entry)==ET.tostring(newer[i]),'Original style changed'
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():strings=[''.join(t.text or '' for t in si.iter(T+'t')) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        values={}
        for name in ['Headroom Score','Headroom Summary']:
            values[name]={}
            for _,cell in ET.iterparse(z.open(paths[name]),events=['end']):
                if cell.tag!=T+'c':continue
                values[name][index(cell.attrib['r'])]=decode(cell,strings)
                formula=cell.find(T+'f')
                if formula is not None:
                    formulas+=1
                    assert cell.find(T+'v') is not None,'Missing formula cache'
                    assert 'Checks!' not in formula.text and "'Checks'!" not in formula.text,'Check drives a score'
                    assert not re.search(r"'Headroom Summary'!\$?B\$?(263|264)\b",formula.text),'Check drives business output'
                cell.clear()
        for table,start in [('gym_headroom',9),('headroom_sensitivity',111)]:
            with (ROOT/'data'/(table+'.csv')).open(encoding='utf-8',newline='') as stream:
                reader=csv.reader(stream);headers=next(reader)
                for ri,row in enumerate(reader,start-1):
                    for ci,raw in enumerate(row):
                        actual=values['Headroom Score'].get((ri,ci))
                        if raw=='':assert actual in [None,'']
                        elif raw in ['True','False']:assert actual==(raw=='True')
                        else:
                            try:expected=float(raw)
                            except ValueError:assert actual==raw,(table,ri,headers[ci],actual,raw)
                            else:assert isinstance(actual,(int,float)) and math.isclose(actual,expected,rel_tol=2e-12,abs_tol=2e-8),(table,ri,headers[ci],actual,expected)
                        checked+=1
        for ri,band in enumerate(['High','Medium','Low'],29):assert values['Headroom Summary'][ri,1]==result['bands'][band]
        segments=['Investigation priority','Stronger headroom indicators','Limited headroom indicators','Mixed indicators']
        for ri,segment in enumerate(segments,35):assert values['Headroom Summary'][ri,1]==result['segments'][segment]
        h=pd.read_csv(ROOT/'data'/'gym_headroom.csv').set_index('gym_id')
        s=pd.read_csv(ROOT/'data'/'headroom_sensitivity.csv').set_index(['gym_id','variant'])
        config=json.loads((AN/'headroom_config.json').read_text())
        leaders=h.sort_values('rank').head(10)
        summary=values['Headroom Summary']
        for i,(gym,row) in enumerate(leaders.iterrows()):
            assert summary[i+59,0]==gym
            assert math.isclose(summary[i+59,2],row.score,abs_tol=2e-8)
            assert summary[i+82,0]==gym
            for j,indicator in enumerate(config['indicators'],1):assert math.isclose(summary[i+82,j],row[indicator+'_contribution'],abs_tol=2e-8)
        for i,(gym,row) in enumerate(h.iterrows()):
            assert summary[i+96,3]==gym
            assert math.isclose(summary[i+96,0],row.competitor_gap_dec2025,abs_tol=2e-8)
            active=2 if row.caution_flag_count>0 else 1
            assert math.isclose(summary[i+96,active],row.churn_rate_2025,abs_tol=2e-8)
            assert summary.get((i+96,3-active)) in [None,''],'Missing scatter observation became zero'
        for i,(gym,row) in enumerate(h.sort_values('rank').iterrows()):
            assert summary[i+180,0]==gym
            for j,variant in enumerate(config['weights'],1):assert summary[i+180,j]==s.loc[(gym,variant),'rank']
        assert abs(summary[262,1])<1e-10 and abs(summary[263,1])<1e-10
        # Every internal relationship resolves, including recursively copied charts/tables.
        for name in z.namelist():
            if not name.endswith('.rels'):continue
            parent=name.replace('/_rels/','/').removesuffix('.rels') if name!='_rels/.rels' else ''
            for relation in ET.fromstring(z.read(name)):
                if relation.attrib.get('TargetMode')=='External':continue
                assert resolve(parent,relation.attrib['Target']) in z.namelist(),(name,relation.attrib['Target'])
        newcharts=[x for x in z.namelist() if x.startswith('xl/drawings/charts/phase4_') and x.endswith('.xml')]
        assert len(newcharts)==3
        ns={'c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
        chart_bindings=[]
        for name in newcharts:
            chart=ET.fromstring(z.read(name));refs=[e.text for e in chart.findall('.//c:f',ns)]
            assert refs and all('Headroom Summary' in ref for ref in refs)
            chart_bindings.append({'part':name,'range_references':refs})
        info.update({'savedCsvCellsCompared':checked,'newFormulaCachesChecked':formulas,'sheetCount':len(paths),'allOriginalAnalysisAndSourcePartsPreserved':True,'originalStylesPreserved':True,'originalSheetCount':len(original),'sourceAndBaselineHashesUnchanged':True,'chartSchedulesMatchPython':True,'filteredScatterObservationsRemainBlank':True,'newNativeCharts':chart_bindings,'phase4_status':'Verified; visual review recorded below'})
    (AN/'headroom_workbook_verification.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    print(json.dumps({k:info[k] for k in ['savedCsvCellsCompared','newFormulaCachesChecked','sheetCount','sourceAndBaselineHashesUnchanged']},indent=2))

if __name__=='__main__':main()
