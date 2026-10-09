# Thirty core interview questions

Use the spoken answers as frameworks, not scripts to memorise. Explain the technical follow-up in your own words. Personalise ownership honestly. Each source supports the documented method; the evidence register provides exact numerical values.

## Commercial economics

### Q01. What business decision does this project support?

**Spoken response:** It asks where a Standard increase could add sustainable revenue after recruitment, incumbent cancellations and downgrades respond. The output is a conditional site action and a controlled test requirement. I would present the revenue gain with its member cost, rather than treat a higher headline price as success.

**Technical follow-up:** Explain the chain from price to perceived value, conversion, acquisition, retention, average-member exposure and revenue. Identify which channels affect current cashflow and which affect future value.

**Evidence:** [analysis/business_brief.md](../analysis/business_brief.md).

**Limit:** The recommendation is hypothetical; the project cannot authorise a real operator to change prices.

### Q02. Why can revenue grow while membership falls?

**Spoken response:** Higher realised yield can outweigh lower member volume. The baseline bridge separates these contributions exactly, while recognising that total ARPMM includes tier mix, joining fees and ancillary income. December membership and annual average exposure measure different things, so I would not divide annual revenue by a single closing stock.

**Technical follow-up:** The bridge uses old ARPMM for the volume contribution and new exposure for the ARPMM contribution. That allocates their interaction to ARPMM and reconciles to the annual revenue change.

**Evidence:** [analysis/baseline_results.json](../analysis/baseline_results.json).

**Limit:** This is descriptive accounting; it does not prove that repricing caused the yield change.

### Q03. How are headline price, subscription yield and ARPMM different?

**Spoken response:** Headline price is the advertised consumer rate. Subscription yield divides net subscription revenue by average-member exposure and reflects legacy rates, discounts and mix. Total ARPMM adds fees and ancillary income to that numerator. I keep all three visible so fee growth cannot disguise weakening membership performance.

**Technical follow-up:** Explain the assumed VAT conversion and why Standard yield needs Standard exposure while estate ARPMM uses all-tier exposure. Query 02 calculates the three revenue components and appropriate denominators.

**Evidence:** [sql/queries/02_weighted_baseline.sql](../sql/queries/02_weighted_baseline.sql).

**Limit:** Average-member exposure is a monthly billing approximation, not exact daily billable membership.

### Q04. Does the projected uplift improve profit or lifetime value?

**Spoken response:** It improves modelled revenue under stated assumptions; profit and LTV are not established. I would ask Finance for incremental service costs, collection failures, contribution margins and acquisition costs, then examine retention by cohort. A member lost through price response may have future value beyond the assessment window.

**Technical follow-up:** A contribution model should distinguish incremental costs from allocated fixed costs. LTV needs a supported survival profile and future contribution, rather than simply dividing ARPMM by one observed monthly churn rate.

**Evidence:** [analysis/scenario_report.md](../analysis/scenario_report.md).

**Limit:** The project does not estimate contribution profit, causal lifetime retention or a completed customer LTV.

### Q05. What does the break-even retention ratio tell you?

**Spoken response:** For a uniformly affected subscription group, old price divided by new price identifies the retained volume needed to preserve subscription revenue. It is a teaching example, not an allowable estate loss. The full model includes unchanged tiers, notice, protected prices, new recruitment, recurring exits and downgrades.

**Technical follow-up:** Explain why the scenario stress test multiplies behavioural responses jointly and searches for revenue crossings, instead of applying a single whole-base elasticity. No crossing means unavailable, not guaranteed safety.

**Evidence:** [analysis/business_brief.md](../analysis/business_brief.md).

**Limit:** The simple ratio excludes timing, member mix, ancillary income, costs and future behavioural persistence.

## Data and billing integrity

### Q06. How did you make the synthetic dataset commercially useful?

**Spoken response:** The design starts with business rules and linked monthly populations, rather than independent random columns. Acquisitions, exits, transfers, billing states and revenue reconcile. Seasonality, market conditions and promotional protection create mixed responses. I would disclose the generator assumptions and explain that reproducibility and internal consistency do not make synthetic relationships real.

**Technical follow-up:** Trace a gym-month from the membership ledger to monthly performance and the baseline. Identify the declared keys, separate random streams and the difference between generated behavioural parameters and later observed-response estimation.

**Evidence:** [analysis/dataset_design.md](../analysis/dataset_design.md).

