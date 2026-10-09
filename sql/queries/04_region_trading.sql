-- Commercial purpose: Compare eight regions without averaging gym-level percentages.
SELECT g.region,CAST(SUBSTR(m.month,1,4) AS INTEGER) AS year,
 COUNT(DISTINCT m.gym_id) AS gym_count,SUM(m.monthly_revenue) AS total_revenue,
 SUM(m.average_members)/12.0 AS average_members,SUM(m.new_members) AS new_members,
 SUM(m.opening_base_cancellations) AS cancellations,
 SUM(m.opening_base_cancellations)*1.0/NULLIF(SUM(m.opening_members),0) AS churn_rate,
 SUM(m.new_members)*1.0/NULLIF(SUM(m.qualified_prospects),0) AS conversion_rate,
 SUM(CASE WHEN SUBSTR(m.month,6,2)='12' THEN m.closing_members ELSE 0 END) AS closing_members
FROM monthly_performance m JOIN gym_master g USING(gym_id)
GROUP BY g.region,SUBSTR(m.month,1,4) ORDER BY g.region,year;
