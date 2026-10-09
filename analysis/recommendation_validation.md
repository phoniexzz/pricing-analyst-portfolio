# Phase 7 Python validation

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.

- PASS: Shared 10000 whole-pair draws retained
- PASS: Site draw ordering matches sorted stable IDs
- PASS: Complete unique source scenario keys
- PASS: All source evidence finite shared draws
- PASS: Exact revenue tie chooses smaller increase
- PASS: Exact 5 percent downside boundary accepted
- PASS: Just beyond member boundary rejected
- PASS: Exact zero competitor gap accepted
- PASS: Negative competitor gap rejected
- PASS: Caution precedence high_churn_exception
- PASS: Caution precedence weak_conversion_exception
- PASS: Caution precedence declining_acquisition_exception
- PASS: Caution precedence peak_capacity_exception
- PASS: Missing decision evidence investigated
- PASS: Zero revenue is valid but does not qualify
- PASS: Zero sensitivity revenue rejects qualification
- PASS: Repeat precedence produces provisional test
- PASS: Repeat warning variant permits raise
- PASS: No qualifying candidates choose smallest plausible test
- PASS: No plausible candidates hold
- PASS: Zero denominator unavailable
- PASS: Policy refresh retains 3 percent variant
- PASS: Policy refresh retains competitor buffer variant
- PASS: Portfolio component reconciliation base/Base
- PASS: Portfolio member bridge base/Base
- PASS: Independent shared draw sum base/Base
- PASS: Portfolio component reconciliation base/Downside
- PASS: Portfolio member bridge base/Downside
- PASS: Independent shared draw sum base/Downside
- PASS: Portfolio component reconciliation base/Upside
- PASS: Portfolio member bridge base/Upside
- PASS: Independent shared draw sum base/Upside
- PASS: Portfolio component reconciliation member_limit_3pct/Base
- PASS: Portfolio member bridge member_limit_3pct/Base
- PASS: Independent shared draw sum member_limit_3pct/Base
- PASS: Portfolio component reconciliation member_limit_3pct/Downside
- PASS: Portfolio member bridge member_limit_3pct/Downside
- PASS: Independent shared draw sum member_limit_3pct/Downside
- PASS: Portfolio component reconciliation member_limit_3pct/Upside
- PASS: Portfolio member bridge member_limit_3pct/Upside
- PASS: Independent shared draw sum member_limit_3pct/Upside
- PASS: Portfolio component reconciliation member_limit_7pct/Base
- PASS: Portfolio member bridge member_limit_7pct/Base
- PASS: Independent shared draw sum member_limit_7pct/Base
- PASS: Portfolio component reconciliation member_limit_7pct/Downside
- PASS: Portfolio member bridge member_limit_7pct/Downside
- PASS: Independent shared draw sum member_limit_7pct/Downside
- PASS: Portfolio component reconciliation member_limit_7pct/Upside
- PASS: Portfolio member bridge member_limit_7pct/Upside
- PASS: Independent shared draw sum member_limit_7pct/Upside
- PASS: Portfolio component reconciliation competitor_buffer_1gbp/Base
- PASS: Portfolio member bridge competitor_buffer_1gbp/Base
- PASS: Independent shared draw sum competitor_buffer_1gbp/Base
- PASS: Portfolio component reconciliation competitor_buffer_1gbp/Downside
- PASS: Portfolio member bridge competitor_buffer_1gbp/Downside
- PASS: Independent shared draw sum competitor_buffer_1gbp/Downside
- PASS: Portfolio component reconciliation competitor_buffer_1gbp/Upside
- PASS: Portfolio member bridge competitor_buffer_1gbp/Upside
- PASS: Independent shared draw sum competitor_buffer_1gbp/Upside
- PASS: Portfolio component reconciliation allow_repeat_repricing/Base
- PASS: Portfolio member bridge allow_repeat_repricing/Base
- PASS: Independent shared draw sum allow_repeat_repricing/Base
- PASS: Portfolio component reconciliation allow_repeat_repricing/Downside
- PASS: Portfolio member bridge allow_repeat_repricing/Downside
- PASS: Independent shared draw sum allow_repeat_repricing/Downside
- PASS: Portfolio component reconciliation allow_repeat_repricing/Upside
- PASS: Portfolio member bridge allow_repeat_repricing/Upside
- PASS: Independent shared draw sum allow_repeat_repricing/Upside
- PASS: 80 unique recommendations
- PASS: 400 unique sensitivity keys
- PASS: 15 unique portfolio keys
- PASS: Five actions only
- PASS: All caution sites investigated
- PASS: No plus3 action or portfolio amount
- PASS: Tests excluded from portfolio increments
- PASS: Source and prior analysis hashes unchanged

## Saved workbook and workflow validation

- PASS: 27 populated sheets; all 25 earlier sheets and native resources preserved apart from authorised guidance updates.
- PASS: 11,740 independent saved-output comparisons covering all 80 gym recommendations, 400 policy decisions and 15 portfolios; maximum rounded-CSV difference £0.000494197, below the £0.01 revenue tolerance.
- PASS: 55,593 new formula caches; no saved formula errors; all relationships resolve and native table names are unique.
- PASS: Actual saved formulas recalculated using Artifact Tool; 1,710 independent checks with maximum difference £0.0000000298023.
- PASS: Eight saved-graph tests covering policy edits, stale intervals, valid zero inputs, missing inputs, named-case independence and manual behavioural overrides.
- PASS: Successful recommendation refresh, current captures, restoration of the existing scenario selector and preservation of all 27 sheets.
- PASS: Phase 6 refresh replacement plumbing accepts the 27-sheet workbook and preserves both later recommendation sheets. Its unchanged forecast engine was not redundantly rerun.
- PASS: Source and earlier-phase evidence hashes unchanged; all three recommendation CSVs reproduce byte-identically.
- PASS: Visual review of both new sheets, four native charts, all three commercial figures and final saved Overview/README guidance.

The formula graph checksum links the saved package to its recalculation evidence. `recommendation_workbook_verification.json` consolidates independent parity, recalculation, refresh, preservation and visual checks. Native Microsoft Excel was not automated; saved formulas and input-change behaviour were tested with Artifact Tool and unchanged saved source caches.

Phase 7 complete; Phase 8 next. No experiment outcome, final rollout threshold or instruction to implement prices is supplied.
