"""Phase 8 stochastic pilot. Reads reconciled evidence, never latent behaviour.

Run from project root with bundled Python. --reproduce compares CSV bytes only.
The existing expected-member forecast is left intact; stochastic paths are separate.
"""
import calendar
import copy
import hashlib
import itertools
import json
import math
import sys
import zlib
from pathlib import Path
from statistics import NormalDist
from zipfile import ZipFile
import numpy as np
import pandas as pd
from scenario_analysis import Model, D1, D2, clean_json, frame_payload
from refresh_scenario_comparison import cells
import append_scenario_sheets as xml

ROOT=Path(__file__).resolve().parents[1];AN=ROOT/'analysis';DATA=ROOT/'data';PRE=AN/'.workbook_previews/phase8'
CFG=json.loads((AN/'experiment_config.json').read_text(encoding='utf-8'))
OUTPUTS=['experiment_design','experiment_monthly','experiment_pair_results','experiment_estimates','experiment_power','experiment_monitoring','experiment_simulation_ledger']
CHECKS=[];FALLBACKS=[];CAPS=[]
TIERS=['Standard','Off-Peak','Plus']

def check(name,ok):
    if not bool(ok):raise AssertionError(name)
    CHECKS.append(name)

def ratio(n,d):return float(n/d) if pd.notna(n) and pd.notna(d) and d>0 else np.nan
def logratio(a,b):return math.log(a/b) if a>0 and b>0 else np.nan
def logit(p):
    p=np.clip(p,CFG['residual_probability_floor'],1-CFG['residual_probability_floor']);return np.log(p/(1-p))
def shifted(p,e):
    if p==0:return 0.
    if p==1:return 1.
    return float(1/(1+np.exp(-np.clip(logit(p)+e,-30,30))))
def rng(stream,*keys):return np.random.default_rng(np.random.SeedSequence([CFG['seed'],CFG['streams'][stream],*map(int,keys)]))
def hashes():
    files=[p for p in DATA.glob('*.csv') if p.stem not in OUTPUTS]
    files += [AN/f for f in ['generation_config.json','baseline_results.json','headroom_config.json','headroom_results.json','response_config.json','response_results.json','scenario_config.json','scenario_results.json','recommendation_config.json','recommendation_results.json']]
    files += [AN/'.workbook_previews/phase6/payload.json',AN/'.workbook_previews/phase6/joint_draws.npz']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}

def verify_current_evidence():
    with ZipFile(ROOT/'excel/gym_pricing_model.xlsx') as z:
        paths=xml.sheet_paths(z);r=cells(z,paths['Recommendations']);s=cells(z,paths['Scenario Inputs']);c=cells(z,paths['Scenario Comparison'])
        check('Current scenario and recommendation evidence',r.get('E5')=='CURRENT EVIDENCE' and c.get('D3')=='CURRENT' and s.get('E23')==0 and all(s.get('I'+str(i)) is None for i in range(9,18)))
        check('Original Phase 7 policy for prospective eligibility',r.get('B4')==.05 and r.get('B5')==0 and r.get('B6')==1)
        selected=[s.get('B3'),s.get('B4')]
    return selected

def matching(model):
    rec=pd.read_csv(DATA/'gym_recommendations.csv').sort_values('gym_id');m=model.m
    inputs=[]
    for _,r in rec.iterrows():
        q=m[(m.gym_id==r.gym_id)&m.month.between('2025-07-01','2025-12-01')].sort_values('month')
        check('Six pre-intervention months '+r.gym_id,len(q)==6)
        inputs.append(dict(gym_id=r.gym_id,standard_price=q.standard_price.mean(),average_members=q.average_members.mean(),
            acquisition_rate=ratio(q.new_members.sum(),q.opening_members.sum()),churn_rate=ratio(q.opening_base_cancellations.sum(),q.opening_members.sum()),
            conversion_rate=ratio(q.new_members.sum(),q.qualified_prospects.sum()),peak_utilisation=q.peak_utilisation_pct.mean(),
            competitor_gap=q.competitor_price_gap.mean(),competitor_count=q.competitor_count_3km.mean(),marketing_per_prospect=ratio(q.marketing_spend.sum(),q.qualified_prospects.sum()),
            member_growth=ratio(q.iloc[-1].closing_members,q.iloc[0].opening_members)-1))
    d=rec[['gym_id','gym_name','region','action','repeated_repricing','caution_flag_count','plus1_complete','plus1_plausible','evidence_status','current_standard_price','competitor_gap_dec2025']].merge(pd.DataFrame(inputs),on='gym_id',validate='one_to_one')
    d['eligible']=d.action.isin(['RAISE £1','RAISE £2','TEST FIRST']) & d.plus1_complete & d.plus1_plausible & (d.caution_flag_count==0) & d[CFG['matching_features']].notna().all(axis=1)
    check('Exactly 16 eligible candidates',d.eligible.sum()==16)
    e=d[d.eligible].set_index('gym_id');x=e[CFG['matching_features']];sd=x.std(ddof=0);active=sd[sd>1e-12].index.tolist();z=(x[active]-x[active].mean())/sd[active]
    pairs=[]
    def perfect(ids):
        if not ids:return [([],0.)]
        a=ids[0];out=[]
        for b in ids[1:]:
            rest=[i for i in ids if i not in [a,b]];dist=float(((z.loc[a]-z.loc[b])**2).sum())
            for choices,cost in perfect(rest):out.append(([(a,b,dist)]+choices,cost+dist))
        return out
    for (region,repeat),g in e.groupby(['region','repeated_repricing'],sort=True):
        ids=sorted(g.index);check('Only singleton reserves or complete even strata '+region,len(ids)==1 or len(ids)%2==0)
        if len(ids)==1:continue
        options=perfect(ids);best=min(options,key=lambda o:(o[1],[(a,b) for a,b,_ in o[0]]))
        for a,b,dist in best[0]:pairs.append(dict(a=a,b=b,region=region,repeated_repricing=bool(repeat),matching_distance_squared=dist))
    pairs.sort(key=lambda p:(p['repeated_repricing'],p['region'],p['a'],p['b']))
    assign=rng('assignment');lookup={}
    for i,p in enumerate(pairs):
        p['pair_id']='EXP26_'+str(i+1).zfill(2);p['population']='Repeat repricing' if p['repeated_repricing'] else 'First repricing'
        p['treatment_gym_id'],p['control_gym_id']=(p['a'],p['b']) if assign.integers(0,2)==0 else (p['b'],p['a'])
        for arm in ['treatment','control']:lookup[p[arm+'_gym_id']]=dict(pair_id=p['pair_id'],assignment=arm.title(),population=p['population'],matching_distance_squared=p['matching_distance_squared'],matched_gym_id=p['control_gym_id'] if arm=='treatment' else p['treatment_gym_id'])
    for f in ['pair_id','assignment','population','matched_gym_id','matching_distance_squared']:
        d[f]=d.gym_id.map(lambda g:lookup.get(g,{}).get(f))
    d['disposition']=np.where(d.assignment.notna(),'Assigned',np.where(d.eligible,'Reserve','Excluded'))
    d['exclusion_reason']=np.where(d.disposition=='Assigned','',np.where(d.disposition=='Reserve','No same-region and same-repricing-history partner',np.where(d.caution_flag_count>0,'Existing Phase 3 caution requires investigation','Phase 7 action is outside pilot eligibility')))
    d['experiment_increment']=np.where(d.assignment=='Treatment',CFG['increment'],0.)
    d['proposed_standard_price']=d.current_standard_price+d.experiment_increment
    d['post_increase_competitor_gap']=d.competitor_gap_dec2025-d.experiment_increment
    d['pre_start']='2025-07-01';d['pre_end']='2025-12-01';d['notification_date']=CFG['intervention_date'];d['new_joiner_effective_date']=CFG['intervention_date'];d['incumbent_effective_date']=CFG['billing_date'];d['seed']=CFG['seed']
    check('Exactly seven disjoint pairs',len(pairs)==7 and len(lookup)==14)
    check('Five first and two repeat pairs',sum(not p['repeated_repricing'] for p in pairs)==5 and sum(p['repeated_repricing'] for p in pairs)==2)
    check('Correct two reserves',set(d.loc[d.disposition=='Reserve','gym_id'])==set(CFG['reserves']))
    check('Balanced assignments',d.assignment.value_counts().to_dict()=={'Control':7,'Treatment':7} or d.assignment.value_counts().to_dict()=={'Treatment':7,'Control':7})
    return d,pairs,dict(active_features=active,mean=x.mean().to_dict(),population_sd=sd.to_dict(),standardised=z.reset_index().to_dict('records'))

def noise(model,assigned):
    """Regional calendar-month effects and year effects, then joint residual blocks."""
    m=model.m.copy();m['region']=m.gym_id.map(model.g.set_index('gym_id').region);l=model.l
    ag=l.groupby(['gym_id','month','membership_type'])[['opening_members','opening_base_cancellations','new_members','same_month_cancellations','transfers_out']].sum()
    rows=[]
    for _,v in m.iterrows():
        rates=[]
        for tier in TIERS:
            a=ag.loc[(v.gym_id,v.month,tier)];rates.append(ratio(a.opening_base_cancellations,a.opening_members))
        st=l[(l.gym_id==v.gym_id)&(l.month==v.month)&(l.membership_type=='Standard')]
        down=ratio(st.loc[st.opening_members>0,'transfers_out'].sum(),st.opening_members.sum())
        vec=[math.log(v.qualified_prospects),logit(v.conversion_rate),*[logit(r) for r in rates],logit(down),logit(ratio(v.same_month_cancellations,v.new_members)),math.log(v.pricing_complaints/v.average_members*1000+.1),math.log(v.visits_per_member),math.log(v.ancillary_revenue)]
        rows.append([v.gym_id,v.region,v.month,*vec])
    fields=['prospects_log','conversion_logit','standard_churn_logit','offpeak_churn_logit','plus_churn_logit','downgrade_logit','same_exit_logit','complaints_log','visits_log','ancillary_log']
    f=pd.DataFrame(rows,columns=['gym_id','region','month',*fields]);check('Complete observed noise inputs',len(f)==1920 and np.isfinite(f[fields]).all().all())
    f['calendar_month']=pd.to_datetime(f.month).dt.month;f['year']=pd.to_datetime(f.month).dt.year
    centered=f[fields]-f.groupby('gym_id')[fields].transform('mean')
    seasonal=centered.groupby([f.region,f.calendar_month]).transform('mean');res=centered-seasonal
    res-=res.groupby([f.region,f.year]).transform('mean')
    region=res.groupby([f.region,f.month]).mean();site=res-region.reindex(pd.MultiIndex.from_frame(f[['region','month']])).set_axis(f.index)
    regions=sorted(f.region.unique());shocks={};samples=[]
    def indices(r):
        starts=r.integers(0,22,4);return np.concatenate([np.arange(s,s+3) for s in starts]),starts.tolist()
    common={}
    for ri,r in enumerate(regions):
        ix,starts=indices(rng('simulation',0,ri));common[r]=region.loc[r].sort_index().to_numpy()[ix];samples.append(dict(level='region',id=r,block_starts=starts))
    for gid in assigned:
        gi=model.gi[gid];r=model.g.set_index('gym_id').loc[gid,'region'];ix,starts=indices(rng('simulation',1,gi));local=site.loc[f.gym_id==gid].to_numpy()[ix]
        shocks[gid]=common[r]+local;samples.append(dict(level='site',id=gid,block_starts=starts))
    return shocks,dict(fields=fields,block_samples=samples,residual_sd=dict(zip(fields,res.std(ddof=0).tolist())),method='Site-centred transforms minus region calendar-month means and region year effects. Regional and site residuals resampled separately in three-month blocks; complete driver vectors retained. Complaints use log(rate+0.1); logits clipped only for residual estimation, valid zero simulation probabilities stay zero.')

