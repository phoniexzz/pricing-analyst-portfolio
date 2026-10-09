"""Phase 7 rules and portfolios. No new behavioural parameters or source mutation."""
import copy
import hashlib
import json
import math
import sys
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent/'.workbook_previews'/'python_packages'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import append_scenario_sheets as ooxml
from refresh_scenario_comparison import cells

ROOT=Path(__file__).resolve().parents[1]; AN=ROOT/'analysis'; DATA=ROOT/'data'
PRE=AN/'.workbook_previews'/'phase7'; P6=AN/'.workbook_previews'/'phase6'
CFG=json.loads((AN/'recommendation_config.json').read_text(encoding='utf-8'))
OUTPUTS=['gym_recommendations','recommendation_sensitivity','recommendation_portfolio']
D1='This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.'
D2='This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.'
CHECKS=[]
FLAGS=['high_churn_exception','weak_conversion_exception','declining_acquisition_exception','peak_capacity_exception']
CONTEXT=['gym_name','city','region','score','rank','band','segment','sensitive','max_absolute_rank_movement','alternative_band_change_count','threshold_sensitive','competitor_gap_dec2025','caution_flag_count',*FLAGS,'churn_rate_2025','conversion_rate_2025','acquisition_growth_yoy','acquisition_growth_q4_yoy','churn_change_pp_q4_yoy','conversion_change_pp_q4_yoy','average_monthly_peak_2025','max_monthly_peak_2025','complaints_per_1000_member_months_2025','promotion_frequency_2025','marketing_spend_2025','standard_mix_2025','offpeak_mix_2025','plus_mix_2025','student_population_pct','historical_price_events','pilot_assignment','pilot_pair_id']
REQUIRED=['incremental_revenue','post_increase_competitor_gap','member_impact','incremental_revenue_lower','incremental_revenue_upper','old_standard_price']
SELECTED=['incremental_revenue','member_difference','member_impact','acquisition_difference','standard_acquisition_impact','incumbent_churn_change_pp','downgrade_change_pp','conversion_change_pp','incremental_revenue_lower','incremental_revenue_upper','month12_members','subscription_yield','standard_yield','arpmm','pricing_complaints','annualised_exit_run_rate','post_increase_competitor_gap']

def check(name,ok):
    if not bool(ok):raise AssertionError(name)
    CHECKS.append(name)

