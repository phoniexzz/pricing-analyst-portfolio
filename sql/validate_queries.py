"""Independent Pandas parity and concrete boundary tests for the SQL interfaces."""
import json,math,sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
from load_data import ROOT,BUILD
from run_queries import run

def read(name):return pd.read_csv(ROOT/'data'/f'{name}.csv')
def ratio(a,b):return a/b.replace(0,np.nan) if hasattr(b,'replace') else (a/b if b else np.nan)

def expected():
    m=read('monthly_performance');g=read('gym_master');y=m[m.month.str.startswith('2025')];out={}
    x=m.sort_values(['gym_id','month']).copy()
    x['bridge_residual']=x.closing_members-x.opening_members-x.new_members+x.opening_base_cancellations+x.same_month_cancellations
    x['previous_closing']=x.groupby('gym_id').closing_members.shift()
    x['continuity_residual']=x.opening_members-x.previous_closing
    out[1]=x
    a=y.groupby('gym_id').sum(numeric_only=True);a['observed_months']=y.groupby('gym_id').size()
    a['total_revenue']=a.monthly_revenue;a['average_members']=a.average_members/12
    a['member_months']=y.groupby('gym_id').average_members.sum()
    a['arpmm']=a.total_revenue/a.member_months;a['subscription_yield']=a.subscription_revenue/a.member_months
    a['standard_yield']=a.standard_subscription_revenue/a.average_standard_members
    out[2]=a.reset_index().merge(g[['gym_id','gym_name','region']],on='gym_id')
    b=read('gym_baseline');period=[]
    for window,p in [('Annual',''),('Q4','q4_')]:
        t=b[['gym_id']].copy();t['period']=window
        t['revenue_2025']=b[f'total_revenue_{p}2025'];t['revenue_2024']=b[f'total_revenue_{p}2024']
        t['revenue_growth_pct']=(t.revenue_2025/t.revenue_2024-1)*100
        t['acquisition_growth_pct']=(b[f'new_members_{p}2025']/b[f'new_members_{p}2024']-1)*100
        t['churn_change_pp']=(b[f'churn_rate_{p}2025']-b[f'churn_rate_{p}2024'])*100
        t['conversion_change_pp']=(b[f'conversion_rate_{p}2025']-b[f'conversion_rate_{p}2024'])*100
        period.append(t)
    out[3]=pd.concat(period)
    r=read('region_year_baseline');r['cancellations']=r.opening_base_cancellations;out[4]=r
    a=y.groupby('gym_id').sum(numeric_only=True)
    a['joins']=a.new_members;a['conversion_rate']=a.joins/a.qualified_prospects
    a['marketing_per_prospect']=a.marketing_spend/a.qualified_prospects;out[5]=a.reset_index()
    a['opening_member_months']=a.opening_members;a['churn_rate']=a.opening_base_cancellations/a.opening_members
    a['monthly_retention']=1-a.churn_rate;a['complaints_per_1000_member_months']=a.pricing_complaints*1000/a.average_members
    out[6]=a.reset_index()
    l=read('membership_ledger');l=l[l.month.str.startswith('2025')].copy();l['gross_paid_exposure']=l.average_members*l.billed_price
    a=l.groupby(['gym_id','membership_type']).sum(numeric_only=True)
    a['member_months']=a.average_members;a['net_subscription_yield']=a.subscription_revenue/a.member_months
    a['gross_average_paid_rate']=a.gross_paid_exposure/a.member_months
    a['membership_mix']=a.member_months/a.groupby(level=0).member_months.transform('sum');out[7]=a.reset_index()
    c=read('competitor_prices');c=c[c.month=='2025-12-01'];a=c.groupby('gym_id').agg(
        competitor_count=('competitor_id','count'),recurring_competitor_price=('competitor_standard_price','mean'),
        competitor_joining_fee=('joining_fee','mean'),competitors_with_promotion=('promotion_active','sum'),
        introductory_promotion_value=('promotion_value','mean')).reset_index()
    a=a.merge(m[m.month=='2025-12-01'][['gym_id','standard_price']],on='gym_id');a['competitor_gap']=a.recurring_competitor_price-a.standard_price;out[8]=a
    a=y.groupby(['gym_id','promotion_active']).sum(numeric_only=True);a['observed_months']=y.groupby(['gym_id','promotion_active']).size()
    a['joins']=a.new_members;a['conversion_rate']=a.new_members/a.qualified_prospects;out[9]=a.reset_index()
    a=read('cohorts')
    for days in [30,90,180]:a[f'retention_{days}d']=a[f'customers_remaining_{days}d']/a.customers_joined.replace(0,np.nan)
    out[10]=a
    a=read('pilot_pair_response');a=a[a.window=='primary_6m'].copy()
    for name,source in [('incumbent_churn_change_pp','incumbent_churn'),('downgrade_change_pp','incumbent_downgrade')]:
        a[name]=((a['treatment_post_'+source]-a['treatment_pre_'+source])-(a['control_post_'+source]-a['control_pre_'+source]))*100
    a['estimated_revenue_difference']=a.monthly_revenue_estimated_difference;out[11]=a
    a=read('gym_scenarios');a=a[a['case']=='Base'].copy();a['annual_revenue']=a.monthly_revenue;out[12]=a
    out[13]=read('gym_recommendations')
    # Independently reproduce portfolio mapping with DataFrame operations, not SQL.
    policy=read('recommendation_sensitivity');s=read('gym_scenarios')
    policy['mapped_increment']=np.where(policy.action.isin(['RAISE £1','RAISE £2']),policy.proposed_increment,0)
    fields=['gym_id','price_increment','case','monthly_revenue','incremental_revenue','month12_members','member_difference','new_members','qualified_prospects','opening_base_cancellations','opening_members']
    selected=policy[['variant','gym_id','action','mapped_increment']].merge(s[fields],left_on=['gym_id','mapped_increment'],right_on=['gym_id','price_increment'],validate='many_to_many')
    fields=['monthly_revenue','incremental_revenue','month12_members','member_difference','new_members','qualified_prospects','opening_base_cancellations','opening_members']
    a=selected.groupby(['variant','case'])[fields].sum().copy()
    a['gym_count']=selected.groupby(['variant','case']).size()
    a['raise_sites']=selected.assign(raise_site=selected.action.isin(['RAISE £1','RAISE £2'])).groupby(['variant','case']).raise_site.sum()
    a['annual_revenue']=a.monthly_revenue;a['conversion_rate']=a.new_members/a.qualified_prospects;a['churn_rate']=a.opening_base_cancellations/a.opening_members
    p=read('recommendation_portfolio')
    for col in ['incremental_revenue_lower','incremental_revenue_upper']:
        if col in a:del a[col]  # Never aggregate interval endpoints.
    out[14]=a.reset_index().merge(p[['variant','case','incremental_revenue_lower','incremental_revenue_upper','excluded_test_first_base_revenue']],on=['variant','case'])
    out[14]['excluded_provisional_test_gains']=out[14].excluded_test_first_base_revenue
    e=read('experiment_estimates');e=e[e.metric=='revenue_effect'].copy();e['revenue_effect']=e.estimate
    d=read('experiment_monitoring')[['simulation','population','checkpoint_months','population_decision']].drop_duplicates()
    out[15]=e.merge(d,on=['simulation','population','checkpoint_months'])
    return out

