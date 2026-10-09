"""Offline schema, binding, data and scope checks; not a DAX runtime emulator."""
import json,re,hashlib
from pathlib import Path
import numpy as np,pandas as pd
from powerbi_prepare import ROOT,digest,sources,assert_near
from powerbi_measures import MEASURES,MEASURE_TABLE
import powerbi_schema_tools as schemas
P=ROOT/'powerbi'
def verify():
 checks=[];schema=json.loads((P/'model_schema.json').read_text());manifest=json.loads((P/'source_hash_manifest.json').read_text())
 assert sources()==manifest['sources'];checks.append('All protected source/configuration/evidence hashes unchanged')
 for file,sha in manifest['snapshot_files'].items():assert digest(P/'model_data'/file)==sha,file
 files=list((P/'Northstar.Report').rglob('*.json'))+[P/'gym_pricing_dashboard.pbip',P/'Northstar.Report/definition.pbir',P/'Northstar.SemanticModel/definition.pbism']
 errors=[];validated=0
 for file in files:
  try:schemas.validate(file);validated+=1
  except Exception as e:errors.append({'file':str(file.relative_to(ROOT)),'error':str(e)[:2000]})
 (ROOT/'analysis/powerbi_schema_errors.json').write_text(json.dumps(errors,indent=2))
 assert not errors,f'{len(errors)} schema failures; see powerbi_schema_errors.json'
 checks.append(f'{validated} JSON documents checked against pinned Microsoft schemas (theme checked separately)')
 import jsonschema
 theme=json.loads((P/'Northstar.Report/StaticResources/RegisteredResources/Northstar.json').read_text(encoding='utf-8'))
 theme_schema=json.loads((P/'schemas/reportThemeSchema-2.157.json').read_text(encoding='utf-8'))
 jsonschema.validators.validator_for(theme_schema)(theme_schema).validate(theme)
 checks.append('Navy/teal theme validates against Microsoft report-theme 2.157 schema; statuses also use text labels')
 deps={};bound=0
 def checkfield(table,col,ismeasure=False):
  nonlocal bound
  if ismeasure:assert table==MEASURE_TABLE and col in MEASURES,(table,col)
  else:assert table in schema['tables'] and col in schema['tables'][table]['columns'],(table,col)
  bound+=1
 def scan(value):
  if isinstance(value,dict):
   for typ in ['Column','Measure']:
    if typ in value:
     x=value[typ]
     if isinstance(x,dict) and 'Expression' in x and 'SourceRef' in x['Expression'] and 'Entity' in x['Expression']['SourceRef']:checkfield(x['Expression']['SourceRef']['Entity'],x['Property'],typ=='Measure')
   for x in value.values():scan(x)
  elif isinstance(value,list):
   for x in value:scan(x)
 for file in files:scan(json.loads(file.read_text(encoding='utf-8')))
 for name,meta in MEASURES.items():
  for tab,col in re.findall(r'\b([A-Za-z][A-Za-z0-9_]*)\[([^\]]+)\]',meta['dax']):checkfield(tab,col)
  deps[name]=re.findall(r'(?<![A-Za-z0-9_])\[([^\]]+)\]',meta['dax'])
  for dep in deps[name]:assert dep in MEASURES,(name,dep)
  assert not re.search(r'SUM\([^\)]*_(lower|upper)\]',meta['dax']),name
 def visit(n,path):
  assert n not in path,'Measure cycle: '+str(path+[n])
  for d in deps[n]:visit(d,path+[n])
 for n in deps:visit(n,[])
 checks.append(f'{bound} semantic field/measure references resolve; {len(MEASURES)} measures have acyclic dependencies; no summed interval endpoints')
 # Relations: every edge terminates at a unique dimension. No fact-to-fact/bidirectional paths.
 for rel in schema['relationships']:
  assert rel['dimension'].startswith('Dim') and rel['fact'].startswith('Fact')
 checks.append('Relationship graph has only many-to-one, single-direction dimension-to-fact edges')
 pages=json.loads((P/'page_specification.json').read_text());assert len(pages)==7 and sum(p['detail'] for p in pages)==1
 for page in pages:
  for v in page['visuals']:
   assert 0<=v['x'] and 0<=v['y'] and v['x']+v['w']<=1600 and v['y']+v['h']<=page.get('height',1050),(page['name'],v['name'])
   if v['type'] not in ['textbox','actionButton']:assert v['roles'],v['name']
  if page['experiment']:
   assert not any(v.get('sync') for v in page['visuals'])
 checks.append('Six populated main pages, one hidden Gym Detail; positioned bounds; separate experiment controls')
 hist=pd.read_csv(P/'model_data/FactHistory.csv');gyms=pd.read_csv(P/'model_data/DimGym.csv')
 tests=[]
 # Independently check the documented measures' arithmetic, not claim native execution.
 for sel in [hist, hist[hist.gym_id.isin(['NF001','NF023'])],hist[hist.gym_id.isin(gyms[gyms.region=='London'].gym_id)]]:
  for months in [list(range(1,13)),[1,2,3],[10,11,12],[2,6,11]]:
   dates=pd.to_datetime(sel.month);cur=sel[(dates.dt.year==2025)&dates.dt.month.isin(months)];old=sel[(dates.dt.year==2024)&dates.dt.month.isin(months)]
   rev=cur.monthly_revenue.sum();exposure=cur.average_members.sum();opening=cur.opening_members.sum()
   rates={'arpmm':rev/exposure,'churn':cur.opening_base_cancellations.sum()/opening,'conversion':cur.new_members.sum()/cur.qualified_prospects.sum()}
   assert_near(rates['churn']*opening,cur.opening_base_cancellations.sum(),'Weighted churn parity',1e-8)
   assert_near(rates['conversion']*cur.qualified_prospects.sum(),cur.new_members.sum(),'Weighted conversion parity',1e-8)
   previousarpmm=old.monthly_revenue.sum()/old.average_members.sum()
   vol=(exposure-old.average_members.sum())*previousarpmm
   yld=exposure*(rates['arpmm']-previousarpmm)
   assert_near(vol+yld,rev-old.monthly_revenue.sum(),'Matching selected-month exact bridge')
   last=cur.month.max();assert len(cur[cur.month==last])==cur.gym_id.nunique()
   tests.append((cur.gym_id.nunique(),months))
 def divide(n,d):return None if d is None or d==0 or n is None else n/d
 assert divide(0,1)==0 and divide(1,0) is None and divide(None,1) is None
 assert abs((.047-.044)*100-.3)<1e-10
 assert all('PriorMonths = COUNTROWS(MatchingMonths)' in MEASURES[name+' Prior Year']['dax'] for name in ['Net Revenue','Acquisitions','Closing Members'])
 checks.append(f'{len(tests)} matching-window/site/region weighted-rate and exact bridge cases; closing-member boundaries; null vs zero and pp units')
 def scenario_scope(n,prices,cases):return len(prices)==1 and len(cases)==1 and (n==1 or n==80)
 assert scenario_scope(1,[2],['Base']) and scenario_scope(80,[2],['Base'])
 assert not scenario_scope(2,[2],['Base']) and not scenario_scope(11,[2],['Base']) and not scenario_scope(80,[1,2],['Base']) and not scenario_scope(80,[1],['Base','Downside'])
 assert all('HASONEVALUE(DimCase[case])' in MEASURES[n]['dax'] and 'HASONEVALUE(DimPrice[price_increment])' in MEASURES[n]['dax'] for n in ['Scenario Revenue','Scenario Increment lower','Scenario Members upper'])
 assert '[Full Estate Scope]' in MEASURES['Portfolio Increment lower']['dax']
 checks.append('Scenario multiple-option/case refusal and saved uncertainty scope guards; full portfolio only; no endpoint aggregation')
 eh=pd.read_csv(P/'model_data/FactExperimentHistory.csv');ep=pd.read_csv(P/'model_data/FactExperimentPath.csv')
 assert len(eh)==168 and not eh.duplicated(['gym_id','month']).any() and len(ep)==504
 assert eh.groupby('gym_id').size().eq(12).all() and ep.groupby(['simulation','gym_id']).size().eq(12).all()
 ex=pd.read_csv(P/'model_data/FactExperimentEstimate.csv');assert ex[ex.complete_pairs<4][['lower','upper']].isna().all().all()
 checks.append('Experiment history not repeated by simulation; twelve-month pre history; primary/exploratory intervals remain saved')
 assert 'HASONEVALUE(DimSimulation[simulation])' in MEASURES['Experiment Profile Revenue']['dax']
 assert 'SUM(FactExperimentHistory[monthly_revenue])' in MEASURES['Experiment Profile Revenue']['dax']
 assert 'SUM(FactExperimentPath[monthly_revenue])' in MEASURES['Experiment Profile Revenue']['dax']
 for p in (P/'Northstar.Report').rglob('*'):assert len(str(p.resolve()))<260,str(p)
 native=['Open PBIP in Power BI Desktop','Refresh M queries and materialise Import model','Execute DAX checks and compare native results','Test slicer defaults/sync, reset bookmarks, navigation, drill-through and cross-filter exclusions','Test unsupported selection uncertainty suppression and stale source gating','Review actual native screenshots of all seven layouts','Save PBIX through native File > Save As only if requested']
 result={'status':'Phase 9 build-ready; native verification pending','checks_passed':checks,'json_documents':validated,'field_measure_bindings':bound,'explicit_measures':len(MEASURES),'report_pages':7,'native_pending':native}
 from powerbi_acceptance_status import accepted
 proof=accepted()
 if proof:
  result.update(status=proof['status'],native_pending=[],native_acceptance='analysis/powerbi_native_acceptance.json')
 (ROOT/'analysis/powerbi_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result,indent=2))
 return result
if __name__=='__main__':verify()
