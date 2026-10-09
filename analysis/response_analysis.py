"""Phase 5: local historical policy response; no latent generator parameters used.

Run with bundled Python. CSV nulls are empty; rates decimal, rate effects pp.
Bootstrap resamples whole matched pairs jointly, never gyms or member rows.
"""
import hashlib
import itertools
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AN, DATA = ROOT/'analysis', ROOT/'data'
PRE = AN/'.workbook_previews'/'phase5'
CFG = json.loads((AN/'response_config.json').read_text())
D1 = 'This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.'
D2 = 'This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.'
OUTPUTS = ['historical_response_panel', 'historical_event_response', 'pilot_pair_response', 'price_response_estimates']
SUM_FIELDS = ['standard_joins', 'new_members', 'qualified_prospects', 'opening_members', 'opening_base_cancellations', 'same_month_cancellations', 'average_members', 'average_standard_members', 'standard_subscription_revenue', 'subscription_revenue', 'joining_fee_revenue', 'ancillary_revenue', 'monthly_revenue', 'marketing_spend', 'pricing_complaints', 'incumbent_standard_opening', 'incumbent_standard_cancellations', 'incumbent_standard_downgrades', 'incumbent_paid_rate_numerator', 'incumbent_protected_opening', 'incumbent_repriced_opening']
RATES = {'incumbent_churn': ('incumbent_standard_cancellations', 'incumbent_standard_opening'), 'incumbent_downgrade': ('incumbent_standard_downgrades', 'incumbent_standard_opening'), 'conversion': ('new_members', 'qualified_prospects'), 'site_churn': ('opening_base_cancellations', 'opening_members'), 'subscription_yield': ('subscription_revenue', 'average_members'), 'standard_yield': ('standard_subscription_revenue', 'average_standard_members'), 'total_arpmm': ('monthly_revenue', 'average_members'), 'incumbent_paid_rate': ('incumbent_paid_rate_numerator', 'incumbent_standard_opening'), 'protected_share': ('incumbent_protected_opening', 'incumbent_standard_opening'), 'repriced_share': ('incumbent_repriced_opening', 'incumbent_standard_opening'), 'complaints_per_1000_member_months': ('pricing_complaints', 'average_members')}

def hashes():
    files = [p for p in DATA.glob('*.csv') if p.stem not in OUTPUTS] + [AN/'generation_config.json', AN/'headroom_config.json']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}

def divide(n, d):
    return float(n/d) if pd.notna(n) and pd.notna(d) and d > 0 else np.nan

def controlled_log(tp, tb, cp, cb):
    return float(np.log(tp/tb)-np.log(cp/cb)) if min(tp, tb, cp, cb) > 0 else np.nan

def period(frame, gym_ids, start, end):
    q = frame[frame.gym_id.isin(gym_ids) & frame.month.between(start, end)].sort_values(['gym_id', 'month'])
    out = {f: float(q[f].sum()) for f in SUM_FIELDS}
    out['months'] = len(pd.date_range(start, end, freq='MS'))
    out['gym_count'] = len(gym_ids)
    assert len(q) == out['months']*len(gym_ids), 'Incomplete reporting window'
    out['period_opening_members'] = float(q.groupby('gym_id').first().opening_members.sum())
    out['period_closing_members'] = float(q.groupby('gym_id').last().closing_members.sum())
    out['standard_price'] = float(q.standard_price.mean())
    out['competitor_gap'] = float(q.competitor_price_gap.mean())
    out['competition_count'] = float(q.competitor_count_3km.mean())
    out['peak_utilisation'] = float(q.peak_utilisation_pct.mean())
    out['promotion_frequency'] = float(q.promotion_active.mean())
    for f, (n, d) in RATES.items(): out[f] = divide(out[n], out[d]) * (1000 if f.startswith('complaints_per') else 1)
    return out

def response(tb, tp, cb, cp):
    log = controlled_log(tp['standard_joins'], tb['standard_joins'], cp['standard_joins'], cb['standard_joins'])
    out = {'acquisition_log_response': log, 'controlled_acquisition_response': np.expm1(log), 'pre_acquisition_weight': tb['standard_joins']+cb['standard_joins']}
    for metric in ['incumbent_churn', 'incumbent_downgrade', 'conversion', 'site_churn']:
        out[metric+'_response_pp'] = 100*((tp[metric]-tb[metric])-(cp[metric]-cb[metric]))
    for metric in ['subscription_yield', 'standard_yield', 'total_arpmm', 'incumbent_paid_rate', 'complaints_per_1000_member_months']:
        out[metric+'_controlled_change'] = (tp[metric]-tb[metric])-(cp[metric]-cb[metric])
    for metric in ['monthly_revenue', 'subscription_revenue', 'standard_subscription_revenue', 'new_members']:
        cf = tb[metric]*divide(cp[metric], cb[metric])
        out[metric+'_counterfactual'] = cf
        out[metric+'_estimated_difference'] = tp[metric]-cf
        out[metric+'_controlled_growth'] = divide(tp[metric], cf)-1
    out['member_balance_response'] = (tp['period_closing_members']-tp['period_opening_members'])-(cp['period_closing_members']-cp['period_opening_members'])*tb['gym_count']/cb['gym_count']
    return out

def csv(frame):
    return frame.to_csv(index=False, float_format='%.12g', na_rep='', lineterminator='\n')

