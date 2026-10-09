-- Commercial purpose: Describe recruitment during promotion months without asserting a causal promotion effect.
SELECT gym_id,promotion_active,COUNT(*) AS observed_months,SUM(new_members) AS joins,
 SUM(qualified_prospects) AS qualified_prospects,
 SUM(new_members)*1.0/NULLIF(SUM(qualified_prospects),0) AS conversion_rate,
 SUM(marketing_spend) AS marketing_spend
FROM monthly_performance WHERE month>='2025-01-01' AND month<'2026-01-01'
GROUP BY gym_id,promotion_active ORDER BY gym_id,promotion_active;
