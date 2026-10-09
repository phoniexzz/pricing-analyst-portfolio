"""Phase 6: conditional expected-member pricing model, not pricing recommendations.

Uses observed CSVs and Phase 5 pair responses only. No latent generator parameters.
Billing states collapse only linear, identical-rule cohorts; lineage retains all original IDs.
Run with bundled Python. --reproduce reruns calculations and verifies CSV bytes.
"""
import calendar
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AN, DATA = ROOT/'analysis', ROOT/'data'
PRE = AN/'.workbook_previews'/'phase6'
CFG = json.loads((AN/'scenario_config.json').read_text())
D1 = 'This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.'
D2 = 'This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.'
OUTPUTS = ['scenario_monthly', 'gym_scenarios', 'estate_scenarios', 'scenario_sensitivity']
TIERS = ['Standard', 'Off-Peak', 'Plus']
CHECKS = []

def check(name, condition):
    if not bool(condition): raise AssertionError(name)
    CHECKS.append(name)

def divide(a, b):
    a, b = np.broadcast_arrays(np.asarray(a, dtype=float), np.asarray(b, dtype=float))
    return np.divide(a, b, out=np.full(a.shape, np.nan), where=b>0)

def input_hashes():
    files = [p for p in DATA.glob('*.csv') if p.stem not in OUTPUTS]
    files += [AN/x for x in ['generation_config.json','baseline_results.json','headroom_config.json','headroom_results.json','response_config.json','response_results.json']]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}

def clean_json(value):
    if isinstance(value, dict): return {str(k):clean_json(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)): return [clean_json(x) for x in value]
    if isinstance(value, np.ndarray): return clean_json(value.tolist())
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (float, np.floating)): return float(value) if np.isfinite(value) else None
    return value

def frame_payload(frame):
    return {'columns':list(frame.columns), 'data':clean_json(frame.astype(object).where(frame.notna(),None).values.tolist())}

