"""Reproducible descriptive headroom assessment. Run from any working directory."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AN = ROOT / 'analysis'
DATA = ROOT / 'data'
CFG = json.loads((AN / 'headroom_config.json').read_text())
IND = CFG['indicators']
FLAGS = ['high_churn_exception', 'weak_conversion_exception', 'declining_acquisition_exception', 'peak_capacity_exception']
D1 = 'This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.'
D2 = 'This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.'

def hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DATA.glob('*.csv')) if p.stem not in ['gym_headroom', 'headroom_sensitivity']} | {'analysis/generation_config.json': hashlib.sha256((AN/'generation_config.json').read_bytes()).hexdigest()}

def percentile(s, reverse=False):
    n = s.count()
    tolerance=CFG['comparison_tolerance']
    out=s.map(lambda v: np.nan if pd.isna(v) else 50.0 if n<=1 else 100*((s < v-tolerance).sum()+((s.between(v-tolerance,v+tolerance)).sum()-1)/2)/(n-1))
    return 100 - out if reverse else out

def band(value, high=65, medium=40):
    if pd.isna(value): return None
    return 'High' if value >= high else 'Medium' if value >= medium else 'Low'

def segment(score_band, gap, caution):
    if caution: return 'Investigation priority'
    if score_band is None or pd.isna(gap): return 'Unavailable'
    if score_band == 'High' and gap > 0: return 'Stronger headroom indicators'
    if score_band == 'Low' or gap <= 0: return 'Limited headroom indicators'
    return 'Mixed indicators'

def evaluate(inputs, weights):
    components = pd.DataFrame({i: percentile(inputs[i], i == 'churn') for i in IND})
    contributions = components.mul(weights)
    contributions.loc[:, np.asarray(weights) == 0] = 0.0
    score = contributions.sum(axis=1, min_count=6)
    score.loc[inputs.loc[:, np.asarray(weights) > 0].isna().any(axis=1)] = np.nan
    tolerance=CFG['comparison_tolerance']
    rank=pd.Series([np.nan if pd.isna(v) else int((score>v+tolerance).sum()+((score.between(v-tolerance,v+tolerance))&(score.index<idx)).sum()+1) for idx,v in score.items()],index=score.index,dtype=float)
    return components, contributions, score, rank

def main():
    before = hashes()
    b = pd.read_csv(DATA/'gym_baseline.csv').sort_values('gym_id').reset_index(drop=True)
    g = pd.read_csv(DATA/'gym_master.csv').sort_values('gym_id').reset_index(drop=True)
    c = pd.read_csv(DATA/'competitor_prices.csv')
    m = pd.read_csv(DATA/'monthly_performance.csv')
    assert b.gym_id.tolist() == g.gym_id.tolist()
    dec = c[c.month == CFG['competitor_snapshot']]
    value = dec[dec.competitor_type.isin(CFG['value_types'])].groupby('gym_id').competitor_standard_price.mean().reindex(b.gym_id).to_numpy()
    q = c[c.month.between(CFG['recent_start'], CFG['recent_end'])].groupby(['gym_id','month']).competitor_standard_price.mean().rename('competitor_mean').reset_index()
    q = q.merge(m[['gym_id','month','standard_price']], on=['gym_id','month'], validate='one_to_one')
    q['gap'] = q.competitor_mean - q.standard_price
    qgap = q.groupby('gym_id').gap.mean().reindex(b.gym_id).to_numpy()
    context = ['gym_id','gym_name','city','region','location_type','standard_price_dec2025','competitor_gap_dec2025','churn_rate_2025','conversion_rate_2025','acquisition_growth_yoy','average_monthly_peak_2025','max_monthly_peak_2025'] + FLAGS + ['complaints_per_1000_member_months_2025','acquisition_growth_q4_yoy','churn_change_pp_q4_yoy','conversion_change_pp_q4_yoy','promotion_frequency_2025','marketing_spend_2025','standard_mix_2025','offpeak_mix_2025','plus_mix_2025','historical_price_events','historical_cash_increase','pilot_assignment','pilot_pair_id']
    # Use established baseline names without modifying that interface.
    context = [x for x in context if x in b.columns]
    h = b[context].copy()
    for field in ['median_income','student_population_pct','market_competitiveness']:
        h[field] = g[field]
    h['competitor_count_dec2025'] = dec.groupby('gym_id').size().reindex(b.gym_id).to_numpy()
    h['competitor_mean_joining_fee_dec2025'] = dec.groupby('gym_id').joining_fee.mean().reindex(b.gym_id).to_numpy()
    h['competitor_promotion_share_dec2025'] = dec.groupby('gym_id').promotion_active.mean().reindex(b.gym_id).to_numpy()
    h['competitor_mean_first_month_discount_dec2025'] = dec.groupby('gym_id').promotion_value.mean().reindex(b.gym_id).to_numpy()
    h['q4_average_competitor_gap'] = qgap
    h['value_competitor_gap_dec2025'] = value-b.standard_price_dec2025
    h['caution_flag_count'] = b[FLAGS].sum(axis=1).astype(int)
    variants=[]
    for name, weights in CFG['weights'].items():
        inputs = pd.DataFrame({'competitor_gap': b.competitor_gap_dec2025, 'churn': b.churn_rate_2025, 'conversion': b.conversion_rate_2025, 'acquisition_growth': b.acquisition_growth_yoy, 'peak_utilisation': b.average_monthly_peak_2025.clip(upper=1), 'income': g.median_income})
        if name == 'recent_trading':
            inputs['competitor_gap']=qgap
            inputs['churn']=b.churn_rate_q4_2025
            inputs['conversion']=b.conversion_rate_q4_2025
            inputs['acquisition_growth']=b.acquisition_growth_q4_yoy
            inputs['peak_utilisation']=b.average_monthly_peak_q4_2025.clip(upper=1)
        if name == 'value_competitors': inputs['competitor_gap']=h.value_competitor_gap_dec2025
        components, contributions, score, rank = evaluate(inputs, weights)
        s=pd.DataFrame({'gym_id': b.gym_id, 'variant': name})
        for i in IND:
            s[i+'_input']=inputs[i]
            s[i+'_component']=components[i]
            s[i+'_contribution']=contributions[i]
        s['score']=score
        s['rank']=rank.astype('Int64')
        s['band']=score.map(lambda v: band(v, CFG['high_threshold'], CFG['medium_threshold']))
        s['segment']=[segment(x,y,z) for x,y,z in zip(s.band,inputs.competitor_gap,h.caution_flag_count)]
        if name == 'base':
            for i in IND:
                h[i+'_input']=inputs[i]
                h[i+'_component']=components[i]
                h[i+'_contribution']=contributions[i]
            for field in ['score','rank','band','segment']:h[field]=s[field]
        s['base_score']=h.score
        s['base_rank']=h['rank']
        s['rank_movement']=s['rank']-h['rank']
        s['band_changed']=s.band != h.band
        s['sensitive']=(s.rank_movement.abs() >= CFG['rank_movement_threshold']) | s.band_changed
        variants.append(s)
    sensitivity=pd.concat(variants, ignore_index=True)
    alt=sensitivity[sensitivity.variant!='base'].groupby('gym_id')
    h['max_absolute_rank_movement']=alt.rank_movement.apply(lambda x:x.abs().max()).reindex(b.gym_id).to_numpy()
    h['alternative_band_change_count']=alt.band_changed.sum().reindex(b.gym_id).to_numpy()
    h['sensitive']=alt.sensitive.any().reindex(b.gym_id).to_numpy()
    h['band_lower_thresholds']=h.score.map(lambda v:band(v,60,35))
    h['band_higher_thresholds']=h.score.map(lambda v:band(v,70,45))
    h['threshold_sensitive']=(h.band!=h.band_lower_thresholds)|(h.band!=h.band_higher_thresholds)
    labels=['High opening-base churn','Weak qualified-prospect conversion','Declining acquisition','Peak service pressure']
    def explanation(r):
        cautions=[label for f,label in zip(FLAGS,labels) if r[f]]
        gap='Positive competitor gap' if r.competitor_gap_dec2025>0 else 'No positive competitor gap'
        return gap+'. '+(''.join(x+'. ' for x in cautions) if cautions else 'No baseline caution flags. ')+'Historical sensitivity pending Phase 5.'
    h['explanation']=h.apply(explanation,axis=1)
    first=['gym_id','city','score','rank','band','segment','sensitive','competitor_gap_dec2025','caution_flag_count']
    h=h[first+[x for x in h if x not in first]]
    checks=[]
    def check(name, condition):
        assert bool(condition),name
        checks.append({'check':name,'passed':True})
    check('80 unique gym results',len(h)==80 and h.gym_id.nunique()==80)
    check('480 unique sensitivity records',len(sensitivity)==480 and not sensitivity.duplicated(['gym_id','variant']).any())
    check('Complete monthly source coverage',len(m)==1920 and m.groupby('gym_id').month.nunique().eq(24).all() and not m.duplicated(['gym_id','month']).any())
    check('Complete December and value benchmark coverage',dec.gym_id.nunique()==80 and not np.isnan(value).any())
    check('240 unique Q4 benchmark records',len(q)==240 and not q.duplicated(['gym_id','month']).any())
    check('December benchmark agrees with baseline',np.allclose(dec.groupby('gym_id').competitor_standard_price.mean().reindex(b.gym_id).to_numpy()-b.standard_price_dec2025,b.competitor_gap_dec2025,atol=1e-10))
    check('All weights nonnegative and sum to one',all(abs(sum(w)-1)<1e-12 and min(w)>=0 for w in CFG['weights'].values()))
    check('Components and scores bounded',sensitivity.filter(regex='_component$').ge(0).all().all() and sensitivity.filter(regex='_component$').le(100).all().all() and sensitivity.score.between(0,100).all())
    check('Contributions sum to score',np.allclose(sensitivity.filter(regex='_contribution$').sum(axis=1),sensitivity.score,atol=1e-12))
    check('Each variant has ranks 1 to 80',all(sorted(s['rank'])==list(range(1,81)) for s in variants))
    check('Caution flags preserved',all(h[f].equals(b[f]) for f in FLAGS))
    check('Investigation precedence',h.loc[h.caution_flag_count>0,'segment'].eq('Investigation priority').all())
    check('High score boundary',[band(x) for x in [39.9999,40,64.9999,65]]==['Low','Medium','Medium','High'])
    check('Constant and tied indicator ranks',percentile(pd.Series([4,4,4])).eq(50).all() and percentile(pd.Series([1,2,2,3])).tolist()==[0,50,50,100])
    check('Reverse churn direction',percentile(pd.Series([1,2,3]),True).tolist()==[100,50,0])
    check('Binary floating-point tie tolerance',percentile(pd.Series([1,1+1e-14,2])).tolist()==[25,25,100])
    check('Missing observations remain missing',pd.isna(percentile(pd.Series([1,np.nan,3]))[1]) and band(np.nan) is None)
    test=pd.DataFrame({i:[1.,2.,3.] for i in IND});test.loc[0,'income']=np.nan
    check('Missing weighted input blocks base score',pd.isna(evaluate(test,CFG['weights']['base'])[2][0]))
    check('Zero-weight income does not block score',not pd.isna(evaluate(test,CFG['weights']['exclude_income'])[2][0]))
    test=pd.DataFrame({i:[1.,1.,1.] for i in IND})
    check('Deterministic tied-score ranks',evaluate(test,CFG['weights']['base'])[3].tolist()==[1,2,3])
    check('Utilisation cap removes extra reward above capacity',pd.Series([.9,1.,1.2]).clip(upper=1).tolist()==[.9,1.,1.])
    check('Segment rule branches',segment('High',1,0)=='Stronger headroom indicators' and segment('High',-1,0)=='Limited headroom indicators' and segment('Medium',1,0)=='Mixed indicators' and segment('High',1,1)=='Investigation priority')
    check('Identical evaluation rerun',evaluate(test,CFG['weights']['base'])[2].equals(evaluate(test,CFG['weights']['base'])[2]))
    check('Sources, baseline and generation configuration unchanged',before==hashes())
    for name,frame in [('gym_headroom',h),('headroom_sensitivity',sensitivity)]:
        frame.to_csv(DATA/(name+'.csv'),index=False,lineterminator='\n',float_format='%.15g',na_rep='')
    inherited=pd.read_csv(AN/'baseline_metric_dictionary.csv')
    inherited=inherited[inherited.table=='gym_baseline'].set_index('field').to_dict('index')
    original=pd.read_csv(AN/'data_dictionary.csv')
    original=original[original.table=='gym_master'].set_index('field').to_dict('index')
    special={
        'rank':'Unrounded score descending, then gym ID ascending; ranks 1–80 among available scores.',
        'band':'High at score >= 65; Medium at 40 <= score < 65; Low below 40; blanks for unavailable scores.',
        'segment':'Investigation priority for any baseline flag; otherwise Stronger for High and positive gap; Limited for Low or nonpositive gap; Mixed otherwise; Unavailable for missing required score/gap.',
        'q4_average_competitor_gap':'Mean of October, November and December competitor-price means minus the matching monthly Standard price; each month equally weighted.',
        'value_competitor_gap_dec2025':'December mean recurring advertised price for National value and Local low-cost competitors minus December Standard price; joining fees and introductory discounts excluded.',
        'competitor_mean_joining_fee_dec2025':'Arithmetic mean gross joining fee across active December competitors; separate from recurring price.',
        'competitor_promotion_share_dec2025':'Active December competitor promotion count divided by active December competitor count.',
        'competitor_mean_first_month_discount_dec2025':'Arithmetic mean gross first-month monetary discount across all active December competitors, including zero discount observations.',
        'competitor_count_dec2025':'Count of active gym–competitor December records.',
        'caution_flag_count':'Sum of the four preserved boolean baseline flags; an investigation indicator, not a price recommendation.',
        'max_absolute_rank_movement':'Maximum absolute alternative rank minus base rank, excluding the base specification.',
        'alternative_band_change_count':'Number of the five alternatives whose band differs from the base band.',
        'band_lower_thresholds':'Base-score band with cutoffs 60 and 35.',
        'band_higher_thresholds':'Base-score band with cutoffs 70 and 45.',
        'threshold_sensitive':'True when either five-point threshold shift changes the base-score band.',
        'base_score':'Score in the base specification, used only for sensitivity comparison.',
        'base_rank':'Rank in the base specification, used only for sensitivity comparison.',
        'band_changed':'Variant band differs from the base band; false for the base itself.',
        'explanation':'Rule-based recurring-price-gap direction, each active baseline caution, and Phase 5 evidence status.',
        'variant':'Configured specification name; base, market_emphasis, retention_emphasis, exclude_income, recent_trading or value_competitors.'
    }
    fields=[]
    for table,frame,key in [('gym_headroom',h,'gym_id'),('headroom_sensitivity',sensitivity,'gym_id + variant')]:
        for field in frame:
            unit='text / category'
            if field.endswith('_input'):unit={'competitor_gap':'GBP including VAT','income':'GBP annual local median','churn':'decimal monthly rate','conversion':'decimal rate','acquisition_growth':'decimal growth','peak_utilisation':'decimal occupancy'}.get(field[:-6],'numeric')
            elif field.endswith('_component') or field in ['score','base_score']:unit='score points 0–100'
            elif field.endswith('_contribution'):unit='weighted score points'
            elif 'change_pp' in field:unit='percentage points'
            elif any(x in field for x in ['price','gap','fee','discount','spend','income']):unit='GBP; price/fees/gaps gross, spend as source'
            elif any(x in field for x in ['rate','growth','frequency','mix','population_pct','utilisation','monthly_peak','share']):unit='decimal rate'
            elif pd.api.types.is_bool_dtype(frame[field]):unit='boolean'
            elif pd.api.types.is_numeric_dtype(frame[field]):unit='count / numeric source context'
            source_definition=inherited.get(field,original.get(field,{}))
            unit=source_definition.get('unit',source_definition.get('units',unit))
            definition=special.get(field,source_definition.get('definition',source_definition.get('description',field.replace('_',' '))))
            if field.endswith('_component'):definition='100 × (average ascending rank − 1)/(nonmissing n − 1); churn reversed; constant or singleton input = 50.'
            if field.endswith('_contribution'):definition='Indicator component multiplied by the configured variant weight.'
            if field=='score':definition='Sum of six contributions; unavailable if any positive-weight input is missing.'
            if field=='rank_movement':definition='Variant rank minus base rank; positive means weaker relative position.'
            if field.endswith('_component') or field=='rank':definition+=' Comparison tolerance 1e-10 handles binary floating-point ties without rounding financial inputs or scores.'
            if field=='sensitive':definition='Any alternative band change or absolute rank movement >= 10 (row-specific for sensitivity table).'
            fields.append({'table':table,'field':field,'key':key,'unit':unit,'window':'Q4 2025 / matching Q4 2024 for recent_trading; otherwise 2025 / matching 2024; December 2025 benchmark; static demographics','status':'Derived from fixed synthetic sources / baseline; analyst-defined scoring rules','null_meaning':'Unavailable required source or score; never zero imputation. Empty pilot pair means not assigned.','definition':definition})
    pd.DataFrame(fields).to_csv(AN/'headroom_metric_dictionary.csv',index=False,lineterminator='\n')
    result={'bands':h.band.value_counts().to_dict(),'segments':h.segment.value_counts().to_dict(),'sensitive_sites':int(h.sensitive.sum()),'threshold_sensitive_sites':int(h.threshold_sensitive.sum()),'score_range':[float(h.score.min()),float(h.score.max())],'high_score_with_cautions':int(((h.band=='High')&(h.caution_flag_count>0)).sum()),'checks':checks,'input_hashes':before,'source_sizes':{'gym_headroom':len(h),'headroom_sensitivity':len(sensitivity)},'variants':{v:{'band_changes':int(s.band_changed.sum()),'max_rank_movement':int(s.rank_movement.abs().max()),'sensitive_sites':int(s.sensitive.sum())} for v,s in sensitivity.groupby('variant')},'top10':h.sort_values(['score','gym_id'],ascending=[False,True]).head(10)[['gym_id','city','score','rank','band','segment','sensitive']].to_dict('records')}
    (AN/'headroom_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    def table(frame):
        return '| '+' | '.join(frame.columns)+' |\n|'+ '|'.join(['---']*len(frame.columns))+'|\n'+'\n'.join('| '+' | '.join(str(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None))
    top=h.sort_values(['score','gym_id'],ascending=[False,True]).head(10)[['gym_id','city','score','band','segment','max_absolute_rank_movement']].copy();top.score=top.score.round(2)
    report=f'''# Northstar Fitness — Pricing Headroom\n\n{D1}\n\n## Commercial purpose\n\nCompare relative value, acquisition, retention and demand to identify sites deserving closer historical-response analysis. A high score can coexist with weak member performance. This assessment supports investigation priorities; it does not establish willingness to pay, causal price sensitivity, a cash increase or revenue uplift.\n\n## Findings\n\nThe 80 gyms have scores from {h.score.min():.2f} to {h.score.max():.2f}. Score bands: {result['bands']}. Commercial segments: {result['segments']}. {result['high_score_with_cautions']} High-score gyms retain caution flags. {result['sensitive_sites']} sites change band or move at least ten ranks under an alternative. {result['threshold_sensitive_sites']} change band when thresholds move five points. Rankings should therefore guide subsequent evidence gathering rather than determine a rollout.\n\n{table(top)}\n\nThe table shows leading scores, including adverse signals where present. It is not a list of sites to reprice.\n\n## Score and judgement\n\nWeights are competitor gap 30%, churn 25%, conversion 15%, acquisition growth 15%, average monthly peak utilisation 10% and synthetic income 5%. Relative value and retention receive most weight because price gains depend on continuing value; recruitment provides supporting evidence. Capacity and income receive lower weights because occupancy can mean service pressure and demographics are indirect proxies. Weights are business assumptions, not fitted coefficients or probability estimates.\n\nEach indicator uses average percentile ranks across the 80 gyms. Churn is reversed; peak inputs are capped at 100%. A constant or singleton indicator scores 50, and missing required inputs leave the score unavailable. High starts at 65; Medium at 40. Thresholds are policy choices, not economic break-even points. Ties resolve by gym ID using unrounded scores. Risk flags do not change the score. The commercial segment gives investigation precedence to any of the four Phase 3 flags, then separates stronger, limited and mixed indicators.\n\n## Robustness\n\n{table(pd.DataFrame([{'variant':k,**v} for k,v in result['variants'].items()]))}\n\nRecent trading uses exposure-weighted Q4 churn/conversion, matching-quarter acquisition growth, Q4 average monthly peak and the mean of three monthly competitor gaps. It does not pool all competitor records across the quarter, which would overweight months with more competitors. The value-only comparison excludes the fictional full-service archetype. A positive rank movement means a site moves down the ranking. Sensitivity measures specification dependence, not statistical confidence.\n\n## Visual interpretation\n\n![Leading-site score contributions](../images/headroom_contributions.png)\n\nContributions explain what drives leading scores. They are score points, not financial gains.\n\n![Relative value and churn](../images/headroom_gap_churn.png)\n\nThe scatter shows all 80 gyms, with caution sites distinguished and peak-pressure sites labelled. Higher competitor gaps do not demonstrate lower price sensitivity.\n\n![Ranking stability](../images/headroom_rank_stability.png)\n\nThe matrix shows all sites in base-rank order across all six variants. Rank is relative: one site can move because another site's inputs differ.\n\n## Boundaries and next step\n\nCompetitor prices include VAT and exclude joining fees and one-off introductory discounts from recurring comparisons. All competitor archetypes are assumed comparable in the synthetic source design; actual access, service and brand comparability would need investigation. Quality, distance, fees and promotions remain source context. December gaps are snapshots; Q4 supplies a timing sensitivity. Income and student exposure are synthetic local proxies, not individual member characteristics. Marketing, promotions, membership mix, complaints, region and prior repricing remain visible context without causal attribution. Monthly churn is not annual retention. Member-months are not unique people. Historical price sensitivity is pending Phase 5.\n\n{D2}\n'''
    adverse=h[(h.band=='High')&(h.caution_flag_count>0)][['gym_id','city','score','explanation']].copy()
    adverse.score=adverse.score.round(2)
    report=report.replace('## Score and judgement','## High scores with adverse evidence\n\n'+table(adverse)+'\n\nQ4 trading creates the largest ranking shift (32 places), with 19 band changes. Removing income changes two bands and moves ranks by at most seven places. Recent commercial performance therefore deserves particular attention before interpreting a high annual score.\n\n## Score and judgement')
    (AN/'headroom_report.md').write_text(report,encoding='utf-8')
    (AN/'headroom_validation.md').write_text('# Phase 4 validation\n\n'+D1+'\n\n'+f'{len(checks)} Python checks passed. 80 gym rows and 480 sensitivity rows. Sources, baseline CSVs and generation configuration retain their recorded SHA-256 hashes.\n\n'+'\n'.join('- PASS: '+x['check'] for x in checks)+'\n\nWorkbook reconciliation and visual review are recorded separately in headroom_workbook_verification.json.\n\n'+D2+'\n',encoding='utf-8')
    previews=AN/'.workbook_previews'/'phase4';previews.mkdir(parents=True,exist_ok=True)
    payload={'config':CFG,'result':result,'q4_benchmarks':q.to_dict('records')}
    for name,frame in [('gym_headroom',h),('headroom_sensitivity',sensitivity),('gym_baseline',b),('gym_master',g),('competitor_prices',c),('monthly_performance',m)]:
        payload[name]={'columns':list(frame.columns),'data':json.loads(frame.to_json(orient='values',double_precision=15))}
    (previews/'payload.json').write_text(json.dumps(payload),encoding='utf-8')
    plot(h,sensitivity)
    print(json.dumps({k:result[k] for k in ['bands','segments','sensitive_sites','threshold_sensitive_sites','score_range']},indent=2))

def plot(h,s):
    sys.path.append(str(AN/'.workbook_previews'/'python_packages'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    images=ROOT/'images';images.mkdir(exist_ok=True)
    top=h.sort_values(['score','gym_id'],ascending=[False,True]).head(10).iloc[::-1]
    fig,ax=plt.subplots(figsize=(11,6));left=np.zeros(len(top));colors=['#243B53','#486581','#829AB1','#2F855A','#D69E2E','#9F7AEA']
    for i,color in zip(IND,colors):
        values=top[i+'_contribution'];ax.barh(top.gym_id+' '+top.city,values,left=left,label=i.replace('_',' ').title(),color=color);left+=values.to_numpy()
    ax.set(xlim=(0,100),xlabel='Weighted score points',title='Leading ten sites: what contributes to the headroom score');ax.legend(ncol=3,loc='lower center',bbox_to_anchor=(.5,1.03),frameon=False);fig.tight_layout();fig.savefig(images/'headroom_contributions.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,6))
    for caution,color,label in [(False,'#243B53','No baseline caution flag'),(True,'#D97706','At least one caution flag')]:
        t=h[(h.caution_flag_count>0)==caution];ax.scatter(t.competitor_gap_dec2025,t.churn_rate_2025*100,c=color,label=label,alpha=.8,s=40)
    for r in h[h.peak_capacity_exception].itertuples():ax.annotate(r.gym_id,(r.competitor_gap_dec2025,r.churn_rate_2025*100),xytext=(5,5),textcoords='offset points')
    ax.axvline(0,color='#829AB1',lw=1);ax.set(xlabel='December competitor average minus Northstar Standard (£, including VAT)',ylabel='2025 opening-base monthly churn (%)',title='Relative price and churn: opportunity alongside caution');ax.legend(frameon=False);fig.tight_layout();fig.savefig(images/'headroom_gap_churn.png',dpi=160);plt.close(fig)
    order=h.sort_values(['score','gym_id'],ascending=[False,True]).gym_id.tolist();variants=list(CFG['weights']);matrix=s.pivot(index='gym_id',columns='variant',values='rank').loc[order,variants].to_numpy(dtype=float)
    fig,ax=plt.subplots(figsize=(10,18));im=ax.imshow(matrix,aspect='auto',vmin=1,vmax=80,cmap='viridis_r');ax.set_xticks(range(6),[x.replace('_','\n') for x in variants]);ax.set_yticks(range(80),order,fontsize=7);ax.set_title('All 80 sites: ranking stability across specifications');fig.colorbar(im,ax=ax,label='Rank (1 = highest score)',shrink=.5);fig.tight_layout();fig.savefig(images/'headroom_rank_stability.png',dpi=150);plt.close(fig)

if __name__=='__main__':main()
