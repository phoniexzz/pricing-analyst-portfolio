# Quick-reference evidence and definitions

All figures below are extracted from saved evidence. Use the reporting window and population with every number. Display rounding never changes the underlying saved value.

## Baseline — synthetic historical trading

| Metric | Saved display | Evidence ID |
|---|---|---|
| 2025 total net revenue | **£107,006,933.85** | `baseline.total_revenue` |
| December 2025 member stock | **396,311** | `baseline.closing_members` |
| 2025 total ARPMM | **£21.97** | `baseline.arpmm` |
| 2025 joins | **221,277** | `baseline.new_members` |
| 2025 monthly opening-base churn | **4.52%** | `baseline.churn_rate` |
| 2025 monthly opening-base retention | **95.48%** | `baseline.retention_rate` |
| 2025 qualified-prospect conversion | **30.73%** | `baseline.conversion_rate` |
| Matching-year net revenue growth | **2.37%** | `baseline.total_revenue_growth` |
| December closing membership growth | **-0.67%** | `baseline.closing_members_growth` |
| Revenue bridge member-volume contribution | **−£425,763.94** | `bridge.member_volume_contribution` |
| Revenue bridge total-ARPMM contribution | **£2,902,054.51** | `bridge.total_arpmm_contribution` |

## Headroom — relative indicators

| Metric | Saved display | Evidence ID |
|---|---|---|
| sensitive sites | **51** | `headroom.sensitive_sites` |
| high score with cautions | **5** | `headroom.high_score_with_cautions` |
| Saved score bands | **15 High; 43 Medium; 22 Low** | `headroom.band.*` |

## Historical pilot — local +£2 policy

| Metric | Saved display | Evidence ID |
|---|---|---|
| Controlled Standard acquisition response | **-8.27%; 95% interval -13.90% to -2.89%** | `pilot.controlled_acquisition_response.estimate` |
| controlled_acquisition_response exact p-value | **0.01660** | `pilot.controlled_acquisition_response.p` |
| Local Standard acquisition elasticity | **-1.120; 95% interval -1.902 to -0.384** | `pilot.acquisition_elasticity.estimate` |
| Monthly incumbent Standard churn change | **0.345 pp; 95% interval 0.182 pp to 0.497 pp** | `pilot.incumbent_churn_response_pp.estimate` |
| incumbent_churn_response_pp exact p-value | **0.00342** | `pilot.incumbent_churn_response_pp.p` |
| Monthly incumbent Standard downgrade change | **0.324 pp; 95% interval 0.294 pp to 0.356 pp** | `pilot.incumbent_downgrade_response_pp.estimate` |
| Estimated cumulative six-month total net revenue difference | **£217,436.41; 95% interval £151,026.19 to £289,220.13** | `pilot.monthly_revenue_estimated_difference.estimate` |

## Conditional RAISE-only portfolio — hypothetical 2026

| Metric | Saved display | Evidence ID |
|---|---|---|
| Base conditional RAISE portfolio uplift | **£148,618.48; conditional 95% range £64,400.37 to £230,752.09** | `portfolio.incremental_revenue` |
| December member difference versus no increase | **-1,209** | `portfolio.member_difference` |
| December member impact versus no increase | **-0.31%** | `portfolio.member_impact` |
| No-increase December 2026 members | **395,423** | `portfolio.counterfactual_month12_members` |
| Conditional-raise December 2026 members | **394,214** | `portfolio.month12_members` |
| Excluded provisional TEST FIRST gains | **£107,177.07** | `portfolio.excluded_test_first_base_revenue` |
| Saved action counts | **1 RAISE £2; 10 RAISE £1; 5 TEST FIRST; 26 HOLD; 38 INVESTIGATE** | `portfolio.*_sites` |

## Experiment — simulated primary first-repricing population