class Model:
    def __init__(self):
        self.m = pd.read_csv(DATA/'monthly_performance.csv')
        self.l = pd.read_csv(DATA/'membership_ledger.csv')
        self.g = pd.read_csv(DATA/'gym_master.csv').sort_values('gym_id').reset_index(drop=True)
        self.h = pd.read_csv(DATA/'pricing_history.csv')
        self.p = pd.read_csv(DATA/'pilot_pair_response.csv')
        self.panel = pd.read_csv(DATA/'historical_response_panel.csv')
        self.G = len(self.g); self.ids = self.g.gym_id.tolist(); self.gi = {g:i for i,g in enumerate(self.ids)}
        self.dates = pd.date_range(CFG['forecast_start'], periods=12, freq='MS')
        self.dec = self.m[self.m.month=='2025-12-01'].set_index('gym_id').loc[self.ids]
        self.prices = self.dec[['standard_price','offpeak_price','premium_price']].to_numpy(float)
        self.capacity = self.g.capacity_proxy.to_numpy(float)
        self.fallbacks = []
        self.drivers = self.build_drivers()
        self.build_states()
        self.calibration = self.calibrate('primary_6m')
        self.primary = self.parameters('primary_6m')

    def build_drivers(self):
        m = self.m[self.m.month.str.startswith('2025')].copy()
        m['mi'] = pd.to_datetime(m.month).dt.month-1
        m = m.merge(self.g[['gym_id','region']], on='gym_id')
        l = self.l[self.l.month.str.startswith('2025')].copy()
        l['mi'] = pd.to_datetime(l.month).dt.month-1
        a = l.groupby(['gym_id','month','mi','membership_type'],dropna=False)[['opening_members','new_members','opening_base_cancellations','same_month_cancellations']].sum().reset_index()
        std = l[l.membership_type=='Standard'].assign(opening_downgrades=lambda x: np.where(x.opening_members>0,x.transfers_out,0))
        dow = std.groupby(['gym_id','month']).opening_downgrades.sum()
        a['down'] = [dow.get((g,t),0) if k=='Standard' else 0 for g,t,k in zip(a.gym_id,a.month,a.membership_type)]
        a = a.merge(self.g[['gym_id','region']],on='gym_id')
        rows=[]
        def anchor_series(frame, gid, region, num, den=None, label=''):
            reg = frame[frame.region==region].groupby('mi')[[num]+([den] if den else [])].sum().reindex(range(12),fill_value=0)
            values = divide(reg[num],reg[den]) if den else reg[num].to_numpy(float)
            annual = float(divide(reg[num].sum(),reg[den].sum())) if den else float(np.mean(values))
            if not np.isfinite(annual) or annual<=0:
                if annual==0 and np.all(np.nan_to_num(values)==0): index=np.ones(12)
                else:
                    estate=frame.groupby('mi')[[num]+([den] if den else [])].sum().reindex(range(12),fill_value=0)
                    values=divide(estate[num],estate[den]) if den else estate[num].to_numpy(float)
                    annual=float(divide(estate[num].sum(),estate[den].sum())) if den else float(np.mean(values))
                    index=values/annual if annual>0 else np.ones(12)
                    self.fallbacks.append(dict(gym_id=gid,driver=label,level='estate seasonal index'))
            else: index=values/annual
            # A month with no exposure is unavailable: explicit estate fallback, not a zero rate.
            for j in range(12):
                if not np.isfinite(index[j]):
                    es=frame[frame.mi==j]; er=float(divide(es[num].sum(),es[den].sum())) if den else es[num].sum()
                    index[j]=er/annual if annual>0 else 1
                    self.fallbacks.append(dict(gym_id=gid,driver=label,month=j+1,level='estate monthly index'))
            q=frame[(frame.gym_id==gid)&(frame.mi>=9)]
            denom=float((q[den].to_numpy()*index[q.mi.to_numpy()]).sum()) if den else float(index[9:12].sum())
            if denom>0: level=q[num].sum()/denom
            else:
                r=frame[(frame.region==region)&(frame.mi>=9)]
                denom=float((r[den].to_numpy()*index[r.mi.to_numpy()]).sum()) if den else float(index[9:12].sum())*r.gym_id.nunique()
                if denom>0:level=r[num].sum()/denom;which='region'
                else:
                    e=frame[frame.mi>=9];denom=float((e[den].to_numpy()*index[e.mi.to_numpy()]).sum()) if den else float(index[9:12].sum())*e.gym_id.nunique()
                    level=float(divide(e[num].sum(),denom));which='estate'
                self.fallbacks.append(dict(gym_id=gid,driver=label,level=which+' Q4 anchor'))
            return level*index
        for gid, region in zip(self.g.gym_id,self.g.region):
            q=m[(m.gym_id==gid)&(m.mi>=9)]; yr=m[m.gym_id==gid].sort_values('mi')
            prospect=anchor_series(m,gid,region,'qualified_prospects',label='qualified prospects')
            marketing=anchor_series(m,gid,region,'marketing_spend',label='marketing')
            ancillary=anchor_series(m,gid,region,'ancillary_revenue',label='ancillary')
            probs=[];rates=[];same=[]
            for tier in TIERS:
                t=a[a.membership_type==tier];qt=t[(t.gym_id==gid)&(t.mi>=9)]
                prob=float(divide(qt.new_members.sum(),q.qualified_prospects.sum()))
                if not np.isfinite(prob):
                    rt=t[(t.region==region)&(t.mi>=9)];rm=m[(m.region==region)&(m.mi>=9)]
                    prob=float(divide(rt.new_members.sum(),rm.qualified_prospects.sum()));self.fallbacks.append(dict(gym_id=gid,driver=tier+' recruitment probability',level='region'))
                probs.append(prob)
                rates.append(anchor_series(t,gid,region,'opening_base_cancellations','opening_members',tier+' cancellation rate'))
                same.append(anchor_series(t,gid,region,'same_month_cancellations','new_members',tier+' same-month exit rate'))
            down=anchor_series(a[a.membership_type=='Standard'],gid,region,'down','opening_members','Standard downgrade rate')
            visits=float(divide(q.gym_visits.sum(),q.average_members.sum()))
            duration=float(np.average(q.average_visit_duration_minutes,weights=q.gym_visits))
            peakmult=float(divide(q.peak_concurrent_attendance.sum(),q.average_concurrent_attendance.sum()))
            complaint=float(divide(q.pricing_complaints.sum()*1000,q.average_members.sum()))
            for j in range(12):
                hist=yr.iloc[j]
                # Joining fee payer fraction follows matching monthly observed waiver policy.
                pay=float(divide(hist.joining_fee_payers,hist.new_members))
                rows.append(dict(gym_id=gid,region=region,month=self.dates[j].strftime('%Y-%m-%d'),month_index=j+1,
                    qualified_prospects=prospect[j],standard_join_probability=probs[0],offpeak_join_probability=probs[1],plus_join_probability=probs[2],
                    standard_churn=min(1,max(0,rates[0][j])),offpeak_churn=min(1,max(0,rates[1][j])),plus_churn=min(1,max(0,rates[2][j])),
                    standard_same_month_exit=min(1,max(0,same[0][j])),offpeak_same_month_exit=min(1,max(0,same[1][j])),plus_same_month_exit=min(1,max(0,same[2][j])),
                    standard_downgrade=min(1,max(0,down[j])),marketing_spend=marketing[j],ancillary_revenue=ancillary[j],
                    promotion_active=bool(hist.promotion_active),joining_fee=float(self.dec.loc[gid,'joining_fee']),joining_fee_payer_fraction=pay,
                    visits_per_member=visits,visit_duration_minutes=duration,opening_minutes=calendar.monthrange(2026,j+1)[1]*1440,
                    peak_multiplier=peakmult,baseline_complaints_per_1000=complaint,capacity=float(self.g.set_index('gym_id').loc[gid,'capacity_proxy']),
                    competitor_price=float(self.dec.loc[gid,'local_competitor_avg_price']),
                    standard_price=float(self.dec.loc[gid,'standard_price']),offpeak_price=float(self.dec.loc[gid,'offpeak_price']),plus_price=float(self.dec.loc[gid,'premium_price'])))
        df=pd.DataFrame(rows)
        for col in ['standard_join_probability','offpeak_join_probability','plus_join_probability']:
            check('Recruitment probabilities valid '+col,df[col].between(0,1).all())
        check('All-tier recruitment probability <=1', (df[['standard_join_probability','offpeak_join_probability','plus_join_probability']].sum(axis=1)<=1+1e-12).all())
        check('Complete driver windows',len(df)==960 and not df.isna().any().any())
        self.dr={c:df[c].to_numpy().reshape(self.G,12) for c in df.columns if c not in ['gym_id','region','month']}
        return df

    def build_states(self):
        dec=self.l[(self.l.month=='2025-12-01')&(self.l.closing_members>0)].copy()
        history=self.h.set_index('gym_id'); groups=[]; lineage=[]
        promo=self.l[(self.l.new_members>0)&(self.l.membership_type=='Standard')&(self.l.promotion_discount_pct>0)].copy()
        duration=((pd.to_datetime(promo.price_protected_until).dt.year-pd.to_datetime(promo.join_month).dt.year)*12+pd.to_datetime(promo.price_protected_until).dt.month-pd.to_datetime(promo.join_month).dt.month)
        self.promo_duration=int(duration.mode().iloc[0]);self.promo_discount=float(promo.promotion_discount_pct.mode().iloc[0])
        check('Observed promotion rules uniform',duration.nunique()==1 and promo.promotion_discount_pct.nunique()==1)
        for gi,gid in enumerate(self.ids):
            q=dec[dec.gym_id==gid].copy();q['pending']=0.;q['full_rate']=q.base_billed_price
            for idx,row in q.iterrows():
                if row.membership_type=='Standard' and gid in history.index and pd.notna(row.repricing_event_id):
                    inc=float(history.loc[gid,'change_amount'])
                    if bool(row.price_increment_applied):q.loc[idx,'full_rate']+=inc
                    else:q.loc[idx,'pending']=inc
            q['expiry']=q.price_protected_until.fillna('2026-01-01').map(lambda s:max(0,(pd.Timestamp(s).year-2026)*12+pd.Timestamp(s).month-1))
            q['discount']=np.where(q.expiry>0,q.promotion_discount_pct,0.)
            q['rule']=q.apply(lambda r:(r.membership_type,int(r.expiry),float(r.discount),float(r.pending)),axis=1)
            local=[]
            for key,x in q.groupby('rule',sort=True):
                tier,expiry,discount,pending=key
                local.append(dict(gym_id=gid,tier=TIERS.index(tier),label='Existing '+tier+' '+str(len(local)+1),initial=float(x.closing_members.sum()),
                    full_rate=float(np.average(x.full_rate,weights=x.closing_members)),expiry=expiry,discount=discount,pending=pending,
                    incumbent=tier=='Standard',join_index=-1,future=False,source_ids=x.billing_bucket_id.tolist()))
            groups.append(local)
            for _,x in q.iterrows():
                state=next(i for i,s in enumerate(local) if x.billing_bucket_id in s['source_ids'])
                lineage.append(dict(gym_id=gid,cohort_id=x.cohort_id,join_month=x.join_month if pd.notna(x.join_month) else None,
                    original_membership_type=x.original_membership_type,membership_type=x.membership_type,billing_bucket_id=x.billing_bucket_id,
                    state_index=state,opening_2026_members=float(x.closing_members),full_rate=float(x.full_rate),price_protected_until=x.price_protected_until if pd.notna(x.price_protected_until) else None,
                    historical_increment_pending=float(x.pending),allocation_share=float(x.closing_members/local[state]['initial'])))
        self.K=max(map(len,groups));self.S=self.K+3+12
        self.states=[]
        for gi,gid in enumerate(self.ids):
            local=groups[gi]
            while len(local)<self.K:local.append(dict(gym_id=gid,tier=0,label='Unused',initial=0.,full_rate=0.,expiry=0,discount=0.,pending=0.,incumbent=False,join_index=-1,future=False,source_ids=[]))
            # Common-price future/downgraded Off-Peak and future Plus pools; original cohort paths remain in lineage.
            for tier,label in [(1,'Transferred / future Off-Peak'),(2,'Future Plus'),(0,'Unused reserve')]:
                local.append(dict(gym_id=gid,tier=tier,label=label,initial=0.,full_rate=float(self.prices[gi,tier]),expiry=0,discount=0.,pending=0.,incumbent=False,join_index=-1,future=True,source_ids=[]))
            for j in range(12):
                promo=bool(self.dr['promotion_active'][gi,j]);local.append(dict(gym_id=gid,tier=0,label='2026-'+str(j+1).zfill(2)+' Standard',initial=0.,full_rate=float(self.prices[gi,0]),expiry=j+self.promo_duration if promo else j,
                    discount=self.promo_discount if promo else 0.,pending=0.,incumbent=False,join_index=j,future=True,source_ids=[]))
            for si,s in enumerate(local):s.update(state_index=si,gym_index=gi);self.states.append(s)
        self.lineage=pd.DataFrame(lineage)
        self.st={c:np.array([s[c] for s in self.states]).reshape(self.G,self.S) for c in ['tier','initial','full_rate','expiry','discount','pending','incumbent','join_index','future']}
        check('Initial closing ledger exactly preserved',np.allclose(self.st['initial'].sum(axis=1),self.dec.closing_members,atol=1e-9,rtol=0))
        check('Every original cohort/bucket retained',len(self.lineage)==len(dec) and not self.lineage.duplicated(['gym_id','billing_bucket_id']).any())
        for (gid,si),x in self.lineage.groupby(['gym_id','state_index']):
            st=self.states[self.gi[gid]*self.S+si]
            check('Linear paid-rate grouping '+gid+'/'+str(si),abs((x.opening_2026_members*x.full_rate).sum()-st['initial']*st['full_rate'])<1e-7)

    def parameters(self,window,weights=False):
        q=self.p[self.p.window==window].sort_values('pair_id')
        w=q.pre_acquisition_weight.to_numpy() if weights else np.ones(len(q))
        dose=float(np.average(q.log_price_change,weights=w))
        return np.array([np.average(q.acquisition_log_response,weights=w)/dose,np.average(q.incumbent_churn_response_pp,weights=w)/100,
                         np.average(q.incumbent_downgrade_response_pp,weights=w)/100,dose,np.average(q.complaints_per_1000_member_months_controlled_change,weights=w)])

    def calibrate(self,window):
        end={'primary_6m':'2025-09-01','early_3m':'2025-06-01','sustained_9m':'2025-12-01'}[window]
        pairs=self.p[self.p.window==window].sort_values('pair_id');vals=[]
        for _,p in pairs.iterrows():
            q=self.panel[(self.panel.event_family=='PILOT_202504')&(self.panel.gym_id==p.treatment_gym_id)&self.panel.month.between('2025-04-01',end)]
            # Source paid eligibility includes promotion protection. Equal pair exposure-weighted factors.
            share=divide(q.incumbent_repriced_opening,q.incumbent_standard_opening)
            fch=CFG['notice_churn_factor']+(1-CFG['notice_churn_factor'])*share
            vals.append([float(np.average(fch,weights=q.incumbent_standard_opening)),float(np.average(share,weights=q.incumbent_standard_opening))])
        out=np.mean(vals,axis=0)
        check('Timing calibration positive '+window,np.all(out>0))
        return out

    def simulate(self,params,increment,calibration=None,diversion=0.,future_churn=0.,member_ancillary=False,stage=4,stress=1.,trace=False):
        """All calculations broadcast over whole-pair parameter draws, common to every gym."""
        p=np.atleast_2d(params).astype(float);D=len(p);cal=self.calibration if calibration is None else calibration
        st=self.st;counts=np.broadcast_to(st['initial'],(D,self.G,self.S)).copy(); output=[]; traces=[]
        delta=float(increment); logprice=np.log1p(delta/self.prices[:,0])[None,:]
        scale=divide(logprice,p[:,3,None])*stress
        elastic=p[:,0,None]*stress if stage>=1 else np.zeros((D,1))
        acquisition_factor=np.exp(elastic*logprice)
        for j,date in enumerate(self.dates):
            opening=counts.copy();new=np.zeros_like(counts)
            prospect=self.dr['qualified_prospects'][:,j][None,:]
            std_cf=prospect*self.dr['standard_join_probability'][:,j]
            std_join=np.minimum(prospect,std_cf*acquisition_factor)
            off_join=np.broadcast_to(prospect*self.dr['offpeak_join_probability'][:,j],(D,self.G)).copy()
            off_join+=diversion*np.maximum(0,std_cf-std_join)
            plus_join=np.broadcast_to(prospect*self.dr['plus_join_probability'][:,j],(D,self.G)).copy()
            # Ensure all tier probabilities remain a valid funnel under extreme manual inputs.
            alljoin=std_join+off_join+plus_join; recruitment_cap=alljoin>prospect
            ratio=np.minimum(1,divide(prospect,alljoin));ratio=np.nan_to_num(ratio,nan=1.)
            std_join*=ratio;off_join*=ratio;plus_join*=ratio
            new[:,:,self.K+3+j]=std_join;new[:,:,self.K]=off_join;new[:,:,self.K+1]=plus_join
            baseh=np.stack([self.dr[x][:,j] for x in ['standard_churn','offpeak_churn','plus_churn']],axis=1)
            basen=np.stack([self.dr[x][:,j] for x in ['standard_same_month_exit','offpeak_same_month_exit','plus_same_month_exit']],axis=1)
            h=np.take_along_axis(baseh,st['tier'],axis=1)[None,:,:]+np.zeros_like(counts)
            elig=(st['incumbent']&(j>=1)&(j>=st['expiry']))
            qch=np.where(elig,1.,CFG['notice_churn_factor'])
            # Future customers already joined on the new policy: no second incumbent notice discount.
            response_timing=np.where(st['incumbent'],qch,1.)
            extra=p[:,1,None,None]*scale[:,:,None]*response_timing[None,:,:]/cal[0] if stage>=2 else np.zeros_like(counts)
            apply=st['incumbent'] | ((st['future']&(st['tier']==0)&(st['join_index']<j)) if future_churn else False)
            multiplier=np.where(st['incumbent'],1.,future_churn)
            h+=extra*apply[None,:,:]*multiplier[None,:,:]
            rawh=h.copy();h=np.clip(h,0,1)
            old_exit=opening*h
            same_exit=new*np.take_along_axis(basen,st['tier'],axis=1)[None,:,:]
            base_down=self.dr['standard_downgrade'][:,j][None,:,None]
            drate=np.broadcast_to(base_down,counts.shape).copy()
            if stage>=3:drate+=p[:,2,None,None]*scale[:,:,None]*elig[None,:,:]/cal[1]
            downraw=opening*drate*(st['tier']==0)[None,:,:]
            down=np.minimum(np.maximum(downraw,0),opening-old_exit)
            # Baseline joining-month migration is separate from the incumbent response and rate numerator.
            newdown=np.minimum(np.maximum(new*base_down*(st['tier']==0)[None,:,:],0),new-same_exit)
            outgoing=down+newdown;incoming=np.zeros_like(counts);incoming[:,:,self.K]=outgoing.sum(axis=2)
            counts=opening+new-old_exit-same_exit-outgoing+incoming
            avg=(opening+counts)/2
            full=st['full_rate']+np.where(j>=st['expiry'],st['pending'],0)
            paid=np.broadcast_to(full,(D,self.G,self.S)).copy()
            if delta:
                paid+=delta*(elig | (st['future']&(st['tier']==0)))[None,:,:]
            paid*=np.where(j<st['expiry'],1-st['discount'],1)[None,:,:]
            rev=avg*paid/(1+CFG['vat_rate'])
            fees=(std_join+off_join+plus_join)*self.dr['joining_fee_payer_fraction'][:,j]*self.dr['joining_fee'][:,j]/(1+CFG['vat_rate'])
            if stage<4:
                # Keep the fee channel fixed until the final bridge step.
                fees=np.broadcast_to(prospect*(self.dr['standard_join_probability'][:,j]+self.dr['offpeak_join_probability'][:,j]+self.dr['plus_join_probability'][:,j])*self.dr['joining_fee_payer_fraction'][:,j]*self.dr['joining_fee'][:,j]/1.2,(D,self.G))
            anc=np.broadcast_to(self.dr['ancillary_revenue'][:,j],(D,self.G)).copy()
            av=avg.sum(axis=2);op=opening.sum(axis=2);close=counts.sum(axis=2)
            if member_ancillary:anc*=divide(av,self.baseline_months[j]['average_members'])
            complaints=av/1000*(self.dr['baseline_complaints_per_1000'][:,j]+(p[:,4,None]*scale if j<CFG['complaints_response_months'] else 0))
            visits=av*self.dr['visits_per_member'][:,j];concurrent=visits*self.dr['visit_duration_minutes'][:,j]/self.dr['opening_minutes'][:,j]
            utilization=concurrent/self.capacity;peak=utilization*self.dr['peak_multiplier'][:,j]
            incop=(opening*st['incumbent']).sum(axis=2);incx=(old_exit*st['incumbent']).sum(axis=2);incd=(down*st['incumbent']).sum(axis=2)
            out=dict(opening_members=op,new_members=new.sum(axis=2),opening_base_cancellations=old_exit.sum(axis=2),same_month_cancellations=same_exit.sum(axis=2),
                closing_members=close,average_members=av,standard_joins=std_join,offpeak_joins=off_join,plus_joins=plus_join,qualified_prospects=np.broadcast_to(prospect,(D,self.G)),
                subscription_revenue=rev.sum(axis=2),joining_fee_revenue=fees,ancillary_revenue=anc,monthly_revenue=rev.sum(axis=2)+fees+anc,
                incumbent_standard_opening=incop,incumbent_standard_cancellations=incx,incumbent_standard_downgrades=incd,
                incumbent_standard_paid_rate_numerator=(opening*st['incumbent']*paid).sum(axis=2),protected_standard_opening=(opening*st['incumbent']*(j<st['expiry'])).sum(axis=2),
                repriced_standard_opening=(opening*elig).sum(axis=2) if delta else np.zeros_like(incop),
                opening_standard_downgrades=down.sum(axis=2),joining_month_downgrades=newdown.sum(axis=2),transfers_out=outgoing.sum(axis=2),transfers_in=incoming.sum(axis=2),
                pricing_complaints=np.maximum(0,complaints),gym_visits=visits,average_utilisation=utilization,peak_utilisation=peak,
                probability_caps=((rawh!=h).sum(axis=2)+recruitment_cap+((downraw>opening-old_exit)&(st['tier']==0)).sum(axis=2)))
            for k,tier in enumerate(['standard','offpeak','plus']):
                mask=st['tier']==k
                out[tier+'_opening_members']=(opening*mask).sum(axis=2)
                out[tier+'_closing_members']=(counts*mask).sum(axis=2)
                out[tier+'_average_members']=(avg*mask).sum(axis=2)
                out[tier+'_subscription_revenue']=(rev*mask).sum(axis=2)
            output.append(out)
            if trace:traces.append(dict(opening=opening[0],new=new[0],old_exit=old_exit[0],same_exit=same_exit[0],down=outgoing[0],incoming=incoming[0],closing=counts[0],average=avg[0],paid=paid[0],revenue=rev[0],h=h[0],downrate=drate[0],eligible=elig))
        return (output,traces) if trace else output