def starting_states(model,gid):
    out={};h=model.h.set_index('gym_id');q=model.l[(model.l.gym_id==gid)&(model.l.month=='2025-12-01')&(model.l.closing_members>0)]
    for _,r in q.iterrows():
        historic=float(h.loc[gid,'change_amount']) if pd.notna(r.repricing_event_id) else 0.
        applied=bool(r.price_increment_applied);base=float(r.base_billed_price)+(historic if applied else 0.)
        out[r.billing_bucket_id]=dict(key=r.billing_bucket_id,cohort_id=r.cohort_id,join_month=r.join_month if pd.notna(r.join_month) else None,original_membership_type=r.original_membership_type,
            tier=r.membership_type,count=int(r.closing_members),base=base,pending=historic if not applied else 0.,historical_applied=applied,historical_event=r.repricing_event_id if pd.notna(r.repricing_event_id) else None,
            protected_until=r.price_protected_until if pd.notna(r.price_protected_until) else None,discount=float(r.promotion_discount_pct),new_policy_applied=False,policy_incumbent=r.membership_type=='Standard',transferred=False)
    check('Integer initial ledger preserved '+gid,sum(s['count'] for s in out.values())==model.dec.loc[gid,'closing_members'])
    return out

def simulate_site(model,gid,simulation,shocks,increment,response_multiplier):
    gi=model.gi[gid];states=starting_states(model,gid);p=model.primary.copy();p[:3]*=response_multiplier
    dose=math.log1p(increment/model.prices[gi,0])/p[3] if increment else 0.;panel=[];ledger=[]
    for j,date in enumerate(model.dates):
        month=date.strftime('%Y-%m-%d');dr=model.dr;shock=shocks[j];flow=lambda stage,key=0:rng('simulation',2,gi,j,stage,key)
        prospects=int(flow(0).poisson(dr['qualified_prospects'][gi,j]*math.exp(shock[0])))
        probs=np.array([dr[k][gi,j] for k in ['standard_join_probability','offpeak_join_probability','plus_join_probability']],float)
        oldsum=probs.sum();probs*=shifted(oldsum,shock[1])/oldsum if oldsum>0 else 0.
        probs[0]*=math.exp(p[0]*math.log1p(increment/model.prices[gi,0]))
        if probs.sum()>1:probs/=probs.sum();CAPS.append([simulation,gid,month,'Recruitment probability'])
        joins=flow(1).multinomial(prospects,[*probs,max(0,1-probs.sum())])[:3]
        for k,tier in enumerate(TIERS):
            key=f'EXP_{gid}_{month}_{tier}';promotion=bool(dr['promotion_active'][gi,j]) and tier=='Standard';expiry=(date+pd.DateOffset(months=model.promo_duration)).strftime('%Y-%m-%d') if promotion else None
            states[key]=dict(key=key,cohort_id=f'{gid}_2026_{j+1:02d}_{tier}',join_month=month,original_membership_type=tier,tier=tier,count=0,new=int(joins[k]),base=float(model.prices[gi,k]),pending=0.,historical_applied=False,historical_event=None,protected_until=expiry,discount=model.promo_discount if promotion else 0.,new_policy_applied=tier=='Standard' and increment>0,policy_incumbent=False,transferred=False)
        movements={};incoming={};incip=incx=incd=paid_num=prot=repriced=joiningdown=0;rowlist=[]
        for key,s in list(states.items()):
            opening=s['count'];new=s.pop('new',0)
            if opening+new==0:continue
            tier=s['tier'];ti=TIERS.index(tier);protected=s['protected_until'] is not None and month<s['protected_until']
            if s['pending'] and not protected:s['base']+=s['pending'];s['pending']=0.;s['historical_applied']=True
            eligible=s['policy_incumbent'] and tier=='Standard' and j>=1 and not protected
            if eligible and increment:s['new_policy_applied']=True
            paid=(s['base']+(increment if s['new_policy_applied'] else 0))*(1-s['discount'] if protected else 1.)
            bh=shifted(dr[['standard_churn','offpeak_churn','plus_churn'][ti]][gi,j],shock[2+ti]);extra=p[1]*dose*(1 if eligible else .5)/model.calibration[0] if s['policy_incumbent'] and tier=='Standard' else 0.
            rawh=bh+extra;ch=float(np.clip(rawh,0,1));same=shifted(dr[['standard_same_month_exit','offpeak_same_month_exit','plus_same_month_exit'][ti]][gi,j],shock[6])
            kd=zlib.crc32(key.encode());ex=int(flow(2,kd).binomial(opening,ch));nx=int(flow(3,kd).binomial(new,same))
            bd=shifted(dr['standard_downgrade'][gi,j],shock[5]);rate=bd+(p[2]*dose/model.calibration[1] if eligible else 0.)
            rawpd=rate/(1-ch) if ch<1 else 0.;pdn=bd/(1-same) if same<1 else 0.
            down=int(flow(4,kd).binomial(opening-ex,np.clip(rawpd,0,1))) if tier=='Standard' else 0
            newdown=int(flow(5,kd).binomial(new-nx,np.clip(pdn,0,1))) if tier=='Standard' else 0
            if rawh!=ch or (tier=='Standard' and (rawpd>1 or rawpd<0 or pdn>1)):CAPS.append([simulation,gid,month,key])
            close=opening+new-ex-nx-down-newdown;s['count']=close;avg=(opening+close)/2
            if down+newdown:
                dest=key+'_TO_OFFPEAK';target=copy.deepcopy(s);target.update(key=dest,tier='Off-Peak',count=0,base=float(model.prices[gi,1]),pending=0.,discount=0.,protected_until=None,new_policy_applied=False,policy_incumbent=False,transferred=True)
                if dest not in states:incoming[dest]=target
                incoming.setdefault(dest,states.get(dest,target));movements[dest]=movements.get(dest,0)+down+newdown
            if s['policy_incumbent'] and tier=='Standard':
                incip+=opening;incx+=ex;incd+=down;paid_num+=opening*paid;prot+=opening if protected else 0;repriced+=opening if s['new_policy_applied'] else 0
            joiningdown+=newdown
            rowlist.append(dict(simulation=simulation,gym_id=gid,month=month,billing_bucket_id=key,cohort_id=s['cohort_id'],join_month=s['join_month'],original_membership_type=s['original_membership_type'],membership_type=tier,
                opening_members=opening,new_members=new,opening_base_cancellations=ex,same_month_cancellations=nx,transfers_in=0,opening_downgrades=down,joining_month_downgrades=newdown,transfers_out=down+newdown,closing_members=close,average_members=avg,
                base_billed_price=s['base'],billed_price=paid,price_protected_until=s['protected_until'],promotion_discount_pct=s['discount'],historical_event_id=s['historical_event'],historical_increment_applied=s['historical_applied'],historical_increment_pending=s['pending'],experiment_increment_applied=s['new_policy_applied'],policy_incumbent=s['policy_incumbent'],subscription_revenue=avg*paid/1.2))
        for dest,count in movements.items():
            target=states.get(dest,incoming[dest]);target['count']+=count;states[dest]=target
            old=next((v for v in rowlist if v['billing_bucket_id']==dest),None)
            if old:
                old['transfers_in']+=count;old['closing_members']+=count;old['average_members']+=count/2;old['subscription_revenue']+=count/2*old['billed_price']/1.2
            else:
                rowlist.append(dict(simulation=simulation,gym_id=gid,month=month,billing_bucket_id=dest,cohort_id=target['cohort_id'],join_month=target['join_month'],original_membership_type=target['original_membership_type'],membership_type='Off-Peak',opening_members=0,new_members=0,opening_base_cancellations=0,same_month_cancellations=0,transfers_in=count,opening_downgrades=0,joining_month_downgrades=0,transfers_out=0,closing_members=count,average_members=count/2,base_billed_price=target['base'],billed_price=target['base'],price_protected_until=None,promotion_discount_pct=0.,historical_event_id=target['historical_event'],historical_increment_applied=target['historical_applied'],historical_increment_pending=0.,experiment_increment_applied=False,policy_incumbent=False,subscription_revenue=count/2*target['base']/1.2))
        f=pd.DataFrame(rowlist);sums=f[['opening_members','new_members','opening_base_cancellations','same_month_cancellations','transfers_in','transfers_out','closing_members','average_members','subscription_revenue']].sum().to_dict()
        fee_payers=int(flow(6).binomial(int(joins.sum()),dr['joining_fee_payer_fraction'][gi,j]));fees=fee_payers*dr['joining_fee'][gi,j]/1.2;anc=dr['ancillary_revenue'][gi,j]*math.exp(shock[9]);av=sums['average_members']
        complaints=int(flow(7).poisson(av/1000*max(0,dr['baseline_complaints_per_1000'][gi,j]*math.exp(shock[7])+(p[4]*dose if j<3 else 0))))
        visits=int(flow(8).poisson(av*dr['visits_per_member'][gi,j]*math.exp(shock[8])));concurrent=visits*dr['visit_duration_minutes'][gi,j]/dr['opening_minutes'][gi,j]
        row=dict(simulation=simulation,gym_id=gid,month=month,is_simulated=True,**sums,qualified_prospects=prospects,standard_joins=int(joins[0]),offpeak_joins=int(joins[1]),plus_joins=int(joins[2]),joining_fee_payers=fee_payers,joining_fee_revenue=fees,ancillary_revenue=anc,monthly_revenue=sums['subscription_revenue']+fees+anc,
            incumbent_standard_opening=incip,incumbent_standard_cancellations=incx,incumbent_standard_downgrades=incd,incumbent_paid_rate_numerator=paid_num,incumbent_protected_opening=prot,incumbent_repriced_opening=repriced,joining_month_downgrades=joiningdown,
            pricing_complaints=complaints,gym_visits=visits,opening_minutes=dr['opening_minutes'][gi,j],visit_duration_minutes=dr['visit_duration_minutes'][gi,j],capacity=dr['capacity'][gi,j],average_utilisation=concurrent/dr['capacity'][gi,j],peak_utilisation=concurrent/dr['capacity'][gi,j]*dr['peak_multiplier'][gi,j],
            marketing_spend=dr['marketing_spend'][gi,j],promotion_active=bool(dr['promotion_active'][gi,j]),standard_price=model.prices[gi,0]+increment,offpeak_price=model.prices[gi,1],plus_price=model.prices[gi,2],competitor_price=dr['competitor_price'][gi,j],competitor_count=float(model.dec.loc[gid,'competitor_count_3km']),probability_caps=sum(x[0]==simulation and x[1]==gid and x[2]==month for x in CAPS))
        for ti,tier in enumerate(TIERS):
            prefix=['standard','offpeak','plus'][ti];t=f[f.membership_type==tier]
            row[prefix+'_opening_members']=int(t.opening_members.sum());row[prefix+'_closing_members']=int(t.closing_members.sum());row[prefix+'_average_members']=float(t.average_members.sum());row[prefix+'_subscription_revenue']=float(t.subscription_revenue.sum())
        panel.append(row);ledger.extend(rowlist)
    return pd.DataFrame(panel),pd.DataFrame(ledger)

