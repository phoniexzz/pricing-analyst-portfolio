-- Commercial purpose: Reconcile integer member stocks and continuity across all historical months.
WITH bridge AS (
 SELECT gym_id,month,opening_members,new_members,opening_base_cancellations,
 same_month_cancellations,closing_members,
 closing_members-opening_members-new_members+opening_base_cancellations+same_month_cancellations AS bridge_residual,
 LAG(closing_members) OVER(PARTITION BY gym_id ORDER BY month) AS previous_closing
 FROM monthly_performance
)
SELECT *, CASE WHEN previous_closing IS NULL THEN NULL ELSE opening_members-previous_closing END AS continuity_residual
FROM bridge ORDER BY gym_id,month;