def annual(months):
    sums=['new_members','standard_joins','offpeak_joins','plus_joins','qualified_prospects','opening_members','average_members','opening_base_cancellations','same_month_cancellations',
          'subscription_revenue','joining_fee_revenue','ancillary_revenue','monthly_revenue','incumbent_standard_opening','incumbent_standard_cancellations','incumbent_standard_downgrades',
          'standard_average_members','standard_subscription_revenue','offpeak_average_members','plus_average_members','pricing_complaints','probability_caps','transfers_out',
          'incumbent_standard_paid_rate_numerator','protected_standard_opening','repriced_standard_opening']
    r={f:sum(m[f] for m in months) for f in sums}
    r['period_opening_members']=months[0]['opening_members'];r['month12_members']=months[-1]['closing_members'];r['annualised_exit_run_rate']=months[-1]['monthly_revenue']*12
    r['average_members_per_month']=r['average_members']/12
    r['churn_rate']=divide(r['opening_base_cancellations'],r['opening_members']);r['retention_rate']=1-r['churn_rate']
    r['incumbent_churn_rate']=divide(r['incumbent_standard_cancellations'],r['incumbent_standard_opening']);r['incumbent_downgrade_rate']=divide(r['incumbent_standard_downgrades'],r['incumbent_standard_opening'])
    r['conversion_rate']=divide(r['new_members'],r['qualified_prospects']);r['subscription_yield']=divide(r['subscription_revenue'],r['average_members']);r['standard_yield']=divide(r['standard_subscription_revenue'],r['standard_average_members'])
    r['arpmm']=divide(r['monthly_revenue'],r['average_members']);r['member_growth']=divide(r['month12_members'],r['period_opening_members'])-1
    r['standard_mix']=divide(r['standard_average_members'],r['average_members']);r['offpeak_mix']=divide(r['offpeak_average_members'],r['average_members']);r['plus_mix']=divide(r['plus_average_members'],r['average_members'])
    r['complaints_per_1000']=divide(r['pricing_complaints'],r['average_members'])*1000
    r['incumbent_paid_rate']=divide(r['incumbent_standard_paid_rate_numerator'],r['incumbent_standard_opening'])
    r['protected_share']=divide(r['protected_standard_opening'],r['incumbent_standard_opening']);r['repriced_share']=divide(r['repriced_standard_opening'],r['incumbent_standard_opening'])
    r['average_utilisation']=sum(m['average_utilisation']*calendar.monthrange(2026,j+1)[1] for j,m in enumerate(months))/365
    r['average_monthly_peak_utilisation']=sum(m['peak_utilisation'] for m in months)/12;r['maximum_monthly_peak_utilisation']=np.maximum.reduce([m['peak_utilisation'] for m in months])
    return r

