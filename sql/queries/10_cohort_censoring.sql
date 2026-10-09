-- Commercial purpose: Keep immature cohort retention and incomplete observed revenue unavailable.
SELECT gym_id,cohort_id,join_month,membership_type,customers_joined,observation_months,
 customers_remaining_30d/NULLIF(customers_joined,0) AS retention_30d,
 customers_remaining_90d/NULLIF(customers_joined,0) AS retention_90d,
 customers_remaining_180d/NULLIF(customers_joined,0) AS retention_180d,
 revenue_6_month,revenue_12_month
FROM cohorts ORDER BY gym_id,cohort_id;