**Limit:** Synthetic data demonstrates a workflow, not the actual economics or behaviour of a named operator.

### Q07. How do opening, average and closing membership differ?

**Spoken response:** Opening members are the population at risk at the start of a month; closing members follow recruitment and exits. Average members approximate revenue exposure. Stocks must not be summed and called unique customers. Across a period, rates use summed exposure, while membership growth compares the appropriate opening and closing boundaries.

**Technical follow-up:** Show the integer historical bridge, including same-month exits. Query 01 also uses LAG to test continuity between months. Forecast membership is fractional expected population; historical membership remains integer.

**Evidence:** [sql/queries/01_membership_bridge.sql](../sql/queries/01_membership_bridge.sql).

**Limit:** Exact joining and cancellation dates would improve the average-member billing approximation.

### Q08. Why separate cancellations from tier migration?

**Spoken response:** An incumbent Standard member moving to Off-Peak remains a member but usually pays less. Counting that transfer as cancellation would overstate lost membership and conceal mix effects. The ledger tracks original cohort identity through current-tier changes, so cohort retention follows the person while revenue follows the current paid rate.

**Technical follow-up:** Define incumbent opening exposure, exclude joining-month transfers from incumbent downgrades, and reconcile transfers out of Standard with transfers into Off-Peak. Apply downgrades only to surviving eligible populations.

**Evidence:** [analysis/response_metric_dictionary.csv](../analysis/response_metric_dictionary.csv).

**Limit:** The model does not identify every real upgrade, substitution or cross-site cannibalisation pathway.

### Q09. How do notice, legacy prices and promotions affect the result?

**Spoken response:** New Standard joiners see the increment immediately, while eligible incumbents receive the same cash increment after notice or protection expiry. A discounted member is not automatically moved to headline price. Historical obligations carry forward, and an applied increment remains a persistent status rather than a monthly addition.

**Technical follow-up:** Trace a protected legacy bucket across notice, expiry and billing. New joiners already paying the changed headline must not receive the same event again. Check consumer paid rates before converting revenue to net VAT.

**Evidence:** [analysis/phase6_methodology.md](../analysis/phase6_methodology.md).

**Limit:** The one-month notice policy and protection handling are fictional operating assumptions, not legal or contractual advice.

### Q10. How do you treat missing denominators and immature cohorts?

**Spoken response:** Unavailable observations remain blank; they are not zero performance. Conversion needs qualified prospects and churn needs opening exposure. Retention milestones are unavailable until their monthly horizon is observed, and incomplete cohort revenue remains unavailable. A valid zero numerator with positive exposure produces a valid zero rate.

**Technical follow-up:** Explain SQL NULLIF and the difference between one-, three- and six-month retention approximations versus revenue windows including the joining month. Demonstrate a zero-prospect fixture and a cohort that is too young.

**Evidence:** [sql/queries/10_cohort_censoring.sql](../sql/queries/10_cohort_censoring.sql).

**Limit:** Monthly milestones are not exact-day retention, and incomplete tenure does not reveal ultimate lifetime value.

## Headroom and competitors

### Q11. Why did you choose the headroom variables and weights?

**Spoken response:** They combine relative value, retention, recruitment, demand pressure and income into a transparent prioritisation aid. Competitor gap receives the largest weight, with churn next. The weights are commercial judgement, so the project exposes alternatives and threshold sensitivity instead of presenting the score as calibrated willingness to pay.

**Technical follow-up:** Explain percentile ranks, average ranks for ties, reversed churn, capped utilisation and unchanged weights when inputs are unavailable. Rankings use unrounded scores with gym ID to break ties.

**Evidence:** [analysis/headroom_config.json](../analysis/headroom_config.json).

**Limit:** Weights and score bands are policy choices; historical elasticity is deliberately excluded from the score.

### Q12. Why not raise every gym priced below competitors?

**Spoken response:** A competitor gap suggests relative-value opportunity, but it cannot tell us how many prospective or incumbent members will respond. Caution flags, downside member loss, revenue uncertainty and sensitivity gates can override that opportunity. Competitor positioning therefore supports an investigation rather than proving an increase is economically acceptable.

**Technical follow-up:** Compare plausibility with qualification. A post-increase non-negative gap is only one requirement; revenue, downside, uncertainty, sensitivity and prior repricing also matter.

**Evidence:** [analysis/recommendation_methodology.md](../analysis/recommendation_methodology.md).