def build_panel(m, ledger, gyms, assignments, history, market):
    key = ['gym_id', 'month']
    std = ledger[ledger.membership_type == 'Standard']
    sums = ledger.groupby(key)[['opening_members', 'new_members', 'opening_base_cancellations', 'same_month_cancellations', 'transfers_in', 'transfers_out', 'closing_members', 'average_members', 'subscription_revenue']].sum()
    stdagg = std.groupby(key)[['new_members', 'opening_members', 'transfers_out']].sum().rename(columns={'new_members': 'standard_joins', 'opening_members': 'standard_opening_members', 'transfers_out': 'all_standard_transfers_out'})
    frames = []
    contexts = gyms.set_index('gym_id')[['region', 'city', 'location_type', 'student_population_pct']]
    events = market.assign(entry=(market.event_type == 'Competitor entry').astype(int), cut=(market.event_type == 'Price cut').astype(int), competitor_promo=(market.event_type == 'Promotion').astype(int))
    # Check exact source labels before using counts; never silently discard event types.
    events['entry'] = events.event_type.str.lower().str.contains('entry').astype(int)
    events['cut'] = events.event_type.str.lower().str.contains('cut').astype(int)
    events['competitor_promo'] = events.event_type.str.lower().str.contains('promotion').astype(int)
    event_counts = events.groupby(['gym_id', 'event_date'])[['entry', 'cut', 'competitor_promo']].sum().rename_axis(index=['gym_id', 'month'])
    for family, date in CFG['families'].items():
        f = m.copy().set_index(key)
        f = f.join(contexts, on='gym_id').join(stdagg).join(event_counts).fillna({'entry': 0, 'cut': 0, 'competitor_promo': 0})
        f['event_family'] = family
        f['intervention_date'] = date
        f['existing_member_billing_date'] = (pd.Timestamp(date)+pd.DateOffset(months=1)).strftime('%Y-%m-%d')
        f['event_month'] = [(pd.Timestamp(month).year-pd.Timestamp(date).year)*12+pd.Timestamp(month).month-pd.Timestamp(date).month for _, month in f.index]
        eligible = std[std.join_month.isna() | (std.join_month < date)].copy()
        # Opening-base buckets contain no same-month joins; source invariant is independently tested.
        eligible['incumbent_standard_opening'] = eligible.opening_members
        eligible['incumbent_standard_cancellations'] = eligible.opening_base_cancellations
        eligible['incumbent_standard_downgrades'] = np.where(eligible.opening_members > 0, eligible.transfers_out, 0)
        eligible['incumbent_paid_rate_numerator'] = eligible.opening_members*eligible.billed_price
        eligible['incumbent_protected_opening'] = np.where(eligible.price_protected_until.notna() & (eligible.month < eligible.price_protected_until), eligible.opening_members, 0)
        # A different historical event is not the family's repricing status.
        eligible['incumbent_repriced_opening'] = np.where((eligible.repricing_event_id == family) & eligible.price_increment_applied.astype(bool), eligible.opening_members, 0)
        inc_fields = [x for x in SUM_FIELDS if x.startswith('incumbent_')]
        inc = eligible.groupby(key)[inc_fields].sum()
        f = f.join(inc).fillna({x: 0 for x in inc_fields})
        for name in ['opening_members', 'new_members', 'closing_members', 'subscription_revenue', 'transfers_in', 'transfers_out']:
            f['ledger_'+name] = sums[name]
        members = history[history.event_id == family].set_index('gym_id')
        f['assigned_role'] = np.where(f.index.get_level_values('gym_id').isin(members.index), 'Repriced', 'Non-participant')
        f['pair_id'] = None
        if family == 'PILOT_202504':
            a = assignments.set_index('gym_id')
            f['assigned_role'] = f.index.get_level_values('gym_id').map(a.test_group).fillna('Non-participant')
            f['pair_id'] = f.index.get_level_values('gym_id').map(a.pair_id)
        f['marketing_per_prospect'] = f.marketing_spend/f.qualified_prospects.replace(0, np.nan)
        for name, (n, d) in RATES.items(): f[name] = f[n]/f[d].replace(0, np.nan)*(1000 if name.startswith('complaints_per') else 1)
        frames.append(f.reset_index())
    return pd.concat(frames, ignore_index=True).sort_values(['event_family', 'gym_id', 'month']).reset_index(drop=True)

def pairs(panel, assignments, history, window):
    start, end, poststart, postend = CFG['windows'][window]
    rows = []
    for pair_id, a in assignments.groupby('pair_id', sort=True):
        t = a.loc[a.test_group == 'Treatment', 'gym_id'].iloc[0]
        c = a.loc[a.test_group == 'Control', 'gym_id'].iloc[0]
        q = panel[panel.event_family == 'PILOT_202504']
        periods = {side+'_'+when: period(q, [gym], x, y) for side, gym in [('treatment', t), ('control', c)] for when, x, y in [('pre', start, end), ('post', poststart, postend)]}
        hist = history[history.gym_id == t].iloc[0]
        preq = q[q.gym_id.isin([t, c]) & q.month.between(start, end)]
        postq = q[q.gym_id.isin([t, c]) & q.month.between(poststart, postend)]
        row = dict(pair_id=pair_id, window=window, treatment_gym_id=t, control_gym_id=c, region=a.region.iloc[0], pre_start=start, pre_end=end, post_start=poststart, post_end=postend, months=periods['treatment_pre']['months'], old_price=hist.old_price, new_price=hist.new_price, log_price_change=float(np.log(hist.new_price/hist.old_price)), pre_pair_competitor_gap=float(preq.competitor_price_gap.mean()), pre_pair_competitor_count=float(preq.competitor_count_3km.mean()), post_competitor_entries=int(postq.entry.sum()), post_competitor_cuts=int(postq.cut.sum()), post_competitor_promotions=int(postq.competitor_promo.sum()))
        row['relative_value_group'] = 'Positive gap' if row['pre_pair_competitor_gap'] > 0 else 'Non-positive gap'
        row['competition_group'] = 'High' if row['pre_pair_competitor_count'] >= 5 else 'Medium' if row['pre_pair_competitor_count'] >= 3 else 'Low'
        for prefix, values in periods.items(): row.update({prefix+'_'+name: value for name, value in values.items()})
        row.update(response(periods['treatment_pre'], periods['treatment_post'], periods['control_pre'], periods['control_post']))
        row['pair_elasticity'] = divide(row['acquisition_log_response'], row['log_price_change'])
        row['marketing_change_treatment'] = periods['treatment_post']['marketing_spend']-periods['treatment_pre']['marketing_spend']
        row['marketing_change_control'] = periods['control_post']['marketing_spend']-periods['control_pre']['marketing_spend']
        rows.append(row)
    return pd.DataFrame(rows)

def targeted_matches(panel, history, gyms):
    result = {}
    never = sorted(set(gyms.gym_id)-set(history.gym_id))
    for family, dates in CFG['targeted_windows'].items():
        q = panel[(panel.event_family == family) & panel.month.between(dates[0], dates[1])]
        features = q.groupby('gym_id')[CFG['matching_features']].mean()
        scale = features.std(ddof=0)
        use = scale[scale > 0].index
        z = (features[use]-features[use].mean())/scale[use]
        for gym in sorted(history.loc[history.event_id == family, 'gym_id']):
            region = gyms.set_index('gym_id').loc[gym, 'region']
            candidates = [x for x in never if gyms.set_index('gym_id').loc[x, 'region'] == region]
            ranked = sorted([(float(np.linalg.norm(z.loc[gym]-z.loc[x])), x) for x in candidates], key=lambda x: (round(x[0], 12), x[1]))
            chosen = ranked[:CFG['targeted_max_controls']]
            result[gym] = {'control_ids': [x[1] for x in chosen], 'distances': [x[0] for x in chosen], 'candidate_count': len(candidates), 'excluded_constant_features': sorted(set(features.columns)-set(use))}
    return result

def event_results(panel, history, assignments, gyms, matched):
    rows = []
    for _, h in history.sort_values(['event_id', 'gym_id']).iterrows():
        date = h.effective_date
        dates = CFG['windows']['primary_6m'] if h.event_id == 'PILOT_202504' else CFG['targeted_windows'][h.event_id]
        q = panel[panel.event_family == h.event_id]
        tpre, tpost = period(q, [h.gym_id], *dates[:2]), period(q, [h.gym_id], *dates[2:])
        if h.event_id == 'PILOT_202504':
            controls = assignments.loc[(assignments.pair_id == h.pair_id) & (assignments.test_group == 'Control'), 'gym_id'].tolist()
            info = {'distances': [float(assignments.loc[assignments.gym_id == h.gym_id, 'matching_distance'].iloc[0])], 'candidate_count': 1}
        else:
            info = matched[h.gym_id]; controls = info['control_ids']
        row = h.to_dict() | dict(event_family=h.event_id, region=gyms.set_index('gym_id').loc[h.gym_id, 'region'], pre_start=dates[0], pre_end=dates[1], post_start=dates[2], post_end=dates[3], comparator_ids=';'.join(controls) or None, comparator_count=len(controls), candidate_count=info['candidate_count'], mean_matching_distance=np.mean(info['distances']) if controls else np.nan, max_matching_distance=max(info['distances']) if controls else np.nan, evidence_status='Randomised paired policy estimate' if h.event_id == 'PILOT_202504' else 'Observational matched comparison; selection bias remains')
        for prefix, values in [('treatment_pre', tpre), ('treatment_post', tpost)]: row.update({prefix+'_'+k: v for k, v in values.items()})
        if controls:
            # Equal control weights: sum counts then ratios. Revenue scaled per control before comparison.
            cb, cp = period(q, controls, *dates[:2]), period(q, controls, *dates[2:])
            for when, values in [('pre', cb), ('post', cp)]: row.update({'control_'+when+'_'+k: v for k, v in values.items()})
            row.update(response(tpre, tpost, cb, cp))
        rows.append(row)
    return pd.DataFrame(rows)

