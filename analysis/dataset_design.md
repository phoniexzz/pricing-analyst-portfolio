# Phase 2 — Synthetic dataset design

**UK Gym Pricing & Revenue Optimisation**  
*Identifying Site-Level Pricing Headroom Across an 80-Gym Estate*

> This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

## Purpose and commercial decisions

This phase creates the evidence needed to examine whether Standard price increases can improve sustainable revenue. It does not decide which gyms should reprice. Real UK city names provide geographical context; demographics, catchments, gyms, members, prices and competitor observations are entirely synthetic.

| Table | What the analyst tries to learn | Business decision supported later |
| --- | --- | --- |
| Gym Master | How catchment, competition, price and capacity differ across 80 mature sites. | Which comparisons and segments are commercially meaningful. |
| Monthly Performance | How recruitment, churn, yield and revenue change together over 24 months. | Whether a site's fundamentals support investigating a price increase. |
| Competitor Pricing | The recurring price position and acquisition offers of local alternatives. | Where relative value might permit an increase or require defence. |
| Pricing History | When price changes affected prospects and existing members. | Which before/after windows and controls are valid. |
| Customer Cohorts | How different joining groups survive and generate revenue. | Whether a short-term gain may conceal later retention damage. |
| Membership Ledger | How member movement, promotions, paid rates and tier switching produce revenue. | Whether apparent yield growth represents actual subscription performance. |
| Experiment Assignments | Which historical gyms were matched and randomly assigned before outcomes. | How to distinguish pilot evidence from commercial selection. |
| Market Events | When competitor entry, promotions and recurring price changes occurred. | Which external shocks might confound a price-response estimate. |

## Data model and dates

The observation window is January 2024–December 2025. A `month` value is the first calendar day of a full monthly observation. The Gym Master is a December 2025 snapshot: static geography applies throughout history, while snapshot prices, competition and utilisation must not be used as if known before historical events. Use Monthly Performance and Competitor Pricing for time-specific features.

| CSV | Primary key |
| --- | --- |
| gym_master | gym_id |
| monthly_performance | gym_id, month |
| competitor_prices | gym_id, competitor_id, month |
| pricing_history | gym_id, event_id |
| cohorts | gym_id, join_month, membership_type |
| membership_ledger | gym_id, month, billing_bucket_id |
| experiment_assignments | experiment_id, gym_id |
| market_events | gym_id, competitor_id, event_date, event_type |

Every `gym_id` references Gym Master. A competitor ID is local to the Northstar catchment, not a shared national observation. `cohort_id` links joining cohorts to the ledger. Cohorts' `membership_type` is the original joining tier; the ledger's is the current tier. Premium columns refer to the Plus product. The field-level dictionary is `data_dictionary.csv` in this folder and the workbook's Data Dictionary sheet.

## Generation sequence and relationships

1. Generate synthetic site geography, affluence, student mix, quality, competition, prices and capacity. Affluence influences prices and sensitivity; student mix affects seasonality and churn. Initial membership weights relate to floor area and demand. Allocate exactly 400,000 opening memberships once.
2. Generate fictional competitor prices, entry dates and promotions. PulseFit is the fictional national value proxy and Forge Fitness the national full-service proxy. The compatibility fields `PureGym_equivalent_price` and `JD_equivalent_price` contain these fictional prices, never observations from real brands.
3. Simulate monthly demand, marketing, conversion and tier choice. January is stronger, summer weaker, and September is stronger for student markets. Acquisitions are integer multinomial outcomes from a single qualified-prospect funnel. Website leads and trials are nested subsets.
4. Simulate exits from opening members and same-month joiners separately. Standard members can downgrade into Off-Peak; switches retain original cohort identity. Apply notification, implementation and delayed churn effects separately from acquisition response. Rejoining is a new activation and cohort, never a resurrected survivor in an old cohort.
5. Roll each billing bucket forward and calculate revenue from average member exposure and the applicable paid rate. Aggregate ledger amounts into tier and gym-month totals. Carry closing members forward without rescaling, resetting or applying a second stock-elasticity loss.
6. Derive observed cohort milestones and December snapshots from generated movements, rather than drawing unrelated retention percentages or snapshot values.

