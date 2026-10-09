"""Independent saved-package parity, native-feature preservation and formula extraction."""
import hashlib
import json
import math
import re
from datetime import date
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import experiment_analysis as analysis
import package_recommendations as pack
import append_scenario_sheets as xml
from refresh_scenario_comparison import cells,col

PRE=analysis.PRE;T=xml.T

def main():
    p=json.loads((PRE/'payload.json').read_text(encoding='utf-8'));l=json.loads((PRE/'layout.json').read_text(encoding='utf-8'));result=json.loads((analysis.AN/'experiment_results.json').read_text(encoding='utf-8'))
    checks=[];count=0;maxdiff=0.;graphs={}
    def check(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(name)
    def compare(v,e,label):
        nonlocal count,maxdiff
        if e is None:check(label,v is None or v=='')
        elif isinstance(e,bool):check(label,v==e)
        elif isinstance(e,(float,int)):
            check(label,isinstance(v,(float,int)));d=abs(v-e);maxdiff=max(maxdiff,d);check(label,d<max(1e-7,abs(e)*2e-10))
        elif isinstance(e,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',e):check(label,v==(date.fromisoformat(e)-date(1899,12,30)).days)
        else:check(label,v==e)
        count+=1
    def objects(frame):return [dict(zip(frame['columns'],r)) for r in frame['data']]
    guides=json.loads((PRE/'guide_updates.json').read_text(encoding='utf-8'))
    with ZipFile(pack.OUTPUT) as z,ZipFile(PRE/'input_workbook.xlsx') as old:
        paths=xml.sheet_paths(z);before=xml.sheet_paths(old);check('31 unique populated sheets',len(paths)==31)
        allowed={'xl/styles.xml','xl/workbook.xml','xl/_rels/workbook.xml.rels','[Content_Types].xml','docProps/app.xml',*(before[n] for n in guides)}
        for name,part in before.items():
            if name not in guides:check('Preserved original sheet '+name,z.read(paths[name])==old.read(part))
        for item in old.infolist():
            if item.filename not in allowed:check('Preserved original native resource '+item.filename,z.read(item.filename)==old.read(item.filename))
        for name,updates in guides.items():
            v=cells(z,paths[name])
            for a,e in updates.items():compare(v.get(a),e,'Guidance '+name+a)
        source=cells(z,paths['Scenario Inputs']);compare(source['B3'],result['selected_scenario'][0],'Scenario case preserved');compare(source['B4'],result['selected_scenario'][1],'Scenario price preserved')
        for name in ['Experiment Design','Experiment Data','Experiment Results','Monitoring']:
            root=ET.fromstring(z.read(paths[name]));values=cells(z,paths[name]);forms={}
            for c in root.iter(T+'c'):
                check('No formula error '+name+c.attrib['r'],c.attrib.get('t')!='e')
                f=c.find(T+'f')
                if f is not None:
                    forms[c.attrib['r']]='='+f.text;check('Formula cache '+name+c.attrib['r'],c.find(T+'v') is not None)
                    check('Checks independent '+name+c.attrib['r'],not re.search(r"(?:Checks|Audit|Reconciliations)'?!",f.text,re.I))
            graphs[name]=dict(values=values,formulas=forms)
        def table(sheet,start,frame,fields,columns):
            v=graphs[sheet]['values']
            for i,row in enumerate(objects(frame)):
                for f in fields:compare(v.get(col(columns.index(f))+str(start+i)),row[f],sheet+'/'+f+'/'+str(i))
        table('Experiment Design',25,p['design'],['gym_id','eligible','disposition','assignment','pair_id','population',*analysis.CFG['matching_features']],l['design_columns'])
        monthly=p['monthly'];mf=[f for f in monthly['columns'] if f not in ['month','notification_date','incumbent_billing_date']]
        table('Experiment Data',21,monthly,mf,l['monthly_columns'])
        table('Experiment Results',140,p['pairs'],['pair_id',*set(analysis.METRICS.values()),'control_growth_factor','member_counterfactual'],l['pair_columns'])
        table('Experiment Results',2450,p['estimates'],['simulation','population','checkpoint_months','metric','estimate','lower','upper','complete_pairs','p_value_one_sided','p_value_two_sided'],l['estimate_columns'])
        table('Experiment Results',40,p['governance'],['simulation','population','checkpoint_months','decision','rule_id','service_trigger','capacity_trigger','complaints_trigger'],l['governance_columns'])
        table('Monitoring',21,p['monitoring'],p['monitoring']['columns'],l['monitoring_columns'])
        for a in ['B931','B932','B933']:check('Independent reconciliation '+a,abs(graphs['Experiment Data']['values'][a])<.01)
        allnames=set(z.namelist())
        for filename in allnames:
            if filename.endswith('.rels'):
                folder,basename=filename.rsplit('/_rels/',1) if '/_rels/' in filename else ('',filename.removeprefix('_rels/'))
                owner=(folder+'/' if folder else '')+basename.removesuffix('.rels')
                for rel in ET.fromstring(z.read(filename)):
                    if rel.attrib.get('TargetMode')!='External':check('Resolved native relationship '+filename+rel.attrib['Id'],xml.resolve(owner,rel.attrib['Target']) in allnames)
        tables=[ET.fromstring(z.read(n)).attrib['name'] for n in allnames if n.startswith('xl/tables/') and n.endswith('.xml')];check('Unique table names',len(tables)==len(set(tables)))
        newcharts=[n for n in allnames if '/charts/phase8_' in n and n.endswith('.xml')];check('Four new native charts',len(newcharts)==4)
        for group in ['fonts','fills','borders','cellXfs','cellStyleXfs','dxfs']:
            a=ET.fromstring(old.read('xl/styles.xml')).find(T+group);b=ET.fromstring(z.read('xl/styles.xml')).find(T+group)
            if a is not None:check('Original styles '+group,[ET.tostring(x) for x in b][:len(a)]==[ET.tostring(x) for x in a])
    check('Prior source and analysis hashes unchanged',analysis.hashes()==result['input_hashes'])
    check('Fixed experiment configuration unchanged',hashlib.sha256((analysis.AN/'experiment_config.json').read_bytes()).hexdigest()==result['configuration_hash'])
    for name,expected in result['csv_hashes'].items():check('Delivered CSV unchanged '+name,hashlib.sha256((analysis.DATA/(name+'.csv')).read_bytes()).hexdigest()==expected)
    check('Seven byte-identical CSVs reproduced',json.loads((PRE/'reproduction.json').read_text(encoding='utf-8'))['csv_hashes']==result['csv_hashes'])
    data=dict(sources=analysis.source_blocks(),graphs=graphs,payload=p,layout=l)
    (PRE/'saved_graph.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    digest=hashlib.sha256(json.dumps({n:graphs[n]['formulas'] for n in sorted(graphs)},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()
    evidence={}
    for key,file in [('recalculation','saved_recalculation.json'),('refresh','refresh_verification.json'),('compatibility','refresh_compatibility.json'),('visual','visual_review.json')]:
        if (PRE/file).exists():evidence[key]=json.loads((PRE/file).read_text(encoding='utf-8'))
    complete=len(evidence)==4 and evidence['recalculation'].get('formula_graph_sha256')==digest and evidence['recalculation'].get('savedWorkbookRecalculated') and evidence['refresh'].get('successful') and evidence['refresh'].get('capture_status')=='CURRENT' and evidence['compatibility'].get('successful') and evidence['visual'].get('passed')
    report=dict(status='Phase 8 complete' if complete else 'Saved package parity passed; completion evidence pending',checks_passed=len(checks),independent_cells_compared=count,max_difference=maxdiff,formula_count=sum(len(g['formulas']) for g in graphs.values()),formula_graph_sha256=digest,prior_sheets_preserved=27,final_sheet_count=31,native_new_charts=4,prior_evidence_unchanged=True,completion_evidence=evidence)
    (analysis.AN/'experiment_workbook_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='completion_evidence'},indent=2))

if __name__=='__main__':main()