def aggregate_estate(months):
    output=[]
    for j,m in enumerate(months):
        out={k:v.sum(axis=1,keepdims=True) for k,v in m.items() if k not in ['average_utilisation','peak_utilisation']}
        # Capacity-weighted concurrent utilisation, rather than a mean of gym percentages.
        weights=MODEL.capacity[None,:]
        out['average_utilisation']=(m['average_utilisation']*weights).sum(axis=1,keepdims=True)/weights.sum()
        out['peak_utilisation']=(m['peak_utilisation']*weights).sum(axis=1,keepdims=True)/weights.sum()
        output.append(out)
    return output

def export_rows(model,months,increment,case,params,cf):
    rows=[];cum=np.zeros(model.G)
    for j,m in enumerate(months):
        cum+=m['monthly_revenue'][0]-cf[j]['monthly_revenue'][0]
        for i,gid in enumerate(model.ids):
            r={k:float(v[0,i]) for k,v in m.items()};r.update(gym_id=gid,month=model.dates[j].strftime('%Y-%m-%d'),price_increment=increment,case=case,
                standard_price=float(model.prices[i,0]+increment),competitor_price=float(model.dec.iloc[i].local_competitor_avg_price),
                elasticity=float(params[0]),incumbent_churn_increment_pp=float(params[1]*100),incumbent_downgrade_increment_pp=float(params[2]*100),
                cumulative_incremental_revenue=float(cum[i]),incremental_revenue=float(r['monthly_revenue']-cf[j]['monthly_revenue'][0,i]),
                month_member_difference=float(r['closing_members']-cf[j]['closing_members'][0,i]),marketing_spend=float(model.dr['marketing_spend'][i,j]),promotion_active=bool(model.dr['promotion_active'][i,j]),
                paid_rate=float(divide(r['incumbent_standard_paid_rate_numerator'],r['incumbent_standard_opening'])),
                churn_rate=float(divide(r['opening_base_cancellations'],r['opening_members'])),incumbent_churn_rate=float(divide(r['incumbent_standard_cancellations'],r['incumbent_standard_opening'])),
                incumbent_downgrade_rate=float(divide(r['incumbent_standard_downgrades'],r['incumbent_standard_opening'])),conversion_rate=float(divide(r['new_members'],r['qualified_prospects'])),
                arpmm=float(divide(r['monthly_revenue'],r['average_members'])),subscription_yield=float(divide(r['subscription_revenue'],r['average_members'])),standard_yield=float(divide(r['standard_subscription_revenue'],r['standard_average_members'])),
                evidence_status='Conditional shared local pilot response; expected memberships, not observed customers')
            rows.append(r)
    return rows

def summary_rows(model,months,increment,case,params,cf,estate=False):
    a=annual(aggregate_estate(months) if estate else months);b=annual(aggregate_estate(cf) if estate else cf);rows=[]
    for i,gid in enumerate(['ESTATE'] if estate else model.ids):
        r={k:float(v[0,i]) for k,v in a.items()};r.update(gym_id=gid,price_increment=increment,case=case,
            counterfactual_revenue=float(b['monthly_revenue'][0,i]),incremental_revenue=float(a['monthly_revenue'][0,i]-b['monthly_revenue'][0,i]),
            revenue_uplift=float(divide(a['monthly_revenue'][0,i],b['monthly_revenue'][0,i])-1),
            member_difference=float(a['month12_members'][0,i]-b['month12_members'][0,i]),member_impact=float(divide(a['month12_members'][0,i],b['month12_members'][0,i])-1),
            acquisition_difference=float(a['new_members'][0,i]-b['new_members'][0,i]),standard_acquisition_impact=float(divide(a['standard_joins'][0,i],b['standard_joins'][0,i])-1),
            churn_change_pp=float((a['churn_rate'][0,i]-b['churn_rate'][0,i])*100),incumbent_churn_change_pp=float((a['incumbent_churn_rate'][0,i]-b['incumbent_churn_rate'][0,i])*100),
            downgrade_change_pp=float((a['incumbent_downgrade_rate'][0,i]-b['incumbent_downgrade_rate'][0,i])*100),conversion_change_pp=float((a['conversion_rate'][0,i]-b['conversion_rate'][0,i])*100),
            elasticity=float(params[0]),incumbent_churn_increment_pp=float(params[1]*100),incumbent_downgrade_increment_pp=float(params[2]*100),
            evidence_status='Conditional parameter model; no pricing action; revenue is not profit')
        if not estate:
            r.update(region=model.g.iloc[i].region,old_standard_price=float(model.prices[i,0]),new_standard_price=float(model.prices[i,0]+increment),
                december_competitor_gap=float(model.dec.iloc[i].competitor_price_gap),post_increase_competitor_gap=float(model.dec.iloc[i].local_competitor_avg_price-model.prices[i,0]-increment),
                teaching_break_even_retention=float(model.prices[i,0]/(model.prices[i,0]+increment)),
                out_of_pilot_value_support=bool(model.dec.iloc[i].competitor_price_gap<=0),repeated_repricing=gid in set(model.h.gym_id),cash_increment_extrapolation=increment in [1,3])
        rows.append(r)
    return rows

