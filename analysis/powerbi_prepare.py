"""Prepare immutable Phase 3–8 evidence for an Import Power BI model.

No forecasts, rankings, assignments or policy decisions are recalculated.
Run before every Power BI refresh. Empty CSV fields represent null, never zero.
"""
from pathlib import Path
import hashlib, json, sys
from datetime import datetime, timezone
from zipfile import ZipFile
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'powerbi/model_data'
META=ROOT/'powerbi'
DISCLAIMERS=[
 'This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.',
 'This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.'
]
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def sources():
 paths=list((ROOT/'data').glob('*.csv'))
 paths += [p for p in (ROOT/'analysis').glob('*.json') if (p.name.endswith('_config.json') or p.name.endswith('_results.json')) and not p.name.startswith('powerbi_')]
 paths += [ROOT/'analysis/.workbook_previews/phase6/joint_draws.npz']
 result={str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in sorted(paths) if p.exists()}
 # Operational payload sources change on workbook refresh. The retained history
 # component is immutable evidence and is hashed independently of those captures.
 payload=json.loads((ROOT/'analysis/.workbook_previews/phase8/payload.json').read_text(encoding='utf-8'))
 result['analysis/.workbook_previews/phase8/payload.json#extended_history']=hashlib.sha256(json.dumps(payload['extended_history'],sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
 return result
def read(name):return pd.read_csv(ROOT/'data'/f'{name}.csv')
def frame(v):return pd.DataFrame(v['data'],columns=v['columns'])
def assert_near(a,b,msg,tol=.01):
 assert np.allclose(a,b,rtol=0,atol=tol,equal_nan=True),msg
def check_key(df,key,name):
 assert not df[key].isna().any().any(),f'{name}: missing key'
 assert not df.duplicated(key).any(),f'{name}: duplicate {key}'
def type_for(col,series):
 if pd.api.types.is_bool_dtype(series):return 'boolean'
 nonnull=series.dropna()
 if len(nonnull) and nonnull.map(lambda x:isinstance(x,(bool,np.bool_))).all():return 'boolean'
 if len(nonnull) and any(t in col for t in ['date','month','start','end']) and nonnull.astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$').all():return 'dateTime'
 if col in {'month','date','opening_date','snapshot_date','notification_date','new_joiner_effective_date','incumbent_effective_date','incumbent_billing_date','review_date','pre_start','pre_end','post_start','post_end','existing_member_effective_date','join_month','event_date'}:return 'dateTime'
 if pd.api.types.is_integer_dtype(series):return 'int64'
 if pd.api.types.is_numeric_dtype(series):return 'double'
 # Explicitly reject mixed numeric/text observations in numeric columns during M import.
 return 'string'
def workbook_status(workbook_path=None):
 import append_scenario_sheets as xml
 from refresh_scenario_comparison import cells
 workbook_path=workbook_path or ROOT/'excel/gym_pricing_model.xlsx'
 with ZipFile(workbook_path) as z:
  paths=xml.sheet_paths(z);assert len(paths)==31
  vals={n:cells(z,paths[n]) for n in ['Scenario Inputs','Scenario Comparison','Recommendations','Recommendation Summary','Experiment Results']}
 si=vals['Scenario Inputs'];rec=vals['Recommendations'];rs=vals['Recommendation Summary']
 cfg=json.loads((ROOT/'analysis/recommendation_config.json').read_text())
 expected=[cfg['member_loss_limit'],cfg['minimum_post_increase_competitor_gap'],int(cfg['test_repeat_repricing'])]
 policy_match=[rec.get('B4'),rec.get('B5'),rec.get('B6')]==expected
 status={
  'scenario_capture':vals['Scenario Comparison'].get('D3'),
  'scenario_ranges':si.get('E23'),
  'recommendation_evidence':rs.get('B4'),
  'recommendation_ready':rs.get('B5'),
  'portfolio_capture':rs.get('E5'),
  'experiment_capture':vals['Experiment Results'].get('F4'),
  'saved_policy_matches':policy_match,
  'selected_case':si['B3'],'selected_price':si['B4'],'sheet_count':31}
 # Also compare active driver cells to original evidence inputs. Selector is not a driver override.
 originals=json.loads((ROOT/'analysis/.workbook_previews/phase6/payload.json').read_text(encoding='utf-8'))
 from refresh_scenario_comparison import col
 differences=[]
 def equal(a,b):return a==b or a in [None,''] and b in [None,'']
 for label,first,n,width in [('drivers',50,len(originals['drivers']['data']),len(originals['drivers']['columns'])),('states',1101,len(originals['states']['data']),len(originals['states']['columns']))]:
  for row in range(first,first+n):
   for c in range(width):
    if not equal(si.get(col(c)+str(row)),si.get(col(c+80)+str(row))):differences.append(col(c)+str(row))
 for row in range(9,18):
  for c in range(5,9):
   if not equal(si.get(col(c)+str(row)),si.get(col(c+80)+str(row))):differences.append(col(c)+str(row))
 overrides=any(isinstance(si.get('I'+str(row)),(float,int)) for row in range(9,18))
 status['independent_driver_difference_count']=len(differences)
 status['manual_behaviour_override']=overrides
 status['scenario_parameter_status']=si.get('E23')
 from powerbi_capture_checks import capture_differences
 capture_count,capture_mismatch=capture_differences(vals)
 status['independent_capture_cells_compared']=capture_count
 status['independent_capture_mismatch_count']=len(capture_mismatch)
 status['forward_current']=bool(status['scenario_capture']=='CURRENT' and status['recommendation_evidence']=='CURRENT EVIDENCE' and status['recommendation_ready']=='READY' and status['portfolio_capture']=='CURRENT' and policy_match and si.get('E23')==0 and not differences and not overrides and not capture_mismatch)
 exp=json.loads((ROOT/'analysis/experiment_config.json').read_text(encoding='utf-8'))
 with ZipFile(workbook_path) as z:
  dv=cells(z,xml.sheet_paths(z)['Experiment Design'])
 expected_guards=[exp[x] for x in ['member_harm_limit','standard_acquisition_harm_limit','churn_harm_limit_pp','downgrade_harm_limit_pp','complaints_service_limit','capacity_service_limit','alpha']]
 status['experiment_saved_guardrails_match']=[dv.get('B'+str(r)) for r in range(4,11)]==expected_guards
 def serial(date):return (pd.Timestamp(date)-pd.Timestamp('1899-12-30')).days
 expected_protocol=[exp['increment'],exp['seed'],exp['bootstrap_samples'],serial(exp['intervention_date']),serial(exp['billing_date'])]
 status['experiment_saved_protocol_match']=[dv.get('B'+str(r)) for r in range(12,17)]==expected_protocol
 return status
def prepare():
 OUT.mkdir(parents=True,exist_ok=True)
 obsolete=OUT/'FactScenarioSensitivity.csv'
 if obsolete.exists():
  assert obsolete.resolve().is_relative_to(OUT.resolve());obsolete.unlink()
 hashes=sources()
 prior=META/'source_hash_manifest.json'
 if prior.exists():
  previous=json.loads(prior.read_text())['sources']
  # One-time migration of the in-progress Phase 9 manifest from whole operational
  # payload to immutable history component; no prior evidence file is changed.
  legacy='analysis/.workbook_previews/phase8/payload.json'
  if legacy in previous:
   previous.pop(legacy);previous[legacy+'#extended_history']=hashes[legacy+'#extended_history']
  assert hashes==previous,'Prior evidence changed. Resolve/version the evidence before replacing the validated snapshot.'
 # Validate against Phase 8's frozen inputs, not merely this project's last run.
 phase8=json.loads((ROOT/'analysis/experiment_results.json').read_text())
 for k,v in phase8['input_hashes'].items():
  path=ROOT/k
  assert digest(path)==v,f'Phase 8 protected evidence changed: {k}'
 for k,v in phase8['csv_hashes'].items():
  path=ROOT/'data'/(k if k.endswith('.csv') else k+'.csv')
  if not path.exists():path=ROOT/k
  assert digest(path)==v,f'Phase 8 output changed: {k}'
 gm=read('gym_master');monthly=read('monthly_performance');head=read('gym_headroom');rec=read('gym_recommendations')
 annual=read('gym_scenarios');variants=read('recommendation_sensitivity');portfolio=read('recommendation_portfolio')
 design=read('experiment_design');payload=json.loads((ROOT/'analysis/.workbook_previews/phase8/payload.json').read_text())
 tables={};keys={};provenance={};relations=[];checks=[]
 def add(name,df,key,source):
  df=df.copy();check_key(df,key,name);tables[name]=df;keys[name]=key;provenance[name]=source
 def link(fact,col,dim,dcol=None):relations.append({'fact':fact,'column':col,'dimension':dim,'dimension_column':dcol or col})
 attrs=gm.merge(head[['gym_id','segment','band','rank','score','sensitive','caution_flag_count']],on='gym_id',validate='1:1').merge(design[['gym_id','population','assignment','pair_id','disposition']],on='gym_id',validate='1:1')
 attrs['experiment_population']=attrs.pop('population');attrs['experiment_assignment']=attrs.pop('assignment');attrs['experiment_pair_id']=attrs.pop('pair_id')
 attrs['competitor_proxy_status']='Fictional comparable competitors; national equivalents are synthetic proxies'
 add('DimGym',attrs,['gym_id'],'gym_master + saved headroom + experiment_design (no changed evidence)')
 dates=pd.date_range('2024-01-01','2025-12-01',freq='MS')
 def calendar(ds):return pd.DataFrame({'month':ds.strftime('%Y-%m-%d'),'year':ds.year,'month_number':ds.month,'month_name':ds.strftime('%b'),'quarter':['Q'+str(x) for x in ds.quarter],'year_month':ds.strftime('%Y-%m')})
 add('DimHistoryMonth',calendar(dates),['month'],'Calendar: historical reporting windows')
 add('DimScenarioMonth',calendar(pd.date_range('2026-01-01','2026-12-01',freq='MS')),['month'],'Separate forecast calendar')
 add('DimExperimentMonth',calendar(pd.date_range('2025-01-01','2026-12-01',freq='MS')),['month'],'Separate experiment calendar, never linked to historical slicer')
 add('DimAssignment',pd.DataFrame({'assignment':['Treatment','Control']}),['assignment'],'Fixed treatment/control arms shared by deduplicated history and simulated paths')
 for name,col,values in [('DimCase','case',['Base','Downside','Upside']),('DimPrice','price_increment',[0,1,2,3]),('DimPolicy','variant',portfolio.variant.drop_duplicates().tolist()),('DimSimulation','simulation',['Main','A/A null','Adverse response']),('DimPopulation','population',read('experiment_estimates').population.drop_duplicates().tolist()),('DimCheckpoint','checkpoint_months',[1,3,6,12])]:
  d=pd.DataFrame({col:values});d['sort_order']=range(1,len(d)+1)
  if name=='DimPrice':d['label']=['No increase','+£1','+£2','+£3']
  if name=='DimPolicy':d['label']=['Base policy','3% member limit','7% member limit','£1 competitor buffer','Repeat repricing warning']
  if name=='DimCheckpoint':d['label']=['30-day approximation','90-day approximation','Six-month primary','Twelve-month sustained']
  add(name,d,[col],'Fixed saved-analysis selectors')
 add('DimBridge',pd.DataFrame({'step':['2024 revenue','Member volume','Total ARPMM','2025 revenue'],'sort_order':[1,2,3,4]}),['step'],'Exact historical decomposition; interaction allocated to ARPMM')
 from powerbi_measures import METRIC_PANELS
 add('DimMetricPanel',pd.DataFrame([{'row_id':panel+' / '+metric,'panel':panel,'metric':metric,'sort_order':j} for panel,metrics in METRIC_PANELS.items() for j,metric in enumerate(metrics)]),['row_id'],'Disconnected presentation rows for existing DAX measures; no new analysis')
 source_tables=[
  ('FactHistory','monthly_performance',['gym_id','month']),
  ('FactCompetitor','competitor_prices',['gym_id','competitor_id','month']),
  ('FactBaseline','gym_baseline',['gym_id']),('FactHeadroom','gym_headroom',['gym_id']),
  ('FactRecommendation','gym_recommendations',['gym_id']),
  ('FactScenarioMonthly','scenario_monthly',['gym_id','month','price_increment','case']),
  ('FactScenarioAnnual','gym_scenarios',['gym_id','price_increment','case']),
  ('FactScenarioEstate','estate_scenarios',['price_increment','case']),
  ('FactPolicyRecommendation','recommendation_sensitivity',['gym_id','variant']),
  ('FactPortfolio','recommendation_portfolio',['variant','case']),
  ('FactHistoricalEstimate','price_response_estimates',['estimator','window','group_type','group','metric']),
  ('FactHistoricalPair','pilot_pair_response',['pair_id','window']),
  ('FactHistoricalEvent','historical_event_response',['gym_id','event_id']),
  ('FactExperimentDesign','experiment_design',['gym_id']),
  ('FactExperimentPair','experiment_pair_results',['simulation','pair_id','checkpoint_months']),
  ('FactExperimentEstimate','experiment_estimates',['simulation','population','checkpoint_months','metric']),
  ('FactExperimentMonitoring','experiment_monitoring',['simulation','gym_id','checkpoint_months']),
  ('FactPower','experiment_power',['design','effect_assumption','method']),
 ]
 # Infer two varied source keys explicitly from declared dictionary after inspecting source headers.
 for name,file,key in source_tables:
  d=read(file)
  if name in {'FactScenarioEstate','FactPortfolio'}:d=d.drop(columns='gym_id',errors='ignore')
  if name=='FactScenarioSensitivity':
   key=['gym_id','price_increment','variant'];d['gym_id']=d['gym_id'].fillna('ESTATE')
  if name=='FactHistoricalEvent':key=['gym_id','event_family'] if 'event_id' not in d else ['gym_id','event_id']
  add(name,d,key,f'data/{file}.csv (saved evidence)')
  if 'gym_id' in d and name!='FactScenarioSensitivity':link(name,'gym_id','DimGym')
  if 'case' in d:link(name,'case','DimCase')
  if 'price_increment' in d:link(name,'price_increment','DimPrice')
  if 'variant' in d and name!='FactScenarioSensitivity':link(name,'variant','DimPolicy')
  if 'simulation' in d:link(name,'simulation','DimSimulation')
  if 'checkpoint_months' in d:link(name,'checkpoint_months','DimCheckpoint')
  if name=='FactExperimentEstimate':link(name,'population','DimPopulation')
 link('FactHistory','month','DimHistoryMonth');link('FactCompetitor','month','DimHistoryMonth');link('FactScenarioMonthly','month','DimScenarioMonth')
 sensitivity=read('scenario_sensitivity');sensitivity['gym_id']=sensitivity.gym_id.fillna('ESTATE')
 add('DimAlternative',pd.DataFrame({'variant':sensitivity.variant.drop_duplicates().tolist()}),['variant'],'Saved named Phase 6 sensitivity alternatives; Base assumptions only')
 for name,estate_scope in [('FactScenarioSiteSensitivity',False),('FactScenarioEstateSensitivity',True)]:
  d=sensitivity[sensitivity.gym_id.eq('ESTATE')==estate_scope].copy();d['case']='Base'
  if estate_scope:d=d.drop(columns='gym_id')
  add(name,d,(['gym_id'] if not estate_scope else [])+['price_increment','variant'],'data/scenario_sensitivity.csv, saved Base alternatives split by site/estate grain')
  link(name,'price_increment','DimPrice');link(name,'variant','DimAlternative');link(name,'case','DimCase')
  if not estate_scope:link(name,'gym_id','DimGym')
 # Price response profiles retain just one event family; no replicated event-family stocks.
 hp=read('historical_response_panel');hp=hp[hp.event_family=='PILOT_202504']
 add('FactHistoricalPilotMonth',hp,['gym_id','month'],'historical_response_panel, PILOT_202504 only');link('FactHistoricalPilotMonth','gym_id','DimGym');link('FactHistoricalPilotMonth','month','DimHistoryMonth')
 # Construct the requested filtered point portfolio from saved scenario rows only.
 mapping=variants[['gym_id','variant','action','proposed_increment']].copy()
 mapping['price_increment']=np.where(mapping.action.isin(['RAISE £1','RAISE £2']),mapping.proposed_increment,0)
 mapping=mapping.drop(columns='proposed_increment')
 ps=mapping.merge(annual,on=['gym_id','price_increment'],how='left',validate='m:m')
 assert len(ps)==1200 and ps['case'].notna().all()
 # Interval endpoints in these site rows are not valid portfolio inputs. Remove them.
 ps=ps.drop(columns=[c for c in ps if c.endswith('_lower') or c.endswith('_upper') or c=='positive_revenue_draw_fraction'])
 add('FactPortfolioSite',ps,['gym_id','variant','case'],'Conditional RAISE maps saved increment; all other actions map no increase; no site ranges')
 link('FactPortfolioSite','gym_id','DimGym');link('FactPortfolioSite','variant','DimPolicy');link('FactPortfolioSite','case','DimCase')
 # Never duplicate 2025 history across Main / A/A / Adverse simulation labels.
 em=read('experiment_monthly');hist=em[~em.is_simulated].copy();unique=hist.drop(columns='simulation').drop_duplicates()
 assert len(unique)==84,'Duplicated history differs across simulation labels'
 early=frame(payload['extended_history']).drop(columns='simulation',errors='ignore')
 history=pd.concat([early,unique],ignore_index=True).drop(columns=['simulation'],errors='ignore')
 assert len(history)==168 and len(history.month.unique())==12
 add('FactExperimentHistory',history,['gym_id','month'],'Deduplicated Jul–Dec 2025 + retained Jan–Jun 2025 inputs')
 future=em[em.is_simulated].copy();assert len(future)==504
 add('FactExperimentPath',future,['simulation','gym_id','month'],'Simulated 2026 observations only; three separate cases')
 for n in ['FactExperimentHistory','FactExperimentPath']:
  link(n,'gym_id','DimGym');link(n,'month','DimExperimentMonth');link(n,'assignment','DimAssignment')
 link('FactExperimentPath','simulation','DimSimulation')
 gov=frame(payload['governance']);add('FactExperimentGovernance',gov,['simulation','population','checkpoint_months'],'Saved Phase 8 governance, not a new decision calculation')
 for c,d in [('simulation','DimSimulation'),('population','DimPopulation'),('checkpoint_months','DimCheckpoint')]:link('FactExperimentGovernance',c,d)
 guards=[];ecfg=payload['config'];ef=tables['FactExperimentEstimate']
 for metric,label,limit in [('member_harm','Closing membership loss',ecfg['member_harm_limit']),('standard_acquisition_harm','Standard acquisition loss',ecfg['standard_acquisition_harm_limit']),('incumbent_churn_change_pp','Monthly incumbent churn',ecfg['churn_harm_limit_pp']),('incumbent_downgrade_change_pp','Monthly incumbent downgrades',ecfg['downgrade_harm_limit_pp'])]:
  for row in ef[ef.metric==metric].to_dict('records'):
   guards.append({**{k:row[k] for k in ['simulation','population','checkpoint_months','metric','estimate','lower','upper','unit','complete_pairs','interval_status']},'label':label,'tolerance':limit,'upper_bound_pass':None if pd.isna(row['upper']) else row['upper']<=limit})
 add('FactExperimentGuardrail',pd.DataFrame(guards),['simulation','population','checkpoint_months','metric'],'Saved experimental estimates with fixed Phase 8 guardrail definitions; no new decisions')
 for c,d in [('simulation','DimSimulation'),('population','DimPopulation'),('checkpoint_months','DimCheckpoint')]:link('FactExperimentGuardrail',c,d)
 status=workbook_status()
 add('EvidenceStatus',pd.DataFrame([{'snapshot_id':hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()[:16],
  'historical_current':True,'forward_current':status['forward_current'],'experiment_current':status['forward_current'] and status['experiment_capture']=='CURRENT' and status['experiment_saved_guardrails_match'] and status['experiment_saved_protocol_match'],
  'evidence_message':'CURRENT saved evidence' if status['forward_current'] else 'UNAVAILABLE authoritative forward conclusions: stale captures, overridden assumptions or changed saved policy',
  'validation_utc':datetime.now(timezone.utc).isoformat(),'native_status':'Phase 9 build-ready; native verification pending',
  'disclaimer_1':DISCLAIMERS[0],'disclaimer_2':DISCLAIMERS[1]}]),['snapshot_id'],'Refresh metadata and workbook capture/parameter status')
 # Keys, foreign keys and one-way dimension-to-fact topology.
 for rel in relations:
  f,d=tables[rel['fact']],tables[rel['dimension']]
  assert set(f[rel['column']].dropna())<=set(d[rel['dimension_column']]),f'Unmatched dimension: {rel}'
 for n,d in tables.items():
  if 'gym_id' in d and n!='FactScenarioSensitivity':assert set(d.gym_id)<=set(gm.gym_id),n
 assert len(monthly)==1920 and monthly.groupby('gym_id').size().eq(24).all()
 assert_near(monthly.opening_members+monthly.new_members-monthly.cancelled_members,monthly.closing_members,'Historical member bridge',0)
 assert_near(monthly.subscription_revenue+monthly.joining_fee_revenue+monthly.ancillary_revenue,monthly.monthly_revenue,'Historical revenue components')
 y25=monthly[monthly.month.str.startswith('2025')];y24=monthly[monthly.month.str.startswith('2024')]
 assert round(y25.monthly_revenue.sum())==107006934
 assert monthly[monthly.month=='2025-12-01'].closing_members.sum()==396311
 assert rec.action.value_counts().to_dict()=={'DEFENSIVE / INVESTIGATE':38,'HOLD PRICE':26,'RAISE £1':10,'TEST FIRST':5,'RAISE £2':1}
 for (v,c),d in ps.groupby(['variant','case']):
  expected=portfolio[(portfolio.variant==v)&(portfolio.case==c)].iloc[0]
  for col in ['monthly_revenue','incremental_revenue','month12_members','new_members','opening_members','opening_base_cancellations','qualified_prospects','incumbent_standard_opening','incumbent_standard_downgrades']:
   assert_near(d[col].sum(),expected[col],f'Portfolio {v}/{c}/{col}')
 assert round(ps[(ps.variant=='base')&(ps.case=='Base')].incremental_revenue.sum())==148618
 assert ps[ps.action=='TEST FIRST'].price_increment.eq(0).all()
 primary=gov[(gov.simulation=='Main')&(gov.population=='First repricing')].set_index('checkpoint_months')
 assert primary.loc[6,'decision']=='EXTEND TEST' and primary.loc[12,'decision']=='STOP'
 e=tables['FactExperimentEstimate'];small=e.complete_pairs<4
 assert e.loc[small,['lower','upper']].isna().all().all()
 assert_near(future.opening_members+future.new_members-future.opening_base_cancellations-future.same_month_cancellations,future.closing_members,'Simulation bridge',0)
 assert_near(future.subscription_revenue+future.joining_fee_revenue+future.ancillary_revenue,future.monthly_revenue,'Simulation net components')
 # Scenario source totals and no-increase identity; never aggregate options/cases.
 estate=tables['FactScenarioEstate']
 for (p,c),d in annual.groupby(['price_increment','case']):
  target=estate[(estate.price_increment==p)&(estate.case==c)].iloc[0]
  for col in ['monthly_revenue','new_members','month12_members']:assert_near(d[col].sum(),target[col],f'Estate {p}/{c}/{col}')
 zero=annual[annual.price_increment==0]
 for _,d in zero.groupby('gym_id'):assert d.monthly_revenue.nunique()==1 and d.month12_members.nunique()==1
 volume=(y25.average_members.sum()-y24.average_members.sum())*(y24.monthly_revenue.sum()/y24.average_members.sum())
 yield_delta=y25.average_members.sum()*(y25.monthly_revenue.sum()/y25.average_members.sum()-y24.monthly_revenue.sum()/y24.average_members.sum())
 assert_near(volume+yield_delta,y25.monthly_revenue.sum()-y24.monthly_revenue.sum(),'Exact bridge')
 checks=['Protected evidence hashes unchanged','Unique reporting keys and complete dimension joins','80 gyms × 24 complete historical months','Member and revenue component bridges','2025 revenue/member/action anchors','1200 portfolio rows and all 15 portfolio totals, tests excluded','12 all-estate scenario combinations reconcile separately','No-increase identity across cases','168 experiment historical rows deduplicated, January–June retained','504 separate simulated path rows with valid integer bridges','Saved Main primary six/twelve-month decisions preserved','Unavailable intervals below four pairs retained','Exact member-volume/total-ARPMM bridge, interaction to ARPMM']
 schema={};outputs={}
 for name,d in tables.items():
  cols={c:type_for(c,d[c]) for c in d}
  # Serialize dates consistently and retain source double precision.
  for c,t in cols.items():
   if t=='dateTime':d[c]=pd.to_datetime(d[c],errors='raise').dt.strftime('%Y-%m-%d')
  path=OUT/f'{name}.csv';d.to_csv(path,index=False,na_rep='',float_format='%.17g',lineterminator='\n')
  schema[name]={'columns':cols,'key':keys[name],'rows':len(d),'source':provenance[name]};outputs[path.name]=digest(path)
 (META/'model_schema.json').write_text(json.dumps({'tables':schema,'relationships':relations},indent=2),encoding='utf-8')
 manifest={'sources':hashes,'snapshot_files':outputs,'snapshot_id':tables['EvidenceStatus'].iloc[0].snapshot_id,'validated_utc':tables['EvidenceStatus'].iloc[0].validation_utc,'workbook_status':status,'checks_passed':checks,'native_verification':'pending'}
 (META/'source_hash_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 result={'status':'reporting snapshot validated','tables':{n:len(d) for n,d in tables.items()},'checks':checks,'anchors':{'revenue_2025':float(y25.monthly_revenue.sum()),'december_members':396311,'base_raise_incremental_revenue':float(ps[(ps.variant=='base')&(ps.case=='Base')].incremental_revenue.sum()),'volume_bridge':float(volume),'arpmm_bridge':float(yield_delta)},'workbook_status':status}
 (ROOT/'analysis/powerbi_preparation_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 assert hashes==sources(),'Protected evidence changed during preparation'
 print(json.dumps(result,indent=2))
 return tables
if __name__=='__main__':prepare()
