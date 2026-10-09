# Viewing, validation and advanced reproduction

## 1. View completed artifacts

Extract `northstar_portfolio.zip` into a new directory. Begin with the root README and presentation PDF. Excel, Power BI Desktop and PowerPoint are needed only to use their respective native files. The CSVs, reports, SQL and screenshots can be inspected without those applications.

The accepted Power BI file was tested in Desktop 2.158.1177.0. Acceptance is attached to the original file hash and project fingerprint, not automatically to a moved or modified project. For a PBIP refresh, change the Power Query **SourceRoot** parameter to the extracted root as described in [Power BI setup](../powerbi/SETUP.md). Refresh only your copy and rerun its checks. Do not rebuild the accepted project merely to view it.

The PPTX has editable charts and notes. Its saved rendering was visually checked with Artifact Tool; native PowerPoint rendering remains unverified. The PDF is image-based, so text searching and text selection are limited. Native dashboard table captures show the visible viewport; use the PBIX for the complete scrollable tables.

## 2. Validate SQL and saved evidence

Use Python 3.11+ and SQLite bundled with Python. From the extracted root:

```powershell
python sql/run_queries.py
python -m pip install -r analysis/requirements.txt
python sql/validate_queries.py
python analysis/package_portfolio.py --verify-only
```

The query runner requires only the standard library. Validation adds the pinned NumPy/Pandas environment. Commands resolve paths relative to their scripts, not a particular user account. SQL databases and outputs stay under ignored `sql/.build/`. The package verifier checks shipped file manifests; full protected-evidence verification requires restoring the supplemental archive below. Files missing from the lean package are reported as unavailable, never as verified.

## 3. Advanced regeneration in an isolated copy

Overlay `northstar_reproduction.zip` onto the extracted portfolio root. It restores the original hidden directory structure, including the shared 10,000-draw uncertainty file, scenario/policy payloads, retained experimental history, layout maps and acceptance hash evidence. These are dependencies, not redundant screenshots. Run the package verifier again after restoration.

The archives do not contain installed runtimes, libraries, application caches or node_modules. Install the pinned Python requirements. Numerical scripts use their own fixed configurations and documented seeds; do not use latent generation parameters to estimate historical responses. Consult the phase runbooks before executing anything:

- [Phase 2](../analysis/phase2_run_instructions.md): regenerates source data and resets the workbook to an early phase.
- [Phase 6](../analysis/phase6_runbook.md): scenario builds and comparison refreshes.
- [Phase 7](../analysis/recommendation_runbook.md): policy refreshes and portfolio uncertainty.
- [Phase 8](../analysis/experiment_protocol.md): experiment design and simulation.
- [Power BI](../powerbi/SETUP.md): reporting snapshot, project and native acceptance requirements.

Run these only in a disposable extracted copy. Several historical `--reproduce` workflows still write diagnostic or lineage files. Workbook refreshes require Excel to release its file lock and can change the workbook hash. The Phase 11 package does not rerun those destructive workflows against accepted artifacts.

Workbook and presentation builds require the **bundled Codex Artifact Tool** and the applicable Spreadsheets/Presentations skill resources. An ordinary pip install is not an equivalent build environment. Historical scripts retain some absolute Windows paths to Node, Python, skill helpers and Poppler. Locate your bundled dependencies and adapt those paths in the disposable copy before advanced builds; do not change commercial configurations. Windows COM/ADOMD/native Desktop scripts also require their documented local applications and libraries. The package deliberately does not claim unattended cross-platform regeneration of those native steps.

Changing Power BI SourceRoot, recalculating a workbook or rebuilding a report creates a new artifact state. Preserve the shipped files and verify your new state independently. External progress guidance is current at Phase 11; the protected workbook retains its older progress captions until a future authorised refresh.

## Packaging

`portfolio/package_config.json` declares root folders, suffixes, exclusions and the supplemental dependency list. `python analysis/package_portfolio.py` validates, stages and packages files in sorted order with fixed ZIP timestamps. Archives and manifests are saved under ignored `dist/`; clean-copy verification uses ignored `analysis/.portfolio_build/`. No Git repository, commit, remote or publication is created.

The ordinary repository package excludes the 150 MB shared-draw NPZ, which exceeds GitHub's [100 MiB ordinary-file limit](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github). A future publisher can attach the supplemental archive as a release asset or choose Git LFS separately. No dependency archive or account has been uploaded.

Both manifests list relative paths, byte sizes and SHA-256 hashes. Archive manifests define shipped file identity. The Phase 11 validation record separately reports the preservation of prior evidence and accepted artifacts. Repeated packaging of identical inputs must produce identical archive bytes.

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
