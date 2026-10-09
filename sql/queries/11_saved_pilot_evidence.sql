-- Commercial purpose: Expose all 12 saved primary pair responses; incumbent changes remain separate from acquisition.
SELECT pair_id,region,treatment_gym_id,control_gym_id,acquisition_log_response,
 controlled_acquisition_response,
 ((treatment_post_incumbent_churn-treatment_pre_incumbent_churn)
 -(control_post_incumbent_churn-control_pre_incumbent_churn))*100 AS incumbent_churn_change_pp,
 ((treatment_post_incumbent_downgrade-treatment_pre_incumbent_downgrade)
 -(control_post_incumbent_downgrade-control_pre_incumbent_downgrade))*100 AS downgrade_change_pp,
 monthly_revenue_estimated_difference AS estimated_revenue_difference
FROM pilot_pair_response WHERE window='primary_6m' ORDER BY pair_id;