| Metric | Saved display | Evidence ID |
|---|---|---|
| Main 6-month revenue effect | **1.02%; 95% interval -0.96% to 3.03%** | `experiment.6.revenue_effect.estimate` |
| p value one sided | **0.18750** | `experiment.6.p_value_one_sided` |
| p value two sided | **0.37500** | `experiment.6.p_value_two_sided` |
| Main 6-month member harm | **2.05%; 95% interval 0.30% to 3.81%** | `experiment.6.member_harm.estimate` |
| Main 6-month standard acquisition harm | **5.27%; 95% interval -1.00% to 11.15%** | `experiment.6.standard_acquisition_harm.estimate` |
| Main 6-month incumbent churn change pp | **0.249 pp; 95% interval -0.083 pp to 0.530 pp** | `experiment.6.incumbent_churn_change_pp.estimate` |
| Main 6-month incumbent downgrade change pp | **0.175 pp; 95% interval 0.142 pp to 0.214 pp** | `experiment.6.incumbent_downgrade_change_pp.estimate` |
| Main 12-month incumbent churn change pp | **0.482 pp; 95% interval 0.315 pp to 0.650 pp** | `experiment.12.incumbent_churn_change_pp.estimate` |
| Main 6-month primary decision | **EXTEND TEST** | `decision.Main.6` |
| Main 12-month primary decision | **STOP** | `decision.Main.12` |
| A/A null 12-month primary decision | **MODIFY** | `decision.A/A null.12` |
| Planning power at assumed 2% revenue effect | **64.7%** | `power.planning_power` |
| Effect detectable at 80% planning power | **2.74%** | `power.effect_detectable_80pct` |

## Policy assumptions — not empirical tolerances

| Metric | Saved display | Evidence ID |
|---|---|---|
| member loss limit | **5.00%** | `policy7.member_loss_limit` |
| minimum post increase competitor gap | **£0.00** | `policy7.minimum_post_increase_competitor_gap` |
| test repeat repricing | **True** | `policy7.test_repeat_repricing` |
| member harm limit | **3.00%** | `policy8.member_harm_limit` |
| standard acquisition harm limit | **10.00%** | `policy8.standard_acquisition_harm_limit` |
| churn harm limit pp | **0.250 pp** | `policy8.churn_harm_limit_pp` |
| downgrade harm limit pp | **0.250 pp** | `policy8.downgrade_harm_limit_pp` |
| Complaints service trigger (per 1,000 average-member months) | **2.0** | `policy8.complaints_service_limit` |
| Capacity service trigger (% concurrent capacity) | **100.00%** | `policy8.capacity_service_limit` |
| Capacity trigger consecutive months | **2** | `policy8.capacity_consecutive_months` |
| alpha | **5.00%** | `policy8.alpha` |
| minimum interval pairs | **4** | `policy8.minimum_interval_pairs` |
| increment | **£1.00** | `policy8.increment` |
| intervention date | **2026-01-01** | `policy8.intervention_date` |
| billing date | **2026-02-01** | `policy8.billing_date` |
| vat rate | **20.00%** | `scenario.vat_rate` |

## Windows and populations

- Historical dataset: January 2024–December 2025; full-year 2025 baseline, matching 2024 and Q4 context.
- Pricing/headroom snapshot: December 2025; original estate ranks retained.
- Historical randomised +£2 primary comparison: October 2024–March 2025 versus April–September 2025; twelve pairs, April notice/new joiner price, May eligible incumbent billing.
- Historical robustness: three-month early, nine-month sustained and three-month pre-intervention placebo; twenty targeted increases remain observational.
- Scenarios: January–December 2026; expected fractional members, common no-increase counterfactual.
- Designed £1 experiment: seven pairs, seven treatment and seven control gyms; five first-repricing pairs primary, two repeat pairs exploratory. Portsmouth and Leicester are reserves.
- Experiment primary: July–December 2025 versus January–June 2026. One-, three- and twelve-month checkpoints use matching-length pre-periods.
- New joiner change/notice: 1 January 2026; eligible incumbent billing: 1 February or later at protection expiry. A real test needs a new prospective calendar.

## Definitions worth being able to derive

