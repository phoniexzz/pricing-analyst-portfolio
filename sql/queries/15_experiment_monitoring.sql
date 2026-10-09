-- Commercial purpose: Show saved first/repeat population decisions and intervals at each checkpoint.
WITH decisions AS (
 SELECT DISTINCT simulation,population,checkpoint_months,population_decision
 FROM experiment_monitoring
)
SELECT e.simulation,e.population,e.checkpoint_months,e.complete_pairs,e.estimate AS revenue_effect,
 e.lower,e.upper,e.interval_status,e.p_value_one_sided,d.population_decision
FROM experiment_estimates e JOIN decisions d USING(simulation,population,checkpoint_months)
WHERE e.metric='revenue_effect' ORDER BY e.simulation,e.population,e.checkpoint_months;
