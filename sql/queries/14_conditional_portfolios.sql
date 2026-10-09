-- Commercial purpose: Map only conditional RAISE actions to saved scenarios; keep complete-portfolio ranges intact.
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
ORDER BY a.variant,a."case";
