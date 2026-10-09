# Reproduce the Phase 2 dataset

Run from the repository root. Dataset generation requires Python with the versions recorded in `requirements.txt`. The Excel builder requires Node and the Codex bundled `@oai/artifact-tool` package. The workbook is authored by Artifact Tool, not pandas or another Excel writer.

For this Windows workspace, the bundled runtimes are:

```powershell
$pythonRuntime = 'C:\Users\prave\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$nodeRuntime = 'C:\Users\prave\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$runtimePackages = 'C:\Users\prave\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'

& $pythonRuntime analysis\generate_synthetic_data.py
& $pythonRuntime analysis\validate_dataset.py

if (-not (Test-Path -LiteralPath 'analysis\node_modules')) {
    New-Item -ItemType Junction -Path 'analysis\node_modules' -Target $runtimePackages | Out-Null
}
& $nodeRuntime --max-old-space-size=8192 analysis\build_dataset_workbook.mjs
& $nodeRuntime --expose-gc --max-old-space-size=8192 analysis\build_dataset_workbook.mjs --ledger-parts
& $pythonRuntime analysis\assemble_workbook.py
& $nodeRuntime --max-old-space-size=16384 analysis\build_dataset_workbook.mjs --verify-assembled
& $pythonRuntime analysis\assemble_workbook.py --update-caches
& $pythonRuntime analysis\verify_saved_workbook.py
```

On another Codex host, obtain its current bundled runtime locations and replace these three path variables. The Windows dependency junction is ignored by Git and is not part of the portfolio. Do not copy the bundled libraries into the repository. The full workbook contains over two million source cells; generation and export need adequate memory.

The generator writes eight CSVs only after validation and two-run hash comparison pass. It also writes the dictionary, validation report and a typed JSON intermediate for the workbook builder. JSON intermediate and PNG previews are ignored by Git; retain the generator, configuration, builder and saved workbook for reproduction.

Artifact Tool cannot export the entire 93,044-row ledger in one operation because its exporter exceeds JavaScript's string-size limit. It authors the core workbook and ledger blocks separately. `assemble_workbook.py` packages these authored cells, types and styles into one native ledger sheet, then the complete saved workbook is re-imported and recalculated in Artifact Tool. The cache-update step records only the recalculated ledger count and revenue check in the existing formulas' cached values; it introduces no business formulas or hardcoded analysis.

The saved-workbook verifier compares every source cell with its CSV and checks dates, numbers, booleans, blanks, exported formulas, native tables and freeze panes. Render previews must also be inspected after building. Recalculation is verified in Artifact Tool, including temporary source edits followed by restoration. Native Microsoft Excel application behaviour has not been automated.

Regenerating overwrites the Phase 2 source files and resets the workbook to its Phase 2 dataset layout. After later phases add analysis, use a new checkout or back up the developed workbook before regenerating. Never silently replace an enriched model with the dataset-only version.

No headroom rankings, future scenarios, recommendations or experiment outcomes are produced by these commands. Phase 3 remains a separate analysis step.
