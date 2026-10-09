# Northstar Fitness — interview defence

**Phase 12 complete; interview preparation materials complete.** This is a written preparation pack for Pricing Analyst interviews. Completion of the materials does not establish your understanding or interview competence. Live mock practice is a separate follow-up.

## Use the pack

1. Practise the [opening pitch and two-minute story](story.md).
2. Learn the [quick-reference sheet](quick_reference.md), including definitions and evidence limits.
3. Work through the [thirty core questions](core_questions.md) and their technical follow-ups.
4. Defend the recommendation against [fifteen stakeholder challenges](stakeholder_challenges.md).
5. Rehearse the [five site examples and artifact demonstration](demonstration.md).
6. Use the [practice sequence and rubric](rehearsal.md) to check your understanding.

The [evidence register](evidence_register.json) records saved values, populations, windows, units, source row keys and rounding. The [validation record](validation.json) describes what was checked. It does not score a candidate's performance.

## Extract and reproduce

Extract `dist/northstar_interview_pack.zip` into the **existing portfolio root**, alongside `analysis/`, `data/`, `excel/`, `powerbi/` and `presentation/`. Alternatively, extract the Phase 11 portfolio and supplemental reproduction archives into a new directory, then overlay the interview pack there. The interview ZIP includes this folder, the new build/validation scripts and authorised README/progress-guidance updates. It does not replace commercial evidence or native deliverables. Source links are repository-relative and require the existing portfolio to be present.

The Phase 11 archives remain unchanged and retain their original Phase 11 README. This separate overlay supplies the current Phase 12 guidance. No GitHub publication or live rehearsal has occurred.

The overlay intentionally changes the root README, ignore rules and external progress guidance. Their current hashes therefore differ from the older Phase 11 file manifest. Use the Phase 12 check command and `INTERVIEW_MANIFEST.json` for this overlay; use the original Phase 11 archive manifests to verify an unmodified Phase 11 extraction. Protected commercial evidence remains unchanged in both.

From the portfolio root:

```powershell
python analysis/build_interview_pack.py --prepare
python analysis/build_interview_pack.py --check
```

Preparation uses only the Python standard library. It builds new interview access materials from saved evidence; it does not regenerate data, fit models or refresh native files. The optional visual-QA script requires the bundled Node, Marked and Playwright environment with Microsoft Edge:

```powershell
node analysis/render_interview_docs.mjs
```

After reviewing its rendered screenshots, the packaging workflow records visual acceptance and creates the local archive. Full protected-evidence verification requires the supplemental dependencies. Missing dependencies fail full validation rather than being treated as zero or verified. Archive SHA-256 is reported separately in `dist/phase12_validation.json`, avoiding a circular hash inside the archive manifest.

## Personal ownership and honest language

Say **“a synthetic portfolio project”**, not “a client engagement” or “an implemented commercial success”. Estimated uplift is modelled revenue, not money earned or profit. The experiment is simulated; it did not recruit real members.

Before interviewing, replace ownership prompts with your actual contribution. Explain any AI-assisted implementation, the decisions you made, checks you personally inspected and what you can independently reproduce. Do not claim to have manually written code, run native acceptance or made decisions you did not make. If you have not yet understood a method, say so and practise it rather than memorising a confident answer.

## Evidence status

Historical records are synthetic observations. Historical pilot effects are local estimates. Scenarios are conditional forecasts of expected memberships. Phase 7 actions are hypothetical and conditional. Phase 8 results are simulated workflow demonstrations. Power BI displays saved evidence; selectors do not rerun the forecast.

The accepted Power BI file and project fingerprint remain unchanged. The presentation was reviewed using Artifact Tool, but native PowerPoint rendering remains unverified. The workbook retains older embedded progress labels; current status is documented externally.

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
