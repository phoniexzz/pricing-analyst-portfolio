# Phase 11 — Portfolio packaging validation

Phase 11 complete; Phase 12 next

Validated: 2026-10-06T12:47:08.613339+00:00
Case study: 740 words. Fifteen SQL queries passed all-field parity and 14 boundary/scope checks.
Protected checks: 50 records; 45 source/configuration/result files; 41 reporting snapshot files. Workbook: 31 sheets, unchanged.

| Archive | Files | Bytes | SHA-256 |
|---|---:|---:|---|
| northstar_portfolio.zip | 603 | 63,481,657 | 02a63000e8b1a841e00954588ec34c59d19ea9c44b7672eea7fa0a1d563ebf7e |
| northstar_reproduction.zip | 28 | 192,263,946 | 4ce4d27073c4acd41a5e5d461547a5a9af0b6a089f568248bdebec19147215b5 |

Largest ordinary package file: 31,909,335 bytes; every file is below 100 MiB.
Clean extracted-copy execution, supplemental restoration, accepted fingerprint, exact member boundaries, weighted rates, links and image files passed. Both ZIPs reproduced byte-for-byte.

Remaining limitations:
- Native PowerPoint rendering unverified
- PDF is image-based
- Native dashboard tables use scrolling
- Advanced historical builders require bundled Artifact Tool and adaptation of host-specific runtime/helper paths
- Protected workbook progress captions remain older; external guidance is current
