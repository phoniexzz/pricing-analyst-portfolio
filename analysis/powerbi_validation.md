# Native Power BI acceptance record

**Status: Phase 9 native verification complete.** Verified 6 October 2026 in Power BI Desktop **2.158.1177.0**. The existing `powerbi/gym_pricing_dashboard.pbix` was opened and refreshed; it was not recreated.

## Reconciliations

- Native Import refresh completed in Desktop without a query or calculation error dialog.
- All 296 explicit measures executed. Eight native DAX check groups passed, including all model table counts, full site baseline reconciliation, matching-period windows, unsupported uncertainty suppression, scenario comparisons, recommendations and experiment conclusions.
- Anchors: 2025 net revenue **£107,006,933.85**; December 2025 members **396,311**; Base conditional-raise portfolio uplift **£148,618.48**. The revenue bridge residual was less than £0.01.
- Saved actions remained **1 RAISE £2, 10 RAISE £1, 5 TEST FIRST, 26 HOLD PRICE, 38 DEFENSIVE / INVESTIGATE**. Main primary experiment remained **EXTEND TEST** at six months and **STOP** at twelve months. Repeat-population intervals and unsupported multi-gym uncertainty remain blank.
- Python parity passed against 41 source tables and 80 gyms, three matching-period windows and 46 protected evidence hashes. The Excel workbook hash is unchanged and it still contains 31 sheets.
- The stale-evidence test passed against the live Desktop model: stale status suppressed scenarios, recommendations and experiment conclusions; restore returned the original query and current evidence. Native DAX and Python parity were rerun after restore.

## Native page and interaction review

All six main pages rendered in Desktop after refresh: Executive Overview, Estate Pricing, Customer & Member Behaviour, Pricing Scenarios, Recommendations, and Experiment & Monitoring. The Gym Detail page was reviewed with a selected gym using the saved native drill-through view. Page navigation, scenario case selection/reset, experiment assessment/population selections, and reset to Main / six months / First repricing were verified. The repeat-repricing selection showed two pairs and blank interval/p-value fields, as required. Existing drill-through and Back interaction evidence is retained in the native Gym Detail capture.

Native screenshots are in `images/native_powerbi/`:

- `01_executive_overview.jpg`
- `02_estate_pricing.jpg`
- `03_member_behaviour.jpg`
- `04_pricing_scenarios.jpg`
- `05_recommendations.jpg`
- `06_experiment_main_6m_first.jpg`
- `07_gym_detail_NF001.jpg`
- `stale_scenario_verification.jpg`, `stale_recommendation_verification.jpg`, and `stale_experiment_verification.jpg`

The Recommendations table has many evidence columns and uses normal Power BI horizontal/vertical scrolling; the full row-level evidence remains available in the visual. At the current Desktop zoom and with authoring panes open, some table columns are outside the viewport. This is a presentation limitation, not a calculation or model error.

## Artifact identity

- Existing PBIX SHA-256: `7889903B8492889866E73DF4EFF32EE0BF999CDEECE906A5BB97A7DC35ACD1F8` (10,521,072 bytes).
- Excel workbook SHA-256: `D13E56FB50B2C110489DE2EE15CDEC4B332379763689065910AC2871C814D3FA` (31 sheets).
- PBIP/report/model and reporting snapshot fingerprint: `6efebefd24071fe8e24332ad29bfcf59e020028f3e2a58e1a830ea6f6e476a79`.
- Machine-readable proof: `analysis/powerbi_native_acceptance.json`.
- Native DAX results and independent parity: `analysis/powerbi_native_dax_results.json` and `analysis/powerbi_native_parity.json`.

This dashboard reports synthetic evidence inspired by UK subscription fitness economics. It contains no confidential information from The Gym Group or any other operator. It uses synthetic data created for portfolio purposes and does not use confidential information from any real operator.

This acceptance applies only to the fingerprint and evidence versions listed above. A later project, model-data or source-evidence refresh requires a new native check. Revenue is not profit; saved scenario uncertainty is conditional parameter uncertainty, not a forecast interval or rollout probability.
