# Phase 10: Management presentation

The deliverable is a ten-slide decision deck for Northstar Fitness's Pricing Manager, Commercial Director and CFO. It communicates the commercial evidence already established in Phases 3–8 and displayed in Phase 9. It adds no elasticity estimation, scenarios, rankings or pricing actions.

**What:** explain current trading, relative pricing evidence, the historical response, conditional site actions, portfolio economics and the planned experiment.

**Why:** positive revenue can coexist with weaker acquisition and more incumbent losses. Management needs to see both financial opportunity and the member cost before choosing a test.

**What the analyst learns:** how to turn a reconciled analysis into a short decision narrative, retaining adverse evidence and the distinctions that change interpretation.

**Decision supported:** whether management should resource a real controlled £1 pilot, investigate flagged gyms and gather stronger evidence before wider pricing implementation.

## Commercial narrative

2025 revenue increased 2.37%, despite a 0.67% decline in December membership. The exact descriptive bridge separates member volume from total ARPMM and assigns the interaction to ARPMM. The headroom score provides relative context, with baseline caution flags remaining separate.

The historical randomised £2 pilot estimates lower Standard acquisition, higher incumbent monthly churn and downgrades, alongside a positive controlled revenue difference. Its positive-gap sample and pre-trend imbalance limit transport to other sites.

The deck clearly separates scenarios affecting all 80 gyms from the selected conditional RAISE portfolio. Saved actions remain one RAISE £2, ten RAISE £1, five TEST FIRST, 26 HOLD PRICE and 38 DEFENSIVE / INVESTIGATE. The Base conditional RAISE portfolio adds £148,618.48 cumulative annual net revenue, with approximately 1,209 fewer December members. Its conditional 95% parameter range is £64,400–£230,752. Provisional TEST FIRST gains are excluded.

Seven pairs form the hypothetical £1 experiment, with five first-repricing pairs primary and two repeat pairs exploratory. The Main simulation remains EXTEND TEST at six months and STOP at twelve months. Simulations provide a workflow demonstration, not new independent evidence. The ten-slide deck ends with the requirements for a prospective real test and the remaining contribution-cost and service questions.

## Deliverables and reproducibility

- `presentation/pricing_recommendation.pptx`: ten slides, four native editable charts with embedded data snapshots, five editable evidence tables, and ten sets of speaker notes.
- `presentation/pricing_recommendation.pdf`: static image-based viewing copy of the reviewed saved-PPTX rendering.
- `presentation/presenter_notes.md`: management narrative, metric interpretation, evidence limits and sources by slide.
- `analysis/presentation_validation.json`: output identity, factual checks, source integrity and review evidence.

Run `python analysis/prepare_management_presentation.py`, then the bundled Node executable on `analysis/build_management_presentation.mjs`. The builder uses the established Arial/navy/teal style and bundled Artifact Tool. It finalizes to a new output name and does not overwrite an existing presentation. Supply an alternative filename as its first argument for a subsequent revision. After reviewing every saved-PPTX slide, run the bundled Python executable on `analysis/finish_management_presentation.py` to produce the PDF, notes and validation evidence. The PDF is a visual copy with raster pages. Use the PPTX to edit content.

Charts use twelve significant digits for portable embedded Excel data. The revenue bridge still reconciles within £0.01, while notes retain source monetary precision. Package and layout checks cover all ten slides. Visual review corrected negative-bar labels and the conditional-site list. Native Microsoft PowerPoint opening and rendering were not tested; this does not claim native acceptance analogous to Phase 9.

The source CSVs, generation and analysis configurations, Excel workbook, PBIP and PBIX are preserved. The workbook remains at 31 sheets. Phase 10 creates presentation artifacts rather than changing prior evidence or the scenario selector.

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.

Revenue is not profit. Monthly rates do not describe annual retention. Member stocks are not unique-customer counts. Annual earned revenue, 12-month modelled revenue and December annualised run-rate remain separate concepts. Forecast parameter ranges exclude future trading shocks and transport uncertainty. Phase 10 is complete once the output checks and visual review in the validation record pass. Phase 11 is portfolio/GitHub packaging.
