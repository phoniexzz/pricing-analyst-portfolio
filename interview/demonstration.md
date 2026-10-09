# Five saved site examples and artifact demonstration

These are unchanged Phase 7 recommendations and Phase 8 design statuses, not a new ranking. Site financial figures describe the saved **assessment increment**, which can be a provisional TEST FIRST amount. The actual conditional portfolio maps TEST FIRST, HOLD and investigation sites to no increase. Provisional test gains are excluded from that portfolio and are not accepted raises.

## NF049 Hull

**Saved action:** RAISE £2; proposed cash increment £2; provisional test amount £0.

**Rule:** `R7_CONDITIONAL_RAISE`. £2 gives the higher qualifying base revenue; downside member loss 4.72%, post-increase competitor gap £0.69

**Saved assessment Base effect at £2:** £23,791.81 incremental net revenue; -3.62% December member impact versus no increase.

**£1 failed gates:** None. **£2 failed gates:** None.

**Experiment status:** Assigned; assignment Treatment; population First repricing.

**Design reason:** Matched and randomised under the saved protocol.

**Evidence:** [recommendation row](../data/gym_recommendations.csv), [design row](../data/experiment_design.csv), keys `gym_id=NF049`; exact values in [register](evidence_register.json).

## NF023 Portsmouth

**Saved action:** RAISE £1; proposed cash increment £1; provisional test amount £0.

**Rule:** `R7_CONDITIONAL_RAISE`. £1 gives the higher qualifying base revenue; downside member loss 2.86%, post-increase competitor gap £0.57

**Saved assessment Base effect at £1:** £10,335.44 incremental net revenue; -2.19% December member impact versus no increase.

**£1 failed gates:** None. **£2 failed gates:** Post-increase competitor gap; Downside member limit.

**Experiment status:** Reserve; assignment Unavailable / not assigned; population Unavailable / not assigned.

**Design reason:** No same-region and same-repricing-history partner

**Evidence:** [recommendation row](../data/gym_recommendations.csv), [design row](../data/experiment_design.csv), keys `gym_id=NF023`; exact values in [register](evidence_register.json).

**Defence:** Portsmouth is commercially qualified but unmatched within its strict region/prior-repricing stratum. It remains a reserve. Do not relax matching or admit flagged sites to inflate power.

## NF013 Reading

**Saved action:** TEST FIRST; proposed cash increment £0; provisional test amount £2.

**Rule:** `R6_REPEAT_REPRICING`. £2 passes financial gates; repeat repricing requires controlled evidence

**Provisional test Base effect at £2:** £27,654.96 incremental net revenue; -3.54% December member impact versus no increase.

**£1 failed gates:** None. **£2 failed gates:** None.

**Experiment status:** Assigned; assignment Control; population Repeat repricing.

**Design reason:** Matched and randomised under the saved protocol.

**Evidence:** [recommendation row](../data/gym_recommendations.csv), [design row](../data/experiment_design.csv), keys `gym_id=NF013`; exact values in [register](evidence_register.json).

**Defence:** Reading passes financial gates but prior repricing creates an evidence gap. The displayed potential gains are provisional and excluded from the conditional-raise portfolio. Its provisional £2 amount does not change the designed £1 experiment, and repeat-repricing inference remains exploratory.

## NF001 London

**Saved action:** HOLD PRICE; proposed cash increment £0; provisional test amount £0.

**Rule:** `R3_NO_PLAUSIBLE`. Neither £1 nor £2 preserves the required competitor gap with positive base revenue

**Saved assessment Base effect at £0:** £0.00 incremental net revenue; 0.00% December member impact versus no increase.

**£1 failed gates:** Post-increase competitor gap. **£2 failed gates:** Post-increase competitor gap.

**Experiment status:** Excluded; assignment Unavailable / not assigned; population Unavailable / not assigned.

**Design reason:** Phase 7 action is outside pilot eligibility

**Evidence:** [recommendation row](../data/gym_recommendations.csv), [design row](../data/experiment_design.csv), keys `gym_id=NF001`; exact values in [register](evidence_register.json).

## NF002 London

**Saved action:** DEFENSIVE / INVESTIGATE; proposed cash increment £0; provisional test amount £0.

**Rule:** `R1_CAUTION`. Investigate qualified-prospect conversion and relative value; Investigate peak service capacity and member experience

**Saved assessment Base effect at £0:** £0.00 incremental net revenue; 0.00% December member impact versus no increase.

**£1 failed gates:** Post-increase competitor gap. **£2 failed gates:** Post-increase competitor gap.

**Experiment status:** Excluded; assignment Unavailable / not assigned; population Unavailable / not assigned.

**Design reason:** Existing Phase 3 caution requires investigation

**Evidence:** [recommendation row](../data/gym_recommendations.csv), [design row](../data/experiment_design.csv), keys `gym_id=NF002`; exact values in [register](evidence_register.json).

## Five-minute artifact demonstration

Open saved files beforehand. The timing below is a rehearsal budget, not a measured session. If native applications are unavailable, use the existing gallery and presentation PDF; do not claim a live refresh or interaction test.

| Time | Action | Explain / fallback |
|---|---|---|
| 0:00–0:35 | Show the presentation opening and evidence scope. | Fictional operator, modelled revenue/member trade-off, no implemented gain. |
| 0:35–1:15 | Open Executive Overview, full-year 2025. | Matching-year revenue/membership and exact bridge. Avoid a revenue-only narrative. |
| 1:15–2:00 | Show Recommendations, then Gym Detail for a saved example and Back. | Ordered gates, failed £2 gate at Portsmouth, repeat status at Reading. Use saved screenshots if needed. |
| 2:00–2:45 | Show Scenario Inputs/Model and captured comparison. | One authoritative selector affects the active model; saved captures require refresh and show freshness. Do not edit the accepted workbook during rehearsal. |
| 2:45–3:25 | Show Pricing Scenarios saved Base/Downside controls. | Report controls select saved combinations, not new forecasts. Unsupported multi-site ranges remain blank; never sum endpoints. |
| 3:25–4:05 | Show Experiment & Monitoring at Main / six months / First repricing, then twelve months. | EXTEND TEST then STOP; reset restores primary defaults. Repeat-pair intervals remain blank. |
| 4:05–5:00 | Explain SQL 02, 12 and 14 plus the next evidence needed. | Weighted exposure, case separation and RAISE-only mapping. Close on a real test and contribution/service evidence. |

Use [Power BI native gallery](../portfolio/dashboard_gallery.md), [accepted PBIX](../powerbi/gym_pricing_dashboard.pbix), [31-sheet workbook](../excel/gym_pricing_model.xlsx), [management presentation](../presentation/pricing_recommendation.pdf) and [SQL guide](../sql/README.md).

SQL cues: [02 weighted baseline](../sql/queries/02_weighted_baseline.sql); [12 saved Base scenarios](../sql/queries/12_saved_base_scenarios.sql); [14 conditional portfolios](../sql/queries/14_conditional_portfolios.sql). Query 14 maps every TEST FIRST site to no increase and joins saved complete-portfolio ranges, rather than summing site bounds.

Before any genuine workbook input demonstration, use a disposable copy. A stale comparison, missing evidence or manual behavioural override must not be presented as authoritative. Consult the existing refresh runbooks; this interview pack neither executes them nor changes the scenario selector.
This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