**Limit:** The competitor benchmark relies on synthetic comparability; amenities, contracts and access conditions could differ in reality.

### Q13. How did you compare competitor prices fairly?

**Spoken response:** The main comparison uses December recurring Standard-equivalent consumer prices under the documented comparability assumption. Joining fees and introductory discounts stay separate. Fictional national-equivalent fields are proxies, not observations of named operators. I would verify real access terms, location, facilities and effective price before using this operationally.

**Technical follow-up:** Query 08 shows recurring price, fees and active introductory promotions separately. Explain why a cheap first month is not the recurring competitor rate and why a snapshot should not replace historical records.

**Evidence:** [sql/queries/08_december_competitors.sql](../sql/queries/08_december_competitors.sql).

**Limit:** The analysis does not establish real-world comparability, actual competitor prices or likely competitor reactions.

### Q14. Why does utilisation provide both opportunity and caution?

**Spoken response:** Strong demand may support value, but peak pressure can damage member experience and retention. The score uses average monthly peak utilisation with a cap, while capacity caution remains separate. Average occupancy and peak congestion answer different questions; a busy peak is not evidence of spare capacity or a free revenue gain.

**Technical follow-up:** Describe attendance, visit duration, calendar opening minutes and concurrent capacity. Explain why capping score input cannot remove a peak-capacity flag or the need to investigate service quality.

**Evidence:** [analysis/headroom_report.md](../analysis/headroom_report.md).

**Limit:** The capacity proxy and visit-duration assumptions are synthetic; real queueing and equipment availability need direct measurement.

### Q15. How stable are the headroom rankings?

**Spoken response:** The project keeps the original ranks and reports movements under alternative weights, recent trading and value-only competitors. A band change or a substantial movement is a sensitivity flag, not a reason to quietly replace the original rank. High-scoring sites can still belong to the investigation segment when caution takes precedence.

**Technical follow-up:** Explain score band separately from commercial segment, and why the ranking is estate-relative. A changed estate or threshold may alter a percentile without changing the underlying site economics.

**Evidence:** [analysis/headroom_report.md](../analysis/headroom_report.md).

**Limit:** Ranking instability exposes judgement sensitivity; it is not a statistical estimate of pricing tolerance.

## Historical response and causality

### Q16. How was acquisition elasticity estimated?

**Spoken response:** The primary historical analysis compares before/after Standard joins for treatment and control within each randomised pair using log changes. It averages pairs equally, then divides the controlled log response by the mean log price dose. This is a local recruitment response around the observed increase, not a cancellation rule for all existing members.

**Technical follow-up:** Write the pair log-ratio contrast and the elasticity denominator. Qualified prospects are all-tier, so Standard conversion is unavailable. Explain fixed pre-acquisition weights as a sensitivity, not post-treatment weighting.

**Evidence:** [analysis/phase5_methodology.md](../analysis/phase5_methodology.md).

**Limit:** The estimate does not establish a complete demand curve or a reliable elasticity for each gym.

### Q17. Why trust the pilot more than the targeted increases?

**Spoken response:** Assignment within matched pilot pairs reduces commercial selection bias and keeps every assigned pair in the primary estimate. Targeted increases were selected commercially; pre-event matching can improve comparability but cannot eliminate unobserved selection. I keep the two evidence families separate rather than pooling them into a stronger-looking causal result.

**Technical follow-up:** Explain how targeted same-region controls use only pre-event features, and how matching distance and control availability are disclosed. Randomisation still needs balance, pre-trend and contamination checks.

**Evidence:** [analysis/response_report.md](../analysis/response_report.md).

**Limit:** Randomisation does not ensure perfect realised balance or automatically transport the selected pilot sample to the estate.

### Q18. How did you quantify uncertainty?

**Spoken response:** Whole-pair bootstrap resampling keeps each pair and its linked outcomes together. Exact within-pair assignment flips test the primary behavioural responses. Intervals describe uncertainty in this sample; significance is not a rollout rule. Regional and small subgroup intervals remain unavailable when there are too few complete pairs.

**Technical follow-up:** Explain why resampling gym-months independently would create pseudo-replication. Distinguish a percentile interval from an exact randomisation p-value, and equal pair weights from exposure-weighted rate calculations.

**Evidence:** [analysis/response_config.json](../analysis/response_config.json).

**Limit:** A small number of pairs and a selected market sample limit interval reliability and transportability.

### Q19. What threatens the historical causal interpretation?

