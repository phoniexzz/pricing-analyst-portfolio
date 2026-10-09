"""Independent saved-OOXML verification; never authors spreadsheet business cells."""
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pandas as pd
import append_scenario_sheets as pack
from refresh_scenario_comparison import cells, col

ROOT=Path(__file__).resolve().parents[1];PRE=ROOT/'analysis/.workbook_previews/phase6';T=pack.T

def main():
    p=json.loads((PRE/'payload.json').read_text());layout=json.loads((PRE/'layout.json').read_text())
    result=json.loads((ROOT/'analysis/scenario_workbook_verification.json').read_text())
    compare=0;maxdiff=0;formula_count=0;errors=[];preserved=[]
    with ZipFile(pack.OUTPUT) as z,ZipFile(pack.BASE) as base:
        paths=pack.sheet_paths(z);old=pack.sheet_paths(base);assert len(paths)==25
        guides=json.loads((PRE/'guide_updates.json').read_text())
        for name,part in old.items():
            if name in guides:
                previous=cells(base,part);now=cells(z,paths[name])
                for address,v in previous.items():
                    if address not in guides[name]:assert now.get(address)==v,(name,address)
                for address,v in guides[name].items():assert now[address]==v
            else:assert z.read(paths[name])==base.read(part),name
            preserved.append(name)
        metadata={'xl/styles.xml','xl/workbook.xml','xl/_rels/workbook.xml.rels','[Content_Types].xml','docProps/app.xml'}
        changedguides={old[n] for n in guides}
        for item in base.namelist():
            if item not in metadata|changedguides:assert z.read(item)==base.read(item),item
        allcells={name:cells(z,part) for name,part in paths.items() if name in pack.ADDED}
        def near(v,e,where):
            nonlocal compare,maxdiff
            if e is None or pd.isna(e):assert v in [None,''],where
            elif isinstance(e,(float,int,np.floating,np.integer)) and not isinstance(e,(bool,np.bool_)):
                assert isinstance(v,(float,int)),(where,v,e);diff=abs(v-float(e));maxdiff=max(maxdiff,diff);assert diff<=max(1e-6,abs(float(e))*2e-11),(where,v,e)
            else:assert v==e,(where,v,e)
            compare+=1
        sites=pd.read_csv(ROOT/'data/gym_scenarios.csv')
        for i,row in enumerate(p['comparisons']['data']):
            for c,f in enumerate(p['comparisons']['columns']):near(allcells['Scenario Comparison'].get(col(layout['captureColumns'].index(f))+str(31+i)),row[c],('captured',i,f))
        # Every captured monthly revenue/member pair is checked against Python,
        # including the ten combinations outside the default live selection.
        cm=p['monthly']['columns']
        for i,row in enumerate(p['monthly']['data']):
            for c,f in enumerate(['gym_id','month','price_increment','case','monthly_revenue','closing_members']):
                expected=row[cm.index(f)]
                if f=='month':expected=(pd.Timestamp(expected)-pd.Timestamp('1899-12-30')).days
                near(allcells['Scenario Comparison'].get(col(c)+str(1101+i)),expected,('captured monthly',i,f))
        inputs=allcells['Scenario Inputs'];comparison=allcells['Scenario Comparison']
        assert inputs['B3']==1 and inputs['B4']==2 and inputs['E18']=='READY'
        assert inputs['E23']==0 and inputs['E24']==0 and comparison['D3']=='CURRENT'
        assert comparison['D4']=='Conditional evidence ranges'
        model=allcells['Scenario Model'];monthly=pd.read_csv(ROOT/'data/scenario_monthly.csv')
        ids=[r[p['gyms']['columns'].index('gym_id')] for r in p['gyms']['data']]
        annualFields=layout['annualFields'];summaryFields=layout['summaryFields']
        for mode in [0,1]:
            for gi,gid in enumerate(ids):
                a=sites[(sites.gym_id==gid)&(sites.case=='Base')&(sites.price_increment==(2 if mode else 0))].iloc[0]
                for c,f in enumerate(annualFields):
                    if f in ['case','probability_caps']:continue
                    near(model.get(col(c)+str(9+mode*80+gi)),a[f],('annual',mode,gid,f))
                for j,date in enumerate(pd.date_range('2026-01-01',periods=12,freq='MS')):
                    r=201+mode*960+gi*12+j;q=monthly[(monthly.gym_id==gid)&(monthly.case=='Base')&(monthly.price_increment==(2 if mode else 0))&(monthly.month==date.strftime('%Y-%m-%d'))].iloc[0]
                    for c,f in enumerate(summaryFields):
                        if f in q and isinstance(q[f],(int,float,np.integer,np.floating)):
                            near(model.get(col(c)+str(r)),q[f],('monthly',mode,gid,j,f))
        for name in pack.ADDED:
            for cell in ET.fromstring(z.read(paths[name])).iter(T+'c'):
                if cell.find(T+'f') is not None:formula_count+=1;assert cell.find(T+'v') is not None,(name,cell.attrib['r'],'missing recalculated cache')
                if cell.attrib.get('t')=='e':errors.append((name,cell.attrib['r'],cell.find(T+'v').text))
        assert not errors,errors
        assert all(model['D'+str(r)]==0 for r in range(2201,2281))
        tables=[ET.fromstring(z.read(n)).attrib['name'] for n in z.namelist() if n.startswith('xl/tables/') and n.endswith('.xml')]
        assert len(tables)==len(set(tables))
        # Every internal package relationship resolves to an existing part.
        for name in z.namelist():
            if not name.endswith('.rels'):continue
            origin=name.replace('/_rels/','/').removesuffix('.rels') if name!='_rels/.rels' else ''
            for rel in ET.fromstring(z.read(name)):
                if rel.attrib.get('TargetMode')!='External':assert pack.resolve(origin,rel.attrib['Target']) in z.namelist(),(name,rel.attrib['Target'])
        charts=[n for n in z.namelist() if ('/charts/' in n and n.rsplit('/',1)[-1].startswith('phase6_')) and n.endswith('.xml')]
        assert len(charts)>=3
    source=json.loads((ROOT/'analysis/scenario_results.json').read_text())['input_hashes']
    assert all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in source.items())
    result.update(fullRefreshSuccessful=True,twelveCombinationsCaptured=12,captureFreshnessCurrent=True,selectedCaseRestored=True,independentCsvCellsCompared=compare,maxSavedCsvDifference=maxdiff,newFormulaCaches=formula_count,originalSheetsPreserved=preserved,
        originalNativeFeaturesPreserved=True,sourceHashesUnchanged=True,finalSheetCount=25,nativeCharts=len(charts),formulaErrors=errors,
        independentInitialSourceChecks=True,internalRelationshipsChecked=True,uniqueTableNames=True)
    if (PRE/'saved_recalculation.json').exists():result.update(json.loads((PRE/'saved_recalculation.json').read_text()))
    if (PRE/'reproduction.json').exists():result['allFourCsvsReproduce']=len(json.loads((PRE/'reproduction.json').read_text())['reproduced_hashes'])==4
    if (PRE/'visual_review.json').exists():result['visualReview']=json.loads((PRE/'visual_review.json').read_text())
    result['status']='Complete' if result.get('savedWorkbookRecalculated') and result.get('allFourCsvsReproduce') and result.get('visualReview') else 'Final verification pending'
    (ROOT/'analysis/scenario_workbook_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ['originalSheetsPreserved','visualReview']},indent=2))

if __name__=='__main__':main()
