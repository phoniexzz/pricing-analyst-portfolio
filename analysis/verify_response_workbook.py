"""Independent saved-OOXML comparison; never authors formulas or styles."""
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
from append_response_sheets import sheet_paths, resolve, T
from verify_headroom_workbook import index, decode

ROOT=Path(__file__).resolve().parents[1]
AN=ROOT/'analysis'; PRE=AN/'.workbook_previews'/'phase5'
TABLES={'historical_response_panel':('Response Data',9),'historical_event_response':('Historical Response',9),'pilot_pair_response':('Historical Response',47),'price_response_estimates':('Elasticity Summary',201)}
DATES={'month','effective_date','notification_date','existing_member_effective_date','intervention_date','existing_member_billing_date','pre_start','pre_end','post_start','post_end'}

def main():
    result=json.loads((AN/'response_results.json').read_text())
    info=json.loads((AN/'response_workbook_verification.json').read_text())
    for name,expected in result['input_hashes'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,'Input changed '+name
    for prior_result in ['headroom_results.json']:
        for name,expected in json.loads((AN/prior_result).read_text())['input_hashes'].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,'Earlier-phase input changed '+name
    assert 'matched 0 entries' in info['formulaErrorScan'],'Formula error scan did not pass'
    cells=formulas=0
    with ZipFile(ROOT/'excel'/'gym_pricing_model.xlsx') as z,ZipFile(PRE/'input_workbook.xlsx') as old:
        paths,prior=sheet_paths(z),sheet_paths(old)
        assert len(prior)==18 and len(paths)==21
        allowed={'xl/styles.xml','xl/workbook.xml','xl/_rels/workbook.xml.rels','[Content_Types].xml','docProps/app.xml',prior['Dataset Overview'],prior['README'],prior['Headroom Summary']}
        preserved=0
        for item in old.infolist():
            if item.filename not in allowed:
                assert old.read(item.filename)==z.read(item.filename),'Original feature changed '+item.filename
                preserved+=1
        for name,addresses in {'Dataset Overview':['D5','E5','E7'],'README':['B20'],'Headroom Summary':['A4']}.items():
            trees=[ET.fromstring(book.read(sheet_paths(book)[name])) for book in [old,z]]
            for tree in trees:
                for cell in tree.iter(T+'c'):
                    if cell.attrib.get('r') in addresses:
                        for child in list(cell):cell.remove(child)
                        cell.attrib.pop('t',None)
            assert ET.tostring(trees[0])==ET.tostring(trees[1]),'Additional unintended guidance-sheet change '+name
        previous=ET.fromstring(old.read('xl/styles.xml')); current=ET.fromstring(z.read('xl/styles.xml'))
        for group in previous:
            newer=current.find(group.tag)
            assert newer is not None
            for i,entry in enumerate(group):assert ET.tostring(entry)==ET.tostring(newer[i]),'Original style changed'
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():strings=[''.join(t.text or '' for t in si.iter(T+'t')) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        values={}
        for name in set(x[0] for x in TABLES.values()):
            values[name]={}
            for _,cell in ET.iterparse(z.open(paths[name]),events=['end']):
                if cell.tag!=T+'c':continue
                values[name][index(cell.attrib['r'])]=decode(cell,strings)
                f=cell.find(T+'f')
                if f is not None:
                    formulas+=1
                    assert cell.find(T+'v') is not None,'Missing cached formula '+name+' '+cell.attrib['r']
                    assert '#REF!' not in (f.text or ''),'Broken formula reference'
                    # Checks compare independently; no summary calculation references them.
                    if name=='Elasticity Summary':assert not re.search(r"(?:Checks|Response Data'!.*577[2-9])",f.text or ''),'Summary depends on checks'
                cell.clear()
        maxdiff=0.
        for key,(name,start) in TABLES.items():
            frame=pd.read_csv(ROOT/'data'/(key+'.csv'))
            assert len(frame)==result['rows'][key]
            for r,row in enumerate(frame.itertuples(index=False,name=None)):
                for c,expected in enumerate(row):
                    actual=values[name].get((r+start-1,c))
                    if pd.isna(expected):assert actual is None or actual=='',f'{key} missing {r} {c}: {actual}'
                    elif frame.columns[c] in DATES:
                        serial=(pd.Timestamp(expected)-pd.Timestamp('1899-12-30')).days
                        assert actual==serial,f'{key} date {r} {c}: {actual}'
                    elif isinstance(expected,(int,float)) and not isinstance(expected,bool):
                        assert isinstance(actual,(int,float)),f'{key} numeric {r} {c}: {actual}'
                        delta=abs(actual-expected);maxdiff=max(maxdiff,delta)
                        assert delta<=max(3e-8,abs(expected)*4e-11),f'{key} {r} {frame.columns[c]}: {actual} vs {expected}'
                    else:assert actual==expected,f'{key} text {r} {c}: {actual} vs {expected}'
                    cells+=1
        for r in range(5773,5797):
            for c in [3,6,7]:assert abs(values['Response Data'][(r-1,c)])<.011,'Independent source check'
        # Native chart schedules agree with monthly arm source aggregates.
        for i,month in enumerate(sorted(set(x['month'] for x in result['monthly_profiles']))):
            for c,arm,metric in [(1,'Treatment','standard_joins'),(2,'Control','standard_joins'),(3,'Treatment','incumbent_churn'),(4,'Control','incumbent_churn'),(5,'Treatment','incumbent_downgrade'),(6,'Control','incumbent_downgrade')]:
                e=next(x[metric] for x in result['monthly_profiles'] if x['month']==month and x['arm']==arm)
                assert math.isclose(values['Elasticity Summary'][(80+i,c)],e,rel_tol=1e-11,abs_tol=1e-10),'Monthly chart helper mismatch'
        pair_frame=pd.read_csv(ROOT/'data'/'pilot_pair_response.csv').query('window == "primary_6m"').reset_index(drop=True)
        for i,row in pair_frame.iterrows():
            for c,f in [(0,'pair_id'),(1,'controlled_acquisition_response'),(2,'incumbent_churn_response_pp')]:
                actual=values['Elasticity Summary'][(102+i,c)];expected=row[f]
                assert actual==expected if c==0 else math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-10),'Pair chart helper mismatch'
        estimate_frame=pd.read_csv(ROOT/'data'/'price_response_estimates.csv')
        subgroup=estimate_frame[(estimate_frame.estimator=='paired_equal')&(estimate_frame.window=='primary_6m')&estimate_frame.group_type.isin(['Overall','Pre-event relative value','Pre-event competitor intensity'])&(estimate_frame.metric=='controlled_acquisition_response')].reset_index(drop=True)
        for i,row in subgroup.iterrows():
            for c,f in [(1,'estimate'),(2,'ci_lower'),(3,'ci_upper')]:
                actual=values['Elasticity Summary'][(120+i,c)];expected=row[f]
                if pd.isna(expected):assert actual in [None,''],'Missing subgroup interval became zero'
                else:assert math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-10),'Subgroup chart helper mismatch'
        # Every internal relationship resolves to a packaged resource.
        for file in z.namelist():
            if not file.endswith('.rels'):continue
            owner=file.replace('/_rels/','/').removesuffix('.rels') if file!='_rels/.rels' else ''
            for relation in ET.fromstring(z.read(file)):
                if relation.attrib.get('TargetMode')!='External':assert resolve(owner,relation.attrib['Target']) in z.namelist(),'Broken relationship '+file
        charts=[n for n in z.namelist() if '/phase5_' in n and '/charts/' in n and n.endswith('.xml')]
        assert len(charts)==5,'Native chart count'
        for chart in charts:
            tree=ET.fromstring(z.read(chart))
            for node in tree.iter():
                if node.tag.endswith('}f') and node.text:assert 'Elasticity Summary' in node.text,'Wrong new-chart source'
            ns={'c':'http://schemas.openxmlformats.org/drawingml/2006/chart','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
            for i,series in enumerate(tree.findall('.//c:ser',ns)):
                color=series.find('c:spPr/a:solidFill/a:srgbClr',ns)
                assert color is not None and color.attrib['val'].upper()==['243B53','2F855A','D69E2E','9F7AEA'][i%4],'Saved chart palette mismatch'
        table_names=[]
        for file in z.namelist():
            if file.startswith('xl/tables/') and file.endswith('.xml'):table_names.append(ET.fromstring(z.read(file)).attrib['name'])
        assert len(table_names)==len(set(table_names)),'Duplicate native table names'
    repro=json.loads((PRE/'reproducibility.json').read_text());assert repro['all_four_csvs_byte_identical']
    visual=json.loads((PRE/'visual_review.json').read_text());assert visual['reviewed']
    info.update(status='Complete',csvCellsComparedIndependently=cells,maxSavedCsvDifference=maxdiff,newFormulaCaches=formulas,originalPackagePartsPreserved=preserved,originalSheetCount=18,finalSheetCount=21,nativeCharts=5,chartSchedulesChecked=True,internalRelationshipsChecked=True,sourceHashesUnchanged=True,allFourCsvsReproduce=True,visualReview=visual,phase6Ready=True)
    (AN/'response_workbook_verification.json').write_text(json.dumps(info,indent=2))
    print(json.dumps(info,indent=2))

if __name__=='__main__':main()