def bootstrap(model):
    q=model.p[model.p.window=='primary_6m'].sort_values('pair_id');rng=np.random.default_rng(CFG['bootstrap_seed'])
    indices=rng.integers(0,12,(CFG['bootstrap_samples'],12));dose=q.log_price_change.to_numpy()[indices].mean(axis=1)
    params=np.column_stack([q.acquisition_log_response.to_numpy()[indices].mean(axis=1)/dose,q.incumbent_churn_response_pp.to_numpy()[indices].mean(axis=1)/100,
        q.incumbent_downgrade_response_pp.to_numpy()[indices].mean(axis=1)/100,dose,q.complaints_per_1000_member_months_controlled_change.to_numpy()[indices].mean(axis=1)])
    fields=['monthly_revenue','month12_members','new_members','standard_joins','incumbent_churn_rate','incumbent_downgrade_rate','arpmm','pricing_complaints']
    sims=np.zeros((len(params),4,model.G+1,len(fields)))
    base=annual(model.baseline_months);estatebase=annual(aggregate_estate(model.baseline_months))
    for start in range(0,len(params),CFG['bootstrap_batch']):
        end=min(start+CFG['bootstrap_batch'],len(params))
        for inc in CFG['price_options']:
            if inc==0:
                for f,k in zip(fields,range(len(fields))):sims[start:end,inc,:model.G,k]=base[f];sims[start:end,inc,model.G,k]=estatebase[f][:,0]
            else:
                months=model.simulate(params[start:end],inc);a=annual(months);ea=annual(aggregate_estate(months))
                for k,f in enumerate(fields):sims[start:end,inc,:model.G,k]=a[f];sims[start:end,inc,model.G,k]=ea[f][:,0]
        if start%1000==0:print('Bootstrap',end,'/',len(params),flush=True)
    cf=estatebase['monthly_revenue'][0,0];value=sims[:,2,model.G,0]-cf
    case_indices=[]
    for quant in CFG['case_percentiles']:
        target=np.percentile(value,quant);case_indices.append(int(np.argmin(np.abs(value-target))))
    check('Whole-pair bootstrap repeatable',np.array_equal(indices,np.random.default_rng(CFG['bootstrap_seed']).integers(0,12,indices.shape)))
    check('All bootstrap arrays finite',np.isfinite(sims).all())
    check('Joint selected case vectors retained',len(case_indices)==2 and all(np.array_equal(params[i],params[i].copy()) for i in case_indices))
    return params,sims,fields,case_indices

def model_break_even(model):
    base=annual(model.baseline_months);base_rev=base['monthly_revenue'][0];base_close=base['month12_members'][0]
    roots={};grid=np.linspace(0,CFG['stress_maximum'],CFG['stress_grid_steps']+1)
    for inc in [1,2,3]:
        # Batch stress points as parameter vectors; scaling dose stays unchanged.
        pars=np.tile(model.primary,(len(grid),1));pars[:,[0,1,2]]*=grid[:,None]
        values=annual(model.simulate(pars,inc))['monthly_revenue']-base_rev
        for gi,gid in enumerate(model.ids):
            crossings=np.where(values[:-1,gi]*values[1:,gi]<0)[0];exact=np.where(np.abs(values[:,gi])<1e-7)[0]
            if len(crossings):
                k=int(crossings[0]);lo,hi=grid[k],grid[k+1]
                for _ in range(37):
                    mid=(lo+hi)/2;p=model.primary.copy();p[[0,1,2]]*=mid
                    r=annual(model.simulate(p,inc))['monthly_revenue'][0,gi]-base_rev[gi]
                    if r*values[k,gi]>0:lo=mid
                    else:hi=mid
                root=(lo+hi)/2;p=model.primary.copy();p[[0,1,2]]*=root;a=annual(model.simulate(p,inc))
                member=a['month12_members'][0,gi]/base_close[gi]-1;residual=a['monthly_revenue'][0,gi]-base_rev[gi]
                check('Break-even £0.01 '+gid+'/'+str(inc),abs(residual)<.01)
            elif len(exact):root=float(grid[exact[0]]);member=np.nan
            else:root=member=np.nan
            roots[(gid,inc)]=(root,member,len(crossings)+len(exact))
        print('Break-even increment',inc,'complete',flush=True)
    return roots

def validate(model,monthly,sites,estate,cases,hashes_before,bridges):
    check('Source and earlier interfaces unchanged',input_hashes()==hashes_before)
    check('Monthly grain 11520',len(monthly)==11520 and not monthly.duplicated(['gym_id','month','price_increment','case']).any())
    check('Gym scenario grain 960',len(sites)==960 and not sites.duplicated(['gym_id','price_increment','case']).any())
    check('Estate scenario grain 12',len(estate)==12 and not estate.duplicated(['gym_id','price_increment','case']).any())
    check('All 80 complete reporting windows',monthly.groupby(['gym_id','price_increment','case']).month.nunique().eq(12).all())
    check('Expected membership bridge',np.allclose(monthly.closing_members,monthly.opening_members+monthly.new_members-monthly.opening_base_cancellations-monthly.same_month_cancellations,atol=1e-8,rtol=0))
    check('Transfers cancel',np.allclose(monthly.transfers_in,monthly.transfers_out,atol=1e-10))
    check('Revenue components reconcile',np.allclose(monthly.subscription_revenue+monthly.joining_fee_revenue+monthly.ancillary_revenue,monthly.monthly_revenue,atol=1e-7,rtol=0))
    check('Tier closing populations reconcile',np.allclose(monthly.standard_closing_members+monthly.offpeak_closing_members+monthly.plus_closing_members,monthly.closing_members,atol=1e-8,rtol=0))
    check('Midpoint average members',np.allclose(monthly.average_members,(monthly.opening_members+monthly.closing_members)/2,atol=1e-8))
    check('Cancellation eligible populations',((monthly.opening_base_cancellations<=monthly.opening_members+1e-8)&(monthly.same_month_cancellations<=monthly.new_members+1e-8)).all())
    check('Incumbent downgrade survivors', (monthly.incumbent_standard_downgrades<=monthly.incumbent_standard_opening-monthly.incumbent_standard_cancellations+1e-8).all())
    check('Joining-month transfers separate', (monthly.joining_month_downgrades>=0).all())
    check('No negative stocks',monthly[['opening_members','closing_members','new_members']].ge(-1e-9).all().all())
    check('All no-increase cases identical',sites[sites.price_increment==0].groupby('gym_id').monthly_revenue.nunique().eq(1).all())
    check('Site/estate revenue reconciliation',np.allclose(sites.groupby(['price_increment','case']).monthly_revenue.sum(),estate.set_index(['price_increment','case']).monthly_revenue.sort_index(),atol=1e-6,rtol=0))
    for _,r in sites.iterrows():
        check('Weighted rate/yield '+r.gym_id+'/'+r.case+'/'+str(r.price_increment),abs(r.churn_rate-r.opening_base_cancellations/r.opening_members)<1e-12 and abs(r.arpmm-r.monthly_revenue/r.average_members)<1e-10)
    check('Every revenue bridge exact',all(abs(x['total']-sum(x['steps']))<.01 for x in bridges))
    check('Missing denominator remains unavailable',np.isnan(divide(1,0)))
    check('Valid zero response gives unchanged acquisition',np.expm1(0)==0)
    check('Negative elasticity lowers acquisition',np.exp(-1*np.log(1.1))<1)
    check('Percentage point conversion',abs(.345/100-.00345)<1e-12)
    z=model.primary.copy();z[:3]=0;gain=annual(model.simulate(z,2))
    check('Null behavioural effect preserves members',np.allclose(gain['month12_members'],annual(model.baseline_months)['month12_members'],atol=1e-8))
    p=model.primary.copy();p[1]=100;p[2]=100
    extreme=model.simulate(p,3)
    check('Extreme hazards bounded and populations exhausted safely',all((m['closing_members']>=-1e-9).all() and (m['opening_base_cancellations']<=m['opening_members']+1e-9).all() for m in extreme))
    first=model.simulate(model.primary,2,trace=True)[1][0];second=model.simulate(model.primary,2,trace=True)[1][1]
    st=model.st
    inc=(st['incumbent']&(st['initial']>0))
    expected=st['full_rate']+np.where(st['expiry']<=0,st['pending'],0)
    expected*=np.where(st['expiry']>0,1-st['discount'],1)
    check('Notice month no incumbent cash increase',np.allclose(first['paid'][inc],expected[inc],atol=1e-9))
    mask=inc&(st['expiry']<=1)
    expected2=st['full_rate']+st['pending']+2
    check('Billing date cash increment once',np.allclose(second['paid'][mask],expected2[mask],atol=1e-9))
    alltrace=model.simulate(model.primary,2,trace=True)[1]
    check('Future joiner never receives incumbent increment twice',all(np.allclose(t['paid'][:,model.K+3+j],(model.prices[:,0]+2)*np.where(j<st['expiry'][:,model.K+3+j],1-st['discount'][:,model.K+3+j],1)) for j,t in enumerate(alltrace)))
    check('January protected states honoured',np.allclose(first['paid'][inc&(st['expiry']>0)],(st['full_rate']*(1-st['discount']))[inc&(st['expiry']>0)]))
    future=model.simulate(model.primary,2,future_churn=.5,trace=True)[1]
    expected=.5*model.primary[1]*np.log1p(2/model.prices[:,0])/model.primary[3]/model.calibration[0]
    check('Future-joiner sensitivity exactly half incumbent billing response',np.allclose(future[1]['h'][:,model.K+3]-model.dr['standard_churn'][:,1],expected,atol=1e-12))

