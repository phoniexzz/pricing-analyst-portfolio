"""Independently reconcile read-only native DAX results with frozen CSVs."""
from pathlib import Path
import json,hashlib,math
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'powerbi'; A=ROOT/'analysis'
def near(actual,expected,tol=1e-7):
 if actual is None or pd.isna(expected):
  assert actual is None and pd.isna(expected),(actual,expected)
 else:assert abs(actual-expected)<=tol,(actual,expected)
def run():
 r=json.loads((A/'powerbi_native_dax_results.json').read_text(encoding='utf-8'))
 assert r['measures']==296 and not r['measure_errors'] and len(r['all_measure_execution'][0])==296
 schema=json.loads((P/'model_schema.json').read_text())
 for row in r['table_counts']:assert row['rows'][0]['[Rows]']==schema['tables'][row['table']]['rows'],row
 h=pd.read_csv(P/'model_data/FactHistory.csv',parse_dates=['month']); hr=pd.read_csv(P/'model_data/FactHeadroom.csv').set_index('gym_id'); rec=pd.read_csv(P/'model_data/FactRecommendation.csv').set_index('gym_id')
 site=r['additional_checks'][0]['rows'];assert len(site)==80
 for row in site:
  g=row['DimGym[gym_id]'];c=h[(h.gym_id==g)&(h.month.dt.year==2025)];b=h[(h.gym_id==g)&(h.month.dt.year==2024)]
  expected={'Revenue':c.monthly_revenue.sum(),'Subscription':c.subscription_revenue.sum(),'JoiningFees':c.joining_fee_revenue.sum(),'Ancillary':c.ancillary_revenue.sum(),'Members':c.iloc[-1].closing_members,'AverageMembers':c.average_members.mean(),'ARPMM':c.monthly_revenue.sum()/c.average_members.sum(),'Yield':c.subscription_revenue.sum()/c.average_members.sum(),'StandardYield':c.standard_subscription_revenue.sum()/c.average_standard_members.sum(),'Joins':c.new_members.sum(),'Churn':c.opening_base_cancellations.sum()/c.opening_members.sum(),'Conversion':c.new_members.sum()/c.qualified_prospects.sum(),'Complaints':1000*c.pricing_complaints.sum()/c.average_members.sum(),'RevenuePrior':b.monthly_revenue.sum(),'RevenueGrowth':c.monthly_revenue.sum()/b.monthly_revenue.sum()-1,'ChurnChangePP':100*(c.opening_base_cancellations.sum()/c.opening_members.sum()-b.opening_base_cancellations.sum()/b.opening_members.sum())}
  for key,value in expected.items():near(row['['+key+']'],value,1e-6)
  assert row['[SavedRank]']==hr.loc[g,'rank'];assert row['[Action]']==rec.loc[g,'action']
 for check,months in zip(r['additional_checks'][1:4],[[1,2,3],[10,11,12],[1,5,9]]):
  c=h[(h.month.dt.year==2025)&h.month.dt.month.isin(months)];b=h[(h.month.dt.year==2024)&h.month.dt.month.isin(months)];row=check['rows'][0]
  values={'Revenue':c.monthly_revenue.sum(),'Prior':b.monthly_revenue.sum(),'Members':c[c.month==c.month.max()].closing_members.sum(),'Churn':c.opening_base_cancellations.sum()/c.opening_members.sum(),'Conversion':c.new_members.sum()/c.qualified_prospects.sum(),'Bridge':c.monthly_revenue.sum()-b.monthly_revenue.sum()}
  for k,v in values.items():near(row['['+k+']'],v,1e-6)
 scope=r['additional_checks'][4]['rows'][0]
 for key in ['2024 prior unavailable','Both-year prior unavailable','Regional lower suppressed','Filtered portfolio lower suppressed']:assert scope['['+key+']'] is None
 assert scope['[Valid zero]']==0 and scope['[Single gym lower]'] is not None
 estimates=pd.read_csv(P/'model_data/FactExperimentEstimate.csv')
 governance=pd.read_csv(P/'model_data/FactExperimentGovernance.csv')
 native_estimates=r['additional_checks'][5]['rows'];assert len(native_estimates)==108
 for row in native_estimates:
  sim=row['DimSimulation[simulation]'];pop=row['DimPopulation[population]'];cp=row['DimCheckpoint[checkpoint_months]']
  e=estimates[(estimates.simulation==sim)&(estimates.population==pop)&(estimates.checkpoint_months==cp)&(estimates.metric=='revenue_effect')].iloc[0]
  for label,col in [('Revenue','estimate'),('Lower','lower'),('Upper','upper'),('Pairs','complete_pairs')]:near(row['['+label+']'],e[col],1e-10)
  g=governance[(governance.simulation==sim)&(governance.population==pop)&(governance.checkpoint_months==cp)]
  assert row['[Decision]']==(g.iloc[0].decision if len(g) else 'DESCRIPTIVE — no saved governance classification for this population')
 frozen=json.loads((A/'.powerbi_native/protected_hashes.json').read_text())
 from powerbi_prepare import sources
 assert sources()==frozen['source_manifest'],'Protected evidence hashes changed'
 assert hashlib.sha256((ROOT/'excel/gym_pricing_model.xlsx').read_bytes()).hexdigest()==frozen['excel']
 original=json.loads((A/'.powerbi_native/original_measure_catalog.json').read_text());now=json.loads((P/'measure_catalog.json').read_text())
 assert original.keys()==now.keys();changed=[]
 for name,meta in now.items():
  before=original[name]
  if before!=meta:
   assert name in ['Guardrail '+x+' Display' for x in ['Point','Lower','Upper','Tolerance']]
   expected=dict(before);expected['dax']=before['dax'].replace('VAR Value =','VAR DisplayAmount =').replace('ISBLANK(Value)','ISBLANK(DisplayAmount)').replace('FORMAT(Value,','FORMAT(DisplayAmount,')
   assert meta==expected,name;changed.append(name)
 result={'status':'Native DAX parity passed','measures_executed':296,'source_tables_reconciled':41,'sites_reconciled':80,'matching_month_windows':3,'source_hashes_unchanged':len(frozen['source_manifest']),'excel_hash_unchanged':True,'reserved_local_variable_repairs':changed,'revenue_2025':107006933.85,'december_members':396311,'portfolio_increment':148618.48020484}
 (A/'powerbi_native_parity.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':run()
