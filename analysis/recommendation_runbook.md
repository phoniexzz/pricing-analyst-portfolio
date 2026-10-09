# Phase 7 workbook and refresh guide

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.

## Controls and interpretation

The Recommendations sheet owns the policy inputs: B4 is the positive downside December member-loss limit (default 5%); B5 is the minimum post-increase competitor gap in VAT-inclusive GBP (default zero); B6 is the repeat-pricing test requirement (1=yes, 0=no). Numeric zero is valid. Missing or invalid inputs suppress authoritative outputs.

Actions always use named Base and Downside comparisons, independent of the existing Scenario Inputs case selector. Conditional RAISE increments are included in the portfolio; TEST FIRST amounts are provisional and excluded. HOLD PRICE and DEFENSIVE / INVESTIGATE keep current prices. The three point-case rows use the same selected mix. Their uncertainty range is common because it evaluates that mix under all 10,000 retained joint parameter draws, rather than providing a separate distribution for each point vector.

The primary gym table begins at row 20. Candidate evidence begins at row 130; source-linked context at row 350; prepared nonzero sensitivity revenues at row 900; policy-variant rules at row 1100; selected site/case portfolio inputs at row 1600. The summary's complete 15-row policy/case table begins at row 130. These rows show useful calculation steps; the independent verification area does not feed the recommendations.

## Policy edits and captures

Policy edits immediately recalculate candidate gates and actions. Portfolio point values update from the selected unchanged Scenario Comparison records. Captured ranges remain valid only while each variant's selected site/increment mix matches its captured mix. A changed mix hides that variant's ranges and shows a stale warning. A policy change that leaves the mix identical does not invalidate its draw distribution.

Save edits in Excel and close the workbook before running `analysis/refresh_recommendation_portfolio.py` with the bundled Python runtime. It reads the saved policy inputs, applies the same Python rules, aggregates the retained common draws, rebuilds the two owned sheets with Artifact Tool and preserves every other sheet/resource. It restores the existing case and price selection, saves current captures and leaves source/analyst-facing CSV evidence unchanged. Refresh both sheets together.

Stale Scenario Comparison captures, changes to evidence assumptions or any numeric manual behavioural override—including zero—make recommendations unavailable. Refreshing point scenarios cannot recreate evidence-derived uncertainty after a behavioural override. Rerun the Phase 6 analysis with revised assumptions before using intervals or authoritative recommendations; do not substitute retained ranges from another model.

The extended Phase 6 `refresh_scenario_comparison.py` replaces only its four owned sheets in a fresh current-workbook copy, retaining later sheets. It then refreshes Phase 7; unavailable evidence remains explicitly suppressed. It no longer reconstructs the final workbook from a 21-sheet snapshot.

## Reproduction and verification

Run `analysis/recommendation_analysis.py` from the project root to regenerate the three recommendation CSVs, documentation and figures from unchanged evidence and the fixed policy configuration. `--reproduce` verifies byte-identical CSV output. The original 10,000 draw file and prepared full-precision records in the Phase 6 audit directory are required. The classifier never reads latent generation behaviour or invents site elasticities.

Artifact Tool authors formulas, formatting, tables and charts in a bounded dependency segment. `package_recommendations.py` transfers the two owned sheets and recalculated caches into a fresh original workbook while preserving native features. It performs no business calculations. The saved-file verifier compares outputs with Python, checks keys, relationships, tables, source hashes and original resources, then extracts the actual saved formulas. `recalculate_recommendations_saved.mjs` recalculates that saved graph with Artifact Tool and tests edits and unavailable inputs. Native Microsoft Excel was not automated.

Phase 7 is a hypothetical 2026 commercial assessment. All increases require controlled testing before wider implementation. Phase 8 will design that experiment and its prospective conditions; no experiment outcome or rollout instruction is delivered here.