def historical_panel(model,ids):
    rows=[]
    for _,v in model.m[(model.m.gym_id.isin(ids))&model.m.month.str.startswith('2025')].iterrows():
        l=model.l[(model.l.gym_id==v.gym_id)&(model.l.month==v.month)];st=l[l.membership_type=='Standard'];old=st[st.opening_members>0]
        row=dict(gym_id=v.gym_id,month=v.month,is_simulated=False,**{f:float(v[f]) for f in ['opening_members','new_members','opening_base_cancellations','same_month_cancellations','closing_members','average_members','subscription_revenue','joining_fee_revenue','ancillary_revenue','monthly_revenue','qualified_prospects','pricing_complaints','marketing_spend','joining_fee_payers','standard_price','offpeak_price','gym_visits','opening_minutes']},
            plus_price=float(v.premium_price),competitor_price=float(v.local_competitor_avg_price),competitor_count=float(v.competitor_count_3km),promotion_active=bool(v.promotion_active),average_utilisation=float(v.utilisation_pct),peak_utilisation=float(v.peak_utilisation_pct),visit_duration_minutes=float(v.average_visit_duration_minutes),capacity=float(model.g.set_index('gym_id').loc[v.gym_id,'capacity_proxy']),
            standard_joins=int(st.new_members.sum()),offpeak_joins=int(l[l.membership_type=='Off-Peak'].new_members.sum()),plus_joins=int(l[l.membership_type=='Plus'].new_members.sum()),
            incumbent_standard_opening=int(st.opening_members.sum()),incumbent_standard_cancellations=int(st.opening_base_cancellations.sum()),incumbent_standard_downgrades=int(old.transfers_out.sum()),incumbent_paid_rate_numerator=float((st.opening_members*st.billed_price).sum()),incumbent_protected_opening=int(st.loc[st.price_protected_until.notna()&(st.month<st.price_protected_until),'opening_members'].sum()),incumbent_repriced_opening=0,
            joining_month_downgrades=int(st.loc[st.new_members>0,'transfers_out'].sum()),transfers_in=int(l.transfers_in.sum()),transfers_out=int(l.transfers_out.sum()),probability_caps=0)
        for ti,tier in enumerate(TIERS):
            t=l[l.membership_type==tier];prefix=['standard','offpeak','plus'][ti]
            for f in ['opening_members','closing_members','average_members','subscription_revenue']:row[prefix+'_'+f]=float(t[f].sum())
        rows.append(row)
    return pd.DataFrame(rows)

SUM_FIELDS=['monthly_revenue','subscription_revenue','joining_fee_revenue','ancillary_revenue','new_members','standard_joins','qualified_prospects','opening_members','average_members','opening_base_cancellations','same_month_cancellations','incumbent_standard_opening','incumbent_standard_cancellations','incumbent_standard_downgrades','incumbent_paid_rate_numerator','incumbent_protected_opening','incumbent_repriced_opening','standard_average_members','standard_subscription_revenue','pricing_complaints','marketing_spend','joining_month_downgrades']
RATE_FIELDS={'incumbent_churn':('incumbent_standard_cancellations','incumbent_standard_opening'), 'incumbent_downgrade':('incumbent_standard_downgrades','incumbent_standard_opening'), 'conversion':('new_members','qualified_prospects'), 'subscription_yield':('subscription_revenue','average_members'), 'standard_yield':('standard_subscription_revenue','standard_average_members'), 'arpmm':('monthly_revenue','average_members'), 'paid_rate':('incumbent_paid_rate_numerator','incumbent_standard_opening'), 'complaints':('pricing_complaints','average_members')}
METRICS={'revenue_effect':'revenue_log','incremental_revenue':'revenue_difference','standard_acquisition_harm':'standard_acquisition_log','all_acquisition_effect':'all_acquisition_log','member_harm':'member_effect','member_difference':'member_difference','incumbent_churn_change_pp':'incumbent_churn_change_pp','incumbent_downgrade_change_pp':'incumbent_downgrade_change_pp','conversion_change_pp':'conversion_change_pp','subscription_yield_change':'subscription_yield_change','standard_yield_change':'standard_yield_change','arpmm_change':'arpmm_change','complaints_change':'complaints_change','subscription_revenue_difference':'subscription_revenue_difference','joining_fee_difference':'joining_fee_difference','ancillary_difference':'ancillary_difference'}

def period(panel,gid,start,end):
    f=panel[(panel.gym_id==gid)&panel.month.between(start,end)].sort_values('month')
    expected=len(pd.date_range(start,end,freq='MS'));check('Period coverage '+gid+'/'+start+'/'+end,len(f)==expected)
    r={k:float(f[k].sum()) for k in SUM_FIELDS};r.update(period_opening=float(f.iloc[0].opening_members),period_closing=float(f.iloc[-1].closing_members),observed_months=expected,average_peak=float(f.peak_utilisation.mean()),maximum_peak=float(f.peak_utilisation.max()),standard_price=float(f.standard_price.mean()),competitor_gap=float((f.competitor_price-f.standard_price).mean()),competitor_count=float(f.competitor_count.mean()),promotion_frequency=float(f.promotion_active.mean()))
    for name,(n,d) in RATE_FIELDS.items():r[name]=ratio(r[n],r[d])*(1000 if name=='complaints' else 1)
    return r

def pair_metrics(tp,tb,cp,cb):
    r=dict(revenue_log=logratio(tp['monthly_revenue'],tb['monthly_revenue'])-logratio(cp['monthly_revenue'],cb['monthly_revenue']),
           standard_acquisition_log=logratio(tp['standard_joins'],tb['standard_joins'])-logratio(cp['standard_joins'],cb['standard_joins']),all_acquisition_log=logratio(tp['new_members'],tb['new_members'])-logratio(cp['new_members'],cb['new_members']))
    factor=ratio(cp['monthly_revenue'],cb['monthly_revenue']);r['revenue_difference']=tp['monthly_revenue']-tb['monthly_revenue']*factor
    for name,field in [('subscription_revenue_difference','subscription_revenue'),('joining_fee_difference','joining_fee_revenue'),('ancillary_difference','ancillary_revenue')]:r[name]=tp[field]-tb[field]*factor
    membercf=tp['period_opening']*ratio(cp['period_closing'],cp['period_opening']);r['member_difference']=tp['period_closing']-membercf;r['member_effect']=ratio(tp['period_closing'],membercf)-1
    for name,target in [('incumbent_churn','incumbent_churn_change_pp'),('incumbent_downgrade','incumbent_downgrade_change_pp'),('conversion','conversion_change_pp'),('subscription_yield','subscription_yield_change'),('standard_yield','standard_yield_change'),('arpmm','arpmm_change'),('complaints','complaints_change')]:r[target]=(tp[name]-tb[name])-(cp[name]-cb[name]);r[target]*=100 if target.endswith('_pp') else 1
    r['control_growth_factor']=factor;r['member_counterfactual']=membercf
    return r

def pair_results(panel,history,pairs):
    full=pd.concat([history.assign(simulation=s) for s in CFG['simulations']]+[panel],ignore_index=True)
    rows=[];periodrows=[]
    for sim in CFG['simulations']:
        f=full[full.simulation==sim]
        for p in pairs:
            for n in CFG['checkpoints']:
                prestart=(pd.Timestamp('2026-01-01')-pd.DateOffset(months=n)).strftime('%Y-%m-%d');postend=f'2026-{n:02d}-01';r=dict(simulation=sim,pair_id=p['pair_id'],population=p['population'],region=p['region'],treatment_gym_id=p['treatment_gym_id'],control_gym_id=p['control_gym_id'],checkpoint_months=n,pre_start=prestart,pre_end='2025-12-01',post_start='2026-01-01',post_end=postend)
                periods={}
                for arm in ['t','c']:
                    gid=p['treatment_gym_id' if arm=='t' else 'control_gym_id']
                    for when,start,end in [('pre',prestart,'2025-12-01'),('post','2026-01-01',postend)]:
                        key=arm+'_'+when;periods[key]=period(f,gid,start,end);periodrows.append(dict(simulation=sim,pair_id=p['pair_id'],checkpoint_months=n,arm_period=key,gym_id=gid,start=start,end=end,**periods[key]))
                        r.update({key+'_'+k:v for k,v in periods[key].items()})
                r.update(pair_metrics(periods['t_post'],periods['t_pre'],periods['c_post'],periods['c_pre']));rows.append(r)
    return pd.DataFrame(rows),pd.DataFrame(periodrows)

def signs(n):return np.array(list(itertools.product([-1,1],repeat=n)),float)
def permutation(v):
    v=np.asarray(v,float);null=signs(len(v))@v/len(v);observed=v.mean();tol=1e-12
    upper=float(np.mean(null>=observed-tol));lower=float(np.mean(null<=observed+tol));return upper,min(1.,2*min(upper,lower))

