"""Write the specification, metric catalog, refresh guide and native checklist."""
import json,re
from pathlib import Path
import pandas as pd
from powerbi_prepare import ROOT,DISCLAIMERS
from powerbi_measures import MEASURES
P=ROOT/'powerbi'
def write(path,text):Path(path).write_text(text.strip()+'\n',encoding='utf-8')
def document():
 schema=json.loads((P/'model_schema.json').read_text(encoding='utf-8'));pages=json.loads((P/'page_specification.json').read_text(encoding='utf-8'))
 validation=json.loads((ROOT/'analysis/powerbi_validation.json').read_text());prep=json.loads((ROOT/'analysis/powerbi_preparation_validation.json').read_text());book=json.loads((ROOT/'analysis/powerbi_workbook_verification.json').read_text());repro=json.loads((ROOT/'analysis/powerbi_refresh_verification.json').read_text());tom=json.loads((ROOT/'analysis/powerbi_tmdl_verification.json').read_text(encoding='utf-8'))
 lookup={}
 for file in (ROOT/'analysis').glob('*dictionary.csv'):
  if file.name.startswith('powerbi_'):continue
  for row in pd.read_csv(file).fillna('').to_dict('records'):
   lookup.setdefault(row['field'],row)
 rows=[]
 for table,meta in schema['tables'].items():
  for field,typ in meta['columns'].items():
   inherited=lookup.get(field,{})
   unit=inherited.get('unit') or ('ISO date' if typ=='dateTime' else 'boolean' if typ=='boolean' else 'text / identifier' if typ=='string' else 'numeric saved evidence')
   definition=inherited.get('definition') or field.replace('_',' ').capitalize()+'. Retained source value; table provenance and declared key define its scope.'
   if table=='FactPortfolioSite':definition+=' Conditional RAISE maps the saved price increment. All other actions map zero; provisional tests are excluded.'
   if table in ['FactScenarioAnnual','FactPortfolioSite','FactPortfolio','FactScenarioEstate'] and field in ['average_members','opening_members']:unit='member-month exposure, summed across 12 forecast months';definition='Sum of monthly average or opening expected membership exposures; not a stock or unique customers.'
   if field in ['month12_members','closing_members']:definition+=' This is a closing stock. Do not sum across months or simulations.'
   if field in ['rank','score','band','segment','action']:definition+=' Saved source result. No new rank, score, segment or action is calculated in Power BI.'
   rows.append({'table':table,'field':field,'data_type':typ,'unit':unit,'key_field':field in meta['key'],'grain_key':'; '.join(meta['key']),'source':meta['source'],'null_meaning':inherited.get('null_meaning') or 'Unavailable / not applicable. Empty CSV field imports as null; valid zero is retained.','definition':definition,'aggregation':'Explicit measures only for facts. Stocks use last month; rates use summed numerators/exposures; intervals use saved scope and SELECTEDVALUE.'})
 pd.DataFrame(rows).to_csv(ROOT/'analysis/powerbi_data_dictionary.csv',index=False)
 pd.DataFrame([{'measure':n,'display_folder':v['folder'],'format':v['format'],'definition':v['description'],'dax':v['dax'],'native_execution':'Pending Power BI Desktop'} for n,v in MEASURES.items()]).to_csv(ROOT/'analysis/powerbi_metric_dictionary.csv',index=False)
 definitions='\n\n'.join(DISCLAIMERS)
 tablecounts='\n'.join(f'| {n} | {v["rows"]:,} | {", ".join(v["key"])} |' for n,v in schema['tables'].items())
 official='[Microsoft PBIP external editing](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-external-editing), [PBIR report files](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report), [semantic-model files](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset), [TMDL](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview) and [star-schema guidance](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema).'
 previews=json.loads((ROOT/'analysis/powerbi_preview_manifest.json').read_text())
 imageindex='\n'.join(f'- [{r["page"]}](../{r["file"]})' for r in previews)
 write(P/'README.md',f'''# Northstar Fitness commercial dashboard

**Phase 9 build-ready; native verification pending.**

Open `gym_pricing_dashboard.pbip` in Power BI Desktop after following [SETUP.md](SETUP.md). The project contains six populated main pages and one hidden Gym Detail drill-through page, an Import semantic model, {len(MEASURES)} explicit DAX measures, local CSV snapshot queries and a navy/teal theme.

The report displays saved Phase 3–8 evidence. It does not re-estimate price responses, rerank sites, change recommendations, rerun forecasts or change the Excel selectors. Only report filters and saved-case selections are interactive.

The 2025 revenue anchor is **£107,006,934**, December membership is **396,311**, and the Base conditional-raise portfolio adds **£148,618** net revenue with approximately **1,209 fewer December members**. Revenue is not profit. Base recommendations are one RAISE £2, ten RAISE £1, five TEST FIRST, 26 HOLD and 38 DEFENSIVE / INVESTIGATE. Provisional TEST FIRST gains are excluded from the raise portfolio.

Main primary simulated experiment findings remain **EXTEND TEST at six months** and **STOP at twelve months**. These simulations are not new independent evidence.

[Native acceptance checklist](NATIVE_VERIFICATION.md), [DAX check queries](DAX_checks.dax), [model dictionary](../analysis/powerbi_data_dictionary.csv), [measure dictionary](../analysis/powerbi_metric_dictionary.csv), [specification](../analysis/powerbi_dashboard_specification.md) and [validation report](../analysis/powerbi_validation.md).

Design previews are **not native Power BI screenshots**. They use the validated snapshot and illustrate default selections. Tables show readable leading records; the native definitions retain full fields and scrolling. The hidden detail preview uses {previews[-1]['preview_scope'].split()[-1]} as an example.

{imageindex}

Project formats follow {official}

{definitions}''')
 write(P/'SETUP.md',f'''# Setup and refresh

**Native verification is pending. Power BI Desktop was not found locally. No PBIX has been created.**

1. Keep the whole `powerbi` folder together. Use a current supported Power BI Desktop release with PBIP, PBIR and TMDL support. Avoid the Report Server edition. The project uses documented PBIP 1.0, PBIR reference 4.0, report-definition version 2.0.0, public report/page/visual schemas and TMDL compatibility level 1601.
2. In PowerShell at the repository root, run the preparation/validation workflow below. It leaves the workbook and authored project definitions unchanged.
3. Open `powerbi/gym_pricing_dashboard.pbip`. In Transform Data → Manage Parameters, set **SourceRoot** to the absolute path of this project's `powerbi/model_data` folder. The delivered default points to this workspace; change it after moving the project. CSVs use UTF-8, decimal-dot numbers and ISO dates. Revenue is already net of the assumed 20% VAT; do not divide it by 1.2 again.
4. Set the local file-source privacy level consistently. Refresh the Import model. Check that all loaded row counts match `model_schema.json` and no conversion errors occur. `PowerQuery.m` is a documented section mirror; the operative queries live in the model TMDL partitions.
5. Execute `DAX_checks.dax` in DAX Query View and complete `NATIVE_VERIFICATION.md`. In Desktop author mode, Ctrl-click navigation/reset buttons as needed.
6. Save the project natively. A PBIX may be created only using verified native **File → Save As**, after the checklist passes. Publishing is outside this phase.

```powershell
& "$env:USERPROFILE\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe" analysis/powerbi_refresh.py
```

For another Python environment, install pandas, numpy and jsonschema. Preview regeneration additionally needs matplotlib. The bundled runtime is preferred. Locally installed validation helpers reside under `analysis/.powerbi_tools`; source evidence is never edited.

To explicitly rebuild generated project definitions and design previews before native customisation:

```powershell
& "$env:USERPROFILE\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe" analysis/powerbi_refresh.py --build
```

`--build` regenerates authored definitions. Use ordinary refresh after making native layout customisations. Public schemas are pinned locally, including Microsoft's report-theme 2.157 schema. Optional TMDL parser check: run `analysis/validate_powerbi_tmdl.ps1` with Microsoft Analysis Services TOM 19.84.1 available at the documented workspace helper path. Parsing is not DAX execution.

Refresh first checks immutable source/configuration hashes, then reproduces the snapshot, validates keys/joins/totals and records a new validation time. Numerical CSVs are byte-identical for unchanged evidence. `EvidenceStatus.csv` and the validation manifest intentionally change refresh timestamps. A changed prior source/configuration fails validation; resolve and explicitly version the evidence before replacing the approved snapshot.

Workbook capture freshness and original-driver comparisons are assessed independently of displayed case/price. In addition, saved numerical/boolean captures, keys and classifications are compared directly with approved CSV evidence; a capture mismatch suppresses authority even if a cached status cell still says CURRENT. Valid zero behavioural overrides, stale scenario captures or a saved-policy mismatch suppress authoritative scenario/recommendation measures. Experiment guardrail/protocol differences suppress experimental authority. Report selections never write back to Excel. Changes after Import remain invisible until preparation and native data refresh run again; the visible snapshot stamp identifies the imported version/time.

The 31-sheet Excel workbook retains all calculations, native resources and selectors. Only five progress cells changed. The existing Phase 6/7/8 packaging helper applies `analysis/latest_phase_guidance.json`, including when an owned sheet is replaced, so refreshes retain Phase 9 guidance. Existing numerical engines are unchanged. Close Excel before running their existing save workflows.

Source manifests identify original data, generation and Phase 3–8 configurations/results, joint draws and the independently hashed retained January–June experiment-history component. Operational workbook payload/source-capture updates do not masquerade as new evidence. Saved policy variants, ranges, ranks and experiment inference remain read-only.

For uncertainty use **DimGym** filters. A single gym or complete estate supports scenario ranges; only the complete named policy portfolio supports portfolio ranges. Other selections display blank ranges and an explanation. Site endpoints are never added. Whole-pair experimental intervals remain unavailable when fewer than four complete pairs exist.

{definitions}''')
 write(P/'NATIVE_VERIFICATION.md','''# Native Power BI acceptance checklist

Status: **pending**. Schema validation, Microsoft TOM parsing, Python arithmetic checks and design previews do not establish native DAX, M, interaction or rendering behaviour.

- [ ] Open PBIP successfully in supported Desktop. Record Desktop version, date, reviewer and any migration prompts. Do not overwrite the verified source project with a failed migration.
- [ ] Set SourceRoot, refresh all Import queries and confirm declared CSV types, nulls and model-table row counts. No missing keys, conversion errors or unexpected auto-date tables.
- [ ] Verify single-direction dimension→fact relationships, no fact-to-fact joins and no ambiguous filter paths. Check the separate historical, scenario and experiment calendars.
- [ ] Execute DAX_checks.dax. Confirm £107,006,933.85 earned 2025 revenue, 396,311 final members, £148,618.48020484 Base raise-only uplift and zero bridge residual within £0.01. Counts: 1 / 10 / 5 / 26 / 38 for RAISE £2 / RAISE £1 / TEST FIRST / HOLD / INVESTIGATE.
- [ ] Check weighted ARPMM, subscription/Standard yields, churn, conversion, acquisition and complaints against summed numerators/exposures. Check final-month stocks and monthly-average membership. No stock sums or annual-retention interpretation.
- [ ] Select January–March, Q4 and non-contiguous 2025 months and compare identical 2024 months. Select 2024 or both years and confirm unavailable incomplete prior-period comparisons. Changes in rates are percentage points, growth is percent. Valid zeros remain zero.
- [ ] Executive: annual/recent labels, exact volume/ARPMM change bridge and all-year revenues reconcile. Total ARPMM includes mix, joining fees and ancillary income. Portfolio gains exclude provisional tests and are visually distinct from all-gym scenarios.
- [ ] Estate Pricing: prices and comparability labels are dated December 2025; gross recurring prices, fees and introductory offers remain separate. Original ranks/bands remain unchanged under filters. Caution flags persist.
- [ ] Behaviour: site conversion uses qualified prospects, not invented Standard conversion. Historical £2 pilot estimates stay at the saved 12-pair scope regardless of site/date selection; intervals and sample sizes match source.
- [ ] Scenarios: Base/Downside/Upside select saved combinations; four increments compare without summing options/cases. No increase is identical across cases. Monthly endpoints and annual totals match CSVs. December ×12 is seasonal exit run-rate. Site break-even results remain unavailable where source has no crossing. £3 parity limitation visible.
- [ ] Recommendations: all 80 actions, price/test amounts, gates and explanations equal saved Phase 7. Base actions stay fixed while five saved sensitivities are displayed. TEST FIRST gains excluded. Single-gym/region point portfolios reconcile from site rows.
- [ ] Uncertainty: full estate and one-gym scenario ranges match saved rows. Arbitrary multi-gym and regional selections blank them. Full named-policy portfolio ranges match saved rows; any filtered portfolio blanks ranges. Never sum endpoints. Positive parameter draws are not rollout probabilities.
- [ ] Experiment defaults: Main, six months, First repricing. Confirm five primary and two exploratory pairs, seven treatments/seven controls, reserves NF023 and NF057. Shared historical filters do not affect experiment comparisons. Common 2025 history is counted once across simulations.
- [ ] Exercise all simulations/checkpoints/populations. Main primary is EXTEND TEST at six months, STOP at twelve. Repeat/regional intervals remain blank below four pairs. Regional views are descriptive where no saved governance classification exists. One-sided p=0.1875 at Main primary six months; two-sided value matches CSV. Primary minimum attainable one-sided p=3.125%.
- [ ] Guardrail upper bounds and limits use correct units and equality passes. Planning power comes from saved pre-period design assumptions, not observed power. Larger-sample approximations disclose additional eligible-site requirements.
- [ ] Inspect revenue/member/churn/downgrade profiles, notice/billing labels, pair results, monitoring responses and power. Test population filtering for profiles, pair rows and monitoring. Check the first-repricing interpretation is preserved.
- [ ] Navigation, synced region/location/segment/gym filters, history year/month controls, reset bookmarks and hidden Gym Detail drill-through work. Reset restores intended defaults. Table/chart selections do not accidentally recalculate inference or filter unrelated totals.
- [ ] In a disposable snapshot, set forward_current false and refresh; authoritative scenarios/recommendations suppress. Set experiment_current false; experimental conclusions suppress. Restore approved snapshot afterwards. Status-derivation input tests are already documented separately.
- [ ] Capture actual native screenshots of all six pages and hidden detail. Review clipping, wrapping, colour contrast, date/currency labels, native legend order, scrolling tables and chart geometry at normal zoom. Design PNGs do not satisfy this check.
- [ ] Confirm Excel workbook remains 31 sheets with original selector behaviour and native resources. Finish any native checks without changing prior evidence or recommendations.
- [ ] Only after acceptance, optionally create PBIX via native Save As. Record filename/hash and acceptance evidence. Keep service publishing out of scope.
''')
 write(P/'DAX_checks.dax','''// Execute in native Power BI DAX Query View. These queries have NOT been executed locally.
EVALUATE
CALCULATETABLE(
 ROW("Revenue 2025", [Net Revenue], "December members", [Closing Members],
 "ARPMM", [ARPMM], "Acquisitions", [Acquisitions], "Monthly churn", [Opening-base Churn],
 "Conversion", [Qualified Conversion], "Volume contribution", [Volume Bridge],
 "ARPMM contribution", [ARPMM Bridge],
 "Bridge residual", [Volume Bridge]+[ARPMM Bridge]-([Net Revenue]-[Net Revenue Prior Year])),
 DimHistoryMonth[year] = 2025)

EVALUATE
CALCULATETABLE(ROW("Base portfolio uplift", [Portfolio Increment],
 "December member difference", [Portfolio Member Difference],
 "Saved portfolio lower", [Portfolio Increment lower], "Saved portfolio upper", [Portfolio Increment upper]),
 DimPolicy[variant]="base", DimCase[case]="Base")

EVALUATE SUMMARIZECOLUMNS(FactRecommendation[action], "Sites", [Recommendation Site Count])

EVALUATE SUMMARIZECOLUMNS(DimCase[case], DimPrice[label],
 "Annual scenario revenue", [Scenario Revenue], "Incremental revenue", [Scenario Incremental Revenue],
 "December members", [Scenario December Members], "Churn", [Scenario Churn])

// Both must be blank: no unique case/option, and unsupported multi-gym uncertainty.
EVALUATE ROW("Multiple-case/option refusal", [Scenario Revenue],
 "Unsupported two-gym interval", CALCULATE([Scenario Increment lower],
 DimCase[case]="Base", DimPrice[price_increment]=2, DimGym[gym_id] IN {"NF001","NF002"}))

EVALUATE CALCULATETABLE(ROW("Main primary six-month decision", [Experiment Saved Decision],
 "Revenue effect", [Experiment Revenue Effect], "Revenue lower", [Experiment Revenue Effect lower],
 "One-sided p", [Experiment One-sided p], "Two-sided p", [Experiment Two-sided p],
 "Member harm upper", [Experiment Member Harm upper], "Complete pairs", [Experiment Complete Pairs]),
 DimSimulation[simulation]="Main", DimPopulation[population]="First repricing", DimCheckpoint[checkpoint_months]=6)

EVALUATE CALCULATETABLE(ROW("Main primary twelve-month decision", [Experiment Saved Decision]),
 DimSimulation[simulation]="Main", DimPopulation[population]="First repricing", DimCheckpoint[checkpoint_months]=12)

EVALUATE CALCULATETABLE(ROW("Repeat interval unavailable", [Experiment Revenue Effect lower]),
 DimSimulation[simulation]="Main", DimPopulation[population]="Repeat repricing", DimCheckpoint[checkpoint_months]=6)
''')
 page_table='\n'.join(f'| {p["title"]} | {p["scope"]} |' for p in pages)
 write(ROOT/'analysis/powerbi_dashboard_specification.md',f'''# Phase 9 dashboard specification

**Phase 9 build-ready; native verification pending.**

The Pricing Manager, Commercial Director and CFO can compare earned revenue, member performance, recurring price position, conditional site actions and the limits of testing. Higher realised yield can accompany weakening recruitment or retention. This communication layer displays the validated Phase 3–8 evidence and supports review of that trade-off; no new response estimation, ranking or recommendation is performed.

| Page | Reporting scope and decision context |
|---|---|
{page_table}

Six visible pages use native cards, line/bar/scatter/waterfall charts, tables, slicers and buttons. Gym Detail is hidden and bound to `DimGym[gym_id]` for drill-through. Navy/teal is the base theme; red/amber/blue statuses also carry text labels. General report filters are region, location type, saved headroom segment and gym. Historical views default to full-year 2025 and use matching 2024 months; December snapshots remain fixed. Separate calendars prevent historical filters from changing saved experiment comparisons.

The Executive waterfall uses member-volume and total-ARPMM contributions; its native total is the revenue change, rather than adding beginning/ending revenue twice. The interaction belongs to ARPMM. For 2025 the exact bridge is **−£425,763.94074156 + £2,902,054.51074155 = £2,476,290.57**. Mix, joining fees and ancillary income affect ARPMM. This is descriptive accounting, not a causal price estimate.

Price scenarios select saved Base, Downside or Upside and compare 0/£1/£2/£3 increments. The report never writes to workbook inputs. +£3 is analytical only and reaches unchanged Plus headline prices at 20 previously +£2 sites. December revenue ×12 is a seasonal exit run-rate, not earned annual revenue or a forecast.

Recommendations remain the 80 saved Base actions. Five policy variants are read-only sensitivities; Base portfolio cards stay labelled and fixed to named Base evidence. Only conditional RAISE increments enter the 1,200-row portfolio-site interface. All other sites retain no increase. Selected-site/region points and rates aggregate flows/exposures; uncertainty is not reconstructed for them.

Scenario ranges support one gym or the complete estate. Portfolio ranges support only a complete named policy portfolio. Unsupported scopes are blank with an explanation; no site endpoints are summed. These are conditional parameter ranges excluding future shocks and transport uncertainty, not forecast confidence intervals or rollout probabilities.

Experiment defaults to Main / six months / First repricing. Five first-repricing pairs are primary; two repeat pairs exploratory. Seven treatments, seven controls and reserves NF023/NF057 retain original assignments. Profiles use common deduplicated 2025 history and one selected 2026 simulation with matching-length windows. Saved population inference is not re-estimated when filtering profiles. Regional groups with no saved governance are descriptive; fewer than four complete pairs have unavailable intervals.

Monthly opening-base churn/retention, incumbent Standard churn and downgrades have distinct eligible populations. Transfers remain members; joining-month transfers are excluded from incumbent downgrades. Qualified prospects define all-tier conversion; no Standard conversion is invented. Planning power, historical parameter uncertainty, simulated trading variation and experimental intervals remain distinct.

The model has {len(schema['tables'])} imported tables plus the measure table, with dimension→fact single-direction relationships and no fact-to-fact paths. Separate monthly, annual, saved-estate and saved-portfolio facts prevent automatic aggregation across grains. Phase 6 sensitivities split site and estate rows; experimental history is not repeated by simulation. Raw numeric fact columns use `summarizeBy: none`; business calculations use explicit measures. CSV nulls import as null, not zero.

Original configurations and evidence are hashed. Source edits fail snapshot validation; stale/overridden forward captures suppress authoritative conclusions. A numeric zero override is detected as an override. Report control selections do not make a fresh capture stale. Snapshot metadata records version, validation UTC and native status. The 31-sheet workbook changes only five progress cells; refresh packaging preserves current guidance and the selector.

The six PNG designs and hidden detail layout are reviewed representations, not native screenshots or proof of runtime behaviour. Native acceptance remains the checklist in `powerbi/NATIVE_VERIFICATION.md`.

Formats and structure follow {official}

{definitions}''')
 checks='\n'.join('- '+x for x in validation['checks_passed'])
 write(ROOT/'analysis/powerbi_validation.md',f'''# Phase 9 validation

**Phase 9 build-ready; native verification pending.**

The reporting snapshot contains {len(schema['tables'])} typed, keyed CSV tables. All original source/configuration/evidence hashes remain unchanged. Saved financial anchors reconcile: earned 2025 net revenue **£107,006,933.85**, December closing members **396,311**, Base conditional-raise incremental net revenue **£148,618.48020484**. Action counts are **1 RAISE £2, 10 RAISE £1, 5 TEST FIRST, 26 HOLD, 38 DEFENSIVE / INVESTIGATE**. Main primary saved decisions are **EXTEND TEST at six months, STOP at twelve**.

{checks}

Microsoft TOM {tom['tom_package'].split()[-1]} parsed **{tom['tables']} tables, {tom['relationships']} relationships and {tom['measures']} measures** at compatibility level {tom['compatibility_level']}. This checks the TMDL object model and references; it does not execute DAX or M. Static bindings and independent Python arithmetic are also not substitutes for native execution.

Reproducibility: **{repro['byte_identical_reporting_csvs']} numerical/reporting CSVs byte-identical** on a repeated preparation; timestamp metadata intentionally changes. Disposable Artifact-authored input changes confirm valid zero overrides, stale captures, inconsistent numeric captures and saved-policy mismatches suppress forward authority. Experimental protocol changes suppress experimental authority. Independent workbook-to-CSV checks compare **{prep['workbook_status']['independent_capture_cells_compared']:,} captured cells** with no differences. A display-case change retains named saved evidence. The actual Excel selector remains Base / £2.

Workbook preservation: **31 sheets**, five authorised guide cells changed, {book['guide_cells_independently_compared']:,} guide-view cells independently compared. Every unaffected worksheet and other native resource is byte-identical, with style metadata structurally identical. Disposable Phase 6/7/8 owned-summary replacement tests retain all 31 sheets, latest guidance and selector. Numerical engines were not changed or rerun; prior engine verification remains applicable.

Design review covers every main page, hidden detail and affected guidance. Navigation labels, currency axes, primary/exploratory labelling, both £1/£2 evidence panels, confidence-bound guardrails and base-versus-sensitivity distinctions were reviewed and corrected. Native tables retain scrolling; previews display selected leading records. Native rendering and interactions remain unverified.

Reporting interfaces:

| Table | Rows | Unique key |
|---|---:|---|
{tablecounts}

Remaining acceptance: open Desktop, materialise Import data, run provided DAX checks, test native filters/bookmarks/drill-through, execute stale/scope checks and review actual screenshots. A PBIX is intentionally absent until a verified native save. Model build-readiness does not establish a causal response outside the historical pilot or approve estate-wide pricing. Revenue is not profit; stocks are not unique customers.

{definitions}''')
 print('Wrote Power BI guides, native checklist, specification, validation and complete field/measure dictionaries.')
 from powerbi_acceptance_status import update_docs
 update_docs()
if __name__=='__main__':document()