def finite(x):return isinstance(x,(int,float,np.integer,np.floating)) and not isinstance(x,(bool,np.bool_)) and math.isfinite(float(x))
def safe(n,d):return n/d if finite(d) and d!=0 else np.nan
def hashes():
    paths=sorted(p for p in DATA.glob('*.csv') if p.stem not in OUTPUTS)
    paths += [AN/f for f in ['generation_config.json','headroom_config.json','response_config.json','scenario_config.json']]
    paths += [P6/'payload.json',P6/'joint_draws.npz']
    return {str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def policy(variant='base',override=None):
    p=dict(member_loss_limit=CFG['member_loss_limit'],minimum_gap=CFG['minimum_post_increase_competitor_gap'],test_repeats=CFG['test_repeat_repricing'])
    if override:p.update(override)
    if variant=='member_limit_3pct':p['member_loss_limit']=.03
    if variant=='member_limit_7pct':p['member_loss_limit']=.07
    if variant=='competitor_buffer_1gbp':p['minimum_gap']=1.
    if variant=='allow_repeat_repricing':p['test_repeats']=False
    return p

def candidate(base,down,sens,p):
    missing=[f'Base {f}' for f in REQUIRED if not finite(base.get(f))]
    missing += [f'Downside {f}' for f in ['incremental_revenue','member_impact'] if not finite(down.get(f))]
    missing += [v for v in CFG['nonzero_sensitivities'] if v not in sens or not finite(sens[v].get('incremental_revenue'))]
    missing += ['repeat status'] if not isinstance(base.get('repeated_repricing'),(bool,np.bool_)) else []
    if missing:return dict(complete=False,plausible=False,qualified=False,failed_gates='Missing '+', '.join(missing),missing='; '.join(missing))
    plausible=base['incremental_revenue']>0 and base['post_increase_competitor_gap']>=p['minimum_gap']
    gates={'Base revenue positive':base['incremental_revenue']>0,'Post-increase competitor gap':base['post_increase_competitor_gap']>=p['minimum_gap'],
           'Downside revenue positive':down['incremental_revenue']>0,'Downside member limit':down['member_impact']>=-p['member_loss_limit'],
           'Conditional lower bound positive':base['incremental_revenue_lower']>0,
           'Every nonzero sensitivity positive':all(sens[v]['incremental_revenue']>0 for v in CFG['nonzero_sensitivities'])}
    return dict(complete=True,plausible=plausible,qualified=all(gates.values()),failed_gates='; '.join(k for k,v in gates.items() if not v),missing='')

def classify(h,options,p):
    flag_missing=any(not isinstance(h.get(f),(bool,np.bool_)) for f in FLAGS)
    candidates={inc:candidate(*v,p) for inc,v in options.items()}
    missing=flag_missing or any(not q['complete'] for q in candidates.values())
    caution=any(bool(h.get(f,False)) for f in FLAGS)
    if missing or caution:
        return 'DEFENSIVE / INVESTIGATE',0,0,'R1_MISSING' if missing else 'R1_CAUTION',candidates
    plausible=[inc for inc,q in candidates.items() if q['plausible']]
    qualified=[inc for inc,q in candidates.items() if q['qualified']]
    if not plausible:return 'HOLD PRICE',0,0,'R3_NO_PLAUSIBLE',candidates
    if not qualified:return 'TEST FIRST',0,min(plausible),'R6_FAILED_QUALIFICATION',candidates
    best=sorted(qualified,key=lambda inc:(-options[inc][0]['incremental_revenue'],inc))[0]
    if p['test_repeats'] and options[best][0]['repeated_repricing']:
        return 'TEST FIRST',0,best,'R6_REPEAT_REPRICING',candidates
    return f'RAISE £{best}',best,0,'R7_CONDITIONAL_RAISE',candidates

class Evidence:
    def __init__(self):
        self.p=json.loads((P6/'payload.json').read_text(encoding='utf-8'))
        frame=lambda k:pd.DataFrame(self.p[k]['data'],columns=self.p[k]['columns'])
        self.s=frame('comparisons');self.t=frame('sensitivity');self.m=frame('monthly')
        self.h=pd.read_csv(DATA/'gym_headroom.csv').sort_values('gym_id').reset_index(drop=True)
        self.g=pd.read_csv(DATA/'gym_master.csv').set_index('gym_id')
        self.ids=self.h.gym_id.tolist();self.sm={(r['gym_id'],int(r['price_increment']),r['case']):r for r in self.s.to_dict('records')}
        self.tm={(r['gym_id'],int(r['price_increment']),r['variant']):r for r in self.t.to_dict('records')}
        z=np.load(P6/'joint_draws.npz');self.draws=z['outcomes'];self.draw_fields=z['fields'].tolist();self.params=z['params'];z.close()
        check('Shared 10000 whole-pair draws retained',self.draws.shape==(10000,4,81,8))
        check('Site draw ordering matches sorted stable IDs',self.p['gyms']['data'] and self.ids==pd.DataFrame(self.p['gyms']['data'],columns=self.p['gyms']['columns']).gym_id.tolist())
        check('Complete unique source scenario keys',len(self.sm)==960 and len(self.tm)==2268)
        check('All source evidence finite shared draws',np.isfinite(self.draws).all())
    def options(self,gid):return {i:(self.sm[gid,i,'Base'],self.sm[gid,i,'Downside'],{v:self.tm[gid,i,v] for v in CFG['nonzero_sensitivities']}) for i in [1,2]}
    def recommend(self,variant,override=None):
        p=policy(variant,override);rows=[]
        for h in self.h.to_dict('records'):
            gid=h['gym_id'];options=self.options(gid);action,inc,test,rule,qs=classify(h,options,p)
            chosen=inc or test;ref=self.sm[gid,chosen,'Base'];down=self.sm[gid,chosen,'Downside'];cf=self.sm[gid,0,'Base']
            r=dict(gym_id=gid,variant=variant,action=action,proposed_increment=inc,provisional_test_increment=test,assessment_increment=chosen,
                current_standard_price=cf['old_standard_price'],proposed_standard_price=cf['old_standard_price']+inc,
                provisional_test_price=cf['old_standard_price']+test if test else np.nan,rule_id=rule,**{f:h[f] for f in CONTEXT},
                member_loss_limit=p['member_loss_limit'],minimum_post_increase_competitor_gap=p['minimum_gap'],test_repeat_repricing=p['test_repeats'],
                repeated_repricing=self.sm[gid,1,'Base']['repeated_repricing'],counterfactual_revenue=cf['monthly_revenue'],counterfactual_month12_members=cf['month12_members'],
                selected_downside_revenue=down['incremental_revenue'],selected_downside_member_impact=down['member_impact'],
                evidence_status='Conditional recommendation; controlled testing required before wider implementation; revenue is not profit')
            for f in SELECTED:r['selected_'+f]=ref[f]
            for i,q in qs.items():
                b,d,t=options[i]
                r.update({f'plus{i}_{f}':q[f] for f in ['complete','plausible','qualified','failed_gates']})
                r.update({f'plus{i}_base_revenue':b['incremental_revenue'],f'plus{i}_downside_revenue':d['incremental_revenue'],f'plus{i}_downside_member_impact':d['member_impact'],
                    f'plus{i}_revenue_lower':b['incremental_revenue_lower'],f'plus{i}_revenue_upper':b['incremental_revenue_upper'],f'plus{i}_post_competitor_gap':b['post_increase_competitor_gap'],
                    f'plus{i}_worst_sensitivity_revenue':min(t[v]['incremental_revenue'] for v in CFG['nonzero_sensitivities']),
                    f'plus{i}_base_member_impact':b['member_impact']})
            b3=self.sm[gid,3,'Base'];plus=self.g.loc[gid,'current_premium_price']
            r.update(plus3_base_revenue=b3['incremental_revenue'],plus3_base_member_impact=b3['member_impact'],plus3_standard_price=b3['new_standard_price'],unchanged_plus_price=plus,
                     plus3_standard_plus_parity=abs(b3['new_standard_price']-plus)<1e-9)
            problems=[]
            for flag,text in zip(FLAGS,['Investigate incumbent retention and member value','Investigate qualified-prospect conversion and relative value','Investigate recruitment decline, marketing and competitor changes','Investigate peak service capacity and member experience']):
                if h[flag]:problems.append(text)
            if rule=='R1_MISSING':problems.append('Restore missing decision evidence before repricing')
            r['investigation_needed']='; '.join(problems)
            if rule.startswith('R1'):reason=r['investigation_needed']
            elif rule=='R3_NO_PLAUSIBLE':reason='Neither £1 nor £2 preserves the required competitor gap with positive base revenue'
            elif rule=='R6_REPEAT_REPRICING':reason=f'£{test} passes financial gates; repeat repricing requires controlled evidence'
            elif rule=='R6_FAILED_QUALIFICATION':reason=f'Test £{test} provisionally; failed gates: '+qs[test]['failed_gates']
            else:reason=f'£{inc} gives the higher qualifying base revenue; downside member loss {abs(down["member_impact"]):.2%}, post-increase competitor gap £{ref["post_increase_competitor_gap"]:.2f}'
            r['explanation']=reason
            limits=['Shared local +£2 pilot response; no site elasticity; conditional parameter intervals exclude trading and transport uncertainty']
            if chosen==1:limits.append('£1 is an extrapolation from +£2 evidence')
            if r['repeated_repricing']:limits.append('Repeat repricing tolerance not identified')
            if h['competitor_gap_dec2025']<=0:limits.append('Outside pilot positive-gap value evidence')
            if h['sensitive']:limits.append('Headroom ranking or band sensitive to specification')
            if r['plus3_standard_plus_parity']:limits.append('+£3 equals unchanged Plus price; upgrades not modelled')
            r['evidence_limitations']='; '.join(limits);rows.append(r)
        return pd.DataFrame(rows)

    def portfolio(self,recs,case):
        incs=recs.set_index('gym_id').loc[self.ids,'proposed_increment'].to_numpy(dtype=int)
        point=pd.DataFrame([self.sm[g,int(i),case] for g,i in zip(self.ids,incs)])
        cf=pd.DataFrame([self.sm[g,0,'Base'] for g in self.ids]);sums=['monthly_revenue','subscription_revenue','joining_fee_revenue','ancillary_revenue','month12_members','period_opening_members','opening_members','average_members','new_members','standard_joins','qualified_prospects','opening_base_cancellations','same_month_cancellations','incumbent_standard_opening','incumbent_standard_cancellations','incumbent_standard_downgrades','standard_average_members','standard_subscription_revenue','offpeak_average_members','plus_average_members','pricing_complaints','annualised_exit_run_rate']
        r={f:float(point[f].sum()) for f in sums}
        r.update(variant=recs.variant.iloc[0],case=case,raise_sites=int((incs>0).sum()),raise_1_sites=int((incs==1).sum()),raise_2_sites=int((incs==2).sum()),
            test_sites=int(recs.action.eq('TEST FIRST').sum()),hold_sites=int(recs.action.eq('HOLD PRICE').sum()),investigate_sites=int(recs.action.eq('DEFENSIVE / INVESTIGATE').sum()),
            counterfactual_revenue=float(cf.monthly_revenue.sum()),counterfactual_month12_members=float(cf.month12_members.sum()),
            incremental_revenue=float(point.incremental_revenue.sum()),member_difference=float(point.member_difference.sum()),acquisition_difference=float(point.acquisition_difference.sum()))
        r['member_impact']=safe(r['member_difference'],r['counterfactual_month12_members']);r['revenue_uplift']=safe(r['incremental_revenue'],r['counterfactual_revenue'])
        r['churn_rate']=safe(r['opening_base_cancellations'],r['opening_members']);r['retention_rate']=1-r['churn_rate']
        r['incumbent_churn_rate']=safe(r['incumbent_standard_cancellations'],r['incumbent_standard_opening']);r['incumbent_downgrade_rate']=safe(r['incumbent_standard_downgrades'],r['incumbent_standard_opening'])
        r['conversion_rate']=safe(r['new_members'],r['qualified_prospects']);r['arpmm']=safe(r['monthly_revenue'],r['average_members']);r['subscription_yield']=safe(r['subscription_revenue'],r['average_members']);r['standard_yield']=safe(r['standard_subscription_revenue'],r['standard_average_members'])
        for tier in ['standard','offpeak','plus']:r[tier+'_mix']=safe(r[tier+'_average_members'],r['average_members'])
        r['complaints_per_1000_member_months']=safe(r['pricing_complaints']*1000,r['average_members'])
        selected=self.draws[:,incs,np.arange(80),:];joint=selected.sum(axis=1)
        for f in ['monthly_revenue','month12_members','new_members','standard_joins']:
            vals=joint[:,self.draw_fields.index(f)];r[f+'_lower'],r[f+'_upper']=map(float,np.percentile(vals,CFG['interval_percentiles']))
        revenue=joint[:,0]-r['counterfactual_revenue'];r['incremental_revenue_lower'],r['incremental_revenue_upper']=map(float,np.percentile(revenue,CFG['interval_percentiles']))
        member=joint[:,1]/r['counterfactual_month12_members']-1;r['member_impact_lower'],r['member_impact_upper']=map(float,np.percentile(member,CFG['interval_percentiles']))
        r['positive_revenue_draw_fraction']=float(np.mean(revenue>1e-8)) if np.any(incs) else 0.
        test=recs[recs.action=='TEST FIRST'];r['excluded_test_first_base_revenue']=float(test.selected_incremental_revenue.sum());r['excluded_test_first_base_member_difference']=float(test.selected_member_difference.sum())
        r['member_loss_limit']=float(recs.member_loss_limit.iloc[0]);r['minimum_post_increase_competitor_gap']=float(recs.minimum_post_increase_competitor_gap.iloc[0]);r['test_repeat_repricing']=bool(recs.test_repeat_repricing.iloc[0])
        r['evidence_status']='Conditional RAISE portfolio only; TEST FIRST remains at no increase; no implementation authorisation'
        check(f'Portfolio component reconciliation {r["variant"]}/{case}',abs(r['monthly_revenue']-r['subscription_revenue']-r['joining_fee_revenue']-r['ancillary_revenue'])<.01)
        check(f'Portfolio member bridge {r["variant"]}/{case}',abs(r['month12_members']-r['period_opening_members']-r['new_members']+r['opening_base_cancellations']+r['same_month_cancellations'])<1e-6)
        check(f'Independent shared draw sum {r["variant"]}/{case}',np.max(np.abs(joint[:,0]-sum(self.draws[:,int(i),j,0] for j,i in enumerate(incs))))<1e-6)
        return r

def edge_tests():
    h={f:False for f in FLAGS};b={f:1. for f in REQUIRED};b.update(repeated_repricing=False,incremental_revenue=10.,member_impact=-.02,old_standard_price=25.)
    d=dict(incremental_revenue=5.,member_impact=-.05);t={v:dict(incremental_revenue=1.) for v in CFG['nonzero_sensitivities']};p=policy()
    opts={1:(b.copy(),d.copy(),copy.deepcopy(t)),2:(b.copy(),d.copy(),copy.deepcopy(t))}
    check('Exact revenue tie chooses smaller increase',classify(h,opts,p)[1]==1)
    check('Exact 5 percent downside boundary accepted',candidate(b,d,t,p)['qualified'])
    check('Just beyond member boundary rejected',not candidate(b,{**d,'member_impact':-.05000000001},t,p)['qualified'])
    check('Exact zero competitor gap accepted',candidate({**b,'post_increase_competitor_gap':0.},d,t,p)['qualified'])
    check('Negative competitor gap rejected',not candidate({**b,'post_increase_competitor_gap':-1e-12},d,t,p)['plausible'])
    for f in FLAGS:check('Caution precedence '+f,classify({**h,f:True},opts,p)[0]=='DEFENSIVE / INVESTIGATE')
    check('Missing decision evidence investigated',classify(h,{**opts,1:({**b,'incremental_revenue_lower':None},d,t)},p)[0]=='DEFENSIVE / INVESTIGATE')
    check('Zero revenue is valid but does not qualify',candidate({**b,'incremental_revenue':0.},d,t,p)['complete'] and not candidate({**b,'incremental_revenue':0.},d,t,p)['qualified'])
    check('Zero sensitivity revenue rejects qualification',not candidate(b,d,{**t,'early_3m':{'incremental_revenue':0.}},p)['qualified'])
    opts[1][0]['repeated_repricing']=True;opts[2][0]['repeated_repricing']=True
    check('Repeat precedence produces provisional test',classify(h,opts,p)[:3]==('TEST FIRST',0,1))
    check('Repeat warning variant permits raise',classify(h,opts,policy('allow_repeat_repricing'))[1]==1)
    check('No qualifying candidates choose smallest plausible test',classify(h,{i:(b,{**d,'member_impact':-.1},t) for i in [1,2]},p)[:3]==('TEST FIRST',0,1))
    check('No plausible candidates hold',classify(h,{i:({**b,'post_increase_competitor_gap':-.1},d,t) for i in [1,2]},p)[0]=='HOLD PRICE')
    check('Zero denominator unavailable',np.isnan(safe(1.,0.)))
    check('Policy refresh retains 3 percent variant',policy('member_limit_3pct',{'member_loss_limit':.05})['member_loss_limit']==.03)
    check('Policy refresh retains competitor buffer variant',policy('competitor_buffer_1gbp',{'minimum_gap':0.})['minimum_gap']==1.)

def clean(value):
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [clean(v) for v in value]
    if isinstance(value,(np.integer,np.floating,np.bool_)):value=value.item()
    if isinstance(value,float) and not math.isfinite(value):return None
    return value
def frame(df):return clean(dict(columns=df.columns.tolist(),data=df.to_numpy().tolist()))

def source_blocks():
    block={}
    with ZipFile(ROOT/'excel/gym_pricing_model.xlsx') as z:
        paths=ooxml.sheet_paths(z)
        for name in ['Baseline','Headroom Score','Gym Master','Scenario Comparison','Scenario Inputs','Dataset Overview','README']:
            allcells=cells(z,paths[name]);selected={}
            for address,v in allcells.items():
                row=int(''.join(filter(str.isdigit,address)))
                if (name in ['Baseline','Headroom Score'] and row<=88) or (name=='Gym Master' and row<=81) or (name=='Scenario Comparison' and row<=990) or (name=='Scenario Inputs' and row<=27) or name in ['Dataset Overview','README']:
                    selected[address]=v
            block[name]=selected
    return block

def docs(e,base,sens,port,results):
    dictionary=[]
    source_dict=pd.read_csv(AN/'scenario_metric_dictionary.csv');source_map={r.field:r for r in source_dict.itertuples() if r.table=='gym_scenarios'}
    head_dict=pd.read_csv(AN/'headroom_metric_dictionary.csv');head_map={r.field:r for r in head_dict.itertuples() if r.table=='gym_headroom'}
    for table,df,keys in zip(OUTPUTS,[base,sens,port],[['gym_id'],['gym_id','variant'],['variant','case']]):
        for f in df.columns:
            underlying=f.removeprefix('selected_');s=source_map.get(underlying)
            unit=s.unit if s is not None else ('boolean' if pd.api.types.is_bool_dtype(df[f]) else 'GBP' if any(k in f for k in ['revenue','price','gap']) else 'decimal rate' if any(k in f for k in ['impact','rate','mix','frequency','limit']) else 'percentage points' if '_pp' in f else 'members / member-month exposure' if any(k in f for k in ['members','member_difference']) else 'text' if df[f].dtype=='object' else 'numeric')
            definition=s.definition if s is not None else f.replace('_',' ')+'; see policy method and source lineage below'
            if f in head_map:
                definition=head_map[f].definition+'; unchanged Phase 4 context, not a Phase 7 causal estimate'
                unit=head_map[f].unit
            if f.startswith('plus1_') or f.startswith('plus2_'):definition=f[5:].replace('_',' ')+' for the '+('£1' if f.startswith('plus1') else '£2')+' candidate, evaluated using named Base/Downside cases and the policy variant'
            specials={'action':'First matching ordered Phase 7 rule. One of the five agreed labels. Conditional raises require testing before implementation.',
                'proposed_increment':'Cash increase for conditional RAISE only. Zero for every other action.', 'provisional_test_increment':'Provisional test amount for TEST FIRST only. It is excluded from the portfolio.',
                'assessment_increment':'Proposed increase, or provisional test increase; zero otherwise. Selected fields describe this option, not an authorised rollout.',
                'selected_downside_member_impact':'December Downside membership versus no increase minus one, for assessment_increment.',
                'selected_downside_revenue':'Downside annual incremental net revenue for assessment_increment.',
                'excluded_test_first_base_revenue':'Sum of provisional test Base incremental revenues. Excluded from RAISE portfolio and not a realised gain.',
                'excluded_test_first_base_member_difference':'Sum of provisional test December member differences. Excluded from RAISE portfolio.',
                'member_loss_limit':'Positive maximum downside December member-loss fraction; policy assumption, not empirical tolerance.',
                'minimum_post_increase_competitor_gap':'Minimum competitor recurring price minus increased Standard price; GBP including VAT.',
                'test_repeat_repricing':'True requires viable historically repriced sites to TEST FIRST.',
                'monthly_revenue':'Cumulative January–December total net revenue, despite retained Phase 6 field name.',
                'opening_members':'Summed opening-member months, not January stock or unique customers.',
                'average_members':'Summed midpoint average-member months, not unique customers.',
                'period_opening_members':'January 2026 starting membership stock.',
                'positive_revenue_draw_fraction':'Fraction of shared conditional parameter draws with positive portfolio revenue; not rollout probability.',
                'variant':'base, member_limit_3pct, member_limit_7pct, competitor_buffer_1gbp, or allow_repeat_repricing.',
                'rule_id':'R1_CAUTION, R1_MISSING, R3_NO_PLAUSIBLE, R6_FAILED_QUALIFICATION, R6_REPEAT_REPRICING or R7_CONDITIONAL_RAISE.',
                'plus3_standard_plus_parity':'Whether hypothetical Standard +£3 equals unchanged Plus headline; tier upgrades are not modelled.',
                'changed_action':'Whether this policy variant changes the base action.', 'changed_amount':'Whether proposed or provisional test amount changes versus base.'}
            definition=specials.get(f,definition)
            if f in ['proposed_increment','provisional_test_increment','assessment_increment']:unit='GBP per month, VAT-inclusive'
            if f in ['current_standard_price','proposed_standard_price','provisional_test_price','minimum_post_increase_competitor_gap','unchanged_plus_price','plus3_standard_price']:unit='GBP, VAT-inclusive recurring price/gap'
            if f.startswith(('plus1_','plus2_')):
                tail=f[6:]
                if tail in ['complete','plausible','qualified']:
                    unit='boolean';definition={'complete':'All required Base, Downside, repeat status and six sensitivity inputs available','plausible':'Positive Base incremental revenue and post-increase gap at least the policy minimum','qualified':'Plausible, positive Downside and conditional lower-bound revenue, Downside member impact at least minus policy limit, and all six nonzero sensitivity revenues positive'}[tail]
                elif tail=='failed_gates':unit='text';definition='Names of failing ordered candidate qualification gates; blank means every gate passed'
                elif tail.endswith('revenue') or tail in ['revenue_lower','revenue_upper']:unit='GBP net of VAT';definition=tail.replace('_',' ')+' for this candidate; annual cumulative increment versus identical no increase. Worst sensitivity is the minimum across the six named nonzero alternatives.'
                elif 'member_impact' in tail:unit='decimal rate';definition='December candidate closing members / corresponding no-increase December stock minus one, in the stated Base or Downside case'
                elif tail=='post_competitor_gap':unit='GBP VAT-inclusive';definition='December comparable recurring competitor mean minus increased Standard headline price; fees and introductory discounts excluded'
            if f.endswith('_lower') or f.endswith('_upper'):definition+='; 2.5th/97.5th percentile of shared Phase 6 draws, conditional on model assumptions'
            if f in ['case','variant','gym_id','rule_id','action']:unit='identifier / category'
            dictionary.append(dict(table=table,field=f,key_field=f in keys,definition=definition,unit=unit,window=CFG['reporting_window'] if table.endswith('portfolio') or f.startswith(('selected','plus')) else '2025 actual synthetic context / hypothetical 2026 decision',source_status='Derived from unchanged synthetic Phase 3–6 evidence or explicit Phase 7 policy',null_meaning='Blank = unavailable evidence, immature/inapplicable context, or no provisional test price; zero is a valid observed/calculated value'))
    pd.DataFrame(dictionary).to_csv(AN/'recommendation_metric_dictionary.csv',index=False,lineterminator='\n')
    a=base.action.value_counts();b=port[(port.variant=='base')&(port['case']=='Base')].iloc[0]
    report=f'''# Northstar Fitness — conditional gym recommendations

{D1}

{D2}

Phase 7 combines relative value, existing commercial cautions and the historical-response scenario model. It supports conditional site decisions, protecting member volume while assessing revenue. This is a hypothetical January–December 2026 assessment, not an instruction to implement prices now.

## Recommendations

'''+ '\n'.join(f'- **{action}: {int(a.get(action,0))} {"gym" if int(a.get(action,0))==1 else "gyms"}.**' for action in CFG['actions'])+f'''

The conditional RAISE portfolio adds **£{b.incremental_revenue:,.0f}** annual net revenue in the Base case, with **{b.member_difference:,.0f}** fewer December members ({b.member_impact:.2%}) versus no increase. Conditional 95% parameter range: **£{b.incremental_revenue_lower:,.0f}–£{b.incremental_revenue_upper:,.0f}**. TEST FIRST opportunities are excluded; their provisional Base increments total £{b.excluded_test_first_base_revenue:,.0f}. These are modelled outcomes, not earned revenue or profit.

The same shared pilot response drives every site. Site interval widths do not reflect locally identified elasticities. Positive parameter draws do not measure rollout probability. Future trading shocks, competitor reactions and transport uncertainty are excluded.

## Ordered policy

Any high churn, weak conversion, declining acquisition, peak-capacity flag or missing decision evidence requires investigation first. Compare £1/£2 candidates using positive Base revenue and the required post-increase competitor gap. Qualifying candidates also need positive Downside and conditional lower-bound revenue, no more than 5% Downside December member loss and positive revenue in all six nonzero-behaviour sensitivities. Select the higher qualifying Base revenue, favouring the smaller price on an exact tie. Repeat repricing goes to TEST FIRST. If only plausible candidates exist, provisionally test the smallest. If neither is plausible, HOLD PRICE.

The 5% member limit and financial gates are explicit management policy assumptions, not measured willingness to pay or Phase 8 rollout thresholds. Competitor gaps use VAT-inclusive recurring prices; joining fees and introductory discounts remain separate. Headroom bands and sensitivity remain context and are not causal evidence or new rankings.

## Portfolio and policy sensitivity

| Policy | £2 raises | £1 raises | Test | Hold | Investigate | Base annual increment | December member impact |
|---|---:|---:|---:|---:|---:|---:|---:|
'''
    for r in port[port['case']=='Base'].itertuples():report+=f'| {r.variant} | {r.raise_2_sites} | {r.raise_1_sites} | {r.test_sites} | {r.hold_sites} | {r.investigate_sites} | £{r.incremental_revenue:,.0f} | {r.member_impact:.2%} |\n'
    report+='\n'+ '\n'.join(f'- {v}: {int(q.changed_action.sum())} action changes; {int(q.changed_amount.sum())} amount changes.' for v,q in sens.groupby('variant',sort=False))
    report+='''

Limits of 3% and 7%, a £1 competitor buffer and allowing repeat repricing each change one policy assumption. These comparisons expose judgement sensitivity, not statistical confidence. No action category is forced to contain gyms.

## What remains uncertain

+£3 remains an analytical option and generally produces higher modelled revenue with greater membership loss. It is outside the action vocabulary. At 20 previously +£2 sites it makes Standard equal unchanged Plus; possible tier upgrades and value-proposition changes are unmodelled. £1 extrapolates from the observed +£2 pilot. All pilot pairs had positive pre-event competitor gaps. Repeat repricing tolerance, future competitor reaction, incremental future-joiner retention and costs remain incompletely identified.

## Commercial visuals

![Actions and exposure](recommendation_actions.png)

Counts and associated conditional RAISE revenue/member exposure show the difference between commercial opportunity and implementation. TEST FIRST opportunities are labelled separately and excluded.

![Site trade-offs](recommendation_tradeoffs.png)

Every site is shown at its provisional/conditional assessment amount, or £1 context where the action is hold/investigate. The latter is context, not a proposed price. Revenue gains can coexist with lost membership.

![Policy sensitivity](recommendation_policy_changes.png)

The matrix shows exactly which sites change action across the five policies. It does not rerank Phase 4 or estimate a different behavioural response.

## Phase 8 handoff

Develop a controlled experiment before implementation, with prospective assignment, adequate power, pre-specified outcomes and revenue/member/service safeguards. Establish how repeated repricing, market coverage, competitor reactions, complaints and sustained retention will be assessed. Investigate flagged sites before choosing experiment eligibility. Phase 7 neither designs that experiment nor simulates its results.

Member stocks are not unique customers; monthly churn is not annual retention. December revenue ×12 is a seasonal exit run-rate, not a forecast. The report and workbook keep subscription yield distinct from ARPMM and keep revenue distinct from profit.
'''
    (AN/'recommendation_report.md').write_text(report,encoding='utf-8')
    (AN/'recommendation_methodology.md').write_text(f'''# Phase 7 method and interfaces

{D1}

{D2}

Keys: gym_recommendations = gym_id (80); recommendation_sensitivity = gym_id, variant (400); recommendation_portfolio = variant, case (15). ISO gym IDs remain stable. Prices/gaps include VAT, revenue excludes assumed 20% VAT, decimal rates and pp changes preserve Phase 3–6 definitions. Historical context uses full-year/Q4 2025; scenarios cover January–December 2026.

Policy order is defined in recommendation_config.json and classifier tests. Base/Downside names are fixed regardless of the displayed workbook case. Source full-precision Phase 6 prepared records are used rather than rounded CSV amounts. Caution flags originate in Phase 3. Headroom scores/bands are retained unchanged. Every required candidate input and every six named nonzero sensitivity is required; no silent imputation. Missing evidence gets R1_MISSING. Zero evidence is valid but strict positive-revenue gates reject zero gains. Missing context is disclosed rather than invented.

Proposed_increment belongs only to conditional RAISE actions. Assessment_increment can be a provisional test amount; selected_* fields describe that assessment and are not portfolio gains. HOLD/INVESTIGATE assessment is zero. +£3 is analytical context only.

Portfolio rows select one unchanged Phase 6 site/case record for each gym, using conditional RAISE increments and zero for all other actions. Sum revenue components, stocks and exposures separately. Churn, incumbent churn, downgrades, conversion, yield, ARPMM, membership mix and complaint rates use summed numerators/denominators. Null denominators remain unavailable. The annualised exit run-rate is a sum of December×12 records.

For uncertainty, retain outcome[d, increment, gym, metric] from Phase 6's 10,000 joint draws (seed 20261006). Sum selected site outcomes inside each d, then take percentile bounds. Subtract the identical no-increase counterfactual for revenue; divide by no-increase December stock for member impact. No resampling, independent site shocks or summing interval endpoints. If the retained draw file is absent, restore it through the existing Phase 6 analysis before completion; do not fabricate intervals.

Run recommendation_analysis.py to regenerate; --reproduce checks byte-identical output without replacing CSVs. Policy-only workbook refresh reads saved policy inputs and applies the same classifier to reconciled saved comparison records; it does not overwrite the analyst-facing evidence interfaces. Refresh must preserve all sheets, restore the existing case selector and refresh captured portfolio uncertainty only against unchanged evidence-derived scenarios/draws. Manual behavioural overrides or stale comparisons suppress authority until Phase 6 evidence is rerun.
''',encoding='utf-8')

def figures(base,sens,port):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    colors={'RAISE £2':'#187D73','RAISE £1':'#4BA3A0','TEST FIRST':'#D59428','HOLD PRICE':'#8795A1','DEFENSIVE / INVESTIGATE':'#B24D4D'}
    actions=CFG['actions'];count=base.action.value_counts();fig,axs=plt.subplots(1,3,figsize=(14,5),layout='constrained')
    groups=[base[base.action==a] for a in actions]
    data=[count.reindex(actions,fill_value=0).to_numpy(),np.array([q.selected_incremental_revenue.sum() if a.startswith('RAISE') or a=='TEST FIRST' else 0 for a,q in zip(actions,groups)])/1000,np.array([q.selected_member_difference.sum() if a.startswith('RAISE') or a=='TEST FIRST' else 0 for a,q in zip(actions,groups)])]
    for ai,(ax,vals,title) in enumerate(zip(axs,data,['Gym count','Base net revenue (£ thousands)','December member difference'])):
        ax.barh(actions,vals,color=[colors[a] for a in actions]);ax.invert_yaxis();ax.set_title(title);ax.grid(axis='x',alpha=.15)
        if ai:ax.tick_params(axis='y',labelleft=False)
        for j,v in enumerate(vals):ax.text(v,j,f' {v:,.0f}',va='center',fontsize=9)
    fig.suptitle('Conditional raises and provisional tests — tests excluded from the raise portfolio');fig.savefig(AN/'recommendation_actions.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,6),layout='constrained')
    for a in actions:
        q=base[base.action==a];incs=q.assessment_increment.where(q.assessment_increment.gt(0),1)
        # View-only context for holds/investigations; never affects decisions.
        y=np.where(incs==2,q.plus2_base_revenue,q.plus1_base_revenue);x=np.where(incs==2,q.plus2_base_member_impact,q.plus1_base_member_impact)*100
        ax.scatter(x,y/1000,label=a,color=colors[a],alpha=.8,s=40)
    ax.axhline(0,color='#243B53',lw=.7);ax.set_xlabel('December member impact versus no increase (%)');ax.set_ylabel('Annual incremental net revenue (£ thousands)');ax.set_title('Assessment amount; holds/investigations shown at £1 for context');ax.legend(fontsize=9);ax.grid(alpha=.15);fig.savefig(AN/'recommendation_tradeoffs.png',dpi=150);plt.close(fig)
    matrix=np.array([[actions.index(sens[(sens.gym_id==g)&(sens.variant==v)].action.iloc[0]) for v in CFG['variants']] for g in base.gym_id])
    from matplotlib.colors import ListedColormap
    fig,ax=plt.subplots(figsize=(10,15),layout='constrained');ax.imshow(matrix,aspect='auto',cmap=ListedColormap([colors[a] for a in actions]),vmin=-.5,vmax=4.5)
    ax.set_xticks(range(5),['Base','3% limit','7% limit','£1 buffer','Allow repeats']);ax.set_yticks(range(80),base.gym_id,fontsize=7);ax.set_title('Action sensitivity in gym ID order; headroom rankings unchanged')
    import matplotlib.patches as patches
    ax.legend(handles=[patches.Patch(color=colors[a],label=a) for a in actions],loc='upper center',bbox_to_anchor=(.5,-.015),ncol=2);fig.savefig(AN/'recommendation_policy_changes.png',dpi=150);plt.close(fig)

def main():
    PRE.mkdir(parents=True,exist_ok=True);before=hashes();e=Evidence();edge_tests()
    allrec={v:e.recommend(v) for v in CFG['variants']};base=allrec['base'].drop(columns='variant');sens=pd.concat(allrec.values(),ignore_index=True)
    ref=allrec['base'].set_index('gym_id')
    sens['base_action']=sens.gym_id.map(ref.action);sens['base_proposed_increment']=sens.gym_id.map(ref.proposed_increment);sens['base_provisional_test_increment']=sens.gym_id.map(ref.provisional_test_increment)
    sens['changed_action']=sens.action!=sens.base_action;sens['changed_amount']=(sens.proposed_increment!=sens.base_proposed_increment)|(sens.provisional_test_increment!=sens.base_provisional_test_increment)
    port=pd.DataFrame([e.portfolio(q,c) for q in allrec.values() for c in CFG['cases']])
    check('80 unique recommendations',len(base)==80 and base.gym_id.is_unique)
    check('400 unique sensitivity keys',len(sens)==400 and not sens.duplicated(['gym_id','variant']).any())
    check('15 unique portfolio keys',len(port)==15 and not port.duplicated(['variant','case']).any())
    check('Five actions only',set(sens.action)<=set(CFG['actions']))
    check('All caution sites investigated',all(base.loc[base[FLAGS].any(axis=1),'action']=='DEFENSIVE / INVESTIGATE'))
    check('No plus3 action or portfolio amount',set(sens.proposed_increment)<=set([0,1,2]))
    check('Tests excluded from portfolio increments',all(sens.loc[~sens.action.str.startswith('RAISE'),'proposed_increment']==0))
    check('Source and prior analysis hashes unchanged',hashes()==before)
    csvhash={}
    for name,df in zip(OUTPUTS,[base,sens,port]):
        raw=df.to_csv(index=False,float_format='%.12g',na_rep='',lineterminator='\n').encode('utf-8');path=DATA/(name+'.csv');csvhash[name]=hashlib.sha256(raw).hexdigest()
        if '--reproduce' in sys.argv:check('Byte-identical '+name,path.read_bytes()==raw)
        else:path.write_bytes(raw)
    results=clean(dict(input_hashes=before,configuration_hash=hashlib.sha256((AN/'recommendation_config.json').read_bytes()).hexdigest(),rows=dict(zip(OUTPUTS,[len(base),len(sens),len(port)])),checks_passed=len(CHECKS),action_counts=base.action.value_counts().to_dict(),csv_hashes=csvhash,portfolio=port.to_dict('records')))
    if '--reproduce' in sys.argv:
        (PRE/'reproduction.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print('All three recommendation CSVs reproduce byte for byte.');return
    (AN/'recommendation_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    if not (PRE/'input_workbook.xlsx').exists():(PRE/'input_workbook.xlsx').write_bytes((ROOT/'excel/gym_pricing_model.xlsx').read_bytes())
    payload=clean(dict(config=CFG,disclaimers=[D1,D2],recommendations=frame(base),sensitivity=frame(sens),portfolio=frame(port),sources=source_blocks(),source_hashes=before,
        source_layout=json.loads((P6/'layout.json').read_text(encoding='utf-8')),headroom_columns=pd.read_csv(DATA/'gym_headroom.csv',nrows=0).columns.tolist(),scenario_sensitivity=frame(e.t[e.t.gym_id!='ESTATE']),results=results))
    (PRE/'payload.json').write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8')
    docs(e,base,sens,port,results);figures(base,sens,port)
    (AN/'recommendation_validation.md').write_text('# Phase 7 Python validation\n\n'+D1+'\n\n'+D2+'\n\n'+'\n'.join('- PASS: '+n for n in CHECKS)+'\n\nWorkbook validation is recorded separately after saved-file verification.\n',encoding='utf-8')
    print(json.dumps(dict(rows=results['rows'],checks=len(CHECKS),actions=results['action_counts'],base_portfolio=port.iloc[0][['incremental_revenue','member_difference','member_impact','incremental_revenue_lower','incremental_revenue_upper']].to_dict()),indent=2))

if __name__=='__main__':main()
