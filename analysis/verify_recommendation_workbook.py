"""Independent saved-package parity, preservation and actual-formula graph extraction."""
import hashlib
import json
import math
import re
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import pandas as pd
import recommendation_analysis as analysis
import package_recommendations as pack
import append_scenario_sheets as xml
from refresh_scenario_comparison import cells

ROOT=analysis.ROOT;PRE=analysis.PRE;T=xml.T

def main():
    payload=json.loads((PRE/'payload.json').read_text(encoding='utf-8'));layout=json.loads((PRE/'layout.json').read_text(encoding='utf-8'))
    results=json.loads((ROOT/'analysis/recommendation_results.json').read_text(encoding='utf-8'));checks=[];count=0;maxdiff=0.
    def check(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(name)
    def compare(v,e,label):
        nonlocal count,maxdiff
        if e is None or (isinstance(e,float) and math.isnan(e)):check(label,v is None or v=='')
        elif isinstance(e,bool):check(label,v==e)
        elif isinstance(e,(int,float)):
            check(label,isinstance(v,(int,float)));d=abs(v-e);maxdiff=max(maxdiff,d);check(label,d<max(.00001,abs(e)*2e-11))
        else:check(label,v==e)
        count+=1
    with ZipFile(pack.OUTPUT) as saved,ZipFile(PRE/'input_workbook.xlsx') as base:
        paths=xml.sheet_paths(saved);old=xml.sheet_paths(base);check('27 unique sheets',len(paths)==27 and len(set(paths))==27)
        guide=json.loads((PRE/'guide_updates.json').read_text(encoding='utf-8'))
        for name,part in old.items():
            if name not in guide:check('Preserved sheet '+name,saved.read(paths[name])==base.read(part))
        metadata={'xl/styles.xml','xl/workbook.xml','xl/_rels/workbook.xml.rels','[Content_Types].xml','docProps/app.xml',*(old[n] for n in guide)}
        for item in base.infolist():
            if item.filename not in metadata:check('Preserved native resource '+item.filename,saved.read(item.filename)==base.read(item.filename))
        rec=cells(saved,paths['Recommendations']);summary=cells(saved,paths['Recommendation Summary']);source=cells(saved,paths['Scenario Inputs'])
        check('Selected scenario preserved',source['B3']==payload['sources']['Scenario Inputs']['B3'] and source['B4']==payload['sources']['Scenario Inputs']['B4'])
        check('Saved evidence current',rec['E5']=='CURRENT EVIDENCE');check('Saved portfolio captures current',summary['E5']=='CURRENT')
        primary=layout['primary'];col=lambda i:analysis.ooxml_col(i) if hasattr(analysis,'ooxml_col') else __import__('refresh_scenario_comparison').col(i)
        expected=pd.read_csv(ROOT/'data/gym_recommendations.csv').to_dict('records')
        for j,r in enumerate(expected):
            for f in primary:
                if f in ['explanation','plus1_failed_gates','plus2_failed_gates']:continue
                compare(rec.get(col(primary.index(f))+str(21+j)),r.get(f),'Saved primary '+f+'/'+r['gym_id'])
        sensitivity=pd.read_csv(ROOT/'data/recommendation_sensitivity.csv').to_dict('records');rulecols=layout['rulescols']
        for j,r in enumerate(sensitivity):
            for f in ['gym_id','variant','action','proposed_increment','provisional_test_increment','assessment_increment','rule_id']:
                compare(rec.get(col(rulecols.index(f))+str(1101+j)),r[f],'Saved rule '+f+'/'+str(j))
        port=pd.read_csv(ROOT/'data/recommendation_portfolio.csv').to_dict('records');pc=layout['portfolioCols']
        for j,r in enumerate(port):
            for f in pc:compare(summary.get(col(pc.index(f))+str(131+j)),r[f],'Saved portfolio '+f+'/'+str(j))
        allnames=set(saved.namelist());errors=[];formula_count=0;graphs={}
        for name in ['Recommendations','Recommendation Summary']:
            tree=ET.fromstring(saved.read(paths[name]));formula={}
            for c in tree.iter(T+'c'):
                if c.attrib.get('t')=='e':errors.append((name,c.attrib['r']))
                f=c.find(T+'f')
                if f is not None:
                    formula[c.attrib['r']]='='+f.text;formula_count+=1
                    check('Cached formula '+name+c.attrib['r'],c.find(T+'v') is not None)
                    check('No terminal audit feeds business '+name+c.attrib['r'],not re.search(r"(?:Checks|Audit|Reconciliations)'?!",f.text,re.I))
            graphs[name]=dict(values=cells(saved,paths[name]),formulas=formula)
        check('No saved formula errors',not errors)
        for filename in allnames:
            if filename.endswith('.rels'):
                folder,basename=filename.rsplit('/_rels/',1) if '/_rels/' in filename else ('',filename.removeprefix('_rels/'))
                owner=(folder+'/' if folder else '')+basename.removesuffix('.rels')
                for rel in ET.fromstring(saved.read(filename)):
                    if rel.attrib.get('TargetMode')!='External':check('Resolved relation '+filename+rel.attrib['Id'],xml.resolve(owner,rel.attrib['Target']) in allnames)
        table_names=[ET.fromstring(saved.read(n)).attrib['name'] for n in allnames if n.startswith('xl/tables/') and n.endswith('.xml')]
        check('Unique native table names',len(table_names)==len(set(table_names)))
        charts=[n for n in allnames if '/charts/' in n and n.endswith('.xml') and '/phase7_' in n];check('Four new native charts',len(charts)==4)
        # Compare original styles by serialisation rather than Element identity.
        before_styles=ET.fromstring(base.read('xl/styles.xml'));after_styles=ET.fromstring(saved.read('xl/styles.xml'))
        for group in ['fonts','fills','borders','cellXfs','cellStyleXfs','dxfs']:
            original=before_styles.find(T+group);final=after_styles.find(T+group)
            if original is not None:check('Original '+group+' preserved',[ET.tostring(x) for x in final][:len(original)]==[ET.tostring(x) for x in original])
        data=dict(sources=analysis.source_blocks(),graphs=graphs,expected=payload['recommendations'],expected_portfolio=payload['portfolio'],layout=layout)
        (PRE/'saved_graph.json').write_text(json.dumps(analysis.clean(data),separators=(',',':')),encoding='utf-8')
    check('Source and prior evidence hashes unchanged',analysis.hashes()==results['input_hashes'])
    check('Three CSVs byte-identically reproduced',json.loads((PRE/'reproduction.json').read_text(encoding='utf-8'))['csv_hashes']==results['csv_hashes'])
    report=dict(status='Saved package parity passed; actual-formula recalculation and refresh evidence required before completion',checks_passed=len(checks),independent_cells_compared=count,max_saved_csv_difference=maxdiff,formula_caches=formula_count,formula_errors=errors,preserved_sheets=25,final_sheet_count=27,native_charts=4,source_hashes_unchanged=True)
    formula_graph_hash=hashlib.sha256(json.dumps({n:graphs[n]['formulas'] for n in sorted(graphs)},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()
    report['formula_graph_sha256']=formula_graph_hash
    evidence_files={'saved_recalculation':'saved_recalculation.json','refresh':'refresh_verification.json','phase6_refresh_compatibility':'phase6_refresh_compatibility.json','visual_review':'visual_review.json'}
    if all((PRE/f).exists() for f in evidence_files.values()):
        evidence={k:json.loads((PRE/f).read_text(encoding='utf-8')) for k,f in evidence_files.items()}
        recalculation=evidence['saved_recalculation'];refresh=evidence['refresh']
        complete=(recalculation.get('savedWorkbookRecalculated') and recalculation.get('formula_graph_sha256')==formula_graph_hash and recalculation.get('selected_case_restored') and refresh.get('successful') and refresh.get('selected_case_restored') and refresh.get('portfolio_status')=='CURRENT' and evidence['phase6_refresh_compatibility'].get('successful') and evidence['visual_review'].get('passed'))
        report['completion_evidence']=evidence
        if complete:report['status']='Phase 7 complete: saved parity, actual formula recalculation, refresh, preservation, reproducibility and visual review passed'
    (ROOT/'analysis/recommendation_workbook_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
