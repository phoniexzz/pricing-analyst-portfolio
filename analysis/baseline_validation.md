# Phase 3 data validation

47 automated data checks passed. Workbook verification is recorded separately in baseline_workbook_verification.json.

- PASS: 80 mature gyms, unique gym-month keys and exact 24-month coverage
- PASS: All source monthly member bridges reconcile exactly
- PASS: Same-month and opening-base cancellations reconcile
- PASS: Attendance utilisation reconstructs source occupancy within rounding tolerance
- PASS: Source visit duration is constant and monthly opening minutes are common across gyms
- PASS: 80 gym, 24 estate-month and 16 region-year derived records with unique keys
- PASS: 2024 site and region totals reconcile: total_revenue
- PASS: 2024 site and region totals reconcile: subscription_revenue
- PASS: 2024 site and region totals reconcile: joining_fee_revenue
- PASS: 2024 site and region totals reconcile: ancillary_revenue
- PASS: 2024 site and region totals reconcile: new_members
- PASS: 2024 site and region totals reconcile: opening_base_cancellations
- PASS: 2024 site and region totals reconcile: same_month_cancellations
- PASS: 2024 site and region totals reconcile: all_cancellations
- PASS: 2024 site and region totals reconcile: qualified_prospects
- PASS: 2024 site and region totals reconcile: member_months
- PASS: 2024 site and region totals reconcile: opening_member_months
- PASS: 2024 site and region totals reconcile: opening_members
- PASS: 2024 site and region totals reconcile: closing_members
- PASS: 2024 revenue components and annual member bridge reconcile
- PASS: 2024 weighted ARPMM and churn independently reconstruct from raw CSV
- PASS: 2025 site and region totals reconcile: total_revenue
- PASS: 2025 site and region totals reconcile: subscription_revenue
- PASS: 2025 site and region totals reconcile: joining_fee_revenue
- PASS: 2025 site and region totals reconcile: ancillary_revenue
- PASS: 2025 site and region totals reconcile: new_members
- PASS: 2025 site and region totals reconcile: opening_base_cancellations
- PASS: 2025 site and region totals reconcile: same_month_cancellations
- PASS: 2025 site and region totals reconcile: all_cancellations
- PASS: 2025 site and region totals reconcile: qualified_prospects
- PASS: 2025 site and region totals reconcile: member_months
- PASS: 2025 site and region totals reconcile: opening_member_months
- PASS: 2025 site and region totals reconcile: opening_members
- PASS: 2025 site and region totals reconcile: closing_members
- PASS: 2025 revenue components and annual member bridge reconcile
- PASS: 2025 weighted ARPMM and churn independently reconstruct from raw CSV
- PASS: Exact annual revenue bridge within GBP 0.01
- PASS: Q4 windows contain exactly October, November and December
- PASS: Percentage-point arithmetic and retention identities
- PASS: Zero and missing denominators are unavailable, positive denominator preserves zero numerator
- PASS: Ranking ties resolve deterministically by gym ID
- PASS: Annual site weighted occupancy matches opening-time-weighted source utilisation
- PASS: Calendar boundaries connect 2024 closing stocks to 2025 opening stocks
- PASS: gym_baseline saved CSV values match calculated outputs
- PASS: estate_monthly_trend saved CSV values match calculated outputs
- PASS: region_year_baseline saved CSV values match calculated outputs
- PASS: All eight source CSVs and generation configuration remain unchanged

Source SHA-256 hashes and configuration hash are stored in baseline_results.json. Re-running the script must reproduce identical derived CSV hashes. Workbook visual review and saved-file checks are required before Phase 3 completion.

## Workbook completion

Phase 3 is complete.

- All **17,792 derived output cells** match the CSVs after full-workbook recalculation and saved-file reload.
- **29,405 new formula cells** retain calculated cached results. Formula error scan matched zero entries.
- The complete assembled workbook was re-imported and recalculated in Artifact Tool. Original ledger and monthly reconciliation checks passed.
- A temporary GBP 120 source-revenue edit propagated to the site annual result; the original input was restored and every derived output rechecked.
- All eight source CSVs and generation configuration hashes are unchanged. Original source worksheet XML, styles, native tables and panes are preserved. Four progress-text cells were updated.
- Four native charts have verified source references and exported colors. All workbook relationship targets exist.
- All three new sheets, two affected guide views, native charts and standalone figures received visual review. Churn/conversion precision and 0.00 reconciliation formatting were corrected and verified.
- All three derived CSVs reproduce byte-for-byte.
- Native Microsoft Excel application execution was not automated. Engine verification used Artifact Tool, with independent saved OOXML checks.

## Remaining simplifications

Monthly midpoint exposure approximates billing. Retention is a monthly opening-base measure, not annual survival or cohort retention. Peak occupancy is an estimate of comfortable-capacity pressure. The revenue bridge is descriptive and includes mix, joining fees and ancillary income. Historical selection, marketing, promotions and competitor events can confound price-response interpretation. December annualisation is seasonal and is not a forecast. No elasticity, headroom scores or pricing actions are estimated in Phase 3.
