# Phase 6 completion validation

Status: Complete. The reconciled scenario model is ready for Phase 7; no pricing actions have been assigned.

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.

## Data and model

- 80 gyms, twelve consecutive 2026 months, four price options and three joint cases.
- Delivered interfaces contain 11,520 monthly records, 960 gym records, 12 estate records and 2,268 sensitivity records, with unique declared keys.
- All 1,500 Python checks passed, including member bridges, tier transfers, billing eligibility, revenue reconciliation, reporting boundaries and behavioural edge cases. Reconciliations use unrounded calculations and the documented £0.01 revenue tolerance.
- All four scenario CSVs reproduce byte for byte. The 10,000 whole-pair draws use seed 20261006 and shared parameter vectors across gyms and price options.
- Source, generation configuration, baseline, headroom and historical-response hashes remain unchanged.

## Saved workbook

- 25 populated sheets; all 21 earlier sheets and native features are preserved. Only authorised progress text is updated on the two existing guidance sheets.
- Actual saved formulas were recalculated with the bundled Artifact Tool in bounded blocks. 672,748 formula caches are present; the formula-error scan found no errors.
- Independent comparison checked 286,240 cells against Python/CSV outputs. The largest difference was £0.0000049943, below the £0.01 tolerance. Saved summary parity differed by at most £0.0000000448.
- The refresh script completed all twelve price/case combinations through the same calculation build and restored the selected Base/+£2 case. Captured comparisons are current.
- Input tests verified valid zero overrides, price and case changes, missing selected inputs, stale-state detection, restoration of freshness and immediate suppression of evidence-derived ranges under manual overrides.
- All four new sheets, affected guidance and charts received visual review. All internal relationships resolve, table names are unique and four new native charts are retained.

Detailed machine-readable evidence is in `scenario_workbook_verification.json`; model checks are in `scenario_validation.md`. Recalculation used Artifact Tool; native Microsoft Excel was not automated.

## Interpretation limits

Revenue gains are not profit gains. Expected membership stocks are not unique customer counts. Monthly exposure-weighted churn is not annual retention. December revenue multiplied by twelve is a seasonal exit run-rate, not a forecast.

Intervals describe conditional pilot-parameter uncertainty, excluding future trading shocks and transport uncertainty. Historic policy effects do not establish estate-wide pricing tolerance. The commercial report documents adverse first-month revenue, member losses, evidence coverage and remaining simplifications.
