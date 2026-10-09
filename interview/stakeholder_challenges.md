# Fifteen stakeholder challenges

Answer the objection directly, make the material concession, then specify evidence that could change the decision. The personal-contribution challenge requires your own truthful details.

## Pricing Manager

### C01. Why should I trust one shared elasticity across very different gyms?

**Defence:** It is a shared local historical estimate, deliberately preferable to noisy invented site elasticities. I show differences through site prices, billing states and baseline trading, with explicit transport warnings. I would use it to frame a test, not to claim that every site has the same causal response.

**Concession:** The pilot does not identify repeat-repricing tolerance or responses in non-positive-gap markets.

**Evidence needed:** Prospective replication across value positions and sufficient pre-specified strata; contemporary recruitment and incumbent exposure data.

**Source:** [analysis/response_report.md](../analysis/response_report.md).

### C02. Why not take the larger analytical increase if it models more revenue?

**Defence:** It is outside the agreed action vocabulary and has additional tier-parity and extrapolation limitations. A larger conditional model gain does not establish acceptable member loss or customer value. I would retain it as an analytical comparison and test the supported policy before proposing a broader increase.

**Concession:** The current model does not identify upgrade reactions when Standard reaches the unchanged Plus price.

**Evidence needed:** A distinct treatment design, value research, tier-migration data and financial/member protection evidence for that dose.

**Source:** [analysis/scenario_report.md](../analysis/scenario_report.md).

### C03. Why would you recommend an increase after a simulated STOP?

**Defence:** Phase 7 is a conditional screening result; Phase 8 demonstrates how future evidence could block implementation. Its STOP cannot rewrite earlier observations or establish a real effect, but the workflow shows why conditions matter. I would not treat the saved raise labels as approval or ignore the churn signal.

**Concession:** The persistent-response assumptions deserve scrutiny, and synthetic scenarios cannot resolve the real trade-off.

**Evidence needed:** A real prospective test, sustained incumbent cohorts, intervention compliance and contribution review before wider implementation.

**Source:** [analysis/experiment_report.md](../analysis/experiment_report.md).

## CFO

### C04. Is this additional revenue actually profit?

**Defence:** No. The model estimates net revenue, not contribution or profit. Lost members may save some variable cost but also reduce future contribution. Additional service, collection and implementation costs may absorb the uplift. I would partner with Finance before calling this a financially attractive rollout.

**Concession:** The current evidence cannot quantify contribution or a defensible LTV effect.

**Evidence needed:** Incremental cost drivers, collection/bad-debt rates, acquisition cost, retention contribution and implementation costs.

**Source:** [analysis/scenario_report.md](../analysis/scenario_report.md).

### C05. Can you guarantee the lower uncertainty bound?

**Defence:** No. It is a conditional parameter percentile under the shared historical evidence and model assumptions. It excludes future trading shocks and transport uncertainty. The portfolio range preserves correlated draws, but it is neither a guarantee nor a comprehensive forecast interval.

**Concession:** Real competition, macro conditions, execution and behaviour may lie outside the modelled distribution.

**Evidence needed:** Trading stress assumptions, real pilot replication, implementation monitoring and an explicit contribution downside assessment.

**Source:** [analysis/recommendation_report.md](../analysis/recommendation_report.md).

### C06. Why are potential test gains excluded from the portfolio?

**Defence:** Those sites lack sufficient qualification or repeat-repricing evidence for a conditional RAISE action. Including provisional gains would inflate the selected commercial portfolio with an unaccepted policy. Their test opportunities remain separately visible, while every non-raise site uses the no-increase path.

**Concession:** This is a conservative policy boundary, not proof that testing those sites would produce no gain.

**Evidence needed:** Completed qualification evidence, controlled repeat-pricing results and any authorised policy revision evaluated transparently.

**Source:** [sql/queries/14_conditional_portfolios.sql](../sql/queries/14_conditional_portfolios.sql).

## Marketing Director

### C07. You are raising prices despite weaker recruitment. How is that sustainable?

**Defence:** The trade-off must be explicit. Acquisition can fall while revenue rises, but future member value and brand perception may make that unattractive. The project shows acquisition separately and gates decisions on downside, sensitivities and controlled testing. I would seek customer-value evidence rather than optimise one revenue line.

**Concession:** The financial model does not fully quantify brand, referral or long-run demand consequences.

**Evidence needed:** Qualified-prospect funnel, acquisition cost, cancellation reasons, satisfaction, referral behaviour and future contribution by cohort.

**Source:** [analysis/recommendation_report.md](../analysis/recommendation_report.md).

### C08. Can a promotion solve the acquisition loss?

