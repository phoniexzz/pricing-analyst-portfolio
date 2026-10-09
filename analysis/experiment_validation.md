# Phase 8 validation — complete

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.

All experiment, saved workbook, refresh, preservation, reproducibility and visual gates pass. Native Excel was not automated: Artifact Tool recalculated the actual saved formula graph and the workbook is set to automatic Excel recalculation.

Python generation checks: 5,443, including per-cohort survivor checks. Full assertion names are retained in the audit directory, not counted as independent experiments. Additional boundary/null/matching fixtures pass.

| Interface | Rows |
|---|---:|
| experiment_design | 80 |
| experiment_monthly | 756 |
| experiment_pair_results | 84 |
| experiment_estimates | 1,728 |
| experiment_power | 114 |
| experiment_monitoring | 168 |
| experiment_simulation_ledger | 61,934 |

- Exactly seven disjoint pairs; five first and two repeat pairs; seven treatments and seven controls. Sixteen eligible candidates; NF023 and NF057 remain reserves.
- All historical matching windows complete; no post-intervention matching input. Separate fixed streams and deterministic assignment.
- Integer member bridges, tier transfers, eligible exits, cohort identity, promotional protection and one-time billed increments reconcile. Zero caps and zero seasonal-driver fallbacks were needed in the fixed run.
- Ledger subscription revenue and revenue components reconcile within £0.01. Rate numerators and member exposure remain visible.
- Ten thousand whole-pair resamples; exact 32/128 assignment enumeration; zero-effect fixtures; unavailable small-group intervals; all governance boundaries and precedence verified.
- Power interface keys are unique; actual five-pair null rejection rate 3.10% is below the pre-specified 5% alpha under the historical planning proxy.
- All seven CSVs reproduce byte-identically. All source, generation, Phase 3–7 evidence and retained Phase 6 shared draws retain their original hashes.

Saved workbook: 31 populated sheets, 27 earlier sheets and native resources preserved apart from authorised guidance updates. 69,088 saved values compare with independent Python results; maximum absolute difference 4.97e-09. 43,304 formula cells have evaluated caches. Formula errors: zero.

Actual saved-formula recalculation passes, including live guardrail edits, missing-versus-zero policy values, outcome/seed stale detection, hidden unavailable intervals and scenario selector independence/restoration. A full comparison refresh succeeds with CURRENT captures. Phase 6/7 replacement plumbing preserves all experiment sheets and current guidance on a disposable copy using their already validated segments.

Every new sheet, native chart, three commercial figures and affected guidance area received visual review. Source-linked monthly/period comparisons and monitoring arithmetic are separated from independent terminal checks.

Evidence files: experiment_results.json, experiment_workbook_verification.json, and the Phase 8 audit directory’s reproduction.json, saved_recalculation.json, refresh_verification.json, refresh_compatibility.json, additional_validation.json and visual_review.json.

Remaining simplifications: small samples, proxy trading residuals, monthly billing exposure approximations, frozen competitor recurring prices and no upgrades/freezes/bad-debt or future operational shocks. Simulated estimates are not independent validation, actual realised revenue or profit.

Phase 8 complete; Phase 9 next.
