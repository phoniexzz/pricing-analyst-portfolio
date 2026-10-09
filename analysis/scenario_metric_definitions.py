"""Phase 6 dictionary refinements; called by the reproducible generator."""
D={
'new_members':'Standard + Off-Peak + Plus forecast joins; summed across months in annual interfaces.',
'qualified_prospects':'Q4 prospect level, adjusted for 2025 regional seasonal indices, multiplied by forecast-month index.',
'opening_base_cancellations':'Sum of opening state members times bounded opening cancellation rate; excludes joining-month exits.',
'same_month_cancellations':'New joins times separately anchored joining-month exit rate.',
'closing_members':'Opening + joins - opening-base cancellations - joining-month exits; site transfers net to zero.',
'subscription_revenue':'Sum of state midpoint member exposure times applicable gross billed rate divided by 1 + VAT.',
'joining_fee_revenue':'All-tier joins times unchanged fee-payer fraction times gross fee divided by 1 + VAT.',
'ancillary_revenue':'Seasonal Q4-anchored net ancillary revenue, equal across main options.',
'incumbent_standard_opening':'Opening current Standard members present before January 2026, including legacy; future joiners excluded.',
'incumbent_standard_cancellations':'Opening-base exits from continuing pre-2026 Standard members.',
'incumbent_standard_downgrades':'Opening Standard-to-Off-Peak transfers from pre-2026 members, capped at opening survivors.',
'incumbent_standard_paid_rate_numerator':'Sum of incumbent Standard opening member exposure times applicable gross paid rate.',
'protected_standard_opening':'Incumbent Standard opening exposure still within carried promotion protection.',
'repriced_standard_opening':'Incumbent Standard opening exposure already billing the one-time forecast cash increment; zero for no increase.',
'opening_standard_downgrades':'Opening Standard-to-Off-Peak transfers, including future joiners in later months.',
'joining_month_downgrades':'Baseline transfers from new Standard survivors; excludes incumbent incremental response.',
'transfers_out':'Opening Standard downgrades + joining-month downgrades.',
'transfers_in':'Transfers received by Off-Peak; equals site transfers out.',
'pricing_complaints':'MAX(0, average-member exposure / 1000 times baseline complaint rate plus dose-scaled pilot increment during Jan-Mar). Weak evidence.',
'gym_visits':'Average members times seasonal observed visits per member; annual sums are visits, not unique visitors.',
'average_utilisation':'Visits times duration / (calendar opening minutes times concurrent capacity); opening-minute weighted across time.',
'peak_utilisation':'Average utilisation times historical peak-to-average multiplier; may exceed comfortable capacity.',
'probability_caps':'Count of state/rate or recruitment cap applications during evaluation; not a probability.',
'price_increment':'VAT-inclusive Standard cash increment received once per eligible billing state.',
'standard_price':'Frozen December Standard headline plus scenario increment.',
'competitor_price':'Frozen December comparable competitor recurring average; fees and introductory offers excluded.',
'old_standard_price':'December 2025 VAT-inclusive Standard headline.',
'new_standard_price':'Old Standard headline + scenario cash increment.',
'elasticity':'Equal-pair mean log acquisition response divided by mean pilot log price dose.',
'incumbent_churn_increment_pp':'Primary incumbent monthly churn rate increment times 100, before timing and dose scaling.',
'incumbent_downgrade_increment_pp':'Primary incumbent monthly downgrade rate increment times 100, before timing and dose scaling.',
'cumulative_incremental_revenue':'Sum of monthly scenario-minus-fixed-counterfactual revenue through this month.',
'month_member_difference':'Scenario closing members minus same-month counterfactual closing members.',
'marketing_spend':'Seasonal source-derived marketing spend, equal across options; context cost not deducted from revenue.',
'promotion_active':'Repeat corresponding-month 2025 promotion calendar; discount and duration inferred from billing records.',
'paid_rate':'Incumbent Standard gross paid-rate numerator / incumbent Standard opening exposure.',
'churn_rate':'Opening-base cancellations / opening-member exposure; summaries use summed numerator and denominator.',
'conversion_rate':'All-tier joins / qualified prospects; no tier-specific prospect conversion is invented.',
'arpmm':'Total net revenue / average-member-month exposure, including joining fees and ancillary income.',
'subscription_yield':'Net subscription revenue / all-tier average-member-month exposure.',
'standard_yield':'Standard net subscription revenue / Standard average-member-month exposure.',
'period_opening_members':'December 2025 closing ledger stock, identical across options and cases.',
'average_members_per_month':'Sum of monthly midpoint member exposures / 12.',
'retention_rate':'One minus exposure-weighted monthly opening-base churn; not annual retention.',
'member_growth':'December 2026 closing members / January 2026 opening members - 1.',
'complaints_per_1000':'Total complaints times 1000 / summed average-member-month exposure.',
'incumbent_paid_rate':'Incumbent Standard paid-rate numerator / incumbent Standard opening exposure.',
'protected_share':'Protected Standard opening exposure / incumbent Standard opening exposure.',
'repriced_share':'Already-billed forecast increase exposure / incumbent Standard opening exposure.',
'average_monthly_peak_utilisation':'Mean of twelve monthly peak utilisation rates; estate capacity weighted.',
'maximum_monthly_peak_utilisation':'Maximum monthly site peak pressure; estate shows maximum site pressure.',
'counterfactual_revenue':'Total annual net revenue from the fixed no-increase seasonal model.',
'revenue_uplift':'Incremental cumulative net revenue / counterfactual cumulative net revenue.',
'member_difference':'December scenario closing stock minus December counterfactual closing stock.',
'acquisition_difference':'Annual scenario all-tier joins minus annual counterfactual joins.',
'standard_acquisition_impact':'Annual scenario Standard joins / counterfactual Standard joins - 1.',
'churn_change_pp':'(Scenario all-tier monthly churn - counterfactual monthly churn) times 100.',
'incumbent_churn_change_pp':'(Scenario incumbent monthly churn - counterfactual incumbent churn) times 100.',
'downgrade_change_pp':'(Scenario incumbent downgrade rate - counterfactual rate) times 100.',
'conversion_change_pp':'(Scenario all-tier conversion - counterfactual conversion) times 100.',
'december_competitor_gap':'Frozen comparable December recurring competitor average minus old Standard headline.',
'post_increase_competitor_gap':'Frozen competitor recurring average minus new Standard headline.',
'out_of_pilot_value_support':'December competitor gap is non-positive, outside positive-gap pilot evidence.',
'repeated_repricing':'Site received an actual 2024/2025 Standard increase.',
'cash_increment_extrapolation':'Cash increase is GBP1 or GBP3 rather than the observed GBP2 pilot policy.',
'break_even_response_multiplier':'First root from joint elasticity/churn/downgrade stress on [0,64]; annual incremental net revenue zero.',
'break_even_member_impact':'December relative member impact at the first stress root.',
'break_even_crossings':'Count of exact zeros or sign changes detected on 257 stress grid points; first crossing refined by bisection.',
'case':'Base point vector or complete joint bootstrap vector near estate GBP2 revenue P10/P90.',
'variant':'Named alternative assumption; not a pricing action.',
'gym_id':'Stable gym ID; ESTATE represents aggregation of all 80 sites.',
'month':'First day of calendar month in January-December 2026.',
'region':'Eight-region geography from unchanged source master.'}
PARAM={'elasticity_parameter':'Shared acquisition elasticity','churn_increment_parameter':'Shared incumbent monthly cancellation increment, decimal rate','downgrade_increment_parameter':'Shared incumbent monthly downgrade increment, decimal rate','pilot_log_dose_parameter':'Mean natural-log pilot new/old headline price ratio','complaints_increment_parameter':'Shared controlled complaints increment per 1000 average-member months'}
def refine(table,f,definition,unit):
    base=f.rsplit('_',1)[0] if f.endswith(('_lower','_upper')) else f
    interval=base!=f
    definition=D.get(base,PARAM.get(base,definition))
    for t in ['standard','offpeak','plus']:
        if base==t+'_joins':definition=t+' joins = prospects times site Q4 tier-join/prospect probability; Standard additionally uses EXP(elasticity times LN(new/old headline)). Total joins capped at prospects.'
        if base==t+'_mix':definition=t+' average-member exposure / all-tier average-member exposure.'
        for suffix in ['opening_members','closing_members','average_members','subscription_revenue']:
            if base==t+'_'+suffix:definition=t+' current-tier '+D.get(suffix,'midpoint (opening + closing)/2 exposure').lower()
    if interval:definition=('2.5th' if f.endswith('_lower') else '97.5th')+' percentile of 10000 common whole-pair draws: '+definition
    if base in ['price_increment','standard_price','competitor_price','old_standard_price','new_standard_price','december_competitor_gap','post_increase_competitor_gap','paid_rate','incumbent_paid_rate']:unit='GBP VAT-inclusive'
    elif base=='incumbent_standard_paid_rate_numerator':unit='GBP VAT-inclusive times expected member exposure'
    elif base=='marketing_spend':unit='GBP marketing spend'
    elif base in ['probability_caps','break_even_crossings']:unit='count'
    elif base in ['out_of_pilot_value_support','repeated_repricing','cash_increment_extrapolation','promotion_active']:unit='boolean'
    elif base in ['elasticity','elasticity_parameter','pilot_log_dose_parameter','break_even_response_multiplier']:unit='dimensionless'
    elif base in ['churn_increment_parameter','downgrade_increment_parameter','member_growth']:unit='decimal fraction'
    elif base in ['complaints_per_1000','complaints_increment_parameter']:unit='complaints / 1000 average-member months'
    elif base in ['arpmm','subscription_yield','standard_yield']:unit='GBP net / average-member month'
    elif base in ['gym_id','region','case','variant','evidence_status']:unit='category / identifier'
    null='Unavailable denominator or observation; numeric zero remains zero.'
    if base.startswith('break_even'):null='No root, or aggregate/sensitivity root not evaluated; unavailable rather than zero.'
    elif interval:null='Conditional parameter interval unavailable in monthly/sensitivity interfaces or under manually revised evidence assumptions.'
    stock=base in ['opening_members','average_members','incumbent_standard_opening','protected_standard_opening','repriced_standard_opening','standard_opening_members','standard_average_members','offpeak_opening_members','offpeak_average_members','plus_opening_members','plus_average_members']
    if stock:unit='expected members' if table=='scenario_monthly' else 'expected member-month exposure'
    if base in ['closing_members','period_opening_members','month12_members','average_members_per_month','standard_closing_members','offpeak_closing_members','plus_closing_members','member_difference','month_member_difference']:unit='expected members'
    return definition,unit,null
