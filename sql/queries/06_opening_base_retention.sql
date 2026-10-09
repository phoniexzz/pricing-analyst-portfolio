-- Commercial purpose: Separate opening-base churn from same-month exits and measure complaints by exposure.
SELECT gym_id,SUM(opening_members) AS opening_member_months,
 SUM(opening_base_cancellations) AS opening_base_cancellations,
 SUM(same_month_cancellations) AS same_month_cancellations,
 SUM(opening_base_cancellations)*1.0/NULLIF(SUM(opening_members),0) AS churn_rate,
 1-SUM(opening_base_cancellations)*1.0/NULLIF(SUM(opening_members),0) AS monthly_retention,
 SUM(pricing_complaints)*1000.0/NULLIF(SUM(average_members),0) AS complaints_per_1000_member_months
FROM monthly_performance WHERE month>='2025-01-01' AND month<'2026-01-01'
GROUP BY gym_id ORDER BY gym_id;