| Measure | Definition and boundary |
|---|---|
| Members | Opening + joins − opening-base exits − same-month exits = closing; tier transfers reconcile within a gym. |
| Average members | Approximate monthly opening/closing midpoint; annual average is mean monthly exposure. |
| Churn / retention | Opening-base exits ÷ summed opening exposure; retention is one minus the monthly exposure-weighted churn, not annual retention. |
| Acquisition / conversion | Joins ÷ opening-member exposure; joins ÷ qualified prospects. Standard conversion is unavailable because prospects are not tier-specific. |
| ARPMM / subscription yield | Total net revenue / summed average-member months; subscription revenue / the same exposure. Standard yield uses Standard exposure. |
| Consumer versus net money | Consumer headline and paid prices include assumed 20% VAT; revenue excludes it. |
| Competitor gap | Comparable recurring competitor price minus Standard headline price; positive means Northstar is cheaper. Fees and introductory discounts stay separate. |
| Cohorts | Original joining cohort survives tier switches. Legacy join dates are unknown. Immature milestones and incomplete revenue stay unavailable. |
| Historical acquisition response | exp(mean paired log join response) − 1. Elasticity = mean paired log response / mean log price dose. |
| Pair acquisition contrast | dᵢ = ln(Treatment post Standard joins / Treatment pre Standard joins) − ln(Control post Standard joins / Control pre Standard joins). |
| Pair-controlled revenue | Treatment post revenue − Treatment pre revenue × (Control post revenue / Control pre revenue). Log contrasts supply the equal-pair percentage effect. |
| Controlled churn/downgrade | Treatment-minus-control before/after opening-exposure rate difference, expressed in percentage points. |
| Revenue bridge | Δ exposure × old ARPMM + new exposure × Δ ARPMM; interaction allocated to ARPMM. |
| Exit run-rate | December monthly revenue ×12, a seasonal annualised exit figure; not earned annual revenue or a forecast. |

## Ordered decision rules

**Phase 7:** caution/missing evidence → investigate; neither candidate plausible → hold; otherwise test qualification, choose higher Base revenue with smaller exact-tie increment, and route repeat repricing to TEST FIRST. Qualifying financial gates require positive Base, Downside, conditional lower-bound and every non-zero sensitivity revenue; sufficient post-increase competitor gap; Downside member loss no greater than policy limit. Equality passes the member-loss and competitor-gap boundaries; zero revenue does not pass a strict-positive gate. £3 remains analytical only.

**Phase 8:** incomplete/invalid/unavailable → EXTEND TEST; revenue upper bound non-positive or harm lower bound above tolerance → STOP; unresolved service or point harm above tolerance → MODIFY; completed primary assessment with positive revenue lower bound, passing one-sided test and all upper harms within tolerance → ROLL OUT; otherwise EXTEND TEST. Equality passes harm limits. Early checks cannot roll out; repeat repricing and A/A cannot authorise progression.

## Uncertainty and common traps

- Conditional parameter uncertainty comes from joint historical pair draws; it excludes trading shocks and transport risk. Shared draws are aggregated before portfolio quantiles; never sum site interval endpoints.
- Simulated trading variation comes from residual blocks and integer flows. Experimental intervals resample whole observed simulated pairs; the simulation supplies no new independent evidence.
- The primary five-pair experiment enumerates 32 flips; minimum one-sided p-value is 3.125%, minimum two-sided 6.25%. Seven pooled pairs give 128 flips. At least four complete pairs are required for subgroup intervals; repeat/regional intervals remain unavailable.
- Main six-month revenue is positive at the point estimate but inconclusive; several upper harm bounds fail. Main twelve-month churn lower harm exceeds its tolerance, producing STOP.
- A/A no-increase diagnostic paths match exactly, yet the comparative estimator can trigger MODIFY from noise/baseline extrapolation. This is a management review signal, not causal harm.
- A missing rate is not zero; valid zero is retained. A member stock or repeated event-family/simulation observation is not a unique customer.
- A high score is not causal willingness to pay. A low p-value is not an implementation rule. Positive parameter draws are not rollout probabilities.
- Revenue is not profit or completed LTV. Persistent response, customer value, contribution costs, bad debt, competitor reactions, cannibalisation and repeat repricing need further evidence.
- The forecast does not acquire authority from an editable selector. Stale comparisons or manual behavioural overrides suppress authoritative ranges/recommendations until the required rerun/refresh.

Sources: [evidence register](evidence_register.json), [historical response](../analysis/response_report.md), [scenario methodology](../analysis/phase6_methodology.md), [recommendation policy](../analysis/recommendation_config.json), [experiment protocol](../analysis/experiment_protocol.md).
This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