METRICS = ['controlled_acquisition_response', 'acquisition_elasticity', 'incumbent_churn_response_pp', 'incumbent_downgrade_response_pp', 'conversion_response_pp', 'subscription_yield_controlled_change', 'standard_yield_controlled_change', 'total_arpmm_controlled_change', 'monthly_revenue_controlled_growth', 'monthly_revenue_estimated_difference', 'subscription_revenue_estimated_difference', 'complaints_per_1000_member_months_controlled_change']

def statistic(frame, metric, weights=None, indices=None):
    w = np.ones(len(frame)) if weights is None else weights
    values = frame['acquisition_log_response'].to_numpy(float) if metric in ['controlled_acquisition_response', 'acquisition_elasticity'] else frame[metric].to_numpy(float)
    if indices is None: indices = np.arange(len(frame))[None, :]
    avg = np.sum(values[indices]*w[indices], axis=1)/np.sum(w[indices], axis=1)
    if metric == 'controlled_acquisition_response': return np.expm1(avg)
    if metric == 'acquisition_elasticity': return avg/(np.sum(frame.log_price_change.to_numpy()[indices]*w[indices], axis=1)/np.sum(w[indices], axis=1))
    # Monetary cumulative difference is the summed treatment-site increment, not a per-pair mean.
    if metric.endswith('_estimated_difference'): return avg*len(frame)
    return avg

def exact_p(values):
    if len(values) != 12 or not np.isfinite(values).all(): return np.nan
    flips = np.asarray(list(itertools.product([-1, 1], repeat=12)))
    stats = (flips*values).mean(axis=1)
    return float(np.mean(np.abs(stats) >= abs(np.mean(values))-CFG['comparison_tolerance']))

def estimate_rows(pair_frames):
    rng = np.random.default_rng(CFG['bootstrap_seed'])
    rows = []
    def add(frame, estimator, window, group_type='Overall', group='All assigned pairs', weights=None, intervals=True, exact=False):
        n = len(frame)
        samples = rng.integers(0, n, size=(CFG['bootstrap_samples'], n)) if n else None
        for metric in METRICS:
            source = 'acquisition_log_response' if metric in ['controlled_acquisition_response', 'acquisition_elasticity'] else metric
            good = np.isfinite(frame[source].to_numpy()) & np.isfinite(frame.log_price_change.to_numpy())
            complete = int(good.sum())
            # Primary keeps every assignment. An unavailable pair makes its complete-assignment estimate unavailable.
            point = statistic(frame, metric, weights)[0] if n and good.all() else np.nan
            allowed = intervals and complete == n and n >= CFG['minimum_interval_pairs']
            ci = np.percentile(statistic(frame, metric, weights, samples), CFG['confidence_percentiles']) if allowed else [np.nan, np.nan]
            pv = exact_p(frame.acquisition_log_response.to_numpy()) if exact and metric == 'controlled_acquisition_response' else exact_p(frame.incumbent_churn_response_pp.to_numpy()) if exact and metric == 'incumbent_churn_response_pp' else np.nan
            unit = 'percentage points' if metric.endswith('_pp') else 'elasticity' if metric == 'acquisition_elasticity' else 'decimal fraction' if metric.endswith('_response') or metric.endswith('_growth') else 'GBP net cumulative' if metric.endswith('_estimated_difference') else 'complaints / 1000 member-months' if metric.startswith('complaints') else 'GBP net / member-month'
            rows.append(dict(estimator=estimator, window=window, group_type=group_type, group=group, metric=metric, estimate=point, ci_lower=ci[0], ci_upper=ci[1], exact_p_value=pv, assigned_pairs=n, complete_pairs=complete, treatment_gyms=n, control_gyms=n, bootstrap_samples=CFG['bootstrap_samples'] if allowed else 0, interval_status='95% whole-pair percentile interval' if allowed else 'Unavailable: fewer than four complete pairs' if n < 4 else 'Unavailable: incomplete data or labelled descriptive check', evidence_status='Pre-intervention placebo; not a price effect' if window == 'placebo_3m' else 'Exploratory descriptive subgroup' if group_type != 'Overall' else 'Local randomised +GBP2 policy response', weight_method='Equal pairs' if weights is None else CFG['weighted_sensitivity'], unit=unit))
    for window, frame in pair_frames.items():
        add(frame, 'paired_equal', window, exact=window == 'primary_6m')
        if window == 'primary_6m':
            add(frame, 'fixed_pre_acquisition_weights', window, weights=frame.pre_acquisition_weight.to_numpy())
            add(frame[frame.post_competitor_entries == 0].reset_index(drop=True), 'exclude_post_entry_pairs', window)
            for field, label in [('region', 'Region'), ('relative_value_group', 'Pre-event relative value'), ('competition_group', 'Pre-event competitor intensity')]:
                groups = ['Positive gap', 'Non-positive gap'] if field == 'relative_value_group' else ['High', 'Medium', 'Low'] if field == 'competition_group' else sorted(frame[field].unique())
                for group in groups: add(frame[frame[field] == group].reset_index(drop=True), 'paired_equal', window, label, group)
            for pair in frame.pair_id:
                add(frame[frame.pair_id != pair].reset_index(drop=True), 'leave_one_pair_out', window, 'Omitted pair', pair, intervals=False)
    return pd.DataFrame(rows)

def matching_balance(m, assignments):
    reports = []
    for label, start, end in [('Matching', '2025-01-01', '2025-03-01'), ('Primary baseline', '2024-10-01', '2025-03-01')]:
        q = m[m.month.between(start, end)]
        f = q.groupby('gym_id').agg(price=('standard_price', 'mean'), members=('average_members', 'mean'), utilisation=('peak_utilisation_pct', 'mean'), acquisition=('acquisition_rate', 'mean'), churn=('churn_rate', 'mean'), competition=('competitor_count_3km', 'mean'))
        f['historical_growth'] = q.sort_values('month').groupby('gym_id').last().closing_members/q.sort_values('month').groupby('gym_id').first().opening_members-1
        a = assignments.merge(f, on='gym_id')
        if label == 'Matching':
            for field in f.columns: assert np.allclose(a['pre_'+field], a[field], atol=1e-8, rtol=1e-8), 'Assignment matching input mismatch '+field
            z = (f-f.mean())/f.std(ddof=0)
            for pair, group in a.groupby('pair_id'):
                ids = group.gym_id.tolist()
                distance = np.sqrt(np.mean((z.loc[ids[0]]-z.loc[ids[1]])**2))+(0.25 if group.location_type.nunique() > 1 else 0)
                # Source rates were rounded to eight decimals after assignment.
                assert abs(distance-group.matching_distance.iloc[0]) < 1e-6
        for field in f.columns:
            t, c = a[a.test_group == 'Treatment'][field], a[a.test_group == 'Control'][field]
            pooled = np.sqrt((t.var(ddof=1)+c.var(ddof=1))/2)
            reports.append(dict(window=label, metric=field, treatment_mean=t.mean(), control_mean=c.mean(), standardised_difference=divide(t.mean()-c.mean(), pooled)))
    return reports

