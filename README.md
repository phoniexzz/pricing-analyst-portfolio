# Northstar Fitness — UK Gym Pricing & Revenue Optimisation

**A commercial analytics portfolio: 80 fictional mature UK gyms, two years of trading evidence, and an auditable pricing decision.**

Which gyms should increase Standard membership prices, by how much, and when does additional yield outweigh weaker recruitment and retention?

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

## Start here

1. Read the [ten-slide management presentation](presentation/pricing_recommendation.pdf), or open the [editable PowerPoint](presentation/pricing_recommendation.pptx).
2. View the [native dashboard gallery](portfolio/dashboard_gallery.md) and [Power BI report](powerbi/gym_pricing_dashboard.pbix).
3. Read the [portfolio case study](portfolio/case_study.md).
4. Inspect the [31-sheet Excel model](excel/gym_pricing_model.xlsx).
5. Explore the [SQL examples](sql/README.md), [methodology](analysis/business_brief.md) and [verification records](portfolio/REPRODUCIBILITY.md).
6. Practise with the [interview pack](interview/README.md).

The presentation PDF is a static, image-based viewing copy. The PPTX contains editable charts, tables and speaker notes. Artifact Tool rendering was reviewed; native PowerPoint rendering has not been verified.

## The business problem

Northstar Fitness operates Standard, Off-Peak and Plus memberships. A price increase improves billed yield, but can reduce conversion, accelerate cancellations and encourage downgrades. Revenue alone therefore cannot determine which sites merit further testing.

The model separates acquisition from retention, headline consumer prices from realised yield, and subscription income from fees and ancillary revenue. Consumer prices include VAT; modelled revenue excludes an assumed 20% VAT. Revenue is not profit.

## Commercial model and approach

`Closing members = Opening members + Joins − Opening-base cancellations − Same-month cancellations`

`Average members ≈ (Opening members + Closing members) / 2`

`Total net revenue = Subscription revenue + Joining-fee revenue + Ancillary revenue`

`ARPMM = Total net revenue / Average-member months`

Monthly billing ledgers preserve original cohorts, legacy billed rates, promotions and tier transfers. Downgrades retain membership and reduce yield; they are separate from cancellations. The average-member approximation does not capture exact intramonth billing dates.

The workflow establishes a 2025 baseline against matching 2024 periods, creates transparent relative headroom indicators, estimates historical responses from a 12-pair randomised +£2 pilot, models 2026 alternatives, applies explicit conditional recommendation gates and demonstrates a seven-pair £1 experiment. Twenty commercially selected historical increases remain observational comparisons. SQL reproduces descriptive evidence; it does not invent new causal estimates or actions.

## Findings and conditional decisions

| Saved result | Commercial interpretation |
|---|---|
| 2025 net revenue **£107,006,933.85**, up **2.37%** | Growth can coexist with declining membership. |
| December 2025 members **396,311**, down **0.67%** year on year | A member stock, not a count of unique annual customers. |
| Exact revenue bridge: volume **−£425,763.94**; total ARPMM **+£2,902,054.51** | The interaction is allocated to ARPMM, which includes mix, fees and ancillary income. |
| Historical pilot Standard acquisition response **−8.27%**; incumbent churn **+0.345 pp** monthly | Acquisition elasticity and incumbent retention response are different parameters. |
| Conditional RAISE-only portfolio: **£148,618.48** incremental 12-month net revenue | Approximately **1,209 fewer December members** versus no increase. |
| Portfolio conditional 95% range **£64,400–£230,752** | Shared parameter uncertainty excludes future trading shocks and transport uncertainty. |

Saved site actions are **one RAISE £2, ten RAISE £1, five TEST FIRST, 26 HOLD PRICE and 38 DEFENSIVE / INVESTIGATE**. All increases require controlled testing before wider implementation. The selected portfolio includes only the eleven conditional RAISE sites; provisional TEST FIRST gains are excluded.

The illustrative £1 experiment contains seven matched pairs: five first-repricing pairs are primary and two repeat-repricing pairs exploratory. Its Main simulation gives **EXTEND TEST at six months** and **STOP at twelve months**. Simulated observations demonstrate governance; they provide no new independent evidence for the forecast or permission to implement prices.

## Dashboard preview

![Native Power BI Executive Overview](images/native_powerbi/01_executive_overview.jpg)

Native Power BI Desktop capture. Six main pages and a hidden Gym Detail page cover trading, pricing, behaviour, saved scenarios, recommendations and experiment monitoring. See the [captioned gallery](portfolio/dashboard_gallery.md) for all seven layouts.

## Tools and verification

- **Python / NumPy / Pandas:** reproducible synthetic generation, commercial analysis, paired inference, expected-member scenarios and stochastic experiment simulation.
- **SQLite:** fifteen runnable queries demonstrating joins, CASE, CTEs and window functions, independently checked against Python and saved evidence.
- **Excel / bundled Artifact Tool:** source-linked formulas, billing bridges, editable policy gates, charts and refresh workflows.
- **Power BI:** Import star model, Power Query, 296 DAX measures and native visuals; PBIP/PBIR/TMDL source definitions.
- **PowerPoint / Artifact Tool:** ten-slide executive narrative with editable charts and evidence tables.

[Native Power BI acceptance](analysis/powerbi_native_acceptance.json) records Desktop 2.158.1177.0, refresh, DAX, interactions and parity checks. It applies to the saved artifact and recorded fingerprint. Changing source paths, refreshing or rebuilding creates a new state requiring verification. Unsupported multi-site uncertainty scopes return blank; site interval endpoints are never summed.

## Repository structure

| Folder | Contents |
|---|---|
| `analysis/` | Business brief, scripts, configurations, dictionaries, reports and validation evidence |
| `data/` | Synthetic source records and saved derived interfaces at documented grains |
| `excel/` | Completed 31-sheet pricing workbook |
| `powerbi/` | Accepted PBIX, editable project, validated reporting snapshot and setup guide |
| `presentation/` | Management PPTX, PDF and presenter notes |
| `images/` | Commercial plots, labelled design previews and native dashboard captures |
| `sql/` | Explicit schema, loader, query runner, independent checks and 15 queries |
| `portfolio/` | Case study, gallery, package configuration and reproducibility guide |
| `interview/` | Story, thirty answers, stakeholder challenges, evidence register and rehearsal guide |

## Run the SQL examples

From the extracted portfolio root, using Python 3.11 or newer:

```powershell
python sql/run_queries.py
python -m pip install -r analysis/requirements.txt
python sql/validate_queries.py
```

The first command requires only the Python standard library. It creates an ignored SQLite database and fifteen CSV outputs under `sql/.build/`. Independent validation uses NumPy/Pandas. See [reproducibility instructions](portfolio/REPRODUCIBILITY.md) before running any earlier analysis or workbook refresh script: those scripts can overwrite saved deliverables.

## Evidence limits and project status

Headroom ranks are relative indicators, not causal pricing tolerance. Historical response identifies a local +£2 policy in positive competitor-gap markets; transport to other sites, repeated repricing and different increments remains uncertain. Monthly retention is not annual retention. Earned annual revenue, modelled 12-month revenue and a seasonal December ×12 run-rate are different quantities. Contribution costs and profit effects are not estimated.

**Phase 12 complete; interview preparation materials complete.** The portfolio includes presentation, SQL and interview materials without changing prior commercial evidence. The unchanged workbook contains older embedded progress labels; this README and external phase guidance describe current project status. The [separate interview pack](interview/README.md) completes written preparation; live mock practice and GitHub publication remain separate work. The two Phase 11 archives are preserved unchanged.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
