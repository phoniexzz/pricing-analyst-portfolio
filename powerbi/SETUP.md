# Setup and refresh

**Native verification completed in Power BI Desktop 2.158.1177.0. `gym_pricing_dashboard.pbix` was created through native Save As. See the native acceptance record.**

1. Keep the whole `powerbi` folder together. Use a current supported Power BI Desktop release with PBIP, PBIR and TMDL support. Avoid the Report Server edition. The project uses documented PBIP 1.0, PBIR reference 4.0, report-definition version 2.0.0, public report/page/visual schemas and TMDL compatibility level 1601.
2. In PowerShell at the repository root, run the preparation/validation workflow below. It leaves the workbook and authored project definitions unchanged.
3. Open `powerbi/gym_pricing_dashboard.pbip`. In Transform Data → Manage Parameters, set **SourceRoot** to the absolute path of this project's `powerbi/model_data` folder. The delivered default points to this workspace; change it after moving the project. CSVs use UTF-8, decimal-dot numbers and ISO dates. Revenue is already net of the assumed 20% VAT; do not divide it by 1.2 again.
4. Set the local file-source privacy level consistently. Refresh the Import model. Check that all loaded row counts match `model_schema.json` and no conversion errors occur. `PowerQuery.m` is a documented section mirror; the operative queries live in the model TMDL partitions.
5. Execute `DAX_checks.dax` in DAX Query View and complete `NATIVE_VERIFICATION.md`. In Desktop author mode, Ctrl-click navigation/reset buttons as needed.
6. Save the project natively. A PBIX may be created only using verified native **File → Save As**, after the checklist passes. Publishing is outside this phase.

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" analysis/powerbi_refresh.py
```

For another Python environment, install pandas, numpy and jsonschema. Preview regeneration additionally needs matplotlib. The bundled runtime is preferred. Locally installed validation helpers reside under `analysis/.powerbi_tools`; source evidence is never edited.

To explicitly rebuild generated project definitions and design previews before native customisation:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" analysis/powerbi_refresh.py --build
```

`--build` regenerates authored definitions. Use ordinary refresh after making native layout customisations. Public schemas are pinned locally, including Microsoft's report-theme 2.157 schema. Optional TMDL parser check: run `analysis/validate_powerbi_tmdl.ps1` with Microsoft Analysis Services TOM 19.84.1 available at the documented workspace helper path. Parsing is not DAX execution.

Refresh first checks immutable source/configuration hashes, then reproduces the snapshot, validates keys/joins/totals and records a new validation time. Numerical CSVs are byte-identical for unchanged evidence. `EvidenceStatus.csv` and the validation manifest intentionally change refresh timestamps. A changed prior source/configuration fails validation; resolve and explicitly version the evidence before replacing the approved snapshot.

Workbook capture freshness and original-driver comparisons are assessed independently of displayed case/price. In addition, saved numerical/boolean captures, keys and classifications are compared directly with approved CSV evidence; a capture mismatch suppresses authority even if a cached status cell still says CURRENT. Valid zero behavioural overrides, stale scenario captures or a saved-policy mismatch suppress authoritative scenario/recommendation measures. Experiment guardrail/protocol differences suppress experimental authority. Report selections never write back to Excel. Changes after Import remain invisible until preparation and native data refresh run again; the visible snapshot stamp identifies the imported version/time.

The 31-sheet Excel workbook retains all calculations, native resources and selectors. Only five progress cells changed. The existing Phase 6/7/8 packaging helper applies `analysis/latest_phase_guidance.json`, including when an owned sheet is replaced, so refreshes retain Phase 9 guidance. Existing numerical engines are unchanged. Close Excel before running their existing save workflows.

Source manifests identify original data, generation and Phase 3–8 configurations/results, joint draws and the independently hashed retained January–June experiment-history component. Operational workbook payload/source-capture updates do not masquerade as new evidence. Saved policy variants, ranges, ranks and experiment inference remain read-only.

For uncertainty use **DimGym** filters. A single gym or complete estate supports scenario ranges; only the complete named policy portfolio supports portfolio ranges. Other selections display blank ranges and an explanation. Site endpoints are never added. Whole-pair experimental intervals remain unavailable when fewer than four complete pairs exist.

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.


Native acceptance record: [verification report](../analysis/powerbi_native_validation.md). Native screenshots are in `images/native_powerbi`, separate from design previews. Later project or snapshot refreshes require a new native check.