def statistic(values,metric):
    mean=values.mean(axis=-1)
    if metric in ['revenue_effect','all_acquisition_effect']:return np.expm1(mean)
    if metric=='standard_acquisition_harm':return -np.expm1(mean)
    if metric=='member_harm':return -mean
    if metric in ['incremental_revenue','member_difference','subscription_revenue_difference','joining_fee_difference','ancillary_difference']:return mean*values.shape[-1]
    return mean

def estimates(pairdata,panel):
    out=[];draw_indices={}
    for si,sim in enumerate(CFG['simulations']):
        for n in CFG['checkpoints']:
            f=pairdata[(pairdata.simulation==sim)&(pairdata.checkpoint_months==n)].sort_values('pair_id')
            groups={'First repricing':f[f.population=='First repricing'],'Repeat repricing':f[f.population=='Repeat repricing'],'All assigned pairs':f}
            groups.update({'Region: '+r:g for r,g in f.groupby('region',sort=True)})
            for gi,(name,g) in enumerate(groups.items()):
                count=len(g);complete=np.isfinite(g[list(METRICS.values())]).all(axis=1);q=g[complete];nc=len(q)
                ix=rng('inference',si,n,gi).integers(0,nc,(CFG['bootstrap_samples'],nc)) if nc else None
                draw_indices[f'{sim}|{n}|{name}']=ix.tolist() if ix is not None else []
                for metric,column in METRICS.items():
                    v=q[column].to_numpy(float);value=float(statistic(v,metric)) if nc else np.nan;lo=hi=np.nan
                    if nc>=CFG['minimum_interval_pairs']:lo,hi=map(float,np.percentile(statistic(v[ix],metric),[2.5,97.5]))
                    po=pt=np.nan
                    if metric=='revenue_effect' and nc>=CFG['minimum_interval_pairs']:po,pt=permutation(q.revenue_log)
                    out.append(dict(simulation=sim,population=name,checkpoint_months=n,metric=metric,estimate=value,lower=lo,upper=hi,assigned_pairs=count,complete_pairs=nc,treated_gyms=nc,control_gyms=nc,assignment_flips=2**nc if nc else 0,p_value_one_sided=po,p_value_two_sided=pt,interval_status='Available' if nc>=CFG['minimum_interval_pairs'] else 'Unavailable: fewer than four complete pairs',evidence_status='Simulated workflow demonstration',is_primary=name=='First repricing' and n==6,unit=metric_unit(metric)))
    return pd.DataFrame(out),draw_indices

def metric_unit(metric):
    if metric.endswith('_pp'):return 'percentage points'
    if metric in ['revenue_effect','standard_acquisition_harm','all_acquisition_effect','member_harm']:return 'decimal proportion'
    if metric=='member_difference':return 'members'
    if metric=='complaints_change':return 'complaints per 1,000 average-member months'
    if metric.endswith('yield_change') or metric=='arpmm_change':return 'GBP net per average-member month'
    return 'GBP net'

def decision(values,n,service=False,valid=True,limits=None):
    limits=limits or CFG;required=['revenue_effect','member_harm','standard_acquisition_harm','incumbent_churn_change_pp','incumbent_downgrade_change_pp']
    if not valid or any(k not in values or not all(np.isfinite(values[k][x]) for x in ['estimate','lower','upper']) for k in required):return 'EXTEND TEST','D1_UNAVAILABLE'
    rv=values['revenue_effect'];gates={'member_harm':limits['member_harm_limit'],'standard_acquisition_harm':limits['standard_acquisition_harm_limit'],'incumbent_churn_change_pp':limits['churn_harm_limit_pp'],'incumbent_downgrade_change_pp':limits['downgrade_harm_limit_pp']}
    if rv['upper']<=0 or any(values[k]['lower']>limit for k,limit in gates.items()):return 'STOP','D2_CONFIRMED_HARM_OR_NO_GAIN'
    if service or any(values[k]['estimate']>limit for k,limit in gates.items()):return 'MODIFY','D3_SERVICE_OR_POINT_HARM'
    if n>=6 and rv['lower']>0 and np.isfinite(rv['p_value_one_sided']) and rv['p_value_one_sided']<=limits['alpha'] and all(values[k]['upper']<=limit for k,limit in gates.items()):return 'ROLL OUT','D4_QUALIFIED_FIRST_REPRICING'
    return 'EXTEND TEST','D5_INCONCLUSIVE'

def governance(est,panel,pairs,limits=None):
    limits=limits or CFG;rows=[]
    for sim in CFG['simulations']:
        for n in CFG['checkpoints']:
            for pop in ['First repricing','Repeat repricing','All assigned pairs']:
                q=est[(est.simulation==sim)&(est.checkpoint_months==n)&(est.population==pop)];values=q.set_index('metric').to_dict('index')
                ids=[p[arm+'_gym_id'] for p in pairs if pop=='All assigned pairs' or p['population']==pop for arm in ['treatment','control']]
                f=panel[(panel.simulation==sim)&panel.gym_id.isin(ids)&(panel.month<=f'2026-{n:02d}-01')].sort_values(['gym_id','month'])
                pressure=any(((g.peak_utilisation>=limits['capacity_service_limit']).astype(int).rolling(2).sum()>=2).any() for _,g in f.groupby('gym_id'))
                complaint=values['complaints_change']['estimate']>limits['complaints_service_limit'];service=pressure or complaint
                action,rule=decision(values,n,service,limits=limits)
                # Repeat and pooled findings cannot license independent wider repricing.
                if pop!='First repricing' and action=='ROLL OUT':action='EXTEND TEST';rule='D6_SUPPORTING_POPULATION'
                if sim=='A/A null' and action=='ROLL OUT':action='EXTEND TEST';rule='D7_AA_VALIDATION_ONLY'
                r=dict(simulation=sim,population=pop,checkpoint_months=n,decision=action,rule_id=rule,service_trigger=service,capacity_trigger=pressure,complaints_trigger=complaint,complete_pairs=int(q.complete_pairs.iloc[0]),scope='Conditional comparable first-repricing £1 progression' if pop=='First repricing' and sim!='A/A null' else 'Exploratory or pipeline validation only')
                for metric in ['revenue_effect','incremental_revenue','member_harm','standard_acquisition_harm','incumbent_churn_change_pp','incumbent_downgrade_change_pp','complaints_change']:
                    r.update({metric+'_'+k:values[metric][k] for k in ['estimate','lower','upper']})
                r['p_value_one_sided']=values['revenue_effect']['p_value_one_sided'];rows.append(r)
    return pd.DataFrame(rows)

def power(model):
    f=model.p[model.p.window=='primary_6m'];hist=model.panel[model.panel.event_family=='PILOT_202504'];values=[]
    for _,pair in f.iterrows():
        totals={}
        for arm in ['treatment','control']:
            for when,start,end in [('pre','2024-10-01','2024-12-01'),('post','2025-01-01','2025-03-01')]:
                q=hist[(hist.gym_id==pair[arm+'_gym_id'])&hist.month.between(start,end)];check('Complete power placebo '+pair.pair_id+'/'+arm+'/'+when,len(q)==3);totals[arm+'_'+when]=q.monthly_revenue.sum()
        values.append(logratio(totals['treatment_post'],totals['treatment_pre'])-logratio(totals['control_post'],totals['control_pre']))
    v=np.array(values);center=v-v.mean();sd=float(center.std(ddof=1));nd=NormalDist();z=nd.inv_cdf(1-CFG['alpha']);rows=[]
    check('Twelve pre-intervention pair noise observations',len(center)==12 and np.isfinite(center).all() and sd>0)
    draws=rng('power').choice(center,(CFG['power_samples'],5),replace=True);sg=signs(5);noise_null=draws@sg.T/5;signmeans=sg.mean(axis=1)
    def exact(effect):
        delta=math.log1p(effect);observed=draws.mean(axis=1)+delta;null=noise_null+delta*signmeans
        p=(null>=observed[:,None]-1e-12).mean(axis=1);return float(np.mean(p<=CFG['alpha']))
    lo=0.;hi=CFG['power_maximum_effect'];mde=np.nan
    if exact(hi)>=CFG['power_target']:
        for _ in range(28):
            mid=(lo+hi)/2
            if exact(mid)>=CFG['power_target']:hi=mid
            else:lo=mid
        mde=hi
    for n in CFG['power_pair_counts']:
        for effect in CFG['power_effects']:
            methods=['Exact assignment Monte Carlo','Paired normal approximation'] if n==5 else ['Paired normal approximation']
            for method in methods:
                approximate=method=='Paired normal approximation';pw=nd.cdf(math.log1p(effect)*math.sqrt(n)/sd-z) if approximate else exact(effect)
                md=math.expm1((z+nd.inv_cdf(CFG['power_target']))*sd/math.sqrt(n)) if approximate else mde
                rows.append(dict(design=f'{n} first-repricing pairs',pairs=n,effect_assumption=effect,method=method,planning_power=pw,target_power=CFG['power_target'],effect_detectable_80pct=md,alpha=CFG['alpha'],noise_log_sd=sd,noise_pairs=12,monte_carlo_samples=CFG['power_samples'] if not approximate else None,additional_eligible_gyms_required=max(0,2*n-10),available_primary_design=n==5,evidence_status='Historical placebo noise proxy; prospective planning assumption, not observed power'))
    for n in CFG['power_pair_counts']:
        for multiplier in [.75,1.25]:
            for effect in CFG['power_effects']:
                proxy=sd*multiplier
                rows.append(dict(design=f'{n} first-repricing pairs',pairs=n,effect_assumption=effect,method=f'Paired normal approximation (noise {multiplier:g}x)',planning_power=nd.cdf(math.log1p(effect)*math.sqrt(n)/proxy-z),target_power=CFG['power_target'],effect_detectable_80pct=math.expm1((z+nd.inv_cdf(CFG['power_target']))*proxy/math.sqrt(n)),alpha=CFG['alpha'],noise_log_sd=proxy,noise_pairs=12,monte_carlo_samples=None,additional_eligible_gyms_required=max(0,2*n-10),available_primary_design=n==5,evidence_status='Historical placebo proxy-noise sensitivity; prospective planning assumption'))
    return pd.DataFrame(rows),dict(centered_historical_placebo=center.tolist(),log_sd=sd,exact_primary_mde=mde)

