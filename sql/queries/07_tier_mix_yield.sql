-- Commercial purpose: Track current-tier exposure, legacy paid rates and net subscription yield from the ledger.
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
FROM tier ORDER BY gym_id,membership_type;
