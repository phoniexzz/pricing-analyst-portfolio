# Phase 9 dashboard specification

**Phase 9 native verification complete.**

The Pricing Manager, Commercial Director and CFO can compare earned revenue, member performance, recurring price position, conditional site actions and the limits of testing. Higher realised yield can accompany weakening recruitment or retention. This communication layer displays the validated Phase 3–8 evidence and supports review of that trade-off; no new response estimation, ranking or recommendation is performed.

| Page | Reporting scope and decision context |
|---|---|
| Executive Overview | Historical selected window. Snapshot Dec 2025. Conditional portfolio Jan–Dec 2026. |
| Estate Pricing | December 2025 snapshot. All competitors and national-equivalent fields are fictional proxies. Recurring prices include VAT; introductory discounts are separate. |
| Customer & Member Behaviour | Historical selected window with matching-year comparison. Historical pilot: Oct 2024–Mar 2025 vs Apr–Sep 2025. |
| Pricing Scenarios | Saved Jan–Dec 2026 scenarios. Conditional parameter uncertainty excludes future shocks and transport uncertainty. |
| Recommendations | Hypothetical 2026 conditional actions. Controlled testing precedes wider implementation. Policy variants are read-only. |
| Experiment & Monitoring | Illustrative £1 experiment. Five first-repricing pairs primary; two repeat pairs exploratory. Simulations are not new evidence. |
| Gym Detail | Selected gym: 2025 trading, Dec 2025 snapshot and saved £1/£2 qualification evidence. |

Six visible pages use native cards, line/bar/scatter/waterfall charts, tables, slicers and buttons. Gym Detail is hidden and bound to `DimGym[gym_id]` for drill-through. Navy/teal is the base theme; red/amber/blue statuses also carry text labels. General report filters are region, location type, saved headroom segment and gym. Historical views default to full-year 2025 and use matching 2024 months; December snapshots remain fixed. Separate calendars prevent historical filters from changing saved experiment comparisons.

The Executive waterfall uses member-volume and total-ARPMM contributions; its native total is the revenue change, rather than adding beginning/ending revenue twice. The interaction belongs to ARPMM. For 2025 the exact bridge is **−£425,763.94074156 + £2,902,054.51074155 = £2,476,290.57**. Mix, joining fees and ancillary income affect ARPMM. This is descriptive accounting, not a causal price estimate.

Price scenarios select saved Base, Downside or Upside and compare 0/£1/£2/£3 increments. The report never writes to workbook inputs. +£3 is analytical only and reaches unchanged Plus headline prices at 20 previously +£2 sites. December revenue ×12 is a seasonal exit run-rate, not earned annual revenue or a forecast.

Recommendations remain the 80 saved Base actions. Five policy variants are read-only sensitivities; Base portfolio cards stay labelled and fixed to named Base evidence. Only conditional RAISE increments enter the 1,200-row portfolio-site interface. All other sites retain no increase. Selected-site/region points and rates aggregate flows/exposures; uncertainty is not reconstructed for them.

Scenario ranges support one gym or the complete estate. Portfolio ranges support only a complete named policy portfolio. Unsupported scopes are blank with an explanation; no site endpoints are summed. These are conditional parameter ranges excluding future shocks and transport uncertainty, not forecast confidence intervals or rollout probabilities.

Experiment defaults to Main / six months / First repricing. Five first-repricing pairs are primary; two repeat pairs exploratory. Seven treatments, seven controls and reserves NF023/NF057 retain original assignments. Profiles use common deduplicated 2025 history and one selected 2026 simulation with matching-length windows. Saved population inference is not re-estimated when filtering profiles. Regional groups with no saved governance are descriptive; fewer than four complete pairs have unavailable intervals.

Monthly opening-base churn/retention, incumbent Standard churn and downgrades have distinct eligible populations. Transfers remain members; joining-month transfers are excluded from incumbent downgrades. Qualified prospects define all-tier conversion; no Standard conversion is invented. Planning power, historical parameter uncertainty, simulated trading variation and experimental intervals remain distinct.

The model has 41 imported tables plus the measure table, with dimension→fact single-direction relationships and no fact-to-fact paths. Separate monthly, annual, saved-estate and saved-portfolio facts prevent automatic aggregation across grains. Phase 6 sensitivities split site and estate rows; experimental history is not repeated by simulation. Raw numeric fact columns use `summarizeBy: none`; business calculations use explicit measures. CSV nulls import as null, not zero.

Original configurations and evidence are hashed. Source edits fail snapshot validation; stale/overridden forward captures suppress authoritative conclusions. A numeric zero override is detected as an override. Report control selections do not make a fresh capture stale. Snapshot metadata records version, validation UTC and native status. The 31-sheet workbook changes only five progress cells; refresh packaging preserves current guidance and the selector.

The six PNG designs and hidden detail layout are reviewed representations, not native screenshots or proof of runtime behaviour. Native acceptance is documented in `powerbi/NATIVE_VERIFICATION.md` and `analysis/powerbi_native_validation.md`.

Formats and structure follow [Microsoft PBIP external editing](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-external-editing), [PBIR report files](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report), [semantic-model files](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset), [TMDL](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview) and [star-schema guidance](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema).

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.


Native acceptance record: [verification report](../analysis/powerbi_native_validation.md). Native screenshots are in `images/native_powerbi`, separate from design previews. Later project or snapshot refreshes require a new native check.
