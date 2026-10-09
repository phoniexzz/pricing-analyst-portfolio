# Northstar Fitness: pricing growth with a visible member cost

## Problem

Which gyms should increase Standard membership prices, by how much, and under what conditions would additional revenue outweigh weaker recruitment and retention? I built a commercial analytics portfolio to answer that question for Northstar Fitness, a fictional operator with 80 mature UK gyms. The objective was sustainable revenue growth while protecting economically valuable members, rather than maximising a headline price.

## Business Context

The estate offers Standard, Off-Peak and Plus memberships and begins the historical window with 400,000 members. Its synthetic evidence covers January 2024 to December 2025. Consumer prices include VAT; financial analysis excludes an assumed 20% VAT. Subscription income, joining fees and ancillary revenue remain separate, because higher fees or ancillary sales can obscure weakening membership economics.

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

## My Approach

I established the commercial rules before generating evidence. New Standard joiners face increases immediately; eligible existing members receive the same cash increment after notice, with promotions protected until expiry. Legacy billed-rate differences remain intact. A Standard-to-Off-Peak downgrade reduces yield but does not remove the member.

I generated reproducible monthly records and a billing ledger, then reconciled acquisitions, cancellations, transfers, cohort retention and revenue. The workflow separates descriptive baseline analysis, relative headroom scoring, historical inference, future scenarios and conditional decisions. Each stage produces documented interfaces and validation evidence.

## Analysis

The baseline compares full-year 2025 with matching 2024 periods and adds Q4 context. Weighted rates use underlying exposure rather than averaging site percentages. A transparent headroom score combines competitor gaps, churn, conversion, acquisition, utilisation and income, while retaining caution flags separately.

Historical response comes primarily from twelve randomised pairs receiving a £2 increase. Acquisition elasticity is estimated separately from incumbent churn and downgrades, with whole-pair bootstrap intervals and exact assignment tests. Commercially selected increases are analysed separately because matching cannot eliminate selection bias.

The 2026 model preserves billing states and compares no increase, £1, £2 and £3 against the same seasonal counterfactual. Shared joint parameter draws preserve relationships between behavioural responses. An explicit policy framework translates the results into auditable conditional actions.

## Key Findings

Annual net revenue reached £107,006,933.85, up 2.37%, while December membership fell 0.67% to 396,311. The exact revenue bridge attributes −£425,763.94 to member volume and +£2,902,054.51 to total ARPMM, allocating the interaction to ARPMM. That yield contribution includes membership mix, fees and ancillary income; it cannot be attributed solely to pricing.

The historical pilot estimates an 8.27% reduction in Standard acquisition and a 0.345 percentage-point increase in monthly incumbent churn. Higher revenue therefore carries a measurable member cost. The evidence is local to the observed policy and positive-gap markets, with transport and pre-trend limitations.

## Recommendation

Saved actions comprise one RAISE £2, ten RAISE £1, five TEST FIRST, 26 HOLD PRICE and 38 DEFENSIVE / INVESTIGATE. All increases remain conditional on controlled testing. Positive revenue alone is insufficient: downside membership, uncertainty, competitor position, sensitivity and repeat-repricing evidence also matter.

A seven-pair £1 experiment demonstrates the next governance step. Five first-repricing pairs are primary; two repeat pairs are exploratory. The Main simulation produces EXTEND TEST at six months and STOP at twelve months. These simulated decisions illustrate the workflow and do not independently validate the forecast.

## Estimated Commercial Impact

The Base conditional RAISE-only portfolio models £148,618.48 additional annual net revenue and approximately 1,209 fewer December members versus no increase. Its conditional 95% parameter range is £64,400–£230,752. Provisional TEST FIRST gains are excluded. Revenue is not profit, and these ranges exclude future trading shocks and transport uncertainty.

## Tools Used

Python, NumPy and Pandas support generation, reconciliation, inference and simulation. SQLite adds fifteen independently validated commercial queries. Excel exposes billing and decision logic; Power BI communicates saved evidence through seven reviewed native layouts. An editable PowerPoint translates the work into a management narrative.

## What I Learned

Trustworthy pricing analysis requires consistent populations, timing, exposure and revenue boundaries. Member stocks are not unique customers; monthly retention is not annual retention. The most useful output is an explainable revenue/member trade-off with explicit uncertainty and conditions for learning, rather than a confident-looking universal price recommendation.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.
