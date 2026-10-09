-- Commercial purpose: Compare four saved Base options with a common counterfactual; no case aggregation.
SELECT gym_id,price_increment,"case",monthly_revenue AS annual_revenue,incremental_revenue,
 month12_members,member_impact,new_members,churn_rate,incumbent_downgrade_rate,arpmm,
 annualised_exit_run_rate,break_even_response_multiplier,break_even_member_impact,
 incremental_revenue_lower,incremental_revenue_upper
FROM gym_scenarios WHERE "case"='Base' ORDER BY gym_id,price_increment;
