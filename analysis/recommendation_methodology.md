# Phase 7 method and interfaces

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.

Keys: gym_recommendations = gym_id (80); recommendation_sensitivity = gym_id, variant (400); recommendation_portfolio = variant, case (15). ISO gym IDs remain stable. Prices/gaps include VAT, revenue excludes assumed 20% VAT, decimal rates and pp changes preserve Phase 3–6 definitions. Historical context uses full-year/Q4 2025; scenarios cover January–December 2026.

Policy order is defined in recommendation_config.json and classifier tests. Base/Downside names are fixed regardless of the displayed workbook case. Source full-precision Phase 6 prepared records are used rather than rounded CSV amounts. Caution flags originate in Phase 3. Headroom scores/bands are retained unchanged. Every required candidate input and every six named nonzero sensitivity is required; no silent imputation. Missing evidence gets R1_MISSING. Zero evidence is valid but strict positive-revenue gates reject zero gains. Missing context is disclosed rather than invented.

Proposed_increment belongs only to conditional RAISE actions. Assessment_increment can be a provisional test amount; selected_* fields describe that assessment and are not portfolio gains. HOLD/INVESTIGATE assessment is zero. +£3 is analytical context only.

Portfolio rows select one unchanged Phase 6 site/case record for each gym, using conditional RAISE increments and zero for all other actions. Sum revenue components, stocks and exposures separately. Churn, incumbent churn, downgrades, conversion, yield, ARPMM, membership mix and complaint rates use summed numerators/denominators. Null denominators remain unavailable. The annualised exit run-rate is a sum of December×12 records.

For uncertainty, retain outcome[d, increment, gym, metric] from Phase 6's 10,000 joint draws (seed 20261006). Sum selected site outcomes inside each d, then take percentile bounds. Subtract the identical no-increase counterfactual for revenue; divide by no-increase December stock for member impact. No resampling, independent site shocks or summing interval endpoints. If the retained draw file is absent, restore it through the existing Phase 6 analysis before completion; do not fabricate intervals.

Run recommendation_analysis.py to regenerate; --reproduce checks byte-identical output without replacing CSVs. Policy-only workbook refresh reads saved policy inputs and applies the same classifier to reconciled saved comparison records; it does not overwrite the analyst-facing evidence interfaces. Refresh must preserve all sheets, restore the existing case selector and refresh captured portfolio uncertainty only against unchanged evidence-derived scenarios/draws. Manual behavioural overrides or stale comparisons suppress authority until Phase 6 evidence is rerun.