KEYS={1:['gym_id','month'],2:['gym_id'],3:['gym_id','period'],4:['region','year'],5:['gym_id'],6:['gym_id'],
      7:['gym_id','membership_type'],8:['gym_id'],9:['gym_id','promotion_active'],10:['gym_id','cohort_id'],11:['pair_id'],
      12:['gym_id','price_increment','case'],13:['gym_id'],14:['variant','case'],15:['simulation','population','checkpoint_months']}

def check_frame(actual,expect,key):
    actual=actual.sort_values(key).reset_index(drop=True);expect=expect.sort_values(key).reset_index(drop=True)
    assert len(actual)==len(expect),(len(actual),len(expect))
    maximum=0.0
    for col in actual:
        assert col in expect,col
        av=actual[col];ev=expect[col]
        assert av.isna().equals(ev.isna()),(col,'unavailable values differ')
        good=~av.isna()
        if pd.api.types.is_numeric_dtype(ev) or pd.api.types.is_bool_dtype(ev):
            delta=np.abs(av[good].astype(float).to_numpy()-ev[good].astype(float).to_numpy())
            monetary=any(s in col for s in ['revenue','price','fee','marketing','yield','arpmm','paid_rate','gap','gains'])
            tolerance=.01 if monetary else (1e-5 if any(s in col for s in ['member','joins','prospects']) else 1e-8)
            assert (delta<=tolerance).all(),(col,float(delta.max()),tolerance)
            if len(delta):maximum=max(maximum,float(delta.max()))
        else:assert av[good].astype(str).equals(ev[good].astype(str)),col
    return maximum

