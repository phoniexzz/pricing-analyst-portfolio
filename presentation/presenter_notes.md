# Northstar Fitness management presentation

Ten-slide presentation for the Pricing Manager, Commercial Director and CFO. Figures describe synthetic historical observations or hypothetical 2026 modelled outcomes.

## Slide 1: UK Gym Pricing & Revenue Optimisation

Executive recommendation: evaluate a controlled £1 pilot before wider implementation. Phase 7 identifies 11 conditional raises: 10 at £1 and one at £2. Their January–December 2026 Base scenario produces £148,618 incremental net revenue and -1,209 December members versus the same no-increase counterfactual. The 95% conditional parameter range is £64,400 to £230,752. TEST FIRST gains are excluded. The planned £1 experiment tests five first-repricing pairs as primary and two repeat pairs as exploratory. Its simulated results do not establish new evidence or authorise implementation. Sources: data/gym_recommendations.csv; data/recommendation_portfolio.csv; data/experiment_estimates.csv; analysis/experiment_report.md.

## Slide 2: 2025 revenue grew 2.37% as members fell 0.67%

2025 net revenue £107,006,934 versus £104,530,643 in 2024, a 2.37% increase. December member stock fell from 399,002 to 396,311, -0.67%. The bridge uses mean monthly average members and total ARPMM. It allocates the interaction to ARPMM: member volume -£425,764, total ARPMM £2,902,055, total change £2,476,291. Total ARPMM includes membership mix, joining fees and ancillary income. This is descriptive accounting, not a causal estimate of repricing. Churn is monthly opening-exposure-weighted, and members are stocks rather than unique people. Sources: analysis/baseline_results.json; data/estate_monthly_trend.csv.

## Slide 3: 31 gyms have no current recurring-price advantage

December 2025 competitor recurring price minus Northstar Standard headline price is positive when Northstar is cheaper. 31 of 80 sites have a non-positive gap. 38 sites retain at least one baseline caution. The scatter is descriptive and does not estimate elasticity. Competitors and national-equivalent benchmarks are fictional proxies under the documented comparability assumption. Joining fees and introductory discounts remain separate. Sources: data/gym_headroom.csv; analysis/headroom_report.md.

## Slide 4: High scores still require behavioural evidence

The weighted percentile score uses competitor gap 30%, low churn 25%, qualified conversion 15%, acquisition growth 15%, average monthly peak utilisation 10% and synthetic income 5%. Bands are High at 65, Medium 40 to less than 65, Low below 40. 15 sites have High scores and 5 of those retain caution flags. 51 sites change band or move at least ten ranks under an alternative. Segment precedence gives investigation priority to caution flags. This score does not estimate willingness to pay. Sources: data/gym_headroom.csv; data/headroom_sensitivity.csv; analysis/headroom_config.json.

## Slide 5: The historical £2 pilot gained revenue and lost joins

All twelve randomised pairs remain in the primary equal-pair analysis. Acquisition elasticity is -1.120, with a 95% whole-pair interval -1.902 to -0.384. It applies locally to Standard joining demand around the historical £2 policy, not to the entire member base. Cancellations and Standard-to-Off-Peak transfers are separate incumbent responses. Revenue is a control-derived six-month estimate across treated gyms. All pairs had positive pre-period gaps. Pre-trend imbalance, contemporary marketing, promotions and competitor changes limit transport. The 20 commercially selected increases stay observational and separate. Source: data/price_response_estimates.csv; analysis/response_report.md.

## Slide 6: Estate-wide increases trade yield for fewer members

The four scenarios start from December 2025's 396,311 ledger members. New Standard joiners see the increment on 1 January; eligible incumbents see it on 1 February or later at protection expiry. Legacy differences, promotional protection and historical obligations carry forward. Q4 site levels and observed regional seasonal drivers define the common trading counterfactual. Shared historical pilot responses affect acquisition, incumbent churn and downgrades separately. The ranges preserve joint whole-pair draws and exclude future shocks and transport uncertainty. Off-Peak and Plus headline prices stay unchanged. £3 is outside the action vocabulary and gives Standard/Plus headline equality at twenty previously +£2 sites. December ×12 is a separate seasonal run-rate, not earned annual revenue. Source: data/estate_scenarios.csv; analysis/scenario_report.md.

