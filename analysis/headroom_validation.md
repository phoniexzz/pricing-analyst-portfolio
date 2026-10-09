# Phase 4 validation

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

24 Python checks passed. 80 gym rows and 480 sensitivity rows. Sources, baseline CSVs and generation configuration retain their recorded SHA-256 hashes.

- PASS: 80 unique gym results
- PASS: 480 unique sensitivity records
- PASS: Complete monthly source coverage
- PASS: Complete December and value benchmark coverage
- PASS: 240 unique Q4 benchmark records
- PASS: December benchmark agrees with baseline
- PASS: All weights nonnegative and sum to one
- PASS: Components and scores bounded
- PASS: Contributions sum to score
- PASS: Each variant has ranks 1 to 80
- PASS: Caution flags preserved
- PASS: Investigation precedence
- PASS: High score boundary
- PASS: Constant and tied indicator ranks
- PASS: Reverse churn direction
- PASS: Binary floating-point tie tolerance
- PASS: Missing observations remain missing
- PASS: Missing weighted input blocks base score
- PASS: Zero-weight income does not block score
- PASS: Deterministic tied-score ranks
- PASS: Utilisation cap removes extra reward above capacity
- PASS: Segment rule branches
- PASS: Identical evaluation rerun
- PASS: Sources, baseline and generation configuration unchanged

Workbook reconciliation and visual review are recorded separately in headroom_workbook_verification.json.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.

## Completed workbook verification

- PASS: full assembled workbook imported and recalculated with Artifact Tool.
- PASS: 19,360 saved output cells match both CSV interfaces. Maximum engine difference is less than 0.000000005 in the stored units.
- PASS: 21,227 new formula caches present; no formula errors.
- PASS: original membership and revenue reconciliations remain valid.
- PASS: invalid weight totals, editable thresholds, valid weight transfers, dynamically ranked lists/chart schedules and missing-input propagation tested; all temporary edits restored.
- PASS: all original 16 sheets, style definitions and native features preserved, except the four authorised progress cells. Final workbook has 18 sheets.
- PASS: chart schedules match Python, filtered scatter observations remain blank, and all package relationships resolve.
- PASS: both new sheets, both affected guides, all three native charts and all three standalone visuals visually reviewed.
- PASS: both derived CSVs reproduce byte for byte using the final configuration.

Phase 4 is complete. Native desktop Excel was not automated; engine verification uses Artifact Tool and independent saved OOXML. Phase 5 remains separate.