**Spoken response:** The pilot has pre-trend imbalance and contemporaneous marketing, competitor cuts and promotions. Randomised assignment is useful evidence, but raw arm totals are not a controlled effect and a placebo difference must be discussed. Positive pre-period gaps across all pairs restrict the supported market population.

**Technical follow-up:** Use matching-window balance, the primary baseline and the pre-intervention placebo. Explain that the competitor-entry exclusion changes nothing here because no primary pair has a post-window entry; it is not a decisive robustness result.

**Evidence:** [analysis/response_report.md](../analysis/response_report.md).

**Limit:** The analysis cannot remove every concurrent shock or prove effects outside the observed positive-gap population.

### Q20. Why not estimate local effects from the headroom segments?

**Spoken response:** The segments use post-intervention behaviour, so grouping causal estimates by them risks conditioning on outcomes of treatment. The exploratory groups instead use pre-period relative value and competition. Sparse regional samples remain descriptive. I would seek a prospectively stratified, adequately sized test before claiming distinct regional responses.

**Technical follow-up:** Explain why a high headroom score is neither a causal treatment effect nor an independent price-sensitivity measurement. Identify what pre-treatment segmentation and replication would support a future subgroup question.

**Evidence:** [analysis/response_report.md](../analysis/response_report.md).

**Limit:** There is no supported non-positive-gap subgroup effect and no precise regional elasticity in this project.

## Scenarios and uncertainty

### Q21. What defines the no-increase counterfactual?

**Spoken response:** All options start from the same December ledger populations. Site Q4 levels are anchored using observed regional seasonal indices, and historical billing obligations continue. Marketing, fees, promotional calendars and main ancillary revenue remain common across price options. This prevents the increase scenario from receiving a more favourable trading baseline.

**Technical follow-up:** Explain exposure-weighted regional seasonal rates, fallback recording, tier recruitment probabilities and why all-tier conversion is calculated from resulting joins. No-increase results must be identical across cases.

**Evidence:** [analysis/phase6_methodology.md](../analysis/phase6_methodology.md).

**Limit:** The counterfactual is conditional on continued trading assumptions; competitor prices are frozen rather than forecast.

### Q22. How is acquisition response different from incumbent response?

**Spoken response:** Standard recruitment uses the elasticity-based multiplicative response to headline price dose. Incumbent churn and downgrades are separate rate increments applied to continuing eligible Standard members, with notice and billing timing. Future joiners receive baseline retention in the main model because their incremental retention response was not identified.

**Technical follow-up:** Explain calibration of timing factors to historical incumbent exposures, persistent response, survival caps and protected billing. Explain the additional future-joiner response and Off-Peak diversion as labelled sensitivities.

**Evidence:** [analysis/scenario_config.json](../analysis/scenario_config.json).

**Limit:** Persistent response, future-joiner retention and diversion assumptions remain uncertain; site-level latent generation parameters are not used.

### Q23. How were Base, Downside and Upside selected?

**Spoken response:** Base uses primary estimates. Downside and Upside use complete joint parameter vectors selected near estate incremental-revenue percentiles for the +£2 option. The same vector applies to every gym and option. They are coherent estate cases, not individual worst and best outcomes for each site.

**Technical follow-up:** Explain joint pair draws retaining acquisition, churn, downgrade and price-dose relationships. Distinguish percentile-selected cases from each metric's saved conditional interval and explain extrapolation to different increments.

**Evidence:** [analysis/phase6_methodology.md](../analysis/phase6_methodology.md).

**Limit:** Case ordering for an estate outcome need not make every site or every behavioural metric equally adverse.

### Q24. Why can we not sum site uncertainty endpoints?

**Spoken response:** The sites share the same behavioural evidence, so their model uncertainty is correlated. Portfolio outcomes are aggregated within each common draw, then percentiles are calculated. Summing lower and upper endpoints loses that dependence. Arbitrary region or multi-gym selections therefore show points but suppress unsupported saved ranges.

**Technical follow-up:** Explain individual-site and complete-estate scenario scope, complete named-policy portfolio scope and the difference between a selected-gym point sum and a statistically supported selection interval.

**Evidence:** [powerbi/SETUP.md](../powerbi/SETUP.md).

**Limit:** These are conditional parameter ranges, excluding future shocks and transport uncertainty; positive draw fractions are not rollout probabilities.

### Q25. What happens if competitors cut prices or retention worsens later?

