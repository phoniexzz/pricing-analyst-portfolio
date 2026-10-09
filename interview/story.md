# Opening pitch and interview story

These scripts describe the documented project. Personalise ownership truthfully before speaking. They are rehearsal aids, not a claim that you independently completed every implementation or validation step. Word counts exclude section headings and this guidance; read-aloud duration remains approximate.

## Opening pitch

<!-- pitch:start -->
My portfolio asks whether a fictional UK gym chain can raise prices without losing enough members to offset the gain. Across eighty gyms, it separates acquisition, incumbent churn and downgrades, then combines historical pilot evidence with conditional scenarios. The selected portfolio models roughly £149,000 additional annual net revenue, with a member cost. A simulated pilot remains inconclusive at six months, showing why testing matters before implementation.
<!-- pitch:end -->

## Two-minute story

### Situation

<!-- story:start -->
I created a synthetic portfolio project for Northstar Fitness, a fictional UK operator with eighty mature gyms. The business question was whether Standard prices could increase without losing enough member volume to offset the additional yield.

### Task

The task was to identify conditional site actions, while protecting acquisition and retention. I treated revenue growth as a commercial trade-off, rather than assuming that a larger competitor price gap justified an increase.

### Analysis

The project first reconciles monthly member movements, tier transfers and net revenue. It compares matching years, builds transparent headroom indicators, and uses a twelve-pair randomised historical pilot to estimate acquisition response separately from incumbent churn and downgrades. A twelve-month scenario model preserves legacy prices, promotional protection and delayed billing. It carries shared parameter uncertainty through to the selected portfolio.

### Recommendation

The saved recommendations contain ten conditional £1 raises, one £2 raise, five TEST FIRST sites, twenty-six holds and thirty-eight investigations. All increases require controlled testing. A seven-pair £1 experiment has five first-repricing pairs as its primary population. Its simulated result is EXTEND TEST at six months and STOP at twelve months, so it does not authorise rollout.

### Impact

The conditional raise-only portfolio models approximately £149,000 additional annual net revenue and about 1,209 fewer December members versus no increase. That is hypothetical revenue, not realised profit. Provisional test gains are excluded, and the uncertainty range excludes future trading shocks and transport risk.

The key lesson was that the highest price isn't necessarily the optimal price. The commercial objective is finding the point where additional yield more than compensates for any member-volume response.
<!-- story:end -->

## Five-minute explanation outline

| Time | Explain | Evidence to point to |
|---|---|---|
| 0:00–0:40 | The commercial question, synthetic context and revenue/member trade-off | Management presentation opening |
| 0:40–1:30 | Baseline growth versus membership; why ARPMM is not headline price | Executive Overview and exact revenue bridge |
| 1:30–2:20 | Separate acquisition and incumbent responses; local causal evidence and limits | Historical response report |
| 2:20–3:15 | Common counterfactual, billing timing and coherent uncertainty | Scenario Comparison and saved portfolio |
| 3:15–4:10 | Ordered gates, site examples and conditional recommendations | Recommendations and Gym Detail |
| 4:10–5:00 | Simulated EXTEND/STOP outcomes, confidence-bound gates and real next steps | Experiment & Monitoring |

This is a spoken explanation outline. The separate [artifact demonstration](demonstration.md) supplies exact navigation and SQL cues. If time is short, explain one trade-off and its limitation rather than listing every tool.

Sources: [baseline](../analysis/baseline_results.json), [saved recommendations](../data/gym_recommendations.csv), [portfolio](../data/recommendation_portfolio.csv), [experiment](../analysis/experiment_report.md). Exact values and rounding are in the [evidence register](evidence_register.json).

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