def monitoring(panel,pairs,gov,pairdata):
    lookup={p[a+'_gym_id']:p for p in pairs for a in ['treatment','control']};rows=[]
    for sim in CFG['simulations']:
        for gid,p in sorted(lookup.items()):
            for n in CFG['checkpoints']:
                f=panel[(panel.simulation==sim)&(panel.gym_id==gid)&(panel.month<=f'2026-{n:02d}-01')].sort_values('month');s=period(panel[panel.simulation==sim],gid,'2026-01-01',f'2026-{n:02d}-01')
                capacity=bool(((f.peak_utilisation>=CFG['capacity_service_limit']).astype(int).rolling(2).sum()>=2).any());decisionrow=gov[(gov.simulation==sim)&(gov.population==p['population'])&(gov.checkpoint_months==n)].iloc[0]
                paired=pairdata[(pairdata.simulation==sim)&(pairdata.pair_id==p['pair_id'])&(pairdata.checkpoint_months==n)].iloc[0]
                rows.append(dict(simulation=sim,gym_id=gid,pair_id=p['pair_id'],population=p['population'],assignment='Treatment' if gid==p['treatment_gym_id'] else 'Control',checkpoint_months=n,review_date=pd.Timestamp(2026,n,calendar.monthrange(2026,n)[1]).strftime('%Y-%m-%d'),review_label={1:'Month 1 (~30 days)',3:'Month 3 (~90 days)',6:'Month 6 (~180 days)',12:'Month 12 sustained'}[n],
                    cumulative_revenue=s['monthly_revenue'],closing_members=s['period_closing'],new_members=s['new_members'],standard_joins=s['standard_joins'],qualified_prospects=s['qualified_prospects'],conversion=s['conversion'],incumbent_churn=s['incumbent_churn'],incumbent_downgrade=s['incumbent_downgrade'],subscription_yield=s['subscription_yield'],arpmm=s['arpmm'],complaints_per_1000=s['complaints'],maximum_peak=s['maximum_peak'],capacity_trigger=capacity,paired_complaints_change=paired['complaints_change'],population_decision=decisionrow.decision,required_response='Investigate service pressure and pricing complaints' if capacity or paired['complaints_change']>CFG['complaints_service_limit'] else 'Maintain assignment and monitoring; '+decisionrow.decision.lower()))
    return pd.DataFrame(rows)

def edge_tests():
    valid={k:dict(estimate=0.,lower=0.,upper=0.,p_value_one_sided=.03125) for k in ['revenue_effect','member_harm','standard_acquisition_harm','incumbent_churn_change_pp','incumbent_downgrade_change_pp']}
    valid['revenue_effect'].update(estimate=.02,lower=.001,upper=.04)
    check('Qualification rule with all valid gates',decision(valid,6)[0]=='ROLL OUT')
    check('Early review cannot authorise rollout',decision(valid,3)[0]=='EXTEND TEST')
    for metric,limit in [('member_harm',.03),('standard_acquisition_harm',.10),('incumbent_churn_change_pp',.25),('incumbent_downgrade_change_pp',.25)]:
        q=copy.deepcopy(valid);q[metric].update(estimate=limit,lower=0.,upper=limit);check('Exact harm boundary passes '+metric,decision(q,6)[0]=='ROLL OUT')
        q[metric]['upper']=limit+1e-8;check('Uncertain harm extends '+metric,decision(q,6)[0]=='EXTEND TEST')
        q[metric]['estimate']=limit+1e-8;check('Point harm modifies '+metric,decision(q,6)[0]=='MODIFY')
        q[metric]['lower']=limit+1e-8;check('Confirmed harm stops '+metric,decision(q,6)[0]=='STOP')
    q=copy.deepcopy(valid);q['revenue_effect']['upper']=0.;check('Exact zero upper revenue stops',decision(q,6)[0]=='STOP')
    q=copy.deepcopy(valid);q['revenue_effect']['lower']=0.;check('Exact zero lower revenue does not qualify',decision(q,6)[0]=='EXTEND TEST')
    q=copy.deepcopy(valid);q['member_harm']['upper']=np.nan;check('Unavailable precedes other rules',decision(q,6,service=True)[1]=='D1_UNAVAILABLE')
    check('Service trigger modifies',decision(valid,6,service=True)[0]=='MODIFY')
    check('Zero versus unavailable denominators',ratio(0,4)==0 and np.isnan(ratio(0,0)))
    check('Valid zero cancellation probability retained',shifted(0,100)==0)
    check('Exhausted cancellation probability bounded',shifted(1,-100)==1)
    check('Elasticity direction',math.exp(-1.12*math.log1p(1/25))<1)
    check('Percentage-point conversion',abs((.02345-.02)*100-.345)<1e-12)
    check('Exact five and seven pair assignment spaces',signs(5).shape==(32,5) and signs(7).shape==(128,7))
    check('Null assignment p values',permutation(np.zeros(5))==(1.,1.))
    check('Minimum directional p value',permutation(np.ones(5))[0]==1/32)
    check('Joint pair resampling preserves metric vector',np.array_equal(np.array([[1,10],[2,20]])[[1,0,1]][:,1],10*np.array([[1,10],[2,20]])[[1,0,1]][:,0]))

def validate(design,panel,ledger,pairdata,est,mon,cf,before):
    keys={'design':(design,['gym_id'],80),'monthly':(panel,['simulation','gym_id','month'],756),'pair results':(pairdata,['simulation','pair_id','checkpoint_months'],84),'estimates':(est,['simulation','population','checkpoint_months','metric'],None),'monitoring':(mon,['simulation','gym_id','checkpoint_months'],168),'ledger':(ledger,['simulation','gym_id','month','billing_bucket_id'],None)}
    for name,(df,key,n) in keys.items():
        check('Unique keys '+name,not df.duplicated(key).any())
        if n:check('Row count '+name,len(df)==n)
    forecast=panel[panel.is_simulated];l=ledger
    check('Twelve forecast months per site/case',(forecast.groupby(['simulation','gym_id']).size()==12).all())
    countfields=['opening_members','new_members','opening_base_cancellations','same_month_cancellations','transfers_in','transfers_out','closing_members']
    check('Nonnegative integer ledger counts',all(((l[f]>=0)&(l[f]%1==0)).all() for f in countfields))
    check('Exact ledger membership bridge',(l.opening_members+l.new_members-l.opening_base_cancellations-l.same_month_cancellations+l.transfers_in-l.transfers_out==l.closing_members).all())
    check('Opening and same-month eligible exits',(l.opening_base_cancellations<=l.opening_members).all() and (l.same_month_cancellations<=l.new_members).all())
    check('Surviving populations cap downgrades',(l.opening_downgrades<=l.opening_members-l.opening_base_cancellations).all() and (l.joining_month_downgrades<=l.new_members-l.same_month_cancellations).all())
    check('Opening average closing distinction',np.allclose(l.average_members,(l.opening_members+l.closing_members)/2,atol=0,rtol=0))
    group=['simulation','gym_id','month'];ag=l.groupby(group)[countfields+['average_members','subscription_revenue']].sum();f=forecast.set_index(group)
    for field in countfields+['average_members','subscription_revenue']:check('Ledger-to-monthly '+field,np.max(np.abs(ag[field]-f[field]))<(.01 if field=='subscription_revenue' else 1e-10))
    check('Exact tier totals',np.array_equal(f[['standard_closing_members','offpeak_closing_members','plus_closing_members']].sum(axis=1),f.closing_members))
    check('Transfers reconcile',(ag.transfers_in==ag.transfers_out).all())
    check('Revenue components reconcile',np.max(abs(f.subscription_revenue+f.joining_fee_revenue+f.ancillary_revenue-f.monthly_revenue))<.01)
    check('Funnel joins valid',(f.new_members<=f.qualified_prospects).all() and np.array_equal(f.standard_joins+f.offpeak_joins+f.plus_joins,f.new_members))
    prev=forecast.sort_values(group).groupby(['simulation','gym_id']).closing_members.shift(1);sort=forecast.sort_values(group);check('Consecutive monthly estate/site bridges',np.array_equal(sort.loc[prev.notna(),'opening_members'],prev.dropna()))
    for key,g in l.groupby(['simulation','gym_id','cohort_id'],sort=False):
        stocks=g.groupby('month').closing_members.sum().sort_index();check('Cohort survivors do not rejoin '+str(key),np.all(np.diff(stocks)<=0))
    treatment=set(design.loc[design.assignment=='Treatment','gym_id']);active=l[(l.gym_id.isin(treatment))&(l.simulation!='A/A null')]
    inc=active[active.policy_incumbent & (active.membership_type=='Standard')];check('January notice: incumbents not yet billed',not inc.loc[inc.month=='2026-01-01','experiment_increment_applied'].any())
    protected=inc.price_protected_until.notna()&(inc.month<inc.price_protected_until);check('Promotion protection prevents incumbent repricing',not inc.loc[protected,'experiment_increment_applied'].any())
    eligible=(inc.month>='2026-02-01')&~protected;check('Eligible incumbents repriced after notice',inc.loc[eligible,'experiment_increment_applied'].all())
    newstd=active[(active.new_members>0)&(active.membership_type=='Standard')];check('New Standard joiners pay policy once',newstd.experiment_increment_applied.all())
    controls=l[~l.gym_id.isin(treatment) | (l.simulation=='A/A null')];check('Controls and A/A never acquire experiment billing',not controls.experiment_increment_applied.any())
    delta=l.experiment_increment_applied.astype(int);protection=l.price_protected_until.notna()&(l.month<l.price_protected_until);expected=(l.base_billed_price+delta)*np.where(protection,1-l.promotion_discount_pct,1.)
    check('Actual paid rates preserve differences and one-time increment',np.max(abs(expected-l.billed_price))<1e-10)
    check('Ledger yield revenue calculation',np.max(abs(l.average_members*l.billed_price/1.2-l.subscription_revenue))<1e-9)
    for sim in CFG['simulations']:
        a=forecast[(forecast.simulation==sim)&(~forecast.gym_id.isin(treatment))].drop(columns=['simulation']).reset_index(drop=True);b=forecast[(forecast.simulation=='Main')&(~forecast.gym_id.isin(treatment))].drop(columns=['simulation']).reset_index(drop=True)
        check('Common control paths across simulations '+sim,a.equals(b))
    aa=forecast[forecast.simulation=='A/A null'][cf.columns].drop(columns='simulation').reset_index(drop=True);check('A/A counterfactual path exactly identical',aa.astype(object).equals(cf.drop(columns='simulation').reset_index(drop=True).astype(object)))
    check('No subgroup intervals below four pairs',est.loc[est.complete_pairs<4,['lower','upper']].isna().all().all())
    check('Complete primary and pooled inference',est.loc[est.population.isin(['First repricing','All assigned pairs']),['lower','upper']].notna().all().all())
    check('Pair revenue component difference reconciliation',np.max(abs(pairdata.subscription_revenue_difference+pairdata.joining_fee_difference+pairdata.ancillary_difference-pairdata.revenue_difference))<.01)
    check('All source and previous-phase hashes unchanged',hashes()==before)