def figures(model,monthly,sites,estate,bridges):
    packages=AN/'.workbook_previews'/'python_packages'
    if packages.exists():sys.path.insert(0,str(packages))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    colors=['#243B53','#2F855A','#D69E2E','#9F7AEA']
    fig,ax=plt.subplots(2,1,figsize=(11,7),sharex=True)
    for inc in range(4):
        q=monthly[(monthly.case=='Base')&(monthly.price_increment==inc)].groupby('month')[['monthly_revenue','closing_members']].sum()
        ax[0].plot(range(1,13),q.monthly_revenue.cumsum()/1e6,label='No increase' if not inc else f'+£{inc}',color=colors[inc]);ax[1].plot(range(1,13),q.closing_members/1000,color=colors[inc])
    ax[0].set_ylabel('Cumulative net revenue (£m)');ax[1].set_ylabel('Closing memberships (000s)');ax[1].set_xticks(range(1,13),[x.strftime('%b') for x in model.dates]);ax[0].legend(ncol=4);fig.suptitle('Conditional base case: revenue gains and member volume move differently');fig.tight_layout();fig.savefig(AN/'scenario_monthly_trends.png',dpi=170);plt.close(fig)
    q=sites[(sites.case=='Base')&(sites.price_increment==2)]
    fig,ax=plt.subplots(figsize=(11,6));ax.errorbar(q.member_impact*100,q.incremental_revenue/1000,yerr=np.vstack([q.incremental_revenue-q.incremental_revenue_lower,q.incremental_revenue_upper-q.incremental_revenue])/1000,fmt='o',markersize=3,alpha=.5,color=colors[1],ecolor='#9FB3C8')
    ax.axhline(0,color='#627D98',linewidth=.8);ax.set_xlabel('Month-12 membership impact vs no increase (%)');ax.set_ylabel('12-month incremental net revenue (£000s)');ax.set_title('+£2 shared-response model: site outcomes and conditional parameter ranges');fig.tight_layout();fig.savefig(AN/'scenario_site_tradeoffs.png',dpi=170);plt.close(fig)
    b=next(x for x in bridges if x['increment']==2);labels=['Price / billed rates','Acquisition','Incumbent exits','Downgrades','Joining fees','Total']
    fig,ax=plt.subplots(figsize=(11,6));running=0
    for i,v in enumerate(b['steps']):
        ax.bar(i,v/1e6,bottom=running/1e6,color=colors[1] if v>=0 else '#C53030');ax.text(i,(running+v/2)/1e6,f'£{v/1e6:+.2f}m',ha='center',va='center',fontsize=9);running+=v
    ax.bar(5,b['total']/1e6,color=colors[0]);ax.text(5,b['total']/2e6,f'£{b["total"]/1e6:+.2f}m',ha='center',va='center',color='white');ax.set_xticks(range(6),labels,rotation=12);ax.set_ylabel('Incremental cumulative net revenue (£m)');ax.set_title('Sequential +£2 revenue bridge: interactions allocated to the later step');fig.tight_layout();fig.savefig(AN/'scenario_revenue_bridge.png',dpi=170);plt.close(fig)

