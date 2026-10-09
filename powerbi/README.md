# Northstar Fitness commercial dashboard

**Phase 9 native verification complete.**

Open `gym_pricing_dashboard.pbip` in Power BI Desktop after following [SETUP.md](SETUP.md). The project contains six populated main pages and one hidden Gym Detail drill-through page, an Import semantic model, 296 explicit DAX measures, local CSV snapshot queries and a navy/teal theme.

The report displays saved Phase 3–8 evidence. It does not re-estimate price responses, rerank sites, change recommendations, rerun forecasts or change the Excel selectors. Only report filters and saved-case selections are interactive.

The 2025 revenue anchor is **£107,006,934**, December membership is **396,311**, and the Base conditional-raise portfolio adds **£148,618** net revenue with approximately **1,209 fewer December members**. Revenue is not profit. Base recommendations are one RAISE £2, ten RAISE £1, five TEST FIRST, 26 HOLD and 38 DEFENSIVE / INVESTIGATE. Provisional TEST FIRST gains are excluded from the raise portfolio.

Main primary simulated experiment findings remain **EXTEND TEST at six months** and **STOP at twelve months**. These simulations are not new independent evidence.

[Native acceptance checklist](NATIVE_VERIFICATION.md), [DAX check queries](DAX_checks.dax), [model dictionary](../analysis/powerbi_data_dictionary.csv), [measure dictionary](../analysis/powerbi_metric_dictionary.csv), [specification](../analysis/powerbi_dashboard_specification.md) and [validation report](../analysis/powerbi_validation.md).

Design previews are **not native Power BI screenshots**. They use the validated snapshot and illustrate default selections. Tables show readable leading records; the native definitions retain full fields and scrolling. The hidden detail preview uses NF049 as an example.

- [Executive Overview](../images/powerbi_p01_executive_overview.png)
- [Estate Pricing](../images/powerbi_p02_estate_pricing.png)
- [Customer & Member Behaviour](../images/powerbi_p03_customer_member_behaviour.png)
- [Pricing Scenarios](../images/powerbi_p04_pricing_scenarios.png)
- [Recommendations](../images/powerbi_p05_recommendations.png)
- [Experiment & Monitoring](../images/powerbi_p06_experiment_monitoring.png)
- [Gym Detail](../images/powerbi_p07_gym_detail.png)

Project formats follow [Microsoft PBIP external editing](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-external-editing), [PBIR report files](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report), [semantic-model files](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset), [TMDL](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview) and [star-schema guidance](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema).

This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.

This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.


Native acceptance record: [verification report](../analysis/powerbi_native_validation.md). Native screenshots are in `images/native_powerbi`, separate from design previews. Later project or snapshot refreshes require a new native check.
