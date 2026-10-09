-- Commercial purpose: Separate 2025 revenue components, average-member exposure and subscription yield by gym.
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
GROUP BY m.gym_id,g.gym_name,g.region ORDER BY m.gym_id;
