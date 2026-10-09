# Phase 4 methodology and reproducibility

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

## Purpose and evidence boundary

Assess site-level Standard pricing headroom using observed synthetic commercial performance. The analyst learns where relative value, acquisition, retention and demand support further investigation, and where caution or specification dependence weakens that evidence. Management can prioritize Phase 5 historical-response work. No elasticity, cash increase, revenue uplift or rollout decision is inferred in this phase.

The reporting base is January–December 2025 compared with the matching 2024 period. Current competition is December 2025. Recent-trading sensitivity uses October–December in both years. Static local characteristics come from Gym Master. Existing baseline flags are retained without penalizing the score. Historical events and randomised pilot assignments are descriptive context, not evidence that a gym tolerated repricing.

## Interfaces and formulas

`gym_headroom.csv` has one row per gym, keyed by `gym_id`. `headroom_sensitivity.csv` has one row per gym and specification, keyed by `gym_id, variant`. There are 80 and 480 rows respectively. Stable gym IDs link to Gym Master and Baseline; all fields are documented in `headroom_metric_dictionary.csv`. Baseline context fields retain the definitions in `baseline_metric_dictionary.csv`, including opening-base churn, exposure-weighted conversion denominators, average tier mix and monthly complaint exposure.

For each indicator, component = 100 × (average ascending rank − 1)/(number of nonmissing observations − 1). Equal values share average ranks. Churn is reversed by subtracting from 100. Peak occupancy is capped at 1 before ranking. Constant and singleton numeric populations receive 50. Missing observations remain blank. The total is the sum of component × variant weight, and is unavailable if a positive-weight input is missing. A missing zero-weight income input does not block the income-exclusion variant. There is no renormalization. Weights must be nonnegative and sum to one.

Ranking sorts unrounded total scores descending, then gym IDs ascending. A comparison tolerance of 1e-10 in the indicator's units or score points handles binary floating-point noise in mathematically tied calculations consistently across Python and Excel. Inputs, contributions and total scores are not financially rounded. Rank-permutation tests confirm that these tolerance comparisons produce unique ranks across all six observed specifications. High starts at 65; Medium starts at 40. Bands represent relative opportunity evidence, not member tolerance or probabilities. The four segment rules apply in the agreed order. Any baseline caution flag gives Investigation priority even when the score is high or unavailable. Otherwise unavailable scores or competitor gaps give Unavailable. Flags are annual baseline flags in every specification; the Q4 sensitivity does not redefine them.

Competitor gap = arithmetic mean of active advertised recurring competitor prices − contemporaneous Northstar Standard headline price. All amounts include VAT. Joining fees and first-month discounts are displayed separately and are not deducted from recurring prices. The base preserves the source's assumed comparability across all three fictional archetypes. Value-only sensitivity excludes National full-service competitors. Quality, distance and service differences are not converted into unsupported price adjustments.

The Q4 benchmark averages three separate monthly gaps, giving each month equal weight. Its membership inputs use the baseline's Q4 exposure-weighted churn and conversion, matching-quarter acquisition growth and average monthly peak utilisation. Income stays fixed. No generator behavioural parameters enter the analysis.

Sensitivity uses the six configured specifications without a Cartesian expansion. Rank movement = variant rank − base rank; positive means a lower position. A site is sensitive if any alternative changes its band or shifts rank by at least ten places. The threshold test holds scores fixed and shifts both base band cutoffs down five points and up five points. These diagnostics are specification checks, not confidence intervals.

## Workbook flow and preservation

Headroom Score owns source links, components, contributions, rankings, segments, explanations and all six sensitivity calculations. The monthly Q4 competitor build occupies rows 610–849. Headroom Summary contains editable weights, thresholds, linked summaries, dynamically ranked leading sites, native charts and live chart schedules. Its two reconciliation cells are terminal checks and do not feed business outputs.

The two sheets are authored with the bundled Artifact Tool. Supporting source copies exist only in the ignored authoring package. Standard-library OOXML packaging appends the two new sheets to a fresh Phase 4 recovery copy of the current 16-sheet workbook, remapping styles, table IDs and relationship targets. Existing sheet and feature parts remain byte-identical except the four explicitly updated progress cells in Dataset Overview and README. Full-workbook import and recalculation verify the assembled workbook without attempting a full-workbook export. Verified formula caches are transferred into the saved package.

The Excel workbook uses ordinary scalar formulas, COUNTIFS-based average ranks and exact gym-ID tie resolution. Weight changes update outputs; invalid totals make scores unavailable. Source observations and the Python delivery remain the reproducible default case. After exploratory workbook edits, restore the delivered controls before comparing against CSVs.

## Reproduction

Run `analysis/headroom_analysis.py` with the bundled Python runtime. Fixed source files and `analysis/headroom_config.json` reproduce both CSVs byte for byte. The script creates the report, dictionary, validation evidence, charts and ignored workbook payload. It records SHA-256 hashes of all pre-existing data CSVs and the generation configuration and checks them again after calculation.

For workbook reproduction, run `analysis/build_headroom_workbook.mjs` with the bundled Node runtime and a 16 GB heap; then `analysis/append_headroom_sheets.py`. Run the builder with `--verify-final`, the packaging script with `--update-caches`, and finally `analysis/verify_headroom_workbook.py`. The packaging script deliberately starts from its own ignored pre-Phase-4 recovery copy on reruns, retaining completed Phase 3 work. Close the delivered workbook in Excel before replacing it; a file lock must not be bypassed by terminating the user's application.

## Verification limits

Python boundary checks, independent saved-file comparisons, Artifact Tool recalculation, temporary input-change tests, formula-error scanning, package relationship validation and visual review establish the delivered analysis. Native desktop Excel recalculation is not automated. Uniform score weights and archetype comparability remain explicit business assumptions. Source attendance, demographics and competitor observations are synthetic proxies. Monthly retention is not annual retention; member stocks and member-months are not unique customers.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