def dictionary(frames):
    source=pd.read_csv(AN/'data_dictionary.csv');base={r.field:r for _,r in source.iterrows()} if 'field' in source else {}
    special={'simulation':'Fixed Main, A/A null or Adverse response path. Never sum repeated historical records across these labels.', 'eligible':'Phase 7 candidate action, complete evidence, no caution and plausible £1 increase.', 'disposition':'Assigned, Reserve or Excluded under strict region/repricing-history matching.', 'population':'First repricing is primary; Repeat repricing exploratory; All assigned pairs supporting; regional estimates descriptive.', 'assignment':'One random treatment/control per fixed pair; sites are experimental units.', 'experiment_increment':'Gross Standard price cash increase. £1 treatment, £0 control. A/A is £0 for both.', 'experiment_increment_applied':'Persistent experiment billing status. A true value does not add another monthly increase.', 'historical_increment_pending':'Unfulfilled cash obligation from an actual pre-2026 price event; discharged once at protection expiry.', 'policy_incumbent':'Current Standard state at December 2025 closing, whose original cohort predates 2026; includes unknown-date legacy cohorts.', 'incumbent_standard_opening':'Opening current Standard exposure of pre-2026 original cohorts. Future joiners excluded.', 'incumbent_standard_cancellations':'Opening-base exits from those incumbent current Standard states.', 'incumbent_standard_downgrades':'Opening incumbent Standard transfers to Off-Peak, separate from joining-month transfers and cancellations.', 'incumbent_repriced_opening':'Opening eligible incumbent Standard exposure with the January 2026 policy cash increment already applied.', 'incumbent_paid_rate_numerator':'Sum of incumbent opening exposure × actual gross paid monthly rate.', 'revenue_log':'Treatment minus control log post/pre cumulative total net revenue.', 'revenue_difference':'Treatment post total net revenue minus treatment pre revenue × control total-revenue post/pre ratio; control-derived estimate.', 'control_growth_factor':'Control cumulative post total revenue divided by matching-length pre total revenue.', 'member_effect':'Treatment closing/opening growth factor divided by control closing/opening factor, minus one.', 'member_counterfactual':'Treatment post-opening stock × control post-closing/post-opening stock ratio.', 'estimate':'Equal-pair point estimate. Log effects back-transformed; monetary/member differences sum pairs; rate changes averaged.', 'lower':'2.5th percentile of 10,000 joint whole-pair bootstrap statistics; unavailable below four complete pairs.', 'upper':'97.5th percentile of the same joint whole-pair bootstrap statistics.', 'p_value_one_sided':'Exact fraction of within-pair flips with equal-pair revenue log statistic at least observed. Pre-specified positive direction.', 'p_value_two_sided':'Twice the smaller exact directional tail fraction, capped at one.', 'planning_power':'Prospective rejection probability under an assumed effect and historical placebo noise; never post-hoc observed power.', 'effect_detectable_80pct':'Assumed revenue proportion detectable with 80% planning power; exact method searches up to 20%, otherwise unavailable.', 'probability_caps':'Number of rate/funnel probability caps in that gym-month; stochastic integer population sampling otherwise respects eligible survivors.', 'checkpoint_months':'One, three, six or twelve completed post-intervention calendar months. Day labels are monthly approximations.'}
    keymap={'experiment_design':['gym_id'],'experiment_monthly':['simulation','gym_id','month'],'experiment_pair_results':['simulation','pair_id','checkpoint_months'],'experiment_estimates':['simulation','population','checkpoint_months','metric'],'experiment_power':['design','effect_assumption','method'],'experiment_monitoring':['simulation','gym_id','checkpoint_months'],'experiment_simulation_ledger':['simulation','gym_id','month','billing_bucket_id']};rows=[]
    for name,df in frames.items():
        for field in df.columns:
            stem=field
            for prefix in ['t_pre_','t_post_','c_pre_','c_post_']:
                if field.startswith(prefix):stem=field[len(prefix):];break
            definition=special.get(stem)
            if stem in METRICS:definition='Controlled '+stem.replace('_',' ')+'. '+('Positive values represent harm.' if 'harm' in stem or 'churn' in stem or 'downgrade' in stem else 'Positive revenue values represent gains.')
            if definition is None and stem in base:definition=str(base[stem].definition)
            if definition is None:definition=stem.replace('_',' ').capitalize()+' for the declared gym/pair/population and reporting checkpoint; generated from the documented experiment inputs.'
            if stem!=field:definition=('Treatment' if field.startswith('t_') else 'Control')+' '+('pre' if '_pre_' in field else 'post')+' matching-length period. '+definition
            unit='text / identifier'
            if pd.api.types.is_bool_dtype(df[field]):unit='boolean'
            elif pd.api.types.is_numeric_dtype(df[field]):
                unit='number'
                if stem.endswith('_pp'):unit='percentage points'
                elif any(x in stem for x in ['price','revenue','fee','marketing']) or stem in ['billed_price','base_billed_price','historical_increment_pending','subscription_yield','standard_yield','arpmm','paid_rate']:unit='GBP gross for prices; GBP net for revenue'
                elif any(x in stem for x in ['rate','effect','harm','conversion','utilisation','power','probability','frequency','p_value']) and not any(x in stem for x in ['paid_rate','harm_limit_pp']):unit='decimal proportion'
                elif any(x in stem for x in ['members','joins','cancellations','downgrades','prospects','pairs','gyms','visits','complaints']):unit='counts or exposure; average members can be halves'
            if stem in ['estimate','lower','upper']:unit='Metric-specific unit: see unit column in this interface (GBP, decimal proportion, percentage points or member count)'
            elif stem.endswith('_log') or stem=='revenue_log':unit='dimensionless natural log ratio / controlled log difference'
            elif stem in ['experiment_increment','historical_increment_pending','standard_price','current_standard_price','competitor_gap','competitor_gap_dec2025','base_billed_price','billed_price','paid_rate']:unit='GBP including assumed 20% VAT'
            elif any(x in stem for x in ['subscription_yield','standard_yield','arpmm']):unit='GBP net per average-member month'
            elif stem=='incumbent_paid_rate_numerator':unit='Gross GBP × opening incumbent member exposure'
            elif stem in ['complaints_change','complaints_per_1000','paired_complaints_change','complaints']:unit='Complaints per 1,000 average-member months'
            elif stem=='marketing_per_prospect':unit='GBP marketing spend per qualified prospect'
            elif stem in ['average_members','standard_average_members']:unit='Average member exposure; period fields sum member-months; half-members are possible'
            elif stem in ['checkpoint_months','observed_months']:unit='calendar months'
            elif stem in ['incumbent_churn','incumbent_downgrade','average_peak','maximum_peak','promotion_discount_pct','alpha']:unit='decimal proportion; churn/downgrade are monthly exposure-weighted rates'
            elif stem in ['member_difference','member_counterfactual','period_opening','period_closing']:unit='members; control-derived differences/counterfactuals can be fractional'
            elif stem.startswith('incumbent_') and stem.endswith('_opening'):unit='Opening incumbent member-month exposure'
            elif stem in ['competitor_count','competitor_count_dec2025']:unit='Active fictional competitor count; period means can be fractional'
            elif stem in ['opening_minutes','visit_duration_minutes']:unit='minutes'
            elif stem=='concurrent_capacity':unit='concurrent members at comfortable capacity'
            elif stem=='matching_distance_squared':unit='dimensionless sum of squared standardised-feature distances'
            elif stem=='noise_log_sd':unit='standard deviation of dimensionless natural-log revenue differences'
            elif stem=='monte_carlo_samples':unit='simulation samples'
            if stem in ['month','join_month','review_date','pre_start','pre_end','post_start','post_end','notification_date','incumbent_effective_date','new_joiner_effective_date','price_protected_until']:unit='ISO date'
            rows.append(dict(table=name,field=field,key_field=field in keymap[name],definition=definition,unit=unit,window='2025 synthetic historical pre-period / 2026 simulated post-period, as specified by month or checkpoint',source_status='Observed synthetic records or separately simulated/derived Phase 8 evidence',null_meaning='Blank = unavailable denominator, insufficient complete pairs, inapplicable date/assignment or not applicable; zero is valid'))
    return pd.DataFrame(rows)

