"""Build Phase 11 access assets only; never rewrite commercial evidence."""
from pathlib import Path
import csv, json, re

ROOT = Path(__file__).resolve().parents[1]
TABLE_KEYS = {
    'gym_master': ['gym_id'], 'monthly_performance': ['gym_id','month'],
    'membership_ledger': ['gym_id','month','cohort_id','membership_type','billing_bucket_id'],
    'competitor_prices': ['gym_id','competitor_id','month'], 'cohorts': ['gym_id','cohort_id'],
    'gym_baseline': ['gym_id'], 'region_year_baseline': ['region','year'],
    'pilot_pair_response': ['pair_id','window'],
    'price_response_estimates': ['estimator','window','group_type','group','metric','weight_method'],
    'gym_scenarios': ['gym_id','price_increment','case'],
    'estate_scenarios': ['gym_id','price_increment','case'],
    'gym_recommendations': ['gym_id'],
    'recommendation_sensitivity': ['gym_id','variant'],
    'recommendation_portfolio': ['variant','case'],
    'experiment_monthly': ['simulation','gym_id','month'],
    'experiment_estimates': ['simulation','population','checkpoint_months','metric'],
    'experiment_monitoring': ['simulation','gym_id','checkpoint_months'],
}

# Each query is a read-only interface with a fixed reporting window and grain.
QUERIES = [
('membership_bridge', 'Reconcile integer member stocks and continuity across all historical months.', '''
WITH bridge AS (
 SELECT gym_id,month,opening_members,new_members,opening_base_cancellations,
 same_month_cancellations,closing_members,
 closing_members-opening_members-new_members+opening_base_cancellations+same_month_cancellations AS bridge_residual,
 LAG(closing_members) OVER(PARTITION BY gym_id ORDER BY month) AS previous_closing
 FROM monthly_performance
)
SELECT *, CASE WHEN previous_closing IS NULL THEN NULL ELSE opening_members-previous_closing END AS continuity_residual
FROM bridge ORDER BY gym_id,month;'''),
('weighted_baseline', 'Separate 2025 revenue components, average-member exposure and subscription yield by gym.', '''
SELECT m.gym_id,g.gym_name,g.region,COUNT(*) AS observed_months,
 SUM(m.monthly_revenue) AS total_revenue,SUM(m.subscription_revenue) AS subscription_revenue,
 SUM(m.joining_fee_revenue) AS joining_fee_revenue,SUM(m.ancillary_revenue) AS ancillary_revenue,
 AVG(m.average_members) AS average_members,SUM(m.average_members) AS member_months,
 SUM(m.monthly_revenue)/NULLIF(SUM(m.average_members),0) AS arpmm,
 SUM(m.subscription_revenue)/NULLIF(SUM(m.average_members),0) AS subscription_yield,
 SUM(m.standard_subscription_revenue)/NULLIF(SUM(m.average_standard_members),0) AS standard_yield,
 SUM(m.new_members) AS new_members
FROM monthly_performance m JOIN gym_master g USING(gym_id)
WHERE m.month >= '2025-01-01' AND m.month < '2026-01-01'
GROUP BY m.gym_id,g.gym_name,g.region ORDER BY m.gym_id;'''),
('matching_periods', 'Compare annual and Q4 growth with matching 2024 windows; rate differences are percentage points.', '''
WITH periods AS (
 SELECT 'Annual' AS period,SUBSTR(month,1,4) AS year,* FROM monthly_performance
 UNION ALL SELECT 'Q4',SUBSTR(month,1,4),* FROM monthly_performance WHERE SUBSTR(month,6,2)>='10'
), a AS (
 SELECT gym_id,period,year,SUM(monthly_revenue) AS revenue,SUM(new_members) AS joins,
 SUM(opening_base_cancellations)*1.0/NULLIF(SUM(opening_members),0) AS churn,
 SUM(new_members)*1.0/NULLIF(SUM(qualified_prospects),0) AS conversion
 FROM periods GROUP BY gym_id,period,year
)
SELECT y.gym_id,y.period,y.revenue AS revenue_2025,p.revenue AS revenue_2024,
 (y.revenue/NULLIF(p.revenue,0)-1)*100 AS revenue_growth_pct,
 (y.joins*1.0/NULLIF(p.joins,0)-1)*100 AS acquisition_growth_pct,
 (y.churn-p.churn)*100 AS churn_change_pp,(y.conversion-p.conversion)*100 AS conversion_change_pp
FROM a y JOIN a p ON y.gym_id=p.gym_id AND y.period=p.period AND p.year='2024'
WHERE y.year='2025' ORDER BY y.gym_id,y.period;'''),
('region_trading', 'Compare eight regions without averaging gym-level percentages.', '''
SELECT g.region,CAST(SUBSTR(m.month,1,4) AS INTEGER) AS year,
 COUNT(DISTINCT m.gym_id) AS gym_count,SUM(m.monthly_revenue) AS total_revenue,
 SUM(m.average_members)/12.0 AS average_members,SUM(m.new_members) AS new_members,
 SUM(m.opening_base_cancellations) AS cancellations,
 SUM(m.opening_base_cancellations)*1.0/NULLIF(SUM(m.opening_members),0) AS churn_rate,
 SUM(m.new_members)*1.0/NULLIF(SUM(m.qualified_prospects),0) AS conversion_rate,
 SUM(CASE WHEN SUBSTR(m.month,6,2)='12' THEN m.closing_members ELSE 0 END) AS closing_members
FROM monthly_performance m JOIN gym_master g USING(gym_id)
GROUP BY g.region,SUBSTR(m.month,1,4) ORDER BY g.region,year;'''),
('qualified_funnel', 'Evaluate recruitment conversion using qualified prospects; trials are not added to leads.', '''
SELECT gym_id,SUM(website_leads) AS website_leads,SUM(trial_visits) AS trial_visits,
 SUM(qualified_prospects) AS qualified_prospects,SUM(new_members) AS joins,
 SUM(new_members)*1.0/NULLIF(SUM(qualified_prospects),0) AS conversion_rate,
 SUM(marketing_spend) AS marketing_spend,
 SUM(marketing_spend)/NULLIF(SUM(qualified_prospects),0) AS marketing_per_prospect
FROM monthly_performance WHERE month>='2025-01-01' AND month<'2026-01-01'
GROUP BY gym_id ORDER BY gym_id;'''),
('opening_base_retention', 'Separate opening-base churn from same-month exits and measure complaints by exposure.', '''
SELECT gym_id,SUM(opening_members) AS opening_member_months,
 SUM(opening_base_cancellations) AS opening_base_cancellations,
 SUM(same_month_cancellations) AS same_month_cancellations,
 SUM(opening_base_cancellations)*1.0/NULLIF(SUM(opening_members),0) AS churn_rate,
 1-SUM(opening_base_cancellations)*1.0/NULLIF(SUM(opening_members),0) AS monthly_retention,
 SUM(pricing_complaints)*1000.0/NULLIF(SUM(average_members),0) AS complaints_per_1000_member_months
FROM monthly_performance WHERE month>='2025-01-01' AND month<'2026-01-01'
GROUP BY gym_id ORDER BY gym_id;'''),
('tier_mix_yield', 'Track current-tier exposure, legacy paid rates and net subscription yield from the ledger.', '''
WITH tier AS (
 SELECT gym_id,membership_type,SUM(average_members) AS member_months,
 SUM(subscription_revenue) AS subscription_revenue,
 SUM(average_members*billed_price) AS gross_paid_exposure
 FROM membership_ledger WHERE month>='2025-01-01' AND month<'2026-01-01'
 GROUP BY gym_id,membership_type
)
SELECT gym_id,membership_type,member_months,subscription_revenue,
 subscription_revenue/NULLIF(member_months,0) AS net_subscription_yield,
 gross_paid_exposure/NULLIF(member_months,0) AS gross_average_paid_rate,
 member_months/NULLIF(SUM(member_months) OVER(PARTITION BY gym_id),0) AS membership_mix
FROM tier ORDER BY gym_id,membership_type;'''),
('december_competitors', 'Compare recurring December consumer prices; fees and first-month offers stay separate.', '''
SELECT c.gym_id,COUNT(*) AS competitor_count,AVG(c.competitor_standard_price) AS recurring_competitor_price,
 m.standard_price,AVG(c.competitor_standard_price)-m.standard_price AS competitor_gap,
 AVG(c.joining_fee) AS competitor_joining_fee,
 SUM(c.promotion_active) AS competitors_with_promotion,AVG(c.promotion_value) AS introductory_promotion_value
FROM competitor_prices c JOIN monthly_performance m ON c.gym_id=m.gym_id AND c.month=m.month
WHERE c.month='2025-12-01' GROUP BY c.gym_id,m.standard_price ORDER BY c.gym_id;'''),
('promotion_context', 'Describe recruitment during promotion months without asserting a causal promotion effect.', '''
SELECT gym_id,promotion_active,COUNT(*) AS observed_months,SUM(new_members) AS joins,
 SUM(qualified_prospects) AS qualified_prospects,
 SUM(new_members)*1.0/NULLIF(SUM(qualified_prospects),0) AS conversion_rate,
 SUM(marketing_spend) AS marketing_spend
FROM monthly_performance WHERE month>='2025-01-01' AND month<'2026-01-01'
GROUP BY gym_id,promotion_active ORDER BY gym_id,promotion_active;'''),
('cohort_censoring', 'Keep immature cohort retention and incomplete observed revenue unavailable.', '''
SELECT gym_id,cohort_id,join_month,membership_type,customers_joined,observation_months,
 customers_remaining_30d/NULLIF(customers_joined,0) AS retention_30d,
 customers_remaining_90d/NULLIF(customers_joined,0) AS retention_90d,
 customers_remaining_180d/NULLIF(customers_joined,0) AS retention_180d,
 revenue_6_month,revenue_12_month
FROM cohorts ORDER BY gym_id,cohort_id;'''),
('saved_pilot_evidence', 'Expose all 12 saved primary pair responses; incumbent changes remain separate from acquisition.', '''
SELECT pair_id,region,treatment_gym_id,control_gym_id,acquisition_log_response,
 controlled_acquisition_response,
 ((treatment_post_incumbent_churn-treatment_pre_incumbent_churn)
 -(control_post_incumbent_churn-control_pre_incumbent_churn))*100 AS incumbent_churn_change_pp,
 ((treatment_post_incumbent_downgrade-treatment_pre_incumbent_downgrade)
 -(control_post_incumbent_downgrade-control_pre_incumbent_downgrade))*100 AS downgrade_change_pp,
 monthly_revenue_estimated_difference AS estimated_revenue_difference
FROM pilot_pair_response WHERE window='primary_6m' ORDER BY pair_id;'''),
('saved_base_scenarios', 'Compare four saved Base options with a common counterfactual; no case aggregation.', '''
SELECT gym_id,price_increment,"case",monthly_revenue AS annual_revenue,incremental_revenue,
 month12_members,member_impact,new_members,churn_rate,incumbent_downgrade_rate,arpmm,
 annualised_exit_run_rate,break_even_response_multiplier,break_even_member_impact,
 incremental_revenue_lower,incremental_revenue_upper
FROM gym_scenarios WHERE "case"='Base' ORDER BY gym_id,price_increment;'''),
('saved_recommendations', 'Inspect unchanged actions, conditional qualification gates and investigation rationale.', '''
SELECT r.gym_id,g.gym_name,g.region,r.action,r.proposed_increment,r.provisional_test_increment,
 r.rule_id,r.plus1_qualified,r.plus2_qualified,r.plus1_failed_gates,r.plus2_failed_gates,
 r.selected_incremental_revenue,r.selected_member_impact,r.explanation
FROM gym_recommendations r JOIN gym_master g USING(gym_id) ORDER BY r.gym_id;'''),
('conditional_portfolios', 'Map only conditional RAISE actions to saved scenarios; keep complete-portfolio ranges intact.', '''
WITH selected AS (
 SELECT r.variant,s."case",r.gym_id,r.action,s.*
 FROM recommendation_sensitivity r JOIN gym_scenarios s ON r.gym_id=s.gym_id
 AND s.price_increment=CASE WHEN r.action IN ('RAISE £1','RAISE £2') THEN r.proposed_increment ELSE 0 END
), a AS (
 SELECT variant,"case",COUNT(*) AS gym_count,
 SUM(CASE WHEN action IN ('RAISE £1','RAISE £2') THEN 1 ELSE 0 END) AS raise_sites,
 SUM(monthly_revenue) AS annual_revenue,SUM(incremental_revenue) AS incremental_revenue,
 SUM(month12_members) AS month12_members,SUM(member_difference) AS member_difference,
 SUM(new_members)/NULLIF(SUM(qualified_prospects),0) AS conversion_rate,
 SUM(opening_base_cancellations)/NULLIF(SUM(opening_members),0) AS churn_rate
 FROM selected GROUP BY variant,"case"
)
SELECT a.*,p.incremental_revenue_lower,p.incremental_revenue_upper,
 p.excluded_test_first_base_revenue AS excluded_provisional_test_gains
FROM a JOIN recommendation_portfolio p ON a.variant=p.variant AND a."case"=p."case"
ORDER BY a.variant,a."case";'''),
('experiment_monitoring', 'Show saved first/repeat population decisions and intervals at each checkpoint.', '''
WITH decisions AS (
 SELECT DISTINCT simulation,population,checkpoint_months,population_decision
 FROM experiment_monitoring
)
SELECT e.simulation,e.population,e.checkpoint_months,e.complete_pairs,e.estimate AS revenue_effect,
 e.lower,e.upper,e.interval_status,e.p_value_one_sided,d.population_decision
FROM experiment_estimates e JOIN decisions d USING(simulation,population,checkpoint_months)
WHERE e.metric='revenue_effect' ORDER BY e.simulation,e.population,e.checkpoint_months;''')
]