**Defence:** It might improve recruitment but can reduce realised yield or leak value to customers who would have joined anyway. The main scenarios hold promotional policy common so it cannot manufacture a pricing gain. A changed promotion is a separate policy that needs its own measured economics.

**Concession:** The descriptive promotion comparison is not a causal estimate of incremental promotion effectiveness.

**Evidence needed:** Offer exposure, redemption, protection expiry, conversion, contribution and a controlled offer comparison.

**Source:** [sql/queries/09_promotion_context.sql](../sql/queries/09_promotion_context.sql).

### C09. What would you do if a competitor responds immediately?

**Defence:** The frozen-price scenario would lose relevance. I would monitor comparable recurring prices and offers, refresh relative value, and distinguish the market change from the price intervention. The test protocol should retain context rather than exclude inconvenient observations after seeing outcomes.

**Concession:** The current forecast does not estimate strategic competitor response or a new elasticity under that response.

**Evidence needed:** Dated competitor events, offer terms, site funnel changes and prospective sensitivity or protocol updates.

**Source:** [analysis/experiment_protocol.md](../analysis/experiment_protocol.md).

## Operations Director

### C10. Your busiest gyms have headroom. Why not raise there first?

**Defence:** Busy peaks can indicate demand or service pressure. Capacity caution takes precedence over headroom, so a high score cannot clear an operational problem. I would investigate equipment availability, queues and member satisfaction before making a pricing argument from utilisation.

**Concession:** Concurrent capacity is a synthetic proxy and cannot measure the full quality of a real visit.

**Evidence needed:** Hourly attendance, equipment occupancy, queues, staffing, service complaints and satisfaction by visit time.

**Source:** [analysis/headroom_report.md](../analysis/headroom_report.md).

### C11. How do we protect discounted members and avoid billing mistakes?

**Defence:** Preserve billed-rate differences, honour active promotion terms, apply the cash increment once and delay protected incumbents until expiry. Keep cohorts and historical obligations intact. Operational eligibility and member communication should be audited independently of the financial calculation.

**Concession:** The project is an aggregate billing simulation, not a production billing implementation or contractual review.

**Evidence needed:** Real contracts, billing-system eligibility rules, communication records, exceptions and reconciliation of first changed bills.

**Source:** [analysis/phase6_methodology.md](../analysis/phase6_methodology.md).

### C12. What if complaints rise but revenue still improves?

**Defence:** A service trigger can require investigation or modification even with positive revenue. Complaints are an experience signal, not automatic causal proof of pricing damage. I would inspect timing, reasons and operational events alongside churn, then follow the pre-specified decision order.

**Concession:** The scenario complaints projection is weakly supported; it must not be treated as a validated rollout threshold.

**Evidence needed:** Complaint categories, exposure, contact timing, service incidents and a resolved management review.

**Source:** [analysis/experiment_config.json](../analysis/experiment_config.json).

## Sceptical interviewer

### C13. Your pilot only lasted eight weeks. Is that enough?

**Defence:** That premise does not match the project. The historical primary comparison has balanced six-month pre/post windows, with early and sustained robustness checks. The designed experiment also has a six-month primary assessment and twelve-month follow-up; its early reviews are safety checks and cannot authorise rollout.

**Concession:** Even the longer windows do not establish complete lifetime response or eliminate small-sample uncertainty.

**Evidence needed:** Check the recorded window boundaries, follow sustained cohorts and replicate prospectively rather than rely on a mistaken short-window description.

**Source:** [analysis/phase5_methodology.md](../analysis/phase5_methodology.md).

### C14. Is synthetic data just confirming assumptions you invented?

**Defence:** Synthetic evidence cannot independently validate real pricing economics. Its value here is showing an internally reconciled decision workflow and exposing adverse outcomes. Generation assumptions remain separate from analyst-facing estimates, and I retain mixed evidence, sensitivity and limitations instead of manufacturing a success story.

**Concession:** A historical synthetic pilot still ultimately originates in a designed world, so its results are portfolio demonstrations.

**Evidence needed:** Real observed prices, billing and cohort histories, randomised or credible comparative evidence and Finance/customer validation.

**Source:** [analysis/dataset_design.md](../analysis/dataset_design.md).

### C15. What did you personally do, and what was AI-assisted?

**Defence:** I would describe my actual contribution, the assistance used, the decisions I understood and the checks I personally inspected. The repository proves artifact results, not my personal authorship of every line. I would demonstrate a calculation I can explain and clearly identify anything I still need to learn.

**Concession:** This answer must be personalised truthfully; it is not evidence that you performed an unrecorded manual check.

**Evidence needed:** Your own work notes, a calculation you can reproduce, actual decisions or revisions, and an honest explanation of tooling assistance.

**Source:** [interview/rehearsal.md](../interview/rehearsal.md).

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
