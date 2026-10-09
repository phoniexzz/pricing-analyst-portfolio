"""Phase 3 descriptive baseline. Never regenerates or edits synthetic observations."""
from pathlib import Path
import csv
import hashlib
import json
import math
import sys

# Optional local plotting dependencies, outside the bundled runtime directory.
sys.path.append(str(Path(__file__).resolve().parent / '.workbook_previews' / 'python_packages'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis'
DATA = ROOT / 'data'
IMAGES = ROOT / 'images'
SHORT = 'This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.'
LONG = 'This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.'
WINDOWS = {'2025': ('2025-01-01', '2025-12-01'), '2024': ('2024-01-01', '2024-12-01'),
           'q4_2025': ('2025-10-01', '2025-12-01'), 'q4_2024': ('2024-10-01', '2024-12-01')}
# Every calculation exposes its numerator or denominator in the derived tables.
METRICS = {
    'months': ('count', 'Number of distinct observed months'),
    'opening_members': ('members', 'Sum of site opening stocks in first reporting month'),
    'closing_members': ('members', 'Sum of site closing stocks in last reporting month'),
    'member_months': ('average-member months', 'Sum of monthly average members'),
    'opening_member_months': ('opening-member months', 'Sum of monthly opening members'),
    'average_members': ('members', 'Average-member months divided by observed months'),
    'subscription_revenue': ('GBP net VAT', 'Sum of net subscription revenue'),
    'joining_fee_revenue': ('GBP net VAT', 'Sum of net joining-fee revenue'),
    'ancillary_revenue': ('GBP net VAT', 'Sum of net ancillary revenue'),
    'total_revenue': ('GBP net VAT', 'Sum of all three revenue components'),
    'average_monthly_revenue': ('GBP net VAT/month', 'Total revenue divided by observed months'),
    'arpmm': ('GBP net VAT/member/month', 'Total revenue divided by average-member months'),
    'subscription_yield': ('GBP net VAT/member/month', 'Subscription revenue divided by average-member months'),
    'standard_member_months': ('average-member months', 'Sum of average Standard members'),
    'standard_subscription_revenue': ('GBP net VAT', 'Sum of Standard subscription revenue'),
    'standard_yield': ('GBP net VAT/member/month', 'Standard subscription revenue divided by Standard average-member months'),
    'new_members': ('activations', 'Sum of joins; rejoining is an activation, not a unique customer'),
    'average_monthly_joins': ('activations/month', 'Total joins divided by observed months'),
    'acquisition_rate': ('decimal rate', 'Joins divided by opening-member months'),
    'opening_base_cancellations': ('exits', 'Exits from the opening population'),
    'same_month_cancellations': ('exits', 'Exits among members joining in the same month'),
    'all_cancellations': ('exits', 'Opening-base exits plus same-month joiner exits'),
    'churn_rate': ('decimal monthly rate', 'Opening-base exits divided by opening-member months'),
    'retention_rate': ('decimal monthly rate', 'One minus exposure-weighted monthly opening-base churn; not annual retention'),
    'qualified_prospects': ('prospects', 'Sum of qualified prospects; leads and trials are not added'),
    'conversion_rate': ('decimal rate', 'Joins divided by qualified prospects'),
    'member_growth': ('decimal growth', 'Last closing stock divided by first opening stock minus one'),
    'occupancy_minutes': ('person-minutes', 'Sum of gym visits times average visit duration'),
    'capacity_minutes': ('comfortable capacity-minutes', 'Sum of opening minutes times static site concurrent capacity'),
    'opening_minutes': ('minutes', 'Sum of site opening minutes'),
    'average_utilisation': ('decimal rate', 'Occupancy minutes divided by comfortable capacity-minutes'),
    'average_monthly_peak': ('decimal rate', 'Opening-time and capacity weighted mean of monthly site peak occupancy estimates'),
    'max_monthly_peak': ('decimal rate', 'Highest monthly site peak estimate within reporting window; not concurrent estate peak'),
    'promotion_gym_months': ('gym-months', 'Count of active promotion gym-months'),
    'promotion_frequency': ('decimal rate', 'Active promotion gym-months divided by observed gym-months'),
    'standard_mix': ('decimal rate', 'Standard average-member months divided by all average-member months'),
    'offpeak_mix': ('decimal rate', 'Off-Peak average-member months divided by all average-member months'),
    'plus_mix': ('decimal rate', 'Plus average-member months divided by all average-member months'),
    'pricing_complaints': ('complaints', 'Sum of recorded pricing complaints'),
    'complaints_per_1000_member_months': ('complaints/1000 average-member months', 'Complaints divided by average-member months times 1000'),
    'marketing_spend': ('GBP', 'Sum of recorded marketing spend; VAT basis of spend unspecified, not netted'),
}


def ratio(a, b):
    return float(a / b) if pd.notna(b) and b != 0 and pd.notna(a) else np.nan


def aggregate(frame):
    f = frame.sort_values(['month', 'gym_id'])
    n = f.month.nunique()
    first, last = f.month.min(), f.month.max()
    s = lambda field: float(f[field].sum())
    m = {'months': int(n), 'opening_members': int(f.loc[f.month.eq(first), 'opening_members'].sum()),
         'closing_members': int(f.loc[f.month.eq(last), 'closing_members'].sum()),
         'member_months': s('average_members'), 'opening_member_months': s('opening_members')}
    for field in ['subscription_revenue', 'joining_fee_revenue', 'ancillary_revenue',
                  'standard_subscription_revenue', 'marketing_spend']:
        m[field] = s(field)
    m['total_revenue'] = s('monthly_revenue')
    m['average_members'] = ratio(m['member_months'], n)
    m['average_monthly_revenue'] = ratio(m['total_revenue'], n)
    m['arpmm'] = ratio(m['total_revenue'], m['member_months'])
    m['subscription_yield'] = ratio(m['subscription_revenue'], m['member_months'])
    m['standard_member_months'] = s('average_standard_members')
    m['standard_yield'] = ratio(m['standard_subscription_revenue'], m['standard_member_months'])
    for field in ['new_members', 'opening_base_cancellations', 'same_month_cancellations', 'qualified_prospects', 'pricing_complaints']:
        m[field] = int(s(field))
    m['all_cancellations'] = int(s('cancelled_members'))
    m['average_monthly_joins'] = ratio(m['new_members'], n)
    m['acquisition_rate'] = ratio(m['new_members'], m['opening_member_months'])
    m['churn_rate'] = ratio(m['opening_base_cancellations'], m['opening_member_months'])
    m['retention_rate'] = 1 - m['churn_rate']
    m['conversion_rate'] = ratio(m['new_members'], m['qualified_prospects'])
    m['member_growth'] = ratio(m['closing_members'], m['opening_members']) - 1
    m['occupancy_minutes'] = float((f.gym_visits * f.average_visit_duration_minutes).sum())
    weights = f.opening_minutes * f.capacity_proxy
    m['capacity_minutes'] = float(weights.sum())
    m['opening_minutes'] = int(s('opening_minutes'))
    m['average_utilisation'] = ratio(m['occupancy_minutes'], m['capacity_minutes'])
    m['average_monthly_peak'] = ratio(float((f.peak_utilisation_pct * weights).sum()), m['capacity_minutes'])
    m['max_monthly_peak'] = float(f.peak_utilisation_pct.max())
    m['promotion_gym_months'] = int(f.promotion_active.sum())
    m['promotion_frequency'] = ratio(m['promotion_gym_months'], len(f))
    for tier, field in [('standard', 'average_standard_members'), ('offpeak', 'average_offpeak_members'), ('plus', 'average_premium_members')]:
        m[tier + '_mix'] = ratio(s(field), m['member_months'])
    m['complaints_per_1000_member_months'] = ratio(m['pricing_complaints'] * 1000, m['member_months'])
    return {k: m[k] for k in METRICS}


def ordered_ids(df, metric, ascending):
    return df.sort_values([metric, 'gym_id'], ascending=[ascending, True], kind='stable').gym_id.tolist()


def main():
    source_files = sorted(DATA.glob('*.csv'))
    # Derived CSVs are excluded on reruns.
    source_files = [p for p in source_files if p.stem not in ['gym_baseline', 'estate_monthly_trend', 'region_year_baseline']]
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    config_hash = hashlib.sha256((OUT / 'generation_config.json').read_bytes()).hexdigest()
    master = pd.read_csv(DATA / 'gym_master.csv')
    monthly = pd.read_csv(DATA / 'monthly_performance.csv', parse_dates=['month'])
    history = pd.read_csv(DATA / 'pricing_history.csv')
    pilots = pd.read_csv(DATA / 'experiment_assignments.csv')
    f = monthly.merge(master[['gym_id', 'capacity_proxy', 'region']], on='gym_id', validate='many_to_one')
    checks = []
    def check(name, condition):
        if not bool(condition):
            raise AssertionError(name)
        checks.append({'check': name, 'status': 'PASS'})
    check('80 mature gyms, unique gym-month keys and exact 24-month coverage',
          len(master) == 80 and master.gym_id.nunique() == 80 and pd.to_datetime(master.opening_date).lt('2022-01-01').all() and len(source_files)==8 and not monthly.duplicated(['gym_id', 'month']).any()
          and all(g.month.tolist() == list(pd.date_range('2024-01-01', '2025-12-01', freq='MS')) for _, g in monthly.sort_values('month').groupby('gym_id')))
    check('All source monthly member bridges reconcile exactly', ((f.opening_members + f.new_members - f.cancelled_members) == f.closing_members).all())
    check('Same-month and opening-base cancellations reconcile', (f.cancelled_members == f.opening_base_cancellations + f.same_month_cancellations).all())
    check('Attendance utilisation reconstructs source occupancy within rounding tolerance', np.allclose(f.utilisation_pct, f.gym_visits*f.average_visit_duration_minutes/(f.opening_minutes*f.capacity_proxy), atol=6e-9, rtol=0))
    check('Source visit duration is constant and monthly opening minutes are common across gyms', f.average_visit_duration_minutes.nunique() == 1 and f.groupby('month').opening_minutes.nunique().eq(1).all())
    rows = []
    for _, site in master.sort_values('gym_id').iterrows():
        g = f.loc[f.gym_id.eq(site.gym_id)]
        r = {k: site[k] for k in ['gym_id', 'gym_name', 'city', 'region', 'location_type', 'capacity_proxy']}
        current = g.loc[g.month.eq(pd.Timestamp('2025-12-01'))].iloc[0]
        r.update(standard_price_dec2025=float(current.standard_price), competitor_price_dec2025=float(current.local_competitor_avg_price),
                 competitor_gap_dec2025=float(current.local_competitor_avg_price-current.standard_price),
                 competitor_count_dec2025=int(current.competitor_count_3km),
                 december_annualised_revenue=float(current.monthly_revenue*12),
                 historical_price_events=int(history.gym_id.eq(site.gym_id).sum()),
                 historical_cash_increase=float(history.loc[history.gym_id.eq(site.gym_id), 'change_amount'].sum()))
        assignment = pilots.loc[pilots.gym_id.eq(site.gym_id)]
        r['pilot_assignment'] = 'Not in pilot' if assignment.empty else str(assignment.iloc[0].test_group)
        r['pilot_pair_id'] = None if assignment.empty else str(assignment.iloc[0].pair_id)
        for window, (start, end) in WINDOWS.items():
            r.update({k+'_'+window: v for k, v in aggregate(g.loc[g.month.between(start, end)]).items()})
        for suffix, now, old in [('yoy', '2025', '2024'), ('q4_yoy', 'q4_2025', 'q4_2024')]:
            for name, metric in [('revenue_growth', 'total_revenue'), ('acquisition_growth', 'new_members'), ('closing_member_growth', 'closing_members')]:
                r[name+'_'+suffix] = ratio(r[metric+'_'+now], r[metric+'_'+old]) - 1
            for metric in ['churn_rate', 'retention_rate', 'conversion_rate']:
                r[metric.replace('_rate', '')+'_change_pp_'+suffix] = 100*(r[metric+'_'+now]-r[metric+'_'+old])
        rows.append(r)
    baseline = pd.DataFrame(rows)
    thresholds = {'churn_upper_quartile': float(baseline.churn_rate_2025.quantile(.75)),
                  'conversion_lower_quartile': float(baseline.conversion_rate_2025.quantile(.25)),
                  'acquisition_growth_lower_quartile': float(baseline.acquisition_growth_yoy.quantile(.25))}
    baseline['high_churn_exception'] = baseline.churn_rate_2025.ge(thresholds['churn_upper_quartile'])
    baseline['weak_conversion_exception'] = baseline.conversion_rate_2025.le(thresholds['conversion_lower_quartile'])
    baseline['declining_acquisition_exception'] = baseline.acquisition_growth_yoy.lt(0) & baseline.acquisition_growth_yoy.le(thresholds['acquisition_growth_lower_quartile'])
    baseline['peak_capacity_exception'] = baseline.max_monthly_peak_2025.ge(1)
    ranks = {}
    for metric in ['total_revenue_2025', 'revenue_growth_yoy', 'member_growth_2025']:
        for direction, ascending in [('highest', False), ('lowest', True)]:
            ids = ordered_ids(baseline, metric, ascending)
            baseline[direction+'_rank_'+metric] = baseline.gym_id.map({gid: i+1 for i, gid in enumerate(ids)})
            ranks[direction+'_'+metric] = ids[:5]
    priority = ['gym_id', 'gym_name', 'city', 'region', 'location_type', 'standard_price_dec2025',
                'competitor_gap_dec2025', 'average_members_2025', 'total_revenue_2025', 'revenue_growth_yoy',
                'arpmm_2025', 'subscription_yield_2025', 'standard_yield_2025', 'member_growth_2025',
                'acquisition_growth_yoy', 'churn_rate_2025', 'conversion_rate_2025', 'average_utilisation_2025',
                'max_monthly_peak_2025', 'high_churn_exception', 'weak_conversion_exception',
                'declining_acquisition_exception', 'peak_capacity_exception']
    baseline = baseline[priority + [c for c in baseline if c not in priority]]
    trend = pd.DataFrame([dict(month=month.strftime('%Y-%m-%d'), **aggregate(g)) for month, g in f.groupby('month', sort=True)])
    regional = pd.DataFrame([dict(region=region, year=int(year), gym_count=g.gym_id.nunique(), **aggregate(g)) for (region, year), g in f.groupby(['region', f.month.dt.year], sort=True)])
    annual = {str(y): aggregate(f.loc[f.month.dt.year.eq(y)]) for y in [2024, 2025]}
    q4 = {str(y): aggregate(f.loc[f.month.dt.year.eq(y) & f.month.dt.month.ge(10)]) for y in [2024, 2025]}
    a, b = annual['2024'], annual['2025']
    bridge = {'2024_revenue': a['total_revenue'],
              'member_volume_contribution': 12*(b['average_members']-a['average_members'])*a['arpmm'],
              'total_arpmm_contribution': 12*b['average_members']*(b['arpmm']-a['arpmm']),
              '2025_revenue': b['total_revenue']}
    bridge['difference'] = bridge['2024_revenue']+bridge['member_volume_contribution']+bridge['total_arpmm_contribution']-bridge['2025_revenue']
    check('80 gym, 24 estate-month and 16 region-year derived records with unique keys', len(baseline)==80 and len(trend)==24 and len(regional)==16 and not regional.duplicated(['region','year']).any())
    for y in [2024, 2025]:
        agg = annual[str(y)]
        for field in ['total_revenue','subscription_revenue','joining_fee_revenue','ancillary_revenue','new_members','opening_base_cancellations','same_month_cancellations','all_cancellations','qualified_prospects','member_months','opening_member_months','opening_members','closing_members']:
            check(f'{y} site and region totals reconcile: {field}', math.isclose(float(baseline[field+'_'+str(y)].sum()), agg[field], abs_tol=.01) and math.isclose(float(regional.loc[regional.year.eq(y),field].sum()), agg[field], abs_tol=.01))
        check(f'{y} revenue components and annual member bridge reconcile', abs(agg['total_revenue']-sum(agg[k] for k in ['subscription_revenue','joining_fee_revenue','ancillary_revenue']))<.01 and agg['opening_members']+agg['new_members']-agg['all_cancellations']==agg['closing_members'])
        check(f'{y} weighted ARPMM and churn independently reconstruct from raw CSV', math.isclose(agg['arpmm'], monthly.loc[monthly.month.dt.year.eq(y),'monthly_revenue'].sum()/monthly.loc[monthly.month.dt.year.eq(y),'average_members'].sum(), abs_tol=1e-10) and math.isclose(agg['churn_rate'],monthly.loc[monthly.month.dt.year.eq(y),'opening_base_cancellations'].sum()/monthly.loc[monthly.month.dt.year.eq(y),'opening_members'].sum(),abs_tol=1e-12))
    check('Exact annual revenue bridge within GBP 0.01', abs(bridge['difference'])<.01)
    check('Q4 windows contain exactly October, November and December', all(v['months']==3 for v in q4.values()) and baseline.months_q4_2025.eq(3).all() and baseline.months_2025.eq(12).all())
    check('Percentage-point arithmetic and retention identities', np.allclose(baseline.churn_change_pp_yoy,100*(baseline.churn_rate_2025-baseline.churn_rate_2024)) and np.allclose(baseline.retention_rate_2025+baseline.churn_rate_2025,1))
    check('Zero and missing denominators are unavailable, positive denominator preserves zero numerator', math.isnan(ratio(1,0)) and math.isnan(ratio(1,np.nan)) and ratio(0,2)==0)
    fixture = pd.DataFrame({'gym_id':['B','A','C'],'metric':[10,10,5]})
    check('Ranking ties resolve deterministically by gym ID', ordered_ids(fixture,'metric',False)==['A','B','C'] and ordered_ids(fixture,'metric',True)==['C','A','B'])
    check('Annual site weighted occupancy matches opening-time-weighted source utilisation', all(abs(row.average_utilisation_2025-np.average(f.loc[f.gym_id.eq(row.gym_id)&f.month.dt.year.eq(2025),'utilisation_pct'],weights=f.loc[f.gym_id.eq(row.gym_id)&f.month.dt.year.eq(2025),'opening_minutes']))<6e-9 for _,row in baseline.iterrows()))
    check('Calendar boundaries connect 2024 closing stocks to 2025 opening stocks', (baseline.closing_members_2024==baseline.opening_members_2025).all())
    for name, df in [('gym_baseline',baseline),('estate_monthly_trend',trend),('region_year_baseline',regional)]:
        df.to_csv(DATA/(name+'.csv'),index=False,float_format='%.12f',na_rep='',lineterminator='\n')
        reload = pd.read_csv(DATA/(name+'.csv'))
        check(f'{name} saved CSV values match calculated outputs', reload.shape==df.shape and all(np.allclose(reload[c],df[c],atol=1e-8,rtol=1e-12,equal_nan=True) if pd.api.types.is_numeric_dtype(df[c]) else reload[c].fillna('').astype(str).equals(df[c].fillna('').astype(str)) for c in df))
    check('All eight source CSVs and generation configuration remain unchanged', before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files} and config_hash==hashlib.sha256((OUT/'generation_config.json').read_bytes()).hexdigest())
    result = {'annual':annual,'q4':q4,'bridge':bridge,'thresholds':thresholds,'rankings':ranks,
              'exception_counts':{c:int(baseline[c].sum()) for c in baseline if c.endswith('_exception')},
              'sources_sha256':before,'generation_config_sha256':config_hash,'checks':checks,
              'derived_rows':{'gym_baseline':len(baseline),'estate_monthly_trend':len(trend),'region_year_baseline':len(regional)}}
    (OUT/'baseline_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    write_dictionary(baseline,trend,regional)
    make_visuals(baseline,trend,bridge,thresholds)
    write_report(result,baseline)
    # Typed handoff for Artifact Tool. Only the small source tables required by Phase 3.
    dictionary = pd.read_csv(OUT/'data_dictionary.csv')
    payload = {}
    for table in ['gym_master','monthly_performance','pricing_history','experiment_assignments']:
        raw = pd.read_csv(DATA/(table+'.csv'))
        date_fields = dictionary.loc[dictionary.table.eq(table)&dictionary.data_type.eq('date'),'field'].tolist()
        payload[table] = {'columns':raw.columns.tolist(),'data':json.loads(raw.to_json(orient='values',double_precision=15)),'dates':date_fields}
    for table,df in [('gym_baseline',baseline),('estate_monthly_trend',trend),('region_year_baseline',regional)]:
        payload[table] = {'columns':df.columns.tolist(),'data':json.loads(df.to_json(orient='values',double_precision=15))}
    payload['result'] = result
    (OUT/'.workbook_previews'/'phase3_payload.json').write_text(json.dumps(payload),encoding='utf-8')
    print(json.dumps({'rows':result['derived_rows'],'checks':len(checks),'annual_revenue_2025':b['total_revenue'],'annual_revenue_growth':b['total_revenue']/a['total_revenue']-1,'bridge':bridge,'exceptions':result['exception_counts']},indent=2))


def field_definition(field):
    for window in sorted(WINDOWS,key=len,reverse=True):
        suffix = '_'+window
        if field.endswith(suffix) and field[:-len(suffix)] in METRICS:
            unit, definition = METRICS[field[:-len(suffix)]]
            return unit, window, definition
    if field in METRICS:
        return METRICS[field][0], 'Row reporting period', METRICS[field][1]
    if '_rank_' in field:
        return 'ordinal rank','2025','Rank by named metric, gym_id ascending breaks ties; 1 is first in indicated direction'
    if field.endswith('_exception'):
        defs = {'high_churn_exception':'2025 churn >= estate 75th percentile', 'weak_conversion_exception':'2025 conversion <= estate 25th percentile',
                'declining_acquisition_exception':'Year-on-year acquisition growth is negative and <= estate 25th percentile', 'peak_capacity_exception':'Maximum monthly 2025 peak utilisation >= 1'}
        return 'boolean','2025',defs[field]+'; investigation indicator, not pricing action'
    if 'change_pp' in field:
        return 'percentage points','Q4 YoY' if field.endswith('q4_yoy') else '2025 versus 2024','100 times current minus matching prior-period rate'
    if field.endswith('_yoy'):
        return 'decimal growth','Q4 YoY' if field.endswith('q4_yoy') else '2025 versus 2024','Current matching-period metric / prior-period metric minus 1; unavailable if prior is zero'
    defs = {'gym_id':('identifier','Stable gym key'), 'gym_name':('text','Fictional Northstar gym name'), 'city':('text','UK city name'),
            'region':('text','Static region'), 'location_type':('text','Static location category'), 'capacity_proxy':('concurrent members','Static comfortable concurrent occupancy capacity'),
            'standard_price_dec2025':('GBP gross VAT','December 2025 Standard advertised monthly price'),
            'competitor_price_dec2025':('GBP gross VAT','December 2025 fictional local competitor mean advertised recurring price; excludes fees and introductory promotions'),
            'competitor_gap_dec2025':('GBP gross VAT','December competitor mean minus Northstar Standard price; positive means Northstar cheaper'),
            'competitor_count_dec2025':('competitors','Active competitors within 3 km in December'),
            'december_annualised_revenue':('GBP net VAT/year run-rate','December total revenue times 12; seasonal annualisation, not a forecast'),
            'historical_price_events':('events','Count of observed Standard increases in 2024-2025'),
            'historical_cash_increase':('GBP gross VAT','Sum of observed Standard headline cash increases in 2024-2025'),
            'pilot_assignment':('category','Treatment, Control, or Not in pilot; descriptive annotation only'),
            'pilot_pair_id':('identifier','Matched-pair identifier; blank when not assigned'), 'month':('ISO date','First day of estate observation month'),
            'year':('calendar year','Year of regional reporting period'), 'gym_count':('gyms','Number of distinct gyms in region-year')}
    unit, definition = defs[field]
    return unit,'Static, dated snapshot or named row period',definition


def write_dictionary(baseline,trend,regional):
    with (OUT/'baseline_metric_dictionary.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['table','field','key','unit','window','provenance','null_meaning','definition'])
        writer.writeheader()
        for table,frame,key in [('gym_baseline',baseline,'gym_id'),('estate_monthly_trend',trend,'month'),('region_year_baseline',regional,'region + year')]:
            for field in frame:
                unit,window,definition=field_definition(field)
                writer.writerow(dict(table=table,field=field,key=key,unit=unit,window=window,provenance='Derived from fixed synthetic observations',null_meaning='Blank means missing observation, zero/missing denominator, or not applicable pilot pair; never zero imputation',definition=definition))


def make_visuals(baseline,trend,bridge,thresholds):
    IMAGES.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig, axes = plt.subplots(1,2,figsize=(12,4.3))
    for y,color,style in [('2024','#829AB1','--'),('2025','#243B53','-')]:
        g=trend.loc[trend.month.str.startswith(y)]
        axes[0].plot(range(1,13),g.average_members,color=color,linestyle=style,label=y,linewidth=2)
        axes[1].plot(range(1,13),g.total_revenue/1e6,color=color,linestyle=style,label=y,linewidth=2)
    for ax,title in zip(axes,['Average estate members','Monthly total revenue (GBP million, net VAT)']):
        ax.set(title=title,xticks=range(1,13),xticklabels=['J','F','M','A','M','J','J','A','S','O','N','D'])
        ax.grid(axis='y',alpha=.2); ax.legend(frameon=False)
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{v/1000:.0f}k'))
    fig.suptitle('Compare matching months before interpreting growth',fontsize=13,x=.02,ha='left')
    fig.tight_layout(); fig.savefig(IMAGES/'baseline_seasonal_trends.png',dpi=170,bbox_inches='tight'); plt.close(fig)
    start=bridge['2024_revenue']; volume=bridge['member_volume_contribution']; yield_=bridge['total_arpmm_contribution']; end=bridge['2025_revenue']
    fig,ax=plt.subplots(figsize=(9,4.5))
    heights=[start,abs(volume),abs(yield_),end]; bottoms=[0,min(start,start+volume),min(start+volume,end),0]
    colors=['#829AB1','#D97706' if volume<0 else '#3C806B','#D97706' if yield_<0 else '#3C806B','#243B53']
    ax.bar(range(4),np.array(heights)/1e6,bottom=np.array(bottoms)/1e6,color=colors,width=.6)
    for i,value in enumerate([start,volume,yield_,end]):
        ax.text(i,(bottoms[i]+heights[i])/1e6+.12,('+' if 0<i<3 and value>=0 else '-' if value<0 else '')+f'£{abs(value)/1e6:.2f}m',ha='center',fontsize=10)
    ax.set(xticks=range(4),xticklabels=['2024 revenue','Member volume','Total ARPMM','2025 revenue'],ylabel='GBP million, net VAT',title='Annual revenue change: member volume and realised revenue yield')
    ax.set_ylim(0,max(start,end)/1e6*1.1); ax.grid(axis='y',alpha=.2)
    fig.text(.02,.01,'Interaction allocated to ARPMM. ARPMM includes tier mix, joining fees and ancillary income.',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,1)); fig.savefig(IMAGES/'baseline_revenue_bridge.png',dpi=170,bbox_inches='tight'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5))
    exception=baseline[['high_churn_exception','weak_conversion_exception','declining_acquisition_exception','peak_capacity_exception']].any(axis=1)
    ax.scatter(baseline.loc[~exception,'acquisition_growth_yoy'],baseline.loc[~exception,'churn_rate_2025'],color='#829AB1',label='Other sites',s=36)
    ax.scatter(baseline.loc[exception,'acquisition_growth_yoy'],baseline.loc[exception,'churn_rate_2025'],color='#D97706',label='One or more investigation indicators',s=40)
    ax.axhline(thresholds['churn_upper_quartile'],color='#243B53',ls='--',lw=1,label='Upper-quartile churn')
    ax.axvline(0,color='#94A3B8',lw=1)
    for _,r in baseline.nsmallest(3,'acquisition_growth_yoy').iterrows():
        ax.annotate(r.gym_id,(r.acquisition_growth_yoy,r.churn_rate_2025),xytext=(4,6),textcoords='offset points',fontsize=9)
    ax.xaxis.set_major_formatter(PercentFormatter(1)); ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set(xlabel='Acquisition growth, 2025 versus 2024',ylabel='2025 exposure-weighted monthly churn',title='Investigate weak recruitment alongside opening-base churn')
    ax.legend(frameon=False,fontsize=8); ax.grid(alpha=.15)
    fig.tight_layout(); fig.savefig(IMAGES/'baseline_acquisition_churn.png',dpi=170,bbox_inches='tight'); plt.close(fig)


def write_report(result,baseline):
    a,b=result['annual']['2024'],result['annual']['2025']; qa,qb=result['q4']['2024'],result['q4']['2025']
    money=lambda v:('-' if v<0 else '')+f'£{abs(v):,.0f}'
    pct=lambda v:f'{v:.2%}'
    lines=['# Northstar Fitness — Commercial Baseline','',SHORT,'',
           '## Business purpose','', 'Assess 2025 revenue, membership, acquisition, retention and capacity before evaluating further Standard price increases. Higher realised yield can outweigh weaker member performance, but the annual result must be examined alongside recent trading. This baseline directs investigation and Phase 4 headroom analysis. It does not estimate causal price effects or assign site actions.','',
           '## Estate results','', '| Measure | 2024 | 2025 | Change |','|---|---:|---:|---:|']
    for label,field in [('Total net revenue','total_revenue'),('Net subscription revenue','subscription_revenue'),('Net joining-fee revenue','joining_fee_revenue'),('Net ancillary revenue','ancillary_revenue')]:
        lines.append(f'| {label} | {money(a[field])} | {money(b[field])} | {pct(b[field]/a[field]-1)} |')
    for label,field in [('Average members','average_members'),('Closing members','closing_members'),('Acquisitions','new_members')]:
        lines.append(f'| {label} | {a[field]:,.0f} | {b[field]:,.0f} | {pct(b[field]/a[field]-1)} |')
    for label,field in [('Total ARPMM','arpmm'),('Subscription yield','subscription_yield'),('Standard subscription yield','standard_yield')]:
        lines.append(f'| {label} | £{a[field]:.2f} | £{b[field]:.2f} | {pct(b[field]/a[field]-1)} |')
    for label,field in [('Monthly churn','churn_rate'),('Conversion','conversion_rate')]:
        lines.append(f'| {label} | {pct(a[field])} | {pct(b[field])} | {100*(b[field]-a[field]):+.2f} pp |')
    bridge=result['bridge']
    lines += ['',f'2025 net revenue changed by **{money(b["total_revenue"]-a["total_revenue"])} ({pct(b["total_revenue"]/a["total_revenue"]-1)})**. The exact descriptive bridge attributes {money(bridge["member_volume_contribution"])} to average member volume and {money(bridge["total_arpmm_contribution"])} to total ARPMM. The latter includes membership mix, joining fees and ancillary income, with the interaction allocated to ARPMM. It is not a causal measure of repricing benefit.','',
              f'2025 membership moved from {b["opening_members"]:,} opening to {b["closing_members"]:,} closing, with {b["new_members"]:,} activations and {b["all_cancellations"]:,} exits. Activations can include rejoiners. Neither summed monthly stocks nor activations are unique-customer counts.','',
              '## Recent trading','',f'Q4 revenue changed {pct(qb["total_revenue"]/qa["total_revenue"]-1)} year on year, acquisitions changed {pct(qb["new_members"]/qa["new_members"]-1)}, and monthly opening-base churn changed {100*(qb["churn_rate"]-qa["churn_rate"]):+.2f} pp. December annualised revenue is {money(baseline.december_annualised_revenue.sum())}, compared with actual 2025 revenue of {money(b["total_revenue"])}. December × 12 is a seasonal run-rate illustration, not a forecast.','',
              '## Site comparisons','', 'Revenue scale, revenue growth and member growth answer different questions. The following rankings use 2025 annual revenue, matching-year revenue growth, and 2025 opening-to-closing member growth. Ties resolve by gym ID.','']
    for key,ids in result['rankings'].items():
        metric=key.replace('highest_','').replace('lowest_',''); label=key.replace('_',' ')
        lines += [f'### {label}','', '| Gym | City | Result |','|---|---|---:|']
        for gid in ids:
            r=baseline.loc[baseline.gym_id.eq(gid)].iloc[0]
            value=money(r[metric]) if metric=='total_revenue_2025' else pct(r[metric])
            lines.append(f'| {gid} | {r.city} | {value} |')
        lines.append('')
    t=result['thresholds']; e=result['exception_counts']
    lines += ['## Investigation indicators','',
              f'- High churn: {e["high_churn_exception"]} sites at or above the 2025 upper quartile ({pct(t["churn_upper_quartile"])} monthly).',
              f'- Weak conversion: {e["weak_conversion_exception"]} sites at or below the lower quartile ({pct(t["conversion_lower_quartile"])}).',
              f'- Declining acquisition: {e["declining_acquisition_exception"]} sites with negative year-on-year growth at or below the lower quartile ({pct(t["acquisition_growth_lower_quartile"])}).',
              f'- Peak capacity: {e["peak_capacity_exception"]} sites with a monthly peak estimate at or above 100% of comfortable concurrent capacity.',
              '', 'Flags overlap and reflect relative estate performance. They are not pricing actions, headroom scores or rollout guardrails. Revenue growth alone does not establish that a site can sustain another increase. Historical targeted repricing and pilot assignments are visible as context, without estimating treatment effects here.','',
              '## Commercial visuals','',
              '![Matching-month membership and revenue](../images/baseline_seasonal_trends.png)','', 'Decision supported: establish whether changes persist across matching seasonal periods.','',
              '![Annual revenue bridge](../images/baseline_revenue_bridge.png)','', 'Decision supported: establish whether member volume or total realised yield explains the annual revenue change.','',
              '![Acquisition and churn](../images/baseline_acquisition_churn.png)','', 'Decision supported: prioritise investigation of weaker recruitment and retention before assessing further price changes.','',
              '## Interpretation and limits','',
              'Churn is an opening-member-exposure-weighted monthly rate. Retention is one minus that monthly churn, not annual survival or cohort retention. Average members use monthly midpoint exposure. Average occupancy and estimated monthly peak occupancy measure different capacity conditions. Estate and regional occupancy are weighted by opening time and capacity. Complaints use average-member months as exposure.','',
              'Competitor gaps compare advertised recurring Standard prices including VAT, excluding joining fees and introductory promotions. All competitor observations are fictional. Revenue excludes assumed 20% VAT. Historical associations are descriptive and confounded by seasonality, marketing, promotions, competitor changes and tier mix. Revenue is not profit.','',
              LONG,'', 'Phase 4 will assess pricing headroom using this baseline.']
    location=lines.index('## Commercial visuals')
    cases=['## Sites to investigate','']
    weak=baseline.loc[baseline.high_churn_exception & baseline.declining_acquisition_exception].sort_values(['acquisition_growth_yoy','gym_id']).head(3)
    for _,r in weak.iterrows():
        cases.append(f'- {r.gym_id} ({r.city}): acquisitions changed {pct(r.acquisition_growth_yoy)}, with {pct(r.churn_rate_2025)} monthly churn. Review recruitment and retention together before assessing another increase.')
    for _,r in baseline.loc[baseline.peak_capacity_exception].iterrows():
        cases.append(f'- {r.gym_id} ({r.city}): maximum monthly peak utilisation reached {pct(r.max_monthly_peak_2025)}. Review service capacity alongside pricing analysis.')
    cases+=['', 'Annual acquisition changed only slightly, while Q4 recruitment weakened more. This makes the recent-period comparison useful even though annual revenue increased. Neither pattern identifies the cause without subsequent historical-response analysis.','']
    lines[location:location]=cases
    (OUT/'baseline_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    check_lines=['# Phase 3 data validation','',f'{len(result["checks"])} automated data checks passed. Workbook verification is recorded separately in baseline_workbook_verification.json.','']
    check_lines += [f'- PASS: {c["check"]}' for c in result['checks']]
    check_lines += ['', 'Source SHA-256 hashes and configuration hash are stored in baseline_results.json. Re-running the script must reproduce identical derived CSV hashes. Workbook visual review and saved-file checks are required before Phase 3 completion.']
    (OUT/'baseline_validation.md').write_text('\n'.join(check_lines)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
