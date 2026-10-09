-- Commercial purpose: Inspect unchanged actions, conditional qualification gates and investigation rationale.
SELECT r.gym_id,g.gym_name,g.region,r.action,r.proposed_increment,r.provisional_test_increment,
 r.rule_id,r.plus1_qualified,r.plus2_qualified,r.plus1_failed_gates,r.plus2_failed_gates,
 r.selected_incremental_revenue,r.selected_member_impact,r.explanation
FROM gym_recommendations r JOIN gym_master g USING(gym_id) ORDER BY r.gym_id;