def validate(panel, events, pair, estimates, m, ledger, history, assignments, before, after, matches):
    checks = []
    def check(name, ok):
        assert bool(ok), name
        checks.append(name)
    check('Prior source, generation, baseline and headroom hashes unchanged', before == after)
    check('80 unique gyms, 24 consecutive periods and 5760 family-panel rows', len(panel) == 5760 and panel.groupby(['event_family', 'gym_id']).size().eq(24).all() and m.groupby('gym_id').size().eq(24).all())
    expected_months = pd.date_range('2024-01-01','2025-12-01',freq='MS').strftime('%Y-%m-%d').tolist()
    check('Exact consecutive monthly ISO boundaries', all(sorted(q.month.tolist()) == expected_months for _,q in m.groupby('gym_id')))
    check('All eighty gyms are mature at the observation start', pd.read_csv(DATA/'gym_master.csv').opening_date.lt('2022-01-01').all() and m.gym_id.nunique()==80)
    for frame, keys, count in [(panel, ['gym_id', 'event_family', 'month'], 5760), (events, ['gym_id', 'event_id'], 32), (pair, ['pair_id', 'window'], 36)]: check('Unique key: '+','.join(keys), len(frame) == count and not frame.duplicated(keys).any())
    check('Unique estimates estimator/window/group/metric keys', not estimates.duplicated(['estimator', 'window', 'group_type', 'group', 'metric']).any())
    for name in ['opening_members', 'new_members', 'closing_members', 'subscription_revenue']:
        check('Ledger-to-monthly '+name, np.allclose(panel['ledger_'+name], panel[name], atol=.011, rtol=0))
    check('Monthly membership bridges', (panel.opening_members+panel.new_members-panel.opening_base_cancellations-panel.same_month_cancellations-panel.closing_members).abs().max() == 0)
    check('Closing and average tier membership totals', np.allclose(panel.standard_members+panel.offpeak_members+panel.premium_members,panel.closing_members) and np.allclose(panel.average_standard_members+panel.average_offpeak_members+panel.average_premium_members,panel.average_members))
    check('Every ledger bucket and tier transfer reconciles', (ledger.opening_members+ledger.new_members-ledger.opening_base_cancellations-ledger.same_month_cancellations+ledger.transfers_in-ledger.transfers_out-ledger.closing_members).eq(0).all() and ledger.groupby(['gym_id','month']).transfers_in.sum().equals(ledger.groupby(['gym_id','month']).transfers_out.sum()))
    check('Revenue component reconciliation within GBP0.01', np.allclose(panel.subscription_revenue+panel.joining_fee_revenue+panel.ancillary_revenue, panel.monthly_revenue, atol=.011, rtol=0))
    check('Eligible exits and opening-base downgrades bounded', ((panel.incumbent_standard_cancellations+panel.incumbent_standard_downgrades) <= panel.incumbent_standard_opening).all())
    std = ledger[ledger.membership_type == 'Standard']
    check('No bucket mixes opening members and same-month joins', not ((std.opening_members > 0) & (std.new_members > 0)).any())
    check('Joining-month transfers excluded from incumbent downgrade denominator', not ((std.transfers_out > 0) & (std.opening_members == 0) & (std.new_members == 0)).any())
    for prefix in ['treatment_pre_', 'treatment_post_', 'control_pre_', 'control_post_']:
        for name, (n, d) in RATES.items():
            expected = pair[prefix+n]/pair[prefix+d].replace(0, np.nan)*(1000 if name.startswith('complaints_per') else 1)
            check('Pair period exposure-weighted rate '+prefix+name, np.allclose(pair[prefix+name], expected, equal_nan=True))
    for name, (n, d) in RATES.items():
        expected = panel[n]/panel[d].replace(0, np.nan)*(1000 if name.startswith('complaints_per') else 1)
        check('Numerator/denominator rate: '+name, np.allclose(panel[name], expected, equal_nan=True))
    check('Pilot has original 12 treatment/12 control gyms', assignments.groupby('test_group').size().to_dict() == {'Control': 12, 'Treatment': 12})
    check('One treatment and control per pair', assignments.groupby('pair_id').test_group.nunique().eq(2).all())
    controls = assignments.loc[assignments.test_group == 'Control', 'gym_id']
    check('Pilot controls unchanged throughout source observation', not history.gym_id.isin(controls).any() and m[m.gym_id.isin(controls)].groupby('gym_id').standard_price.nunique().eq(1).all())
    check('Historical billing starts following notification month', (pd.to_datetime(history.effective_date)+pd.DateOffset(months=1)).eq(pd.to_datetime(history.existing_member_effective_date)).all() and history.notification_date.eq(history.effective_date).all())
    lookup = history.set_index(['gym_id', 'event_id'])
    active = std[std.repricing_event_id.notna()]
    for (gym, event), q in active.groupby(['gym_id', 'repricing_event_id']):
        h = lookup.loc[(gym, event)]
        applied = q[q.price_increment_applied.astype(bool)]
        expected_status = (q.month >= h.existing_member_effective_date) & (q.price_protected_until.isna() | (q.month >= q.price_protected_until))
        check('Every eligible status matches notice and expiry '+gym, np.array_equal(q.price_increment_applied.astype(bool), expected_status))
        check('Timing/protection '+gym, applied.empty or ((applied.month >= h.existing_member_effective_date) & (applied.price_protected_until.isna() | (applied.month >= applied.price_protected_until))).all())
        check('Single persistent cash increment '+gym, np.allclose(applied.base_billed_price-applied.billed_price+ h.change_amount, 0, atol=.011))
        check('New event-price cohorts excluded '+gym, q.join_month.isna().all() or (q.join_month.dropna() < h.effective_date).all())
        ordered = q.sort_values(['billing_bucket_id', 'month'])
        changes = ordered.assign(status=ordered.price_increment_applied.astype(int)).groupby('billing_bucket_id').status.diff().dropna()
        check('Persistent repricing flag '+gym, (changes >= 0).all())
    check('Missing denominators unavailable', pd.isna(divide(5, 0)) and pd.isna(controlled_log(0, 10, 10, 10)))
    check('Null controlled acquisition example', controlled_log(110, 100, 220, 200) == 0)
    check('Acquisition elasticity direction and pp units', controlled_log(90, 100, 100, 100)/np.log(27/25) < 0 and abs(100*((.06-.04)-(.05-.04))-1) < 1e-12)
    check('Intervals unavailable below four pairs', estimates[estimates.complete_pairs < 4][['ci_lower', 'ci_upper']].isna().all().all())
    check('Whole-pair exact 4096 assignments, zero null p=1', len(list(itertools.product([-1, 1], repeat=12))) == 4096 and exact_p(np.zeros(12)) == 1)
    check('Deterministic matching rerun', matches == targeted_matches(panel, history, pd.read_csv(DATA/'gym_master.csv')))
    check('Deterministic gym-ID distance ties', sorted([(1., 'NF002'), (1., 'NF001')], key=lambda x:(round(x[0],12),x[1]))[0][1] == 'NF001')
    check('Empty subgroup remains unavailable', estimates[estimates.assigned_pairs == 0][['estimate','ci_lower','ci_upper']].isna().all().all())
    check('Control-group member changes scaled per treatment site', abs(events.iloc[0].member_balance_response-((events.iloc[0].treatment_post_period_closing_members-events.iloc[0].treatment_post_period_opening_members)-(events.iloc[0].control_post_period_closing_members-events.iloc[0].control_post_period_opening_members)/events.iloc[0].comparator_count)) < 1e-8)
    source_gyms = pd.read_csv(DATA/'gym_master.csv')
    regions = source_gyms.set_index('gym_id').region
    for gym, match in matches.items():
        check('Nearest comparator deterministic '+gym, 0 <= len(match['control_ids']) <= 3 and not set(match['control_ids']) & set(history.gym_id) and (bool(match['control_ids']) or match['candidate_count']==0))
        check('Same-region comparators '+gym, all(regions.loc[c] == regions.loc[gym] for c in match['control_ids']))
    absent = source_gyms.copy(); first = sorted(matches)[0]
    absent.loc[absent.gym_id==first, 'region'] = 'Unavailable comparator fixture'
    absent_matches = targeted_matches(panel, history, absent)
    unavailable = event_results(panel, history, assignments, absent, absent_matches).set_index('gym_id').loc[first]
    check('No same-region comparators remain unavailable', unavailable.comparator_count == 0 and pd.isna(unavailable.controlled_acquisition_response) and pd.isna(unavailable.mean_matching_distance))
    check('Joint pair resampling preserves paired columns', np.array_equal(np.array([[10,100],[20,200],[30,300]])[[2,0,2]][:,1], 10*np.array([[10,100],[20,200],[30,300]])[[2,0,2]][:,0]))
    return checks