def main():
    sql=ROOT/'sql';(sql/'queries').mkdir(parents=True,exist_ok=True)
    schema={}
    for name,keys in TABLE_KEYS.items():
        with (ROOT/'data'/f'{name}.csv').open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);rows=list(reader);columns={}
        for col in reader.fieldnames:
            values={r[col] for r in rows if r[col]!=''}
            boolean=bool(values) and values <= {'True','False'}
            if boolean:typ='INTEGER';kind='boolean'
            elif values and all(re.fullmatch(r'-?\d+',v) for v in values):typ='INTEGER';kind='integer'
            elif values and all(re.fullmatch(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?',v) for v in values):typ='REAL';kind='number'
            else:typ='TEXT';kind='date' if values and all(re.fullmatch(r'\d{4}-\d{2}-\d{2}',v) for v in values) else 'text'
            columns[col]={'sqlite_type':typ,'kind':kind,'nullable':any(r[col]=='' for r in rows)}
        schema[name]={'csv':f'data/{name}.csv','key':keys,'columns':columns}
    (sql/'schema.json').write_text(json.dumps(schema,indent=2)+'\n',encoding='utf-8')
    catalog=[]
    for i,(name,purpose,query) in enumerate(QUERIES,1):
        filename=f'{i:02d}_{name}.sql'
        (sql/'queries'/filename).write_text('-- Commercial purpose: '+purpose+'\n'+query.strip()+'\n',encoding='utf-8')
        catalog.append({'id':i,'file':filename,'purpose':purpose})
    (sql/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf-8')
    captions=[('01_executive_overview.jpg','Executive Overview','2025 trading and exact volume/ARPMM bridge.'),
      ('02_estate_pricing.jpg','Estate Pricing','December 2025 price snapshots and original headroom evidence.'),
      ('03_member_behaviour.jpg','Customer & Member Behaviour','Weighted acquisition, churn and historical policy response.'),
      ('04_pricing_scenarios.jpg','Pricing Scenarios','Saved combinations; controls do not rerun forecasts.'),
      ('05_recommendations.jpg','Recommendations','Saved conditional actions and qualification evidence.'),
      ('06_experiment_main_6m_first.jpg','Experiment & Monitoring','Main simulation, six months, five first-repricing pairs: EXTEND TEST.'),
      ('07_gym_detail_NF001.jpg','Gym Detail','NF001 drill-through with trading and recommendation rationale.')]
    gallery='# Native Power BI dashboard gallery\n\nThese are native Desktop captures, not design previews. All seven layouts and interactions passed the [recorded acceptance](../analysis/powerbi_native_acceptance.json). Screenshots show the captured viewport; scrollable tables contain additional rows in the PBIX.\n\n'
    for filename,title,caption in captions:
        assert (ROOT/'images/native_powerbi'/filename).is_file()
        gallery+=f'## {title}\n\n{caption}\n\n![Native Power BI — {title}](../images/native_powerbi/{filename})\n\n'
    gallery+='Separate `images/powerbi_p*.png` files are design previews, not native Power BI screenshots.\n'
    (ROOT/'portfolio/dashboard_gallery.md').write_text(gallery,encoding='utf-8')
    guidance=json.loads((ROOT/'analysis/latest_phase_guidance.json').read_text())
    guidance['Dataset Overview'].update(D5='Phase 11 complete',E5='Portfolio + SQL',E7='Phase 12 next')
    guidance['README']['B20']='Phase 11 complete; Phase 12 next. Power BI native verification complete.'
    guidance['Recommendation Summary']['A17']='Phase 11 complete; Phase 12 next. Conditional actions unchanged.'
    (ROOT/'analysis/latest_phase_guidance.json').write_text(json.dumps(guidance,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
