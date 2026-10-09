"""Read the frozen Phase 3–8 evidence and prepare the management deck inputs."""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd
from powerbi_prepare import sources
from powerbi_acceptance_status import accepted, fingerprint

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'analysis/.presentation_build'
BUILD.mkdir(parents=True, exist_ok=True)

def records(frame):
    return json.loads(frame.to_json(orient='records', double_precision=15))

def prepare():
    frozen = json.loads((ROOT/'analysis/.powerbi_native/protected_hashes.json').read_text())
    assert sources() == frozen['source_manifest'], 'Protected evidence changed'
    assert hashlib.sha256((ROOT/'excel/gym_pricing_model.xlsx').read_bytes()).hexdigest() == frozen['excel']
    assert accepted(), 'Native Power BI acceptance is not current'
    b = json.loads((ROOT/'analysis/baseline_results.json').read_text())
    h = pd.read_csv(ROOT/'data/gym_headroom.csv')
    r = pd.read_csv(ROOT/'data/gym_recommendations.csv')
    p = pd.read_csv(ROOT/'data/recommendation_portfolio.csv')
    s = pd.read_csv(ROOT/'data/estate_scenarios.csv')
    hist = pd.read_csv(ROOT/'data/price_response_estimates.csv')
    hist = hist[(hist.estimator=='paired_equal') & (hist.window=='primary_6m') & (hist.group_type=='Overall')]
    e = pd.read_csv(ROOT/'data/experiment_estimates.csv')
    primary = e[(e.simulation=='Main') & (e.population=='First repricing') & (e.checkpoint_months==6)]
    sustained = e[(e.simulation=='Main') & (e.population=='First repricing') & (e.checkpoint_months==12)]
    power = pd.read_csv(ROOT/'data/experiment_power.csv')
    power = power[(power.pairs==5) & (power.method=='Exact assignment Monte Carlo')]
    design = pd.read_csv(ROOT/'data/experiment_design.csv')
    assert len(r)==80 and r.gym_id.is_unique and len(h)==80
    counts = r.action.value_counts().to_dict()
    assert counts == {'DEFENSIVE / INVESTIGATE':38,'HOLD PRICE':26,'RAISE £1':10,'TEST FIRST':5,'RAISE £2':1}
    base = p[(p.variant=='base') & (p['case']=='Base')].iloc[0]
    assert abs(base.incremental_revenue-148618.48020484)<.01
    assert abs(b['annual']['2025']['total_revenue']-107006933.85)<.01
    assert b['annual']['2025']['closing_members']==396311
    bridge = b['bridge']
    assert abs(bridge['member_volume_contribution']+bridge['total_arpmm_contribution']-(bridge['2025_revenue']-bridge['2024_revenue']))<.01
    raises = r[r.action.str.startswith('RAISE')].sort_values(['proposed_increment','gym_id'])
    assert abs(raises.selected_incremental_revenue.sum()-base.incremental_revenue)<.01
    assert abs(raises.selected_member_difference.sum()-base.member_difference)<1e-5
    assigned = design[design.disposition=='Assigned']
    # Accept case variants in the saved disposition label.
    if len(assigned)!=14: assigned=design[design.assignment.isin(['Treatment','Control'])]
    assert len(assigned)==14 and assigned.pair_id.nunique()==7
    assert set(design[design.disposition=='Reserve'].gym_id)=={'NF023','NF057'}
    assert int(primary.loc[primary.metric=='revenue_effect','complete_pairs'].iloc[0])==5
    data={
        'baseline':b['annual'], 'q4':b['q4'], 'bridge':bridge,
        'headroom': records(h[['gym_id','competitor_gap_dec2025','churn_rate_2025','caution_flag_count','score','band','segment','sensitive']]),
        'headroom_segments':h.segment.value_counts().to_dict(),
        'headroom_bands':h.band.value_counts().to_dict(),
        'high_with_caution':int(((h.band=='High')&(h.caution_flag_count>0)).sum()),
        'sensitive_sites':int(h.sensitive.sum()),
        'nonpositive_gaps':int((h.competitor_gap_dec2025<=0).sum()),
        'median_standard_price':float(h.standard_price_dec2025.median()),
        'action_counts':counts,
        'raise_sites':records(raises[['gym_id','city','proposed_increment','selected_incremental_revenue','selected_member_difference']]),
        'portfolio':records(p), 'scenarios':records(s[s['case']=='Base'].sort_values('price_increment')),
        'history':records(hist), 'experiment_primary':records(primary), 'experiment_sustained':records(sustained),
        'power':records(power), 'assignments':records(assigned),
        'input_hashes':frozen['source_manifest'], 'excel_hash':frozen['excel'],
        'powerbi_fingerprint':fingerprint(),
        'disclaimers':[
            'This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.',
            'This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.'
        ]
    }
    (BUILD/'inputs.json').write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'status':'presentation evidence reconciled','raises':len(raises),'protected_hashes':len(frozen['source_manifest']),'source_workbook_unchanged':True,'native_acceptance_current':True}))
    return data

if __name__=='__main__': prepare()