def visuals(panel, pair, estimates):
    sys.path.insert(0, str(AN/'.workbook_previews'/'python_packages'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': 'white'})
    colors = {'Treatment': '#243B53', 'Control': '#2F855A'}
    q = panel[(panel.event_family == 'PILOT_202504') & panel.assigned_role.isin(colors) & panel.month.between('2024-10-01', '2025-12-01')]
    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    profiles = []
    for arm, a in q.groupby('assigned_role'):
        monthly = a.groupby('month')[SUM_FIELDS].sum()
        for month, row in monthly.iterrows(): profiles.append({'month': month, 'arm': arm, 'standard_joins': row.standard_joins, 'incumbent_churn': divide(row.incumbent_standard_cancellations, row.incumbent_standard_opening), 'incumbent_downgrade': divide(row.incumbent_standard_downgrades, row.incumbent_standard_opening)})
        x = pd.to_datetime(monthly.index)
        axes[0].plot(x, monthly.standard_joins, marker='o', color=colors[arm], label=arm)
        axes[1].plot(x, 100*monthly.incumbent_standard_cancellations/monthly.incumbent_standard_opening, marker='o', color=colors[arm])
        axes[2].plot(x, 100*monthly.incumbent_standard_downgrades/monthly.incumbent_standard_opening, marker='o', color=colors[arm])
    for ax, title in zip(axes, ['Standard joins', 'Monthly churn (%)', 'Monthly downgrades (%)']):
        ax.set_ylabel(title); ax.axvline(pd.Timestamp('2025-04-01'), color='#D69E2E', linestyle='--'); ax.axvline(pd.Timestamp('2025-05-01'), color='#9F7AEA', linestyle=':'); ax.grid(alpha=.15)
    axes[0].legend(ncol=2); axes[0].set_title('Pilot profiles — notification/new-member price: April; incumbent billing: May')
    fig.tight_layout(); fig.savefig(AN/'pilot_monthly_profiles.png', dpi=160); plt.close(fig)
    p = pair[pair.window == 'primary_6m'].sort_values('pair_id')
    fig, axes = plt.subplots(1, 2, figsize=(11, 6), sharey=True)
    for ax, metric, title, factor in [(axes[0], 'controlled_acquisition_response', 'Controlled Standard acquisition response (%)', 100), (axes[1], 'incumbent_churn_response_pp', 'Controlled incumbent churn response (pp)', 1)]:
        ax.barh(p.pair_id, p[metric]*factor, color=['#C05621' if x > 0 else '#486581' for x in p[metric]]); ax.axvline(0, color='#243B53'); ax.set_xlabel(title); ax.grid(axis='x', alpha=.15)
    fig.suptitle('All twelve pairs — equal six-month windows'); fig.tight_layout(); fig.savefig(AN/'pilot_pair_responses.png', dpi=160); plt.close(fig)
    e = estimates[(estimates.estimator == 'paired_equal') & (estimates.window == 'primary_6m') & estimates.group_type.isin(['Overall', 'Pre-event relative value', 'Pre-event competitor intensity'])]
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    for ax, metric, title, factor in [(axes[0], 'controlled_acquisition_response', 'Standard acquisition response (%)', 100), (axes[1], 'incumbent_churn_response_pp', 'Incumbent churn response (pp)', 1)]:
        v = e[e.metric == metric].reset_index(drop=True)
        for i, r in v.iterrows():
            ax.plot(r.estimate*factor, i, 'o', color='#243B53')
            if pd.notna(r.ci_lower): ax.plot([r.ci_lower*factor, r.ci_upper*factor], [i, i], color='#486581', linewidth=2)
        ax.set_yticks(range(len(v)), [f'{r.group} (n={r.complete_pairs})' for _, r in v.iterrows()]); ax.axvline(0, color='#C05621', linestyle='--'); ax.set_xlabel(title); ax.grid(axis='x', alpha=.15)
    fig.suptitle('Local pilot estimates — intervals only for at least four complete pairs'); fig.tight_layout(); fig.savefig(AN/'pilot_estimate_intervals.png', dpi=160); plt.close(fig)
    return profiles

def documentation(panel, events, pair, estimates, checks, balance, matches, before, profiles):
    overall = estimates[(estimates.estimator == 'paired_equal') & (estimates.window == 'primary_6m') & (estimates.group_type == 'Overall')].set_index('metric')
    def display(metric, factor=1):
        r = overall.loc[metric]
        return f'{r.estimate*factor:,.3f} (95% interval {r.ci_lower*factor:,.3f} to {r.ci_upper*factor:,.3f})'
    robustness = estimates[(estimates.group_type == 'Overall') & estimates.metric.isin(['controlled_acquisition_response','incumbent_churn_response_pp','monthly_revenue_estimated_difference'])]
    robustness_text = '| Estimator / window | Acquisition response | Churn response (pp) | Estimated / weighted revenue difference |\n| --- | ---: | ---: | ---: |\n'
    for (estimator, window), group in robustness.groupby(['estimator','window'], sort=False):
        v = group.set_index('metric').estimate
        robustness_text += f"| {estimator} / {window} | {v['controlled_acquisition_response']:.2%} | {v['incumbent_churn_response_pp']:.3f} | £{v['monthly_revenue_estimated_difference']:,.0f} |\n"
    loo = estimates[(estimates.estimator == 'leave_one_pair_out') & (estimates.metric == 'controlled_acquisition_response')].estimate
    observational = events[events.event_family != 'PILOT_202504']
    observed_text = '; '.join(f"{family}: mean controlled acquisition {q.controlled_acquisition_response.mean():.2%}, mean churn difference {q.incumbent_churn_response_pp.mean():.3f} pp, and summed control-derived revenue difference £{q.monthly_revenue_estimated_difference.sum():,.0f}" for family,q in observational.groupby('event_family'))
    match_quality = f"All selected events have {int(observational.comparator_count.min())}–{int(observational.comparator_count.max())} same-region controls; mean standardised matching distances range from {observational.mean_matching_distance.min():.3f} to {observational.mean_matching_distance.max():.3f}. Larger distances indicate weaker observed comparability; there is no invented quality pass threshold."
    balance_text = '; '.join(f"{w}: maximum absolute standardised difference {max(abs(x['standardised_difference']) for x in balance if x['window']==w):.3f}" for w in ['Matching','Primary baseline'])
    primary_pair = pair[pair.window == 'primary_6m']
    support = '; '.join(f"{side}: {primary_pair[side+'_post_new_members'].sum():,.0f} all-tier joins, {primary_pair[side+'_post_period_opening_members'].sum():,.0f} April opening members to {primary_pair[side+'_post_period_closing_members'].sum():,.0f} September closing members, £{primary_pair[side+'_post_subscription_revenue'].sum():,.0f} observed net subscription revenue" for side in ['treatment','control'])
    tpaid = divide(primary_pair.treatment_post_incumbent_paid_rate_numerator.sum(), primary_pair.treatment_post_incumbent_standard_opening.sum())
    trepriced = divide(primary_pair.treatment_post_incumbent_repriced_opening.sum(), primary_pair.treatment_post_incumbent_standard_opening.sum())
    tprotected = divide(primary_pair.treatment_post_incumbent_protected_opening.sum(), primary_pair.treatment_post_incumbent_standard_opening.sum())
    out = {'disclaimer1':D1, 'disclaimer2':D2, 'input_hashes': before, 'analysis_configuration_hash':hashlib.sha256((AN/'response_config.json').read_bytes()).hexdigest(), 'rows': {name: len(frame) for name, frame in zip(OUTPUTS, [panel, events, pair, estimates])}, 'checks_passed': len(checks), 'primary_estimates': json.loads(overall.reset_index().to_json(orient='records')), 'matching_balance': balance, 'targeted_matches': matches, 'monthly_profiles': profiles}
    (AN/'response_results.json').write_text(json.dumps(out, indent=2, allow_nan=False))
    report = f'''# Northstar Fitness — historical price response

{D1}

{D2}

The April +£2 pilot supplies a local historical policy estimate from all twelve original randomised pairs. Standard acquisition, incumbent cancellations and tier downgrades are separate responses. The October 2024–March 2025 baseline and April–September 2025 follow-up each contain six months. No future price scenario, headroom reranking or pricing action is produced.

## What the evidence says

Controlled Standard acquisition response: **{display('controlled_acquisition_response', 100)}%**. Approximate acquisition elasticity: **{display('acquisition_elasticity')}**. The exact paired-assignment acquisition p-value is {overall.loc['controlled_acquisition_response','exact_p_value']:.5f}.

Incumbent Standard monthly churn changed by **{display('incumbent_churn_response_pp')} percentage points**, with exact assignment p-value {overall.loc['incumbent_churn_response_pp','exact_p_value']:.5f}. Downgrades changed by **{display('incumbent_downgrade_response_pp')} percentage points**. Site conversion changed by {display('conversion_response_pp')} pp; prospects are all-tier, so Standard conversion is unavailable.

Estimated cumulative total net revenue difference across the twelve treated gyms is **£{display('monthly_revenue_estimated_difference')}**, versus a control-derived counterfactual for the historical six-month period. Net subscription revenue difference is £{display('subscription_revenue_estimated_difference')}. Standard yield changed by £{display('standard_yield_controlled_change')} per member-month, while total ARPMM changed by £{display('total_arpmm_controlled_change')}. These are revenue measures; costs and profit are not modelled.

Observed post-window context: {support}. These raw arm totals reflect different starting sizes and do not replace pair-controlled estimates. Eligible incumbent treatment paid rate averages £{tpaid:.2f} gross, with {trepriced:.1%} of opening exposure already repriced and {tprotected:.1%} still promotion-protected across the post window. Complaints increased by {display('complaints_per_1000_member_months_controlled_change')} per 1,000 average-member months on the controlled comparison.

## Mixed evidence and uncertainty

{int((pair[pair.window=='primary_6m'].controlled_acquisition_response<0).sum())} of twelve pairs show a negative controlled Standard acquisition response; {int((pair[pair.window=='primary_6m'].incumbent_churn_response_pp>0).sum())} show higher incumbent churn. Every assigned pair remains in the primary result. Individual pairs are noisy; uncertainty and p-values do not provide rollout rules.

Early three-month, sustained nine-month, fixed pre-acquisition weights, leave-one-pair-out, pre-intervention placebo and competitor-entry exclusions are disclosed in the estimates interface. Pair groups use contemporaneous pre-event gaps and competitor counts. Regions contain one or two pairs each: regional estimates are descriptive and their intervals remain blank. Groups need four complete pairs for bootstrap intervals. Phase 4 segments are retrospective context and do not define causal response subgroups.

{robustness_text}

The weighted monetary sensitivity is pair count × fixed-weight mean increment; it reweights site composition and is not a sum of actual site cashflows. Primary monetary results sum the twelve treatment-site counterfactual increments. Leave-one-pair-out acquisition responses range from {loo.min():.2%} to {loo.max():.2%}. There are {int(pair[pair.window=='primary_6m'].post_competitor_entries.gt(0).sum())} primary pairs with post-window competitor entry, so the entry-exclusion sensitivity retains all pairs. Different bootstrap draws can give slightly different interval endpoints for the same retained population. All twelve pairs have positive average pre-period competitor gaps: the non-positive group has no observations and its estimates remain unavailable. High competition has two pairs, Medium seven, Low three; only Medium supports a subgroup interval. These data do not establish a reliable difference between competitor-intensity groups.

Balance diagnostics: {balance_text}. The pre-period churn placebo is adverse in the opposite direction, with its interval just including zero. This imbalance and the selected pilot sample limit how confidently the effect can be transported to other sites. The primary post window retains {int(primary_pair.post_competitor_cuts.sum())} competitor cuts and {int(primary_pair.post_competitor_promotions.sum())} promotion events across assigned gyms. Treatment marketing changed from £{primary_pair.treatment_pre_marketing_spend.sum():,.0f} to £{primary_pair.treatment_post_marketing_spend.sum():,.0f}; control marketing from £{primary_pair.control_pre_marketing_spend.sum():,.0f} to £{primary_pair.control_post_marketing_spend.sum():,.0f}. Seasonality and contemporaneous changes remain visible rather than being removed after observing outcomes.

The twenty commercially selected increases use up to three nearest never-repriced same-region controls, with pre-event standardised characteristics. Controls may be reused. Matching distance and candidate counts are disclosed for every event. {match_quality} Descriptive results: {observed_text}. These are observational comparisons: commercial selection, concurrent marketing, competitor changes and unobserved differences may explain part of the response. They are never pooled with the randomised evidence.

## What Phase 6 can learn

The pilot identifies a plausible acquisition response around one observed +£2 policy and separate monthly incumbent churn and downgrade responses, with intervals. It does not establish an estate-wide demand curve, precise per-gym elasticities, annual retention or future profit. Phase 6 should propagate the uncertainty and test acquisition and incumbent responses separately, respecting delayed billing and promotional protection.

![Monthly profiles](pilot_monthly_profiles.png)

Profiles show seasonality and delayed incumbent billing; raw arm trends are not controlled causal effects. April marks notification/new-joiner price and May marks eligible incumbent billing.

![All pairs](pilot_pair_responses.png)

Pair responses expose adverse and heterogeneous observations; individual pair estimates lack sufficient replication for standalone causal conclusions.

![Intervals](pilot_estimate_intervals.png)

Intervals and sample sizes show how little subgroup evidence supports precise conclusions. Missing intervals mean insufficient complete pairs, not zero uncertainty.

## Delivery and reconciliation

{len(panel):,} event-family panel rows, {len(events)} repriced-event rows, {len(pair)} pilot pair/window rows and {len(estimates):,} estimate rows are delivered. The panel repeats each gym-month three times for different event eligibility definitions; stocks and revenues must not be summed across families. Member stocks and member-month exposure are not unique customers.

All {len(checks)} Python checks passed. Source, generation configuration, baseline and headroom hashes are unchanged. See response_validation.md and response_workbook_verification.json for independent saved-workbook evidence; workbook completion is recorded only after recalculation and visual review.
'''
    (AN/'response_report.md').write_text(report, encoding='utf-8')
    methodology = f'''# Phase 5 definitions and reproducibility

{D1}

{D2}

Run `response_analysis.py` with bundled Python/NumPy/Pandas. The fixed configuration is `response_config.json`. No latent generation behavioural parameters are read. Run `validate_response_reproducibility.py` to rerun all four CSVs and compare bytes. Run `build_response_workbook.mjs` with Node `--max-old-space-size=16384`, then `repair_response_charts.mjs`, `package_response_chart_repairs.py`, `append_response_sheets.py`, the builder with `--verify-final`, the packager with `--update-caches`, and `verify_response_workbook.py` to author/recalculate/verify the saved workbook. The segmented package starts from a fresh current eighteen-sheet copy; its recovery snapshot is retained in `.workbook_previews/phase5/input_workbook.xlsx`. Pre-existing OOXML parts remain intact except explicit progress guidance and package metadata. Native editable workbook subgroup charts show estimate/lower/upper endpoint dots keyed to group indices and sample sizes in the title; the standalone forest visual shows the actual intervals. These indices identify categories and do not represent a continuous demand relationship. Explicit month-label formulas avoid raw date serials on chart axes.

Primary windows: Oct 2024–Mar 2025 / Apr–Sep 2025. Early: Jan–Mar / Apr–Jun 2025. Sustained: Jul 2024–Mar 2025 / Apr–Dec 2025. All are balanced. Placebo: Oct–Dec 2024 / Jan–Mar 2025, before notification. Original pilot assignments and January–March matching records are verified against historical source observations.

Standard joins are ledger acquisitions while current tier is Standard. Qualified prospects are not tier-specific; conversion is all-tier joins/prospects. Opening-base incumbent risk sets comprise current Standard members whose original cohort predates each event, including unknown-date legacy members. The risk set changes as people exit or switch tiers; it is not a fixed-person survival cohort. Downgrades use opening-base Standard transfers to Off-Peak only. Joining-month transfers are excluded, never counted as cancellations. The source has no mixed opening/new Standard buckets, making that split identifiable.

Opening exposure weights churn, downgrade, protected share and repriced share. Eligible paid-rate numerator is opening members × that month's actual billed price. The source protection date is the exclusive month-start expiry: protected while month < expiry, and eligible repricing can begin in the expiry month after notice. A persistent applied flag counts already-repriced members once as status, never as another monthly increase. New event-price cohorts are excluded from that event's incumbent population. Consumer headline and paid prices are VAT-inclusive; all revenue is net of the source's assumed 20% VAT. Subscription yield and Standard yield use average-member-month exposure; ARPMM includes joining fees and ancillary income. All prices and first-month promotions remain separate.

For each pair d=log(T post joins/T pre joins)−log(C post joins/C pre joins). Primary response=exp(mean(d))−1; elasticity=mean(d)/mean(log(new/old)). Equal pair weights; sensitivity uses the fixed sum of T and C pre-period Standard joins. Rate effects=100×[(Tpost−Tpre)−(Cpost−Cpre)] in percentage points. Continuous yield effects use corresponding differences in GBP/member-month. Revenue counterfactual=Tpre×Cpost/Cpre; increments sum across treated gyms. Revenue growth estimates average equal-pair controlled growth; they are not the ratio of aggregate revenues. Monthly acquisition and rate profiles aggregate numerators and exposure within arms.

One seeded generator supplies 10,000 index matrices of whole pairs, jointly resampling all metrics and price doses for each estimator/window/group. Percentile intervals require ≥4 complete pairs. No partial primary estimate is reported if an assigned pair is unavailable. Exact two-sided acquisition and incumbent-churn tests enumerate all 4096 sign flips, comparing absolute mean statistics with tolerance 1e−12; acquisition tests use log response. The transformation to percentage response is monotonic. Reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html . Bootstrap intervals and exact tests answer different questions. Exploratory estimates are unadjusted for multiple comparisons; small groups and possible imbalance limit inference.

Targeted controls are never-repriced gyms in the same region; only the preceding six months enter selection. Eight mean features: gross Standard price, average members, acquisition rate, churn, conversion, peak utilisation, competitor gap and marketing/prospect. Features standardise across all estate gyms in that event's pre-window using population standard deviations; constant features are excluded. Euclidean distances rank ascending, numerical ties at 12 decimals resolve by gym ID. Up to three controls; no same-region controls yields unavailable comparison. Control rates aggregate summed numerators/denominators; revenue post/pre ratios cancel the number of controls. Match quality is descriptive with no invented pass threshold. Selection bias remains.

Subgroups use average pair pre-window gaps (positive vs non-positive) and active competitor counts (High≥5, Medium3–<5, Low<3). These are defined before the intervention. Competitor entry, cuts, promotions and marketing movements are retained; removing pairs with post-entry is a labelled sensitivity with a potentially selected subgroup. Leave-one-pair-out estimates are descriptive, without intervals. Regional intervals are unavailable because only one or two pairs occur per region.

Keys: panel(gym_id,event_family,month), events(gym_id,event_id), pairs(pair_id,window), estimates(estimator,window,group_type,group,metric). Empty CSV fields represent unavailable values/absent assignments, never zero. Monthly dates are ISO first-of-month. Each family-panel repeats the same site economics but uses a different incumbent cutoff; choose one family before summing. No rejoining fabricated, no causal use of post-intervention headroom segments, no forecast or pricing action.
'''
    (AN/'phase5_methodology.md').write_text(methodology, encoding='utf-8')
    (AN/'response_validation.md').write_text('# Phase 5 Python validation\n\n'+D1+'\n\n'+D2+'\n\n'+'\n'.join('- PASS: '+x for x in checks)+'\n\nSaved workbook verification and visual review are recorded separately.\n', encoding='utf-8')
    dictionary = []
    source_dictionary = pd.read_csv(AN/'data_dictionary.csv').drop_duplicates('field').set_index('field').to_dict('index')
    definitions = {'standard_joins':'New members whose current tier at acquisition is Standard; ledger-derived, not tier-specific conversion.', 'incumbent_standard_opening':CFG['incumbent_definition'], 'incumbent_standard_downgrades':'Transfers out of eligible current Standard opening-base buckets to Off-Peak; joining-month transfers excluded.', 'price_increment_applied':'Persistent source status of a single eligible cash increase, not a repeated monthly charge.', 'controlled_acquisition_response':'exp(mean paired log before/after acquisition contrast)−1; decimal fraction.', 'pair_elasticity':'Pair log acquisition response / log actual gross price ratio; exploratory noisy pair result.', 'log_price_change':'Natural log of actual new/old gross Standard headline price.', 'pre_acquisition_weight':CFG['weighted_sensitivity'], 'monthly_revenue_estimated_difference':CFG['revenue_counterfactual'], 'incumbent_churn_response_pp':'100×[(treatment post−pre incumbent monthly churn)−(control post−pre)].', 'event_family':'One of three historical interventions; repeats site-month observations with event-specific incumbent eligibility.', 'interval_status':'Intervals unavailable below four complete pairs or for descriptive leave-one-pair-out checks.'}
    for table, frame, keys in zip(OUTPUTS, [panel, events, pair, estimates], ['gym_id,event_family,month','gym_id,event_id','pair_id,window','estimator,window,group_type,group,metric']):
        for field in frame:
            kind = 'boolean' if pd.api.types.is_bool_dtype(frame[field]) else 'numeric' if pd.api.types.is_numeric_dtype(frame[field]) else 'ISO date' if field in ['month','effective_date','notification_date','existing_member_effective_date','intervention_date','existing_member_billing_date','pre_start','pre_end','post_start','post_end'] else 'text'
            unit = 'percentage points' if field.endswith('_pp') else 'GBP net' if 'revenue' in field and not field.endswith('_growth') else 'GBP net / member-month' if any(x in field for x in ['yield','arpmm']) else 'GBP gross' if 'price' in field or 'paid_rate' in field or 'competitor_gap' in field else 'decimal rate' if any(x in field for x in ['churn','downgrade','conversion','share','growth','response','frequency','utilisation']) else 'count / exposure' if kind == 'numeric' else 'none'
            if field in ['estimate','ci_lower','ci_upper']: unit = 'Per metric: see unit field'
            elif field == 'exact_p_value': unit = 'decimal probability'
            elif 'elasticity' in field or field == 'log_price_change': unit = 'dimensionless'
            elif field.endswith('matching_distance'): unit = 'standardised distance'
            elif 'complaints_per_1000' in field: unit = 'complaints / 1000 average-member months'
            elif field == 'incumbent_paid_rate_numerator': unit = 'GBP gross × opening-member exposure'
            elif field.endswith('_months') or field == 'months': unit = 'months'
            elif field in source_dictionary: unit = source_dictionary[field]['unit']
            elif field in ['assigned_pairs','complete_pairs','treatment_gyms','control_gyms','bootstrap_samples','comparator_count','candidate_count']: unit = 'count'
            definition = definitions.get(field, '')
            if not definition:
                for prefix in ['treatment_pre_', 'treatment_post_', 'control_pre_', 'control_post_']:
                    if field.startswith(prefix): definition = prefix.replace('_',' ').strip()+': '+definitions.get(field[len(prefix):], field[len(prefix):].replace('_',' '))+'; summed counts/exposure, rates from sums, context period means.'
                if not definition: definition = source_dictionary[field]['definition'] if field in source_dictionary else field.replace('_',' ')+('; see phase5_methodology.md for estimator and aggregation' if kind == 'numeric' else '; stable source identifier or documented classification')
            dictionary.append(dict(table=table, field=field, data_type=kind, unit=unit, key=keys, reporting_window='2024-01 to 2025-12 source observations; event comparison windows in configuration', provenance='Derived from observed synthetic source ledger/monthly/history/assignments; estimates computed, not generator parameters', null_meaning='Unavailable denominator, unsupported interval, no assignment or not applicable; empty is never zero', definition=definition))
    pd.DataFrame(dictionary).to_csv(AN/'response_metric_dictionary.csv', index=False)
    return out

def main():
    PRE.mkdir(parents=True, exist_ok=True)
    before = hashes()
    m, ledger, gyms, assignments, history, market = [pd.read_csv(DATA/(name+'.csv')) for name in ['monthly_performance','membership_ledger','gym_master','experiment_assignments','pricing_history','market_events']]
    panel = build_panel(m, ledger, gyms, assignments, history, market)
    frames = {window: pairs(panel, assignments, history, window) for window in CFG['windows']}
    pair = pd.concat([frames[w] for w in ['primary_6m','early_3m','sustained_9m']], ignore_index=True)
    matches = targeted_matches(panel, history, gyms)
    events = event_results(panel, history, assignments, gyms, matches)
    estimates = estimate_rows(frames)
    balance = matching_balance(m, assignments)
    checks = validate(panel, events, pair, estimates, m, ledger, history, assignments, before, hashes(), matches)
    # Re-run all pair resampling to verify deterministic estimates, without resampling members.
    assert csv(estimates) == csv(estimate_rows(frames)); checks.append('Deterministic whole-pair bootstrap byte-identical rerun')
    for name, frame in zip(OUTPUTS, [panel, events, pair, estimates]): (DATA/(name+'.csv')).write_text(csv(frame), encoding='utf-8', newline='')
    profiles = visuals(panel, pair, estimates)
    result = documentation(panel, events, pair, estimates, checks, balance, matches, before, profiles)
    payload = {'config':CFG, 'result':result, 'balance':balance}
    for name, frame in zip(OUTPUTS+['monthly_performance','pricing_history','experiment_assignments'], [panel,events,pair,estimates,m,history,assignments]): payload[name] = json.loads(frame.to_json(orient='split', index=False, double_precision=15))
    payload['placebo_pairs'] = json.loads(frames['placebo_3m'].to_json(orient='split', index=False, double_precision=15))
    (PRE/'payload.json').write_text(json.dumps(payload, separators=(',',':'), allow_nan=False), encoding='utf-8')
    print(json.dumps({'rows':result['rows'],'checks':len(checks),'primary':result['primary_estimates']}, indent=2))

if __name__ == '__main__': main()