The seed is **20261004**. Site characteristics, market events, pilot assignments and individual gyms' monthly behaviour use separate seeded random streams. Configuration and generator code expose assumed mechanisms. They are not observed estimates and must not be substituted for estimated elasticity later. No assumed elasticity, pricing-headroom score or final action is included in analyst-facing CSVs.

## Historical interventions

July 2024 contains 12 targeted +£1 changes selected from January–June performance. February 2025 contains eight other targeted +£2 changes selected from August 2024–January 2025. Commercial selection uses preceding competitor gaps, peak utilisation, acquisition and churn. This deliberately creates selection bias to discuss later.

In April 2025, select 12 pairs from previously unrepriced gyms. Match within region using January–March price, average members, peak utilisation, acquisition, churn, competitor count and growth. Standardise the features and use nearest-pair distances, adding a small penalty for different location types. Select one pair per region first, then the four best remaining pairs. Randomly assign treatment within each selected pair. Treatment receives +£2; all 12 controls remain unrepriced to December 2025. Pre-match features and matching distances are retained in assignments. Pair quality and balance must still be assessed during historical analysis; random assignment does not make observationally targeted changes causal.

Historical pilot observations belong in this history. The proposed future test and its simulated results are separate Phase 8 work. No historical test result is interpreted in Phase 2.

## Billing and revenue conventions

All advertised and paid consumer prices include VAT. Revenue uses an assumed uniform 20% VAT convention. Subscription revenue is the sum of ledger midpoint membership exposure times paid consumer rate divided by 1.20, rounded to pennies per row. Joining fees are recognised in the joining month as a documented simplification. Ancillary receipts use a site-area and seasonal baseline, disclosed separately. Marketing spend is an expense, not a deduction from revenue.

Opening Standard members have a £2 legacy discount. Off-Peak and Plus opening members pay their starting advertised rates. New joiners receive the current headline tier price. Northstar Standard promotions discount the first two billing months by 20%; price protection expires at the first day of the following month. Fee waivers increase during promotions.

Existing eligible Standard members receive a historical cash increment only after both notice and promotional protection end. Notice starts with the month-start headline change; implementation is no earlier than the next month. New members on the already increased headline price never receive that same increase twice. Switching to Off-Peak ends Standard exposure and uses Off-Peak pricing. The first model includes downgrades only; upgrades, Plus-to-Standard migration, cross-gym transfers, fixed terms and freezes are not simulated.

`average_members` is the midpoint of opening and closing counts, including at billing-bucket level. This makes the bridge reconcilable but approximates timing within a month. `billed_price` is the full member-month paid recurring rate, not a second proration amount. The generator does not claim to reproduce cash collection, bad debt, refund or detailed revenue-recognition systems.

## Retention, attendance and missing values

The 30-, 90- and 180-day cohort fields mean end-of-month survivors one, three and six calendar months after the joining month. They are monthly approximations, not exact-day measures. Revenue windows include the joining month plus the next five or eleven months. Incomplete windows remain blank; they are not projected or filled with zero. Cohort revenue excludes fees and ancillary income.

`average_tenure` is observed midpoint member-month exposure divided by original joins. It is a censored restricted mean over available history, not completed lifetime tenure. Opening legacy join dates are unknown and blank in the ledger; legacy groups are excluded from the joining-cohort summary.

Average attendance equals visits times the assumed 60-minute stay divided by all calendar opening minutes. The estate operates 24 hours daily. Peak attendance is estimated using a site-specific within-day concentration factor. Capacity is a comfortable occupancy proxy, not a legal maximum; peak utilisation above 100% indicates service pressure. Do not interpret membership stock divided by occupancy capacity as utilisation.

## Reproduce and extend

Run `analysis/generate_synthetic_data.py` using Python with NumPy and pandas, then run the workbook builder using the bundled Node runtime and `@oai/artifact-tool`. Reproduction commands for this workspace are included in `phase2_run_instructions.md`. The generator makes two full in-memory runs and compares CSV SHA-256 hashes before writing the dataset. Use the recorded package versions for exact reproduction.

Generation parameters are fixed assumptions. Adjusting them rebuilds history and invalidates downstream analysis. Do not tune them to force a preferred recommendation. Dataset validation reports shape, reconciliation and observed ranges; it does not claim causal validation or commercial success.

Phase 3 will calculate the executive baseline from this evidence. Neither site recommendations nor experiment interpretation has started.

> This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