def documentation(design,pairs,panel,pairdata,est,powerdata,gov,results):
    p=gov[(gov.simulation=='Main')&(gov.population=='First repricing')&(gov.checkpoint_months==6)].iloc[0];lines=['# Northstar Fitness — controlled £1 pricing pilot','',D1,'',D2,'','Phase 8 designs a small matched-pair experiment and demonstrates its analysis using simulated results. It supports a controlled commercial decision about whether yield gains compensate for recruitment, retention and tier-migration losses. It does not supply independent evidence validating Phase 6 or change Phase 7 actions.','',f'## Main six-month result: {p.decision}','',f'The five primary first-repricing pairs show controlled net revenue {p.revenue_effect_estimate:.2%} (95% interval {p.revenue_effect_lower:.2%} to {p.revenue_effect_upper:.2%}), estimated cumulative cash difference £{p.incremental_revenue_estimate:,.0f} (interval £{p.incremental_revenue_lower:,.0f}–£{p.incremental_revenue_upper:,.0f}). One-sided exact assignment p = {p.p_value_one_sided:.5f}. These are simulated control-derived six-month results, not realised revenue or profit.','', '| Measure | Point | 95% interval | Limit |','|---|---:|---:|---:|']
    for metric,limit in [('member_harm',.03),('standard_acquisition_harm',.10),('incumbent_churn_change_pp',.25),('incumbent_downgrade_change_pp',.25)]:
        if metric.endswith('_pp'):fmt=lambda v:f'{v:.3f} pp'
        else:fmt=lambda v:f'{v:.2%}'
        lines.append(f'| {metric.replace("_"," ")} | {fmt(p[metric+"_estimate"])} | {fmt(p[metric+"_lower"])} to {fmt(p[metric+"_upper"])} | {fmt(limit)} |')
    lines+=['',f'Rule: {p.rule_id}. Service trigger: {p.service_trigger}. Qualification requires confidence bounds, not just positive revenue. The 3% member, 10% Standard acquisition and +0.25 pp churn/downgrade tolerances are Phase 8 management assumptions, distinct from Phase 7 gates.','', '## Design and limits','', 'Fourteen gyms form seven same-region, same-prior-repricing pairs: five first-repricing pairs are primary; two repeat pairs exploratory. Seven gyms receive £1 and seven remain unchanged. NF023 Portsmouth and NF057 Leicester are reserves because they lack a partner in their strict stratum. Eligibility and matching use only data available by December 2025. £2 is not tested. Controls remain unchanged through December 2026, even if a six-month decision supports conditional progression elsewhere.','', 'New Standard prices and notice begin 1 January 2026. Eligible incumbents change on 1 February or at protection expiry. Legacy paid-rate differences and historical obligations persist. Churn, acquisition and downgrades are separate channels; joining-month downgrades are not incumbent responses. Off-Peak and Plus prices stay fixed.','', '## Decisions by simulation','', '| Simulation | Month 1 | Month 3 | Month 6 | Month 12 |','|---|---|---|---|---|']
    for sim in CFG['simulations']:
        vals=gov[(gov.simulation==sim)&(gov.population=='First repricing')].set_index('checkpoint_months');lines.append('| '+sim+' | '+' | '.join(vals.loc[n,'decision'] for n in CFG['checkpoints'])+' |')
    powerrow=powerdata[(powerdata.pairs==5)&(powerdata.method=='Exact assignment Monte Carlo')&(powerdata.effect_assumption==.02)].iloc[0]
    lines+=['',f'## Power and uncertainty','',f'At an assumed 2% revenue effect, planning power is {powerrow.planning_power:.1%}. The estimated 80%-power detectable effect is {powerrow.effect_detectable_80pct:.2%}. Noise is a proxy from twelve historical pre-intervention pair comparisons, not the new experiment’s observed outcome. The one-sided test has 32 assignment flips and minimum p = 3.125%; the minimum two-sided p is 6.25%. Small-sample bootstrap ranges and transport remain uncertain. Repeat pairs and regions have fewer than four pairs: intervals remain unavailable, and they cannot authorise rollout.','', 'Historical parameter uncertainty is the Phase 5/6 uncertainty in assumed effects. Simulated variation is the regional/site trading noise and integer customer-flow sampling. Experimental intervals resample the seven or five observed simulated pairs. They are different distributions. Known simulated no-increase paths are diagnostics and are excluded from the estimator. All A/A paths exactly equal those diagnostic no-increase paths; ordinary treatment/control A/A estimates can still be noisy.','', 'Service review triggers are controlled complaints above two per 1,000 member-months or capacity at/above 100% for two consecutive months in either arm. These flag service investigation, not causal attribution. Competitor recurring prices are frozen in the main simulation; actual competitor reaction and treatment contamination require monitoring in a real pilot.','', 'ROLL OUT permits conditional £1 progression only for comparable first-repricing sites, retaining study controls. Missing evidence extends the test; confirmed harm or no gain stops; unresolved service/point harm modifies. No early review, repeat subgroup, A/A path or pooled supporting result licenses rollout.','', '## Commercial visuals','', '![Pilot profiles](experiment_profiles.png)','', 'Profiles distinguish immediate joining prices from delayed incumbent billing and show why revenue and member trends can diverge. Raw arm totals are not controlled estimates.','', '![Pairs and tolerances](experiment_effects.png)','', 'Pair variation and primary intervals show financial and behavioural uncertainty. Pair dots are not reliable standalone gym causal estimates.','', '![Decisions and power](experiment_decisions.png)','', 'Checkpoint decisions and planning power expose conditions under which a small pilot remains inconclusive. Larger-sample calculations do not invent additional eligible sites.','', '## Delivery and completion','',f'Rows: '+', '.join(f'{k}: {v:,}' for k,v in results['rows'].items())+'.',f'Python validation: {results["checks_passed"]} checks passed. Earlier evidence hashes unchanged. Workbook completion is recorded separately after saved-file recalculation, parity, refresh and visual review.','', 'Monthly membership figures are stocks, not unique customers. Monthly churn is not annual retention. Revenue is net of assumed 20% VAT and is not profit. Historical observations are repeated across simulation labels; do not sum across labels. Simulated post-period integer flows do not replace Phase 6 fractional expected forecasts.','', 'Phase 9 will design the Power BI communication layer after Phase 8 validation is complete.']
    (AN/'experiment_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    method=f'''# Experiment protocol and reproducibility

{D1}

{D2}

What: test a £1 policy in 14 gyms using matched-pair randomisation. Why: a price increase can raise realised yield while harming recruitment, incumbent retention and tier mix. Learn: whether six-month controlled net revenue gains pass explicit member protection. Decision: simulated ROLL OUT, EXTEND TEST, MODIFY or STOP, constrained to comparable first-repricing sites.

Configuration: experiment_config.json. Seed 20261007; SeedSequence keys begin with stream IDs assignment=0, simulation=1, inference=2, power=3. Assignment draws occur after immutable optimal matching. Simulation substreams key regional/site residual block sampling and each site/month/channel/bucket (CRC32 stable bucket keys). The same innovations apply across fixed scenarios and no-increase diagnostics. Adding a scenario does not change existing assignment or flow draws. Bootstrap resamples whole pairs and retains their complete metric vectors. Interval threshold is four complete pairs. Rates use underlying numerators and exposure; zero denominators are unavailable.

Matching uses July–December 2025, same region and prior repricing status. Standardisation uses eligible-candidate population standard deviations. Minimise total squared feature distance over all perfect matchings within each even stratum; ties use lexicographic gym IDs. Singleton reserves are explicit. No post-2026 record informs matching. Primary: five first-repricing pairs. Repeat: two pairs, descriptive. Pooled and regional estimates are supporting only.

Monthly trading noise: site-centred log prospects, logit conversion and cancellation/downgrade/same-month-exit rates, log(complaints per 1,000 +0.1), log visits/member and log ancillary. Subtract region calendar-month and region year effects from 24 observations per gym. Split residual into common region and site deviation. Sample four contiguous three-month blocks from the 24-month history, retaining all driver columns jointly. Logit floor 0.000001 is a transform convention, not an imputation of observed rates; valid zero simulation probabilities remain zero. Counts use Poisson prospects/attendance/complaints, multinomial tier recruitment, binomial eligible exits and survivor-conditioned downgrades. Joining fee payer counts are binomial. Caps are logged. No latent generation parameters are read.

Billing starts from every December cohort/bucket closing integer balance. Historical pending cash obligations apply once at protection expiry. Existing £1 experiment increments start February or later; future Standard joiners receive the increased headline price once, with unchanged promotions. Original cohort follows tier transfers. Opening cancellations precede separately sampled surviving-member downgrades. Average exposure=(opening+closing)/2, acknowledging intra-month timing approximation. Subscription revenue=average exposure×applicable gross paid rate/1.2. Ancillary/marketing/fee policy and shocks are shared across each site's policy/counterfactual. Off-Peak/Plus recurring prices remain unchanged. Only Standard-to-Off-Peak migration is modelled; upgrades, freezes, payment arrears and real operational interventions are omitted.

Primary log revenue difference=ln(Tpost/Tpre)-ln(Cpost/Cpre); equal-pair effect=exp(mean)-1. GBP estimate=sum(Tpost-Tpre×Cpost/Cpre). Component revenue differences use the SAME total-control-growth factor so their sum exactly reconciles to the total difference; they are descriptive allocations, not isolated causal mechanisms. Acquisition uses equivalent log changes. Harm Standard acquisition=1-exp(mean log change). Member harm=negative mean of treatment closing/opening growth divided by control closing/opening growth minus one. Churn/downgrade/conversion use equal-pair before/after differences in exposure-weighted rates, multiplied by 100 for percentage points. Complaints use the analogous per-1,000 exposure rate. Monetary/member difference bootstrap statistics sum the resampled pair contributions, not site interval endpoints. Raw arm summaries use summed numerators/exposures alongside the equal-pair estimates.

Six-month pre: July–December 2025; post: January–June 2026. One, three and twelve months use December; October–December; January–December 2025 pre-periods respectively. One-month reviews approximate 30 days, not exact daily retention milestones. January is notice; February first incumbent billing. Incumbents predate January 2026, including unknown legacy dates; new 2026 joiners have baseline retention, and no joining-month transfer enters incumbent downgrade response.

Exact one-sided revenue test enumerates all 2^n within-pair sign flips, with 1e-12 tie tolerance. Two-sided p=2×min(directional tail probabilities), capped at one. Hypothesis is pre-specified positive revenue, alpha .05. Five pairs imply minimum one-sided p=.03125, two-sided=.0625. Method reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html . NumPy enumeration requires no SciPy installation.

Planning power uses twelve centred historical pilot placebo log revenue effects (October–December 2024 versus January–March 2025). This three-month proxy may misrepresent six-month future variance. Actual five-pair power uses 10,000 sampled null pair vectors and exact 32-flip tests. Search effect 0–20% for 80% power by deterministic bisection. Larger designs use paired normal approximations, explicitly hypothetical and requiring extra eligible sites. Report power curve, MDE and ±25% proxy-noise sensitivity, never observed power.

Decision precedence: missing/invalid uncertainty extends; non-positive revenue upper bound or harm lower bound above tolerance stops; unresolved service or excessive harm point modifies; month >=6, positive revenue lower, one-sided p<=.05 and all harm upper bounds within tolerance conditionally roll out; otherwise extend. Equality passes harm gates, while revenue lower must be strictly positive. Repeat, pooled and A/A populations never independently license rollout. Decisions do not alter simulated paths. Study controls stay unrepriced through twelve months.

Interfaces: experiment_design keyed gym_id (80); experiment_monthly keyed simulation/gym_id/month (756, July 2025–December 2026); experiment_pair_results keyed simulation/pair_id/checkpoint_months (84); experiment_estimates keyed simulation/population/checkpoint_months/metric; experiment_power keyed design/effect_assumption/method; experiment_monitoring keyed simulation/gym_id/checkpoint_months (168); experiment_simulation_ledger keyed simulation/gym_id/month/billing_bucket_id. Historical January–June 2025 is retained as common prepared input for twelve-month comparisons, not duplicated into the 756-row interface. Units and nulls are defined field-by-field in experiment_metric_dictionary.csv.

Run experiment_analysis.py with bundled Python. --reproduce compares byte-identical seven CSVs without replacing source or delivered outputs. experiment_simulation_ledger.csv is the audit billing evidence, not unique customer records. No-increase diagnostic paths and bootstrap selections are retained in the Phase 8 audit directory, excluded from estimator inputs. Both source and preceding analysis hashes are checked before/after. CSVs use ISO dates, numeric GBP, decimal rates, explicit blank unavailable observations and deterministic ordering.
'''
    (AN/'experiment_protocol.md').write_text(method,encoding='utf-8')

def figures(panel,pairdata,est,powerdata,gov):
    sys.path.insert(0,str(AN/'.workbook_previews/python_packages'));import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10});colors={'Treatment':'#176B87','Control':'#A6611A'}
    main=panel[(panel.simulation=='Main')&panel.is_simulated];fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for arm,c in colors.items():
        g=main[main.assignment==arm].groupby('month').sum(numeric_only=True);x=np.arange(1,13)
        for ax,y,label in [(axes[0,0],g.monthly_revenue/1000,'Total net revenue (£ thousands)'),(axes[0,1],g.closing_members,'Closing members'),(axes[1,0],g.incumbent_standard_cancellations/g.incumbent_standard_opening*100,'Incumbent monthly churn (%)'),(axes[1,1],g.incumbent_standard_downgrades/g.incumbent_standard_opening*100,'Incumbent monthly downgrades (%)')]:ax.plot(x,y,label=arm,color=c,marker='o');ax.set_ylabel(label);ax.set_xticks([1,3,6,9,12]);ax.axvline(1,color='#829AB1',linestyle=':');ax.axvline(2,color='#829AB1',linestyle='--');ax.grid(alpha=.15)
    axes[0,0].legend();fig.suptitle('Simulated £1 pilot profiles. January notice; February incumbent billing.');fig.savefig(AN/'experiment_profiles.png',dpi=150);plt.close(fig)
    q=pairdata[(pairdata.simulation=='Main')&(pairdata.checkpoint_months==6)];fig,axes=plt.subplots(1,3,figsize=(14,6),layout='constrained')
    for ax,field,title,limit,scale in [(axes[0],'revenue_log','Controlled revenue effect (%)',0,100),(axes[1],'incumbent_churn_change_pp','Incumbent churn change (pp)',.25,1),(axes[2],'incumbent_downgrade_change_pp','Downgrade change (pp)',.25,1)]:
        vals=np.expm1(q[field])*scale if field=='revenue_log' else q[field]*scale;ax.scatter(vals,np.arange(7),c=['#176B87' if p=='First repricing' else '#A6611A' for p in q.population]);ax.set_yticks(np.arange(7),q.pair_id if ax==axes[0] else ['']*7);ax.set_xlabel(title);ax.axvline(limit,color='#B23A48',linestyle='--');ax.grid(alpha=.15)
        metric='revenue_effect' if field=='revenue_log' else field;r=est[(est.simulation=='Main')&(est.population=='First repricing')&(est.checkpoint_months==6)&(est.metric==metric)].iloc[0]
        ax.errorbar(r.estimate*scale,8,xerr=[[max(0,(r.estimate-r.lower)*scale)],[max(0,(r.upper-r.estimate)*scale)]],fmt='s',color='#243B53',capsize=4);ax.text(.02,.03,'Square: primary 5-pair interval',transform=ax.transAxes,fontsize=9)
    fig.suptitle('Seven pair results and primary uncertainty. Repeat pairs are exploratory.');fig.savefig(AN/'experiment_effects.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,5),layout='constrained');actions=['ROLL OUT','EXTEND TEST','MODIFY','STOP'];cmap=['#2F855A','#718096','#C05621','#B23A48'];matrix=np.array([[actions.index(gov[(gov.simulation==s)&(gov.population=='First repricing')&(gov.checkpoint_months==n)].decision.iloc[0]) for n in CFG['checkpoints']] for s in CFG['simulations']])
    from matplotlib.colors import ListedColormap
    axes[0].imshow(matrix,cmap=ListedColormap(cmap),vmin=-.5,vmax=3.5,aspect='auto');axes[0].set_yticks(range(3),CFG['simulations']);axes[0].set_xticks(range(4),['Month 1','Month 3','Month 6','Month 12'])
    for i in range(3):
        for j in range(4):axes[0].text(j,i,actions[matrix[i,j]],ha='center',va='center',color='white',fontsize=9)
    axes[0].set_title('Primary population decisions')
    for n in [5,10,15]:
        q=powerdata[(powerdata.pairs==n)&(powerdata.method==('Exact assignment Monte Carlo' if n==5 else 'Paired normal approximation'))];axes[1].plot(q.effect_assumption*100,q.planning_power*100,marker='o',label=f'{n} pairs'+(' actual design' if n==5 else ' hypothetical'))
    axes[1].axhline(80,color='#829AB1',linestyle='--');axes[1].set_xlabel('Assumed revenue effect (%)');axes[1].set_ylabel('Planning power (%)');axes[1].set_ylim(0,100);axes[1].legend(fontsize=9);axes[1].grid(alpha=.15);axes[1].set_title('Historical placebo-noise assumption');fig.savefig(AN/'experiment_decisions.png',dpi=150);plt.close(fig)

def source_blocks():
    names=['Recommendations','Scenario Inputs','Scenario Comparison','Monthly Performance','Dataset Overview','README','Recommendation Summary']
    with ZipFile(ROOT/'excel/gym_pricing_model.xlsx') as z:
        paths=xml.sheet_paths(z);out={name:cells(z,paths[name]) for name in names}
    out['Recommendations']={a:v for a,v in out['Recommendations'].items() if 20<=int(''.join(filter(str.isdigit,a)))<=100 or a in ['B4','B5','B6','E4','E5']}
    out['Scenario Inputs']={a:v for a,v in out['Scenario Inputs'].items() if a in ['B3','B4','E23',*[f'I{n}' for n in range(9,18)]]}
    out['Scenario Comparison']={'D3':out['Scenario Comparison']['D3']}
    out['Recommendation Summary']={'A17':out['Recommendation Summary']['A17']}
    return out

def main():
    PRE.mkdir(parents=True,exist_ok=True);CHECKS.clear();CAPS.clear();before=hashes();selected=verify_current_evidence();edge_tests();model=Model();design,pairs,matchinginfo=matching(model);ids=sorted(design.loc[design.disposition=='Assigned','gym_id']);shocks,noiseinfo=noise(model,ids)
    panels=[];ledgers=[];diagnostics=[];lookup=design.set_index('gym_id')
    for gid in ids:
        counter,cl=simulate_site(model,gid,'A/A null',shocks[gid],0,0);diagnostics.append(counter)
        for name,policy in CFG['simulations'].items():
            increment=policy['increment'] if lookup.loc[gid,'assignment']=='Treatment' else 0
            f,l=simulate_site(model,gid,name,shocks[gid],increment,policy['response_multiplier']);panels.append(f);ledgers.append(l)
    forecast=pd.concat(panels,ignore_index=True).sort_values(['simulation','gym_id','month']).reset_index(drop=True);ledger=pd.concat(ledgers,ignore_index=True).sort_values(['simulation','gym_id','month','billing_bucket_id']).reset_index(drop=True);history=historical_panel(model,ids)
    pairdata,periods=pair_results(forecast,history,pairs);est,bootstrap=estimates(pairdata,forecast);powerdata,powerinfo=power(model);gov=governance(est,forecast,pairs);mon=monitoring(forecast,pairs,gov,pairdata)
    panel=pd.concat([history[history.month>='2025-07-01'].assign(simulation=s) for s in CFG['simulations']]+[forecast],ignore_index=True).sort_values(['simulation','gym_id','month']).reset_index(drop=True)
    for field in ['pair_id','assignment','population','region']:panel[field]=panel.gym_id.map(lookup[field]);ledger[field]=ledger.gym_id.map(lookup[field])
    panel['notification_date']=CFG['intervention_date'];panel['incumbent_billing_date']=CFG['billing_date'];panel['source_status']=np.where(panel.is_simulated,'Simulated experiment','Observed synthetic history repeated across labels')
    cf=pd.concat(diagnostics,ignore_index=True).sort_values(['simulation','gym_id','month']).reset_index(drop=True);validate(design,panel,ledger,pairdata,est,mon,cf,before)
    frames=dict(zip(OUTPUTS,[design,panel,pairdata,est,powerdata,mon,ledger]));csvhash={}
    for name,df in frames.items():
        csv=df.to_csv(index=False,float_format='%.12g',lineterminator='\n',na_rep='');encoded=csv.encode('utf-8');csvhash[name]=hashlib.sha256(encoded).hexdigest()
        if '--reproduce' in sys.argv:check('Byte-identical CSV '+name,(DATA/(name+'.csv')).read_bytes()==encoded)
        else:(DATA/(name+'.csv')).write_bytes(encoded)
    results=clean_json(dict(input_hashes=before,configuration_hash=hashlib.sha256((AN/'experiment_config.json').read_bytes()).hexdigest(),csv_hashes=csvhash,rows={k:len(v) for k,v in frames.items()},checks_passed=len(CHECKS),selected_scenario=selected,pairs=pairs,matching=matchinginfo,noise=noiseinfo,power=powerinfo,assumed_response_parameters=model.primary.tolist(),timing_calibration=model.calibration.tolist(),source_driver_fallbacks=model.fallbacks,probability_cap_count=len(CAPS),governance=gov.to_dict('records')))
    if '--reproduce' in sys.argv:
        (PRE/'reproduction.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print('All seven experiment CSVs reproduce byte-identically.');return
    dictionary(frames).to_csv(AN/'experiment_metric_dictionary.csv',index=False,lineterminator='\n');documentation(design,pairs,panel,pairdata,est,powerdata,gov,results);figures(panel,pairdata,est,powerdata,gov)
    (AN/'experiment_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8');(AN/'experiment_validation.md').write_text('# Phase 8 Python validation\n\n'+D1+'\n\n'+D2+'\n\n'+'\n'.join('- PASS: '+c for c in CHECKS)+'\n\nWorkbook completion requires saved-file checks separately.\n',encoding='utf-8')
    (PRE/'diagnostic_no_increase.csv').write_text(cf.to_csv(index=False,float_format='%.12g',lineterminator='\n'),encoding='utf-8');(PRE/'bootstrap_indices.json').write_text(json.dumps(bootstrap,separators=(',',':')),encoding='utf-8')
    (PRE/'input_workbook.xlsx').write_bytes((ROOT/'excel/gym_pricing_model.xlsx').read_bytes()) if not (PRE/'input_workbook.xlsx').exists() else None
    payload=clean_json(dict(config=CFG,sources=source_blocks(),recommendation_columns=json.loads((AN/'.workbook_previews/phase7/layout.json').read_text(encoding='utf-8'))['primary'],monthly_columns=model.m.columns.tolist(),monthly_keys=model.m[['gym_id','month']].to_dict('records'),design=frame_payload(design),monthly=frame_payload(panel),extended_history=frame_payload(history[history.month<'2025-07-01']),pairs=frame_payload(pairdata),periods=frame_payload(periods),estimates=frame_payload(est),power=frame_payload(powerdata),monitoring=frame_payload(mon),governance=frame_payload(gov),pair_assignments=pairs,results=results))
    (PRE/'payload.json').write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8');print(json.dumps(dict(rows=results['rows'],checks=results['checks_passed'],main_six_month=gov[(gov.simulation=='Main')&(gov.population=='First repricing')&(gov.checkpoint_months==6)].to_dict('records')),indent=2))

if __name__=='__main__':main()
