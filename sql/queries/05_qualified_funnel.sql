-- Commercial purpose: Evaluate recruitment conversion using qualified prospects; trials are not added to leads.
SELECT gym_id,SUM(website_leads) AS website_leads,SUM(trial_visits) AS trial_visits,
 SUM(qualified_prospects) AS qualified_prospects,SUM(new_members) AS joins,
 SUM(new_members)*1.0/NULLIF(SUM(qualified_prospects),0) AS conversion_rate,
 SUM(marketing_spend) AS marketing_spend,
 SUM(marketing_spend)/NULLIF(SUM(qualified_prospects),0) AS marketing_per_prospect
FROM monthly_performance WHERE month>='2025-01-01' AND month<'2026-01-01'
GROUP BY gym_id ORDER BY gym_id;
