# Reproduce the commercial baseline

The baseline uses the fixed Phase 2 observations. It never calls the synthetic generator or reads latent behavioural parameters. Primary periods are the two complete calendar years, with October–December compared separately. All 80 mature sites appear in both years.

The three derived CSVs in `data` have keys `gym_id`, `month`, and `region + year`, respectively. `baseline_metric_dictionary.csv` documents every derived field, its unit, reporting window, null meaning and formula. Blank cells indicate unavailable results or an unassigned pilot pair. Decimal rates are stored as fractions. Percentage-point changes are stored in points, so 0.10 means 0.10 pp.

Average members, monthly revenue, ARPMM, acquisition, churn, conversion and promotion frequency have different denominators. Site rates are not averaged to obtain estate or regional rates. Revenue and behavioural rates pool their underlying counts or exposure. The requested revenue/member measure is ARPMM; an annual revenue divided by closing membership would mix annual flows with a single stock.

Average utilisation weights monthly occupancy by opening minutes at each site. Regional and estate occupancy additionally weight by concurrent capacity. The average monthly peak is an exposure-weighted average of estimated monthly site peaks. The maximum is the largest site-month estimate, not a simultaneous estate occupancy rate. The workbook shows the attendance and capacity calculation schedule on Estate Trends.

Annual member growth compares January opening with December closing. Closing-member year-on-year growth is also provided. Acquisition and revenue growth compare matching reporting windows. Churn, conversion and retention changes are percentage-point differences. December revenue times 12 is a seasonal run-rate illustration, separate from cumulative calendar-year revenue and any forecast.

The exact revenue bridge uses `12 × average members × ARPMM` for each year. Member-volume contribution is `12 × (2025 members − 2024 members) × 2024 ARPMM`. Total-ARPMM contribution is `12 × 2025 members × (2025 ARPMM − 2024 ARPMM)`. This order allocates interaction to ARPMM. It does not isolate Standard pricing, which also affects membership mix and behaviour. Total ARPMM includes subscription, joining-fee and ancillary revenue. Revenue is net of assumed 20% VAT; advertised membership and competitor prices are gross.

Rankings use annual revenue, matching-year revenue growth and opening-to-closing annual member growth independently. Both highest and lowest lists resolve metric ties using gym ID ascending. Quartiles use linear interpolation, equivalent to Excel PERCENTILE.INC. High churn uses the upper quartile, weak conversion the lower quartile, and declining acquisition requires both negative growth and growth at or below the lower quartile. Peak service pressure uses a site-month maximum of at least 100% of comfortable capacity. Flags overlap and do not assign pricing actions.

## Run sequence

Install the versions in `requirements.txt` in an isolated Python environment if needed. This workspace uses the bundled Python and Node runtimes. Missing plotting dependencies were installed in the ignored `analysis/.workbook_previews/python_packages` folder without changing the bundled runtime.

```powershell
$pythonRuntime = 'C:\Users\prave\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$nodeRuntime = 'C:\Users\prave\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'

& $pythonRuntime analysis\baseline_analysis.py
& $nodeRuntime --max-old-space-size=16384 analysis\build_baseline_workbook.mjs
& $pythonRuntime analysis\append_baseline_sheets.py
& $nodeRuntime --max-old-space-size=16384 analysis\build_baseline_workbook.mjs --verify-final
& $nodeRuntime analysis\build_baseline_workbook.mjs --style-repairs
& $pythonRuntime analysis\append_baseline_sheets.py --update-caches
& $pythonRuntime analysis\verify_baseline_workbook.py
```

Use the Spreadsheets operation marker immediately before workbook authoring when running through the skill. The Node dependency junction established in Phase 2 points to bundled `@oai/artifact-tool`. It is not a portfolio dependency to copy between machines.

The workbook builder authors the three new sheets with Artifact Tool against small, exact copies of the required source sheets. The packaging script appends those sheets, tables and charts to the preserved workbook, remapping styles and relationship IDs. No workbook business formulas are authored in Python. The complete assembled workbook is re-imported and recalculated before its formula caches are saved. Only Phase 3 progress text is updated in the existing overview and README. All original source parts, formulas, native tables and freeze panes remain intact.

The targeted style-repair step displays executive churn and conversion rates to two decimals, and reconciliation differences as 0.00. It transfers only Artifact Tool-authored formats for those nine cells. Source sheets and formulas are unaffected. Close the workbook in Excel before assembly or cache updates because Excel holds an exclusive replacement lock.

The ignored recovery file `analysis/.workbook_previews/phase3/input_workbook.xlsx` is the pre-Phase-3 workbook. Repeated assembly uses this recovery copy to avoid duplicate analysis tabs. After subsequent phases extend the model, do not rerun the Phase 3 assembly sequence over that enriched workbook. Preserve it or work from a separate copy instead.

## Interpretation

The report and three exported figures provide the management-facing findings. They are descriptive synthetic results. Historical targeted price changes, pilot membership, seasonality, promotions, marketing and competitor events remain potential confounders. Baseline analysis does not estimate price elasticity, pilot treatment effects, pricing headroom, future revenue uplift or profit. The two identical annual ancillary totals are a feature of the synthetic source history, not independent evidence of stable real-world ancillary performance.

Native Microsoft Excel application behaviour has not been automated. Formula calculation is tested in Artifact Tool and the saved file is checked independently using OOXML. Complete visual review remains necessary after any rebuild.

After inspecting all changed sheet renders and figures, run `analysis/verify_baseline_workbook.py --visual-review-confirmed` to record completion. The initial verifier run intentionally leaves visual review pending. The source-linked workbook calculations require adequate memory and take several minutes; allow each step to complete before starting the next.

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