**Spoken response:** I would refresh relative-value evidence and investigate service and trading conditions before using the old conditional recommendation. A price cut changes the frozen counterfactual assumptions; delayed churn changes the response path. I would run a documented new sensitivity or prospective test rather than verbally invent an updated uplift from the existing model.

**Technical follow-up:** Discuss early and sustained historical windows, downside cases, non-zero sensitivities and the six-month primary/twelve-month follow-up. Specify which new data would justify rerunning assumptions and which saved evidence would become stale.

**Evidence:** [analysis/scenario_report.md](../analysis/scenario_report.md).

**Limit:** The current ranges do not include future competitor reactions or arbitrary trading shocks.

## Recommendations and experiment governance

### Q26. How were site actions assigned?

**Spoken response:** Baseline caution or missing evidence takes investigation precedence. Plausible increases need positive Base revenue and sufficient post-increase competitor gap. Qualification adds Downside revenue, member protection, a positive conditional lower bound and positive non-zero sensitivity outcomes. Repeat repricing requires testing; otherwise the best qualifying option is selected, with smaller increments winning exact ties.

**Technical follow-up:** Explain HOLD versus TEST FIRST, show a failed gate and separate the scenario member-loss policy from experimental guardrails. The larger analytical option remains outside the action vocabulary.

**Evidence:** [analysis/recommendation_config.json](../analysis/recommendation_config.json).

**Limit:** Qualification gates are management assumptions, not empirically proven member tolerances or approval to implement prices.

### Q27. Why is Portsmouth a conditional raise but an experiment reserve?

**Spoken response:** Commercial qualification and experimental matchability are different questions. Portsmouth qualifies for a conditional raise but lacks a partner in its strict region/prior-repricing stratum. It remains a reserve instead of weakening matching or admitting flagged gyms to increase sample size. The pilot tests comparable sites, not every commercially interesting site.

**Technical follow-up:** Compare Portsmouth with Hull and Reading in the saved examples. Explain why the planned experiment tests the smaller increment, even when another site has a provisional larger test amount.

**Evidence:** [data/experiment_design.csv](../data/experiment_design.csv).

**Limit:** Strict matching reduces sample size and power; reserve status does not overturn the saved recommendation.

### Q28. Why is positive six-month revenue insufficient for rollout?

**Spoken response:** The primary revenue interval includes no gain and the exact one-sided test does not meet the stated criterion. Several harm upper bounds also exceed their tolerances. The saved decision is therefore EXTEND TEST. At twelve months, the incumbent-churn lower bound exceeds its tolerance, giving STOP despite an inconclusive revenue interval.

**Technical follow-up:** Apply the ordered decisions: unavailable evidence, confirmed no gain/harm, unresolved service or point harm, qualifying rollout, then remaining inconclusive evidence. Early reviews cannot authorise rollout.

**Evidence:** [analysis/experiment_report.md](../analysis/experiment_report.md).

**Limit:** These results are simulated; they illustrate governance and cannot independently validate the scenario model.

### Q29. What do the power analysis and small sample imply?

**Spoken response:** Only the five first-repricing pairs form the primary population. The exact test has coarse attainable p-values, and planning power is based on a historical noise proxy rather than the realised test result. The design may remain inconclusive for modest effects. Repeat and regional results cannot support precise intervals with such sparse replication.

**Technical follow-up:** Explain one-sided versus two-sided testing, the full assignment enumeration and the minimum attainable p-value. Larger-sample approximations need additional eligible sites; they do not create those sites or constitute observed power.

**Evidence:** [data/experiment_power.csv](../data/experiment_power.csv).

**Limit:** Historical noise and small-sample bootstrap behaviour may differ from a real future experiment.

### Q30. Why can an A/A null simulation produce MODIFY?

**Spoken response:** The known no-increase paths are identical in the A/A validation, confirming zero simulated policy intervention. The treatment/control estimator still compares different sites using baseline extrapolation and trading noise. Its harm point estimates can trigger a management review. MODIFY is therefore a workflow signal, not evidence that unchanged prices caused harm.

**Technical follow-up:** Distinguish historical parameter uncertainty, simulated trading variation and experimental sampling uncertainty. Explain why using the known simulated counterfactual in the estimator would artificially improve inference and invalidate the exercise.

**Evidence:** [analysis/experiment_report.md](../analysis/experiment_report.md).

**Limit:** An A/A path verifies aspects of the pipeline; one noisy realisation does not establish calibration or a real pricing effect.

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
