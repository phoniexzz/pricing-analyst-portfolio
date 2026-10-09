# Fifteen commercial SQL examples

These queries expose the existing Northstar evidence. They do not rerank gyms, estimate new responses or revise saved recommendations. Use Python 3.11+; SQLite is included in the standard library.

```powershell
python sql/run_queries.py
python -m pip install -r analysis/requirements.txt
python sql/validate_queries.py
```

The loader uses the committed [schema](schema.json): source paths, types, declared keys and unavailable meanings are explicit. Empty CSV fields become SQL NULL; boolean fields become 0/1; ISO dates remain sortable TEXT; GBP and decimal rates use REAL; historical counts use INTEGER. REAL is adequate for analysis at the documented £0.01 reconciliation tolerance, rather than financial transaction posting. The existing [metric dictionaries](../analysis/data_dictionary.csv) define source units and commercial semantics; later-phase dictionaries are linked from the main README reports.

`sql/.build/` receives the database, import hash manifest, query CSVs and independent validation. It is excluded from packaging and Git. Connections are read-only after import. Each declared grain has a unique constraint; unexpected fields, invalid dates, non-finite values or inconsistent repeated experimental history fail import.

| Query | Commercial purpose |
|---|---|
| [01](queries/01_membership_bridge.sql) | Integer member bridges and LAG continuity across 24 historical months |
| [02](queries/02_weighted_baseline.sql) | 2025 revenue components, exposure-weighted yields and average members |
| [03](queries/03_matching_periods.sql) | Matching annual/Q4 growth; churn and conversion changes in percentage points |
| [04](queries/04_region_trading.sql) | Eight-region, two-year trading summary and December stocks |
| [05](queries/05_qualified_funnel.sql) | Qualified-prospect conversion and marketing per prospect |
| [06](queries/06_opening_base_retention.sql) | Monthly churn/retention, same-month exits and complaints exposure |
| [07](queries/07_tier_mix_yield.sql) | Ledger-derived current-tier mix, gross paid rates and net yield |
| [08](queries/08_december_competitors.sql) | December recurring competitor gap, with fees/offers separate |
| [09](queries/09_promotion_context.sql) | Descriptive promotion context; not a causal promotion estimate |
| [10](queries/10_cohort_censoring.sql) | Original join cohorts and unavailable immature milestones |
| [11](queries/11_saved_pilot_evidence.sql) | Saved six-month pair acquisition, incumbent and revenue responses |
| [12](queries/12_saved_base_scenarios.sql) | Four saved Base options; annual revenue versus seasonal exit run-rate |
| [13](queries/13_saved_recommendations.sql) | Saved action, £1/£2 gates and commercial rationale |
| [14](queries/14_conditional_portfolios.sql) | Five policies × three cases; only RAISE increments; saved joint intervals |
| [15](queries/15_experiment_monitoring.sql) | Saved first/repeat checkpoint decisions and uncertainty |

The schema covers 17 tables at their original grains. Historical reporting defaults to full-year 2025; Q4 comparisons use the same months in 2024. Price snapshots are dated December 2025. Query 12 filters Base explicitly and returns 320 rows; summing all price options or cases would duplicate populations. Query 14 returns 15 separate named portfolios and does not sum uncertainty endpoints.

The `experiment_history` view deduplicates July–December 2025 observations repeated under three simulation labels, from 252 rows to 84 unique gym-months. January–June 2025 history used for saved twelve-month comparisons is retained in the supplemental Phase 8 payload and Power BI snapshot, not fabricated by this view. Query 15 reads the completed saved inference rather than reconstructing those comparisons. Repeat intervals are unavailable because only two pairs are assigned. Queries return all three simulations and four checkpoints separately; they must not be aggregated as independent evidence.

Acquisition rates divide joins by opening-member exposure; conversion divides joins by qualified prospects. Trials are not added to website leads. Opening-base churn excludes same-month joiner exits. Tier switches stay distinct from cancellations. Retention milestones approximate one, three and six months; cohort revenue is observed subscription revenue, excluding fees and ancillary income. Competitors and national operator equivalents are fictional proxies, not real market observations.

Growth columns ending `_pct` are percentages; `_pp` columns are percentage points; other rates are decimal fractions. Money is GBP; revenue is net of assumed 20% VAT, while advertised and paid consumer prices include VAT. Missing denominators remain NULL; valid zeros remain zero.

Validation checks every output field against independent source aggregation or frozen evidence, then exercises zero denominators, reporting boundaries, case separation, history deduplication and unsupported intervals. It preserves prior evidence. See [reproduction guidance](../portfolio/REPRODUCIBILITY.md).

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
