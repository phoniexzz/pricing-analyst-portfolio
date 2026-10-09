# Phase 2 — Dataset validation

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

Period: January 2024–December 2025. Seed: 20261004.

## Dataset sizes

| Table | Rows |
| --- | ---: |
| monthly_performance | 1,920 |
| competitor_prices | 7,344 |
| pricing_history | 32 |
| membership_ledger | 93,044 |
| experiment_assignments | 24 |
| market_events | 941 |
| cohorts | 5,760 |
| gym_master | 80 |

Opening estate members: **400,000**. December 2025 closing estate members: **396,311**.
Monthly closing stock ranges from 391,550 to 417,099. These are stocks, not unique people or a sum across months.

## Observed data ranges

| Metric | Minimum | Maximum |
| --- | ---: | ---: |
| standard_price | 19.9900 | 33.9900 |
| churn_rate | 0.0265 | 0.0662 |
| conversion_rate | 0.2065 | 0.4332 |
| utilisation_pct | 0.1263 | 0.3669 |
| peak_utilisation_pct | 0.3647 | 1.0600 |
| realised_ARPMM | 16.6002 | 28.1000 |

Rates and utilisation above are decimal fractions. Prices include VAT; ARPMM is net of VAT. Peak occupancy may exceed the comfortable-capacity proxy.

## Automated checks

- PASS: Two complete generations produce identical CSV SHA-256 hashes
- PASS: 80 unique gyms and 1,920 complete consecutive gym-months
- PASS: Every gym mature at observation start
- PASS: Unique non-null declared primary keys
- PASS: All foreign gym keys exist
- PASS: Exact 400,000 opening members
- PASS: Estate member stock remains within 300,000–500,000
- PASS: Gym member bridges and monthly continuity
- PASS: Ledger bridges and exposures
- PASS: Cancellations eligible and member counts non-negative
- PASS: Every billing bucket carries its own closing membership forward
- PASS: Member movement counts are integers
- PASS: Ledger rolls up to gym member counts
- PASS: Tier member totals and tier subscription revenue reconcile
- PASS: Ledger subscription revenue reconciles
- PASS: Revenue components, VAT and ARPMM reconcile
- PASS: Acquisition, conversion and opening-base churn rates reconcile
- PASS: Attendance utilisation derived from visits and capacity
- PASS: 32 actual price events; no zero changes or repeated site events
- PASS: Headline changes and one-month notice match event history
- PASS: Existing-member repricing eligibility and protected promotions
- PASS: Billed rate applies eligible cash increase exactly once
- PASS: 12 randomised matched treatment/control pairs
- PASS: Historical controls remain unrepriced
- PASS: Cohort acquisitions reconcile and all three origin tiers present
- PASS: Cohort survivors never rise after joining
- PASS: Observed cohort milestones and revenues reconcile; immature outputs blank
- PASS: December master snapshot matches monthly records
- PASS: Competitor entry, prices and promotional events align
- PASS: No analyst-facing assumed elasticity or opportunity rankings
- PASS: Controlled higher-price conversion response
- PASS: Controlled promotion improves conversion
- PASS: Controlled existing-member price response increases churn
- PASS: Lagged churn is distinct from notification response
- PASS: Equivalent relative price rise from competitor cut reduces conversion

Delivered CSVs were reloaded independently. The validator detected these deliberate in-memory defects; files remained unchanged:

- Incorrect gym membership bridge: detected by Gym member bridges and monthly continuity.
- Cancellations larger than eligible pool: detected by Ledger bridges and exposures.
- Incorrect total revenue: detected by Revenue components, VAT and ARPMM reconcile.

## Right-censored cohorts

- customers_remaining_30d: 240 unavailable observations.
- customers_remaining_90d: 720 unavailable observations.
- customers_remaining_180d: 1,440 unavailable observations.
- revenue_6_month: 1,200 unavailable observations.
- revenue_12_month: 2,640 unavailable observations.

## Workbook verification

- Every source cell matches CSV: **2,422,644 cells** across eight source tables and the 170-field dictionary.
- **15,373 formulas** exported with cached results; all reconciliation differences are zero.
- **9 native Excel tables**; source headers and identifying columns are frozen.
- The complete saved workbook was re-imported and recalculated in Artifact Tool. Full-ledger subscription revenue and all 1,920 monthly reconciliation rows passed.
- Input-change checks proved member and revenue formula dependencies update; original source inputs were restored.
- Formula error scan matched zero entries.
- Visual review: completed for all 13 sheets, including final ledger values and tail rows.
- Native Microsoft Excel application behaviour was not automated; this is not a claim of native Excel execution.

All source sheets and ledger blocks were authored with Artifact Tool. Its whole-workbook exporter exceeded JavaScript memory/string limits for the full ledger, so exported blocks were packaged into one native sheet. No records were removed. Typed values, styles, native table range and formula results were verified after assembly.

## Limits

Monthly member exposure and retention ages are approximations. All causal mechanisms are assumed by the generator. Behavioural noise, competitor events and commercial selection complicate later observational estimation. The historical pilot is synthetic and its outcome has not been interpreted. Cohort revenue excludes fees and ancillary income. Contribution profit and completed lifetime value are not available.

Phase 3 baseline analysis has not started.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