def boundaries():
    schema=json.loads((ROOT/'sql/schema.json').read_text());c=sqlite3.connect(':memory:')
    cols=schema['monthly_performance']['columns']
    c.execute('CREATE TABLE monthly_performance ('+','.join('"'+x+'" '+v['sqlite_type'] for x,v in cols.items())+')')
    fields=['gym_id','month','opening_members','new_members','qualified_prospects','opening_base_cancellations','same_month_cancellations','average_members','pricing_complaints','website_leads','trial_visits','marketing_spend','monthly_revenue']
    rows=[['ZERO','2025-01-01',0,0,0,0,0,0,0,0,0,0,0],['VALID','2025-01-01',10,0,10,0,0,10,0,0,0,0,0],['ZERO','2024-01-01',0,0,0,0,0,0,0,0,0,0,0]]
    c.executemany('INSERT INTO monthly_performance ('+','.join(fields)+') VALUES ('+','.join('?' for _ in fields)+')',rows)
    f=pd.read_sql_query((ROOT/'sql/queries/05_qualified_funnel.sql').read_text(),c).set_index('gym_id')
    assert pd.isna(f.loc['ZERO','conversion_rate']) and f.loc['VALID','conversion_rate']==0
    f=pd.read_sql_query((ROOT/'sql/queries/06_opening_base_retention.sql').read_text(),c).set_index('gym_id')
    assert pd.isna(f.loc['ZERO','monthly_retention']) and f.loc['VALID','monthly_retention']==1
    f=pd.read_sql_query((ROOT/'sql/queries/03_matching_periods.sql').read_text(),c)
    assert f.revenue_growth_pct.isna().all() and f.acquisition_growth_pct.isna().all()
    c.close()
    c=sqlite3.connect((BUILD/'northstar.sqlite').as_uri()+'?mode=ro',uri=True)
    assert c.execute('SELECT COUNT(*) FROM experiment_history').fetchone()[0]==84
    assert c.execute('SELECT COUNT(*) FROM experiment_monthly WHERE is_simulated=0').fetchone()[0]==252
    assert c.execute('SELECT COUNT(*) FROM gym_scenarios').fetchone()[0]==960
    assert c.execute('SELECT COUNT(*) FROM gym_scenarios WHERE "case"="Base"').fetchone()[0]==320
    assert c.execute('SELECT COUNT(*) FROM monthly_performance WHERE month="2025-12-01"').fetchone()[0]==80
    assert c.execute('SELECT SUM(closing_members) FROM monthly_performance WHERE month="2025-12-01"').fetchone()[0]==396311
    assert abs(c.execute('SELECT SUM(monthly_revenue) FROM monthly_performance WHERE month>="2025-01-01"').fetchone()[0]-107006933.85)<.01
    r=pd.read_sql_query('SELECT * FROM gym_recommendations',c)
    assert r.action.value_counts().to_dict()=={'DEFENSIVE / INVESTIGATE':38,'HOLD PRICE':26,'RAISE £1':10,'TEST FIRST':5,'RAISE £2':1}
    p=pd.read_sql_query('SELECT * FROM recommendation_portfolio WHERE variant="base" AND "case"="Base"',c)
    assert abs(p.iloc[0].incremental_revenue-148618.48)<.01
    assert ((r.action=='TEST FIRST') & (r.proposed_increment!=0)).sum()==0
    assert c.execute('SELECT COUNT(*) FROM experiment_estimates WHERE population="Repeat repricing" AND (lower IS NOT NULL OR upper IS NOT NULL)').fetchone()[0]==0
    dec=pd.read_sql_query('SELECT DISTINCT checkpoint_months,population_decision FROM experiment_monitoring WHERE simulation="Main" AND population="First repricing"',c).set_index('checkpoint_months')
    assert dec.loc[6,'population_decision']=='EXTEND TEST' and dec.loc[12,'population_decision']=='STOP'
    bridge=pd.read_csv(BUILD/'outputs/01_membership_bridge.csv')
    assert bridge.bridge_residual.eq(0).all() and bridge.continuity_residual.dropna().eq(0).all()
    query=pd.read_csv(BUILD/'outputs/14_conditional_portfolios.csv')
    saved=read('recommendation_portfolio')
    joined=query.merge(saved,on=['variant','case'],suffixes=('_sql','_saved'),validate='one_to_one')
    for sql_col,saved_col in [('annual_revenue','monthly_revenue'),('incremental_revenue','incremental_revenue'),('month12_members','month12_members'),('member_difference','member_difference')]:
        left=sql_col+'_sql' if sql_col in saved else sql_col
        right=saved_col+'_saved' if saved_col in query else saved_col
        assert np.max(np.abs(joined[left]-joined[right]))<.01,(sql_col,'saved portfolio parity')
    for col in ['churn_rate','conversion_rate']:assert np.max(np.abs(joined[col+'_sql']-joined[col+'_saved']))<1e-9
    cohorts=read('cohorts')
    for days,offset in [(30,1),(90,3),(180,6)]:
        mature=cohorts.observation_months>offset
        assert cohorts.loc[~mature,f'customers_remaining_{days}d'].isna().all()
        assert cohorts.loc[mature,f'customers_remaining_{days}d'].notna().all()
    for months in [6,12]:
        mature=cohorts.observation_months>=months
        assert cohorts.loc[~mature,f'revenue_{months}_month'].isna().all()
        assert cohorts.loc[mature,f'revenue_{months}_month'].notna().all()
    try:
        c.execute('DELETE FROM gym_master');raise AssertionError('Read-only database accepted a write')
    except sqlite3.OperationalError:pass
    c.close()
    return ['Zero denominator stays unavailable; valid zero conversion remains zero',
      'Monthly retention and weighted churn use opening-base exposures',
      'Zero prior-period comparisons remain unavailable',
      'Annual/Q4 windows and pp units independently reconciled',
      'Repeated history deduplicates from 252 records to 84 gym-months',
      'Saved Base scenarios contain 320 rows, not all 960 cases',
      'TEST FIRST is mapped to no increase in all portfolios',
      'Complete-portfolio intervals are joined, never summed',
      'Repeat population intervals remain unavailable',
      'Three anchors, action counts and Main decisions match saved evidence',
      'Query connection rejects mutations',
      'All 1920 member bridges and continuity balances are exact',
      'All fifteen site-mapped portfolios match saved revenue and weighted rates',
      'Cohort maturity boundaries preserve unavailable retention and revenue']

def main():
    run();frames=expected();report=[]
    for entry in json.loads((ROOT/'sql/catalog.json').read_text()):
        file=Path(entry['file']);actual=pd.read_csv(BUILD/'outputs'/(file.stem+'.csv'))
        error=check_frame(actual,frames[entry['id']],KEYS[entry['id']])
        report.append({'query':file.name,'rows':len(actual),'columns_checked':len(actual.columns),'maximum_absolute_difference':error,'passed':True})
    result={'status':'pass','queries':report,'boundary_tests':boundaries(),'money_tolerance_gbp':.01,
            'sql_runtime':sqlite3.sqlite_version,'python_independent_expected':'Pandas source aggregation / frozen interface parity'}
    (BUILD/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    return result

if __name__=='__main__':main()
