-- Commercial purpose: Compare annual and Q4 growth with matching 2024 windows; rate differences are percentage points.
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
WHERE y.year='2025' ORDER BY y.gym_id,y.period;