## Slide 7: Only 11 gyms qualify for conditional raises

Apply the ordered Phase 7 rules using unrounded evidence. Baseline caution or missing decision evidence gives DEFENSIVE / INVESTIGATE. Plausibility needs positive Base revenue and a non-negative post-increase competitor gap. Qualification additionally needs positive Downside revenue, a positive 95% conditional lower revenue bound, no more than 5% Downside December member loss and positive revenue in every non-zero-behaviour sensitivity. Select the qualifying increment with higher Base revenue, preferring £1 on ties. Repeat repricing sends a qualifying candidate to TEST FIRST. If neither increment is plausible, HOLD PRICE. The 5% gate is a policy assumption, distinct from experimental limits. All eighty actions remain in data/gym_recommendations.csv. Sources: data/gym_recommendations.csv; analysis/recommendation_config.json.

## Slide 8: The £149k portfolio depends on management policy

The Base conditional-raise portfolio sums only saved RAISE increments. Every other gym uses the no-increase path. Base net uplift £148,618, December member difference -1,209 (-0.31%), conditional 95% range £64,400 to £230,752. Portfolio ranges aggregate each selected site outcome within the same one of 10,000 joint draws before calculating quantiles; they never sum site endpoints. Downside and Upside use coherent shared parameter vectors, not every site's own best/worst outcome. Policy sensitivity changes judgement assumptions rather than re-estimating behaviour. TEST FIRST's provisional Base gains of £107,177 remain excluded. Source: data/recommendation_portfolio.csv; analysis/recommendation_report.md.

## Slide 9: The simulated £1 pilot is inconclusive at six months

Seven matched same-region/same-prior-pricing pairs assign seven treatment gyms and seven controls. Five first-repricing pairs define the primary population, two repeat pairs remain exploratory, with unavailable intervals. NF023 Portsmouth and NF057 Leicester remain reserves. Notice and new-joiner prices start 1 January 2026; protected/eligible incumbent bills change from 1 February. Six-month primary decision EXTEND TEST: revenue effect 1.02%, interval -0.96% to 3.03%, one-sided exact p 0.1875, two-sided 0.375. Harm upper bounds are compared with management-assumed limits, equality passes. Twelve-month STOP arises because incumbent churn's lower bound 0.315 pp exceeds +0.250 pp. Actual five-pair exact-test planning power is 64.7% at a 2% effect; its 80%-power detectable effect is 2.74%. Minimum attainable one-sided p is 3.125%. Sources: data/experiment_estimates.csv; data/experiment_design.csv; data/experiment_power.csv; analysis/experiment_report.md.

## Slide 10: New evidence is needed before broader repricing

Decision supported: whether to resource a real controlled £1 test for comparable first-repricing sites and the investigations needed before wider implementation. Refresh site eligibility and competitor comparability using current observations, match prospectively and randomise after fixing pairs. A real calendar must replace the hypothetical 2026 programme. Keep repeat repricing exploratory and retain controls. Conduct approximately 30- and 90-day safety reviews, a six-month primary assessment and twelve-month follow-up. A rollout decision requires complete evidence, revenue lower bound above zero, primary one-sided p no more than 5%, and upper harm bounds within the 3% member, 10% Standard acquisition and +0.25 pp monthly churn/downgrade limits. Service complaints above two per 1,000 member-months or consecutive months at capacity prompt investigation. Excluded markets, repeated repricing, £2/£3 and competitor reactions need separate evidence. Finance should assess contribution costs, bad debt and collection economics before treating revenue as profit. Sources: analysis/experiment_config.json; analysis/experiment_report.md; analysis/recommendation_report.md.

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.
This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.

## Delivery and use

Use the editable PPTX for presentation or revision. The PDF is a static, image-based viewing copy of the reviewed slides. The PowerPoint contains native charts with embedded data snapshots, five editable evidence tables and speaker notes. The PDF does not expose searchable text.

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