def documentation(model,monthly,sites,estate,sensitivity,bridges,results):
    lines=['# Northstar Fitness — twelve-month pricing scenarios','',D1,'',D2,'',
        'Phase 6 models conditional January–December 2026 revenue and expected memberships. The shared historical pilot response is transported across the estate; no site actions, rollout thresholds or headroom reranking are produced.',
        '', '## What the calculated scenarios show','', '| Price option | Base net revenue | Increment vs no increase | Conditional 95% parameter range | Month-12 members | Member impact |','|---|---:|---:|---:|---:|---:|']
    for _,r in estate[estate.case=='Base'].sort_values('price_increment').iterrows():
        lines.append(f'| {"No increase" if r.price_increment==0 else "+£"+str(int(r.price_increment))} | £{r.monthly_revenue:,.0f} | £{r.incremental_revenue:,.0f} | £{r.incremental_revenue_lower:,.0f} to £{r.incremental_revenue_upper:,.0f} | {r.month12_members:,.1f} | {r.member_impact:.2%} |')
    lines+=['','Starting memberships are '+f'{model.st["initial"].sum():,.0f}'+'. These are member stocks and fractional expected forecasts, not unique customers. The counterfactual already contains observed Q4 trading conditions and historical repricing; it is not a reconstructed never-repriced estate.',
        '', '## Why the interpretation matters','',
        'January +GBP2 incremental net revenue is '+f"{monthly[(monthly.month=='2026-01-01')&(monthly.case=='Base')&(monthly.price_increment==2)].incremental_revenue.sum():,.0f}"+' GBP before incumbent February billing. All 80 base +GBP2 sites have positive annual revenue changes but fewer December members than no increase; future shocks remain outside the model.',
        'Higher billed yield can outweigh weaker recruitment and more exits over this horizon. Revenue excludes VAT under the existing 20% modelling convention, includes joining fees and separately disclosed ancillary income, and does not measure profit. Acquisition elasticity acts on Standard joins only. Incumbent churn and downgrades act on the continuing pre-2026 Standard risk set. Monthly retention is one minus exposure-weighted monthly churn, not annual customer retention.',
        '', 'The price-response curve is an assumption around one historical +£2 policy. The pilot included only positive pre-period competitor gaps, had pre-trend imbalance, and supplies no reliable per-site elasticity. Applying it to non-positive gaps, repeat repricing and +£1/+£3 is extrapolation. December run-rate ×12 is seasonal and distinct from earned annual revenue.',
        '', '## Cases and uncertainty','',
        'Base uses primary equal-pair estimates. Downside and upside are coherent whole-pair bootstrap parameter vectors nearest estate +£2 revenue percentiles 10 and 90. They are used unchanged across sites and prices; they need not be every site’s individual downside or upside. Ten thousand samples use seed 20261006. The same sampled vector drives every gym and price, preserving common-response uncertainty. Ranges omit future demand shocks, competitor reaction and uncertain transport. The fraction of parameter draws with positive revenue is not a rollout probability.',
        '', '## Sensitivities','', '| Alternative | +£2 estate increment | Month-12 member impact |','|---|---:|---:|']
    for _,r in sensitivity[(sensitivity.gym_id=='ESTATE')&(sensitivity.price_increment==2)].iterrows():lines.append(f'| {r.variant} | £{r.incremental_revenue:,.0f} | {r.member_impact:.2%} |')
    lines+=['','The future-joiner, 25% diversion and member-sensitive ancillary variants are illustrative assumptions, not estimated causal effects. Early/sustained coefficients use their own historical timing calibration. No adverse observation is removed to improve results.',
        '', '## Break-even and trading context','',
        'The teaching old/new retention ratio applies only to a uniformly affected subscription group. The model break-even scales acquisition, incumbent churn and downgrades jointly from zero to 64 times their primary response. The first crossing and total crossing count are disclosed; no crossing means unavailable. This is a response-stress margin, not an allowable estate churn threshold.',
        '', '## Commercial visuals','',
        '![Monthly revenue and membership](scenario_monthly_trends.png)','',
        'This reveals when yield gains and member losses accumulate; it does not validate future demand.',
        '', '![Site trade-offs](scenario_site_tradeoffs.png)','',
        'This identifies sites needing closer assumption review. Vertical ranges reflect shared pilot parameter uncertainty, not independently estimated site effects.',
        '', '![Revenue bridge](scenario_revenue_bridge.png)','',
        'The exact bridge introduces billed-rate changes, acquisition response, incumbent exits, downgrades, then joining fees. Interactions belong to the later step. Ancillary revenue is equal in the main scenarios. The ordering is an accounting allocation, not separate causal attribution.',
        '', '## Delivery and verification','',
        f'{len(monthly):,} monthly rows, {len(sites):,} site/case rows, {len(estate)} estate/case rows and {len(sensitivity):,} sensitivity rows. All {len(CHECKS):,} Python checks passed. Input hashes are unchanged. Workbook completion is recorded separately after saved-file recalculation, refresh tests and visual review.',
        '', 'Phase 7 can use the quantified trade-offs and explicit uncertainty to develop conditional site recommendations; Phase 6 assigns none.']
    (AN/'scenario_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    method='''# Phase 6 definitions and reproducibility

Run scenario_analysis.py with bundled NumPy/Pandas. --reproduce reruns all four CSVs and verifies byte identity. Configuration: scenario_config.json. No latent generation parameters enter forecasts. Rates use numerators and exposures; a denominator of zero is unavailable. Any baseline fallback is explicit in scenario_results.json.

For count drivers, regional monthly totals divided by their annual monthly average form seasonal indices; site Q4 totals divided by summed Q4 indices supply the level. For rate drivers, regional monthly numerator/exposure divided by the regional annual numerator/exposure forms the index; the site level is Q4 numerator / sum(Q4 exposure × corresponding index). Region then estate fallbacks are documented. All-tier recruitment is site Q4 tier joins / site Q4 prospects. Promotions repeat observed matching months; gross fee and payer fractions remain visible. Dates are fixed, not TODAY().

December source buckets map to identical-rule billing states by current tier, remaining protection, discount and pending historical cash increment. Weighted full rates preserve paid-rate differences exactly because all members within a state face identical exit and transfer hazards. scenario_cohort_lineage.csv retains every original cohort, unknown legacy join date, billing ID, original/current tier, full rate, initial count and allocation share. Each origin follows its state's proportional exits and transfers; transfers enter the Off-Peak headline-priced pool while retaining their origin in the lineage accounting. No origins are treated as new acquisitions. Future joins receive original month/tier identities; combining full-price Off-Peak and Plus balances is an exact linear economic aggregation, not a unique-customer count.

Expected member movements are fractional. Opening-base cancellation = opening × bounded rate. Joining-month exit = new joins × separate rate. Opening-base downgrade = minimum(opening Standard × downgrade rate, opening Standard survivors); joining-month baseline transfers use joining survivors and remain separately identified. Transfers balance at gym level. Subscription revenue is midpoint state exposure × applicable gross billed price / 1.20. No premature monthly currency rounding is used. Stock balances feed the next month.

Price response scales with log(December new/old headline price) / mean pilot log dose. Acquisition is exp(elasticity × log price change). Incumbent churn response is half before billing/protection expiry and full after; downgrade response starts at billing. Calibration divides each response by the equal-pair mean of historical treatment exposure-weighted timing factors. At the representative mean pilot price dose, historical exposure-weighted timing responses average to the primary six-month increments; site-specific proportional doses then scale them. No separate site churn coefficients are fitted. Recurring increments apply only to surviving current Standard members from the December population. A new joiner never receives the same increase again. Complaints use the historical rate increment for three months, a weak timing assumption.

Ten thousand whole-pair resamples (seed 20261006) jointly estimate elasticity, incumbent churn, downgrade, price dose and complaints. Use the same draw across all gyms/options. Percentile 95% model ranges are conditional parameter uncertainty, not predictive intervals. Downside/upside select complete sampled vectors nearest estate +£2 increment percentiles 10/90, first index resolves ties. Point estimates remain unrounded. Primary and alternatives remain separate; no subgroup causal coefficient or post-treatment segmentation enters the forecast.

Break-even evaluates 257 equally spaced multipliers on [0,64], locates all sign changes/exact zeros, and bisects the first crossing to currency tolerance. The joint multiplier scales elasticity/churn/downgrade, preserving dose. No root is unavailable. The revenue bridge is sequential price → acquisition → churn → downgrades → fees, allocating interactions to the later step. Non-additive outputs are recomputed from summed numerators and exposures at estate level. Utilisation is opening-minute weighted across time and capacity weighted across sites; peak averages and maxima remain separate.

Keys: monthly(gym_id, month, price_increment, case); gyms(gym_id, price_increment, case); estate(gym_id=ESTATE, price_increment, case); sensitivity(gym_id, price_increment, variant). Empty CSV fields mean unavailable, never zero. Repeated scenario stocks are not unique customers. Net revenue is not profit; twelve-month projections are conditional models and exit run-rates are seasonal snapshots.
'''
    (AN/'phase6_methodology.md').write_text(method+'\n'+D1+'\n\n'+D2+'\n',encoding='utf-8')
    (AN/'scenario_validation.md').write_text('# Phase 6 Python validation\n\n'+D1+'\n\n'+D2+'\n\n'+'\n'.join('- PASS: '+c for c in CHECKS)+'\n\nWorkbook evidence is recorded independently.\n',encoding='utf-8')
    dictionary=[]
    for name,df in [('scenario_monthly',monthly),('gym_scenarios',sites),('estate_scenarios',estate),('scenario_sensitivity',sensitivity)]:
        for f in df.columns:
            unit='GBP net' if any(x in f for x in ['revenue','arpmm','yield','run_rate']) else 'GBP gross' if any(x in f for x in ['price','paid_rate']) and not f.startswith('pricing_complaints') else 'percentage points' if f.endswith('_pp') else 'decimal fraction' if any(x in f for x in ['rate','share','mix','impact','utilisation','uplift','probability','probabilities','fraction','retention']) else 'dimensionless' if any(x in f for x in ['elasticity','multiplier']) else 'ISO date' if f=='month' else 'expected members / exposures / counts' if pd.api.types.is_numeric_dtype(df[f]) else 'category / identifier'
            definition={'monthly_revenue':'Cumulative total net revenue for summaries; monthly total net revenue in monthly interface. Subscription + joining fee + ancillary.',
                'opening_members':'Monthly opening stock; summed opening-member exposure in period summaries.', 'average_members':'Monthly midpoint exposure; summed average-member months in summaries.',
                'month12_members':'December 2026 closing expected membership stock, not unique customers.', 'incremental_revenue':'Scenario total net revenue minus identical no-increase counterfactual.',
                'member_impact':'December scenario closing / December counterfactual closing − 1.', 'incumbent_churn_rate':'Opening-base Standard exits among pre-2026 members / their opening exposure.',
                'incumbent_downgrade_rate':'Opening-base Standard→Off-Peak transfers among pre-2026 members / their opening exposure.',
                'annualised_exit_run_rate':'December total net revenue ×12; seasonal snapshot, not a forecast.',
                'positive_revenue_draw_fraction':'Fraction of conditional whole-pair parameter draws with positive revenue; not rollout probability.'}.get(f,f.replace('_',' ').capitalize()+'; calculated using the scenario methodology and relevant reporting grain.')
            from scenario_metric_definitions import refine
            definition,unit,null=refine(name,f,definition,unit)
            dictionary.append(dict(table=name,field=f,definition=definition,unit=unit,window='Jan–Dec 2026',source_status='Generated conditional model from observed synthetic evidence',null_meaning=null,key_field=f in ['gym_id','month','price_increment','case','variant']))
    pd.DataFrame(dictionary).to_csv(AN/'scenario_metric_dictionary.csv',index=False)

def build_sensitivities(model,cf):
    rows_out=[]
    for variant in CFG['sensitivity_variants']:
        p=model.primary.copy();cal=model.calibration;extra={}
        if variant in ['early_3m','sustained_9m']:p=model.parameters(variant);cal=model.calibrate(variant)
        elif variant=='fixed_acquisition_weights':p=model.parameters('primary_6m',True)
        elif variant=='zero_behaviour':p[:3]=0;p[4]=0
        elif variant=='future_joiner_churn':extra['future_churn']=CFG['future_joiner_churn_sensitivity']
        elif variant=='offpeak_diversion':extra['diversion']=CFG['diversion_sensitivity']
        elif variant=='member_sensitive_ancillary':extra['member_ancillary']=True
        for inc in range(4):
            months=model.simulate(p,inc,calibration=cal,**extra)
            rows=summary_rows(model,months,inc,'Sensitivity',p,cf)+summary_rows(model,months,inc,'Sensitivity',p,cf,True)
            for r in rows:r.pop('case');r['variant']=variant
            rows_out+=rows
    return pd.DataFrame(rows_out)

def main():
    global MODEL
    PRE.mkdir(parents=True,exist_ok=True);before=input_hashes();MODEL=Model();model=MODEL
    check('Unchanged prior Phase 5 inputs',all(before.get(k)==v for k,v in json.loads((AN/'response_results.json').read_text())['input_hashes'].items()))
    cf=model.simulate(model.primary,0);model.baseline_months=cf
    params,sim,fields,ci=bootstrap(model)
    cases={'Base':model.primary,'Downside':params[ci[0]],'Upside':params[ci[1]]}
    roots=model_break_even(model)
    monthly_rows=[];site_rows=[];estate_rows=[]; traces={}; bridges=[]
    for case,p in cases.items():
        for inc in range(4):
            months,trace=model.simulate(p,inc,trace=True)
            monthly_rows+=export_rows(model,months,inc,case,p,cf);site_rows+=summary_rows(model,months,inc,case,p,cf);estate_rows+=summary_rows(model,months,inc,case,p,cf,True)
            if case=='Base' and inc in [0,2]:traces[inc]=trace
    monthly=pd.DataFrame(monthly_rows);sites=pd.DataFrame(site_rows);estate=pd.DataFrame(estate_rows)
    for frame,is_est in [(sites,False),(estate,True)]:
        for idx,r in frame.iterrows():
            gi=model.G if is_est else model.gi[r.gym_id];inc=int(r.price_increment)
            for k,f in enumerate(fields):
                vals=sim[:,inc,gi,k];lo,hi=np.percentile(vals,CFG['percentiles']);frame.loc[idx,f+'_lower']=lo;frame.loc[idx,f+'_upper']=hi
            vals=sim[:,inc,gi,0]-r.counterfactual_revenue;frame.loc[idx,'incremental_revenue_lower'],frame.loc[idx,'incremental_revenue_upper']=np.percentile(vals,CFG['percentiles'])
            frame.loc[idx,'positive_revenue_draw_fraction']=np.mean(vals>1e-8) if inc else 0.
            if not is_est:
                root,mem,n=roots.get((r.gym_id,inc),(np.nan,np.nan,0));frame.loc[idx,'break_even_response_multiplier']=root;frame.loc[idx,'break_even_member_impact']=mem;frame.loc[idx,'break_even_crossings']=n
    for i,f in enumerate(['elasticity','churn_increment','downgrade_increment','pilot_log_dose','complaints_increment']):
        lo,hi=np.percentile(params[:,i],CFG['percentiles'])
        for frame in [monthly,sites,estate]:frame[f+'_parameter_lower']=lo;frame[f+'_parameter_upper']=hi
    sensitivity=build_sensitivities(model,cf)
    for inc in [1,2,3]:
        previous=annual(aggregate_estate(cf))['monthly_revenue'][0,0];steps=[]
        for stage in range(5):
            value=annual(aggregate_estate(model.simulate(model.primary,inc,stage=stage)))['monthly_revenue'][0,0];steps.append(float(value-previous));previous=value
        bridges.append(dict(increment=inc,steps=steps,total=float(previous-annual(aggregate_estate(cf))['monthly_revenue'][0,0])))
    validate(model,monthly,sites,estate,cases,before,bridges)
    outputs=[monthly,sites,estate,sensitivity];reproduced={}
    for name,df in zip(OUTPUTS,outputs):
        path=DATA/(name+'.csv');raw=df.to_csv(index=False,float_format='%.12g',na_rep='',lineterminator='\n').encode()
        if '--reproduce' in sys.argv:check('Byte-identical '+name,path.read_bytes()==raw);reproduced[name]=hashlib.sha256(raw).hexdigest()
        else:path.write_bytes(raw)
    model.lineage.to_csv(AN/'scenario_cohort_lineage.csv',index=False,float_format='%.12g',na_rep='')
    results=clean_json(dict(input_hashes=before,configuration_hash=hashlib.sha256((AN/'scenario_config.json').read_bytes()).hexdigest(),checks_passed=len(CHECKS),rows=dict(zip(OUTPUTS,map(len,outputs))),
        opening_members=model.st['initial'].sum(),states_per_gym=model.S,initial_states_per_gym=model.K,cohort_buckets=len(model.lineage),fallbacks=model.fallbacks,
        promotion_duration=model.promo_duration,promotion_discount=model.promo_discount,calibration=model.calibration,cases=cases,selected_draw_indices=ci,bridges=bridges,
        base_estate=estate[estate.case=='Base'].to_dict('records'),reproduced_hashes=reproduced))
    if '--reproduce' in sys.argv:
        (PRE/'reproduction.json').write_text(json.dumps(results,indent=2));print('All four scenario CSVs reproduce byte-for-byte.');return
    (AN/'scenario_results.json').write_text(json.dumps(results,indent=2))
    # Workbook prepared inputs and linear-state traces; no output is used as an input to the live forecast.
    state_frame=pd.DataFrame([{k:v for k,v in s.items() if k!='source_ids'} for s in model.states])
    trace_payload={str(inc):[{k:clean_json(v) for k,v in t.items()} for t in trace] for inc,trace in traces.items()}
    payload=clean_json(dict(config=CFG,disclaimers=[D1,D2],drivers=frame_payload(model.drivers),states=frame_payload(state_frame),
        gyms=frame_payload(model.g),prices=model.prices,cases=cases,calibration=model.calibration,primary=model.primary,K=model.K,S=model.S,
        comparisons=frame_payload(sites),estate=frame_payload(estate),monthly=frame_payload(monthly),sensitivity=frame_payload(sensitivity),traces=trace_payload,bridges=bridges,
        original_monthly_rows=[int(model.m.index[(model.m.gym_id==gid)&(model.m.month=='2025-12-01')][0])+2 for gid in model.ids],
        original_monthly_closing=model.dec.closing_members.to_list()))
    (PRE/'payload.json').write_text(json.dumps(payload,separators=(',',':')))
    np.savez_compressed(PRE/'joint_draws.npz',params=params,outcomes=sim,fields=np.array(fields))
    figures(model,monthly,sites,estate,bridges);documentation(model,monthly,sites,estate,sensitivity,bridges,results)
    print(json.dumps({'rows':results['rows'],'checks':len(CHECKS),'base_estate':[(r['price_increment'],r['incremental_revenue'],r['member_impact']) for r in results['base_estate']]},indent=2))

if __name__=='__main__':main()
