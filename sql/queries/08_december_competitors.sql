-- Commercial purpose: Compare recurring December consumer prices; fees and first-month offers stay separate.
SELECT c.gym_id,COUNT(*) AS competitor_count,AVG(c.competitor_standard_price) AS recurring_competitor_price,
 m.standard_price,AVG(c.competitor_standard_price)-m.standard_price AS competitor_gap,
 AVG(c.joining_fee) AS competitor_joining_fee,
 SUM(c.promotion_active) AS competitors_with_promotion,AVG(c.promotion_value) AS introductory_promotion_value
FROM competitor_prices c JOIN monthly_performance m ON c.gym_id=m.gym_id AND c.month=m.month
WHERE c.month='2025-12-01' GROUP BY c.gym_id,m.standard_price ORDER BY c.gym_id;
