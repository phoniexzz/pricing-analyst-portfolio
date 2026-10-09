"""Generate and verify Phase 2. Run with bundled Python; no workbook authoring here."""
from __future__ import annotations

import calendar
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(__file__).with_name("generation_config.json")
TIERS = ("Standard", "Off-Peak", "Plus")
DISCLAIMER = "This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses."
LONG_DISCLAIMER = "This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator."
REGIONS = {
    "London": ["London"] * 12,
    "South East": ["Reading", "Brighton", "Oxford", "Southampton", "Portsmouth", "Milton Keynes"] * 2,
    "South West": ["Bristol", "Bath", "Exeter", "Plymouth"] * 2,
    "North West": ["Manchester", "Liverpool", "Preston", "Bolton", "Chester", "Lancaster"] * 2,
    "Yorkshire": ["Leeds", "Sheffield", "York", "Bradford", "Hull"] * 2,
    "Midlands": ["Birmingham", "Nottingham", "Leicester", "Coventry", "Derby"] * 2,
    "Scotland": ["Glasgow", "Edinburgh", "Aberdeen", "Dundee"] * 2,
    "Wales": ["Cardiff", "Swansea", "Newport", "Wrexham"] * 2,
}
UNIVERSITY_CITIES = {"Oxford", "Bath", "Exeter", "Lancaster", "York", "Nottingham", "Leicester", "Coventry", "Dundee"}


def integer_allocation(total, weights):
    raw = total * np.asarray(weights) / np.sum(weights)
    counts = np.floor(raw).astype(int)
    counts[np.argsort(-(raw - counts), kind="stable")[:total - counts.sum()]] += 1
    return counts


def date_str(months, index):
    return (months[0] + pd.DateOffset(months=int(index))).strftime("%Y-%m-%d")


def standard_conversion(base_probability, price_ratio, elasticity, promotion):
    return float(np.clip(base_probability * price_ratio ** elasticity * (1 + 0.65 * promotion), 0.025, 0.48))


def churn_probability(base, uplift_fraction, sensitivity, lag):
    # Notification, implementation, then a delayed retention effect.
    profile = {0: 0.35, 1: 1.0, 2: 1.2, 3: 1.0, 4: 0.7, 5: 0.5}.get(lag, 0.3 if lag >= 6 else 0.0)
    return float(np.clip(base + sensitivity * uplift_fraction / 0.10 * profile, 0.006, 0.15))


def csv_bytes(frame):
    return frame.to_csv(index=False, na_rep="", float_format="%.8f", lineterminator="\n").encode("utf-8")


def generate(cfg):
    seed = cfg["seed"]
    site_rng = np.random.default_rng(np.random.SeedSequence([seed, 0]))
    event_rng = np.random.default_rng(np.random.SeedSequence([seed, 1]))
    assignment_rng = np.random.default_rng(np.random.SeedSequence([seed, 2]))
    months = pd.date_range(cfg["start_month"], periods=cfg["months"], freq="MS")
    sites, competitors, market_events = [], [], []
    for region, cities in REGIONS.items():
        for city in cities:
            index = len(sites)
            gid = f"NF{index + 1:03d}"
            affluence = float(np.clip(site_rng.normal(0.76 if region == "London" else 0.56 if region == "South East" else 0.37, 0.16), 0.05, 0.95))
            students = float(site_rng.uniform(0.19, 0.35) if city in UNIVERSITY_CITIES else site_rng.uniform(0.035, 0.17))
            quality = float(site_rng.uniform(0.35, 0.94))
            competition = int(site_rng.integers(2, 6) + (region == "London"))
            initial_price = round(float(np.clip(20 + 12 * affluence + site_rng.normal(0, 1.25), 20, 35))) - 0.01
            floor = int(site_rng.integers(160, 321)) * 100
            target = float(floor / 4.8 * site_rng.uniform(0.85, 1.18) * (1.10 if region == "London" else 1.0))
            elasticity = float(np.clip(-0.55 - 0.15 * competition - 1.0 * students + 0.65 * affluence + site_rng.normal(0, 0.16), *cfg["acquisition_elasticity_bounds"]))
            base_churn = float(np.clip(0.037 + 0.04 * students + 0.006 * (1 - quality) + site_rng.normal(0, 0.003), *cfg["opening_churn_bounds"]))
            site = dict(gym_id=gid, gym_name=f"Northstar {city} {sum(s['city'] == city for s in sites) + 1:02d}", city=city, region=region,
                        location_type="University town" if city in UNIVERSITY_CITIES else str(site_rng.choice(["City centre", "Urban residential", "Retail park"])),
                        opening_date=f"{int(site_rng.integers(2013, 2021))}-{int(site_rng.integers(1,13)):02d}-01",
                        floor_space_sqft=floor, capacity_proxy=int(round(floor / site_rng.uniform(100, 125))),
                        local_population=int(site_rng.integers(45000, 180001)), median_income=int(round(22000 + affluence * 32000)),
                        student_population_pct=round(students, 6), market_competitiveness="High" if competition >= 5 else "Medium" if competition >= 3 else "Low")
            # Private generation attributes are removed from the analyst-facing master.
            site.update(_affluence=affluence, _quality=quality, _competition=competition, _initial_price=initial_price,
                        _target=target, _elasticity=elasticity, _churn=base_churn,
                        _churn_sensitivity=float(site_rng.uniform(*cfg["churn_response_per_10pct_price_increase_bounds"])),
                        _conversion=float(np.clip(0.255 + 0.09 * quality - 0.12 * students, 0.21, 0.35)),
                        _visit_frequency=float(site_rng.uniform(5.1, 7.8)), _peak_factor=float(site_rng.uniform(2.6, 3.6)),
                        _promo_months=set(int(x) for x in event_rng.choice(np.arange(24), size=5, replace=False)),
                        _marketing_base=float(site_rng.uniform(2500, 6500)), _event=None)
            sites.append(site)
            for c in range(competition + (index % 10 == 0)):
                kind = "National value" if c == 0 else "National full-service" if c == 1 else "Local low-cost"
                cname = "PulseFit" if c == 0 else "Forge Fitness" if c == 1 else f"Local Motion {index+1:03d}-{c-1}"
                cid = f"{gid}_C{c+1:02d}"
                start = int(event_rng.integers(8, 21)) if c == competition else 0
                price = round(float(np.clip(initial_price + event_rng.normal(1.0, 2.2), 16.99, 39.99)), 2)
                change_month = int(event_rng.integers(max(4, start + 1), 24))
                delta = float(event_rng.choice([-2, -1, 1, 2]))
                promo_months = set(int(x) for x in event_rng.choice(np.arange(start, 24), size=2, replace=False))
                comp = dict(gym_id=gid, competitor_id=cid, competitor_name=cname, competitor_type=kind,
                            distance_km=round(float(event_rng.uniform(0.25, 2.95)), 2), joining_fee=float(event_rng.choice([0, 5, 10, 15])),
                            estimated_quality_score=round(float(event_rng.uniform(5.5, 9)), 1), start=start, initial_price=price,
                            change_month=change_month, delta=delta, promo_months=promo_months)
                competitors.append(comp)
                if start:
                    market_events.append(dict(gym_id=gid, competitor_id=cid, event_date=date_str(months, start), event_type="Competitor entry", old_price=None, new_price=price, promotion_value=0.0, description="Fictional local competitor begins trading within 3km."))
                market_events.append(dict(gym_id=gid, competitor_id=cid, event_date=date_str(months, change_month), event_type="Price cut" if delta < 0 else "Price increase", old_price=price, new_price=round(price + delta, 2), promotion_value=0.0, description="Recurring competitor Standard price changes."))
                for pm in sorted(promo_months):
                    market_events.append(dict(gym_id=gid, competitor_id=cid, event_date=date_str(months, pm), event_type="Promotion", old_price=None, new_price=None, promotion_value=5.0, description="One-month acquisition offer: £5 off the first month; recurring price unchanged."))

    opening = integer_allocation(cfg["opening_estate_members"], [s["_target"] for s in sites])
    pools, behaviours = {}, {}
    for i, site in enumerate(sites):
        gid = site["gym_id"]
        site["_opening"] = int(opening[i])
        behaviours[gid] = np.random.default_rng(np.random.SeedSequence([seed, 3, i]))
        mix = [0.68, 0.13 + site["student_population_pct"] * 0.10, 0.19 - site["student_population_pct"] * 0.10]
        tier_counts = integer_allocation(opening[i], mix)
        pools[gid] = {}
        for tier, count in zip(TIERS, tier_counts):
            rate = site["_initial_price"] + (cfg["offpeak_price_difference"] if tier == "Off-Peak" else cfg["plus_price_difference"] if tier == "Plus" else -2.0)
            cid = f"{gid}_LEGACY_{tier.replace('-', '').upper()}"
            pools[gid][(cid, tier)] = dict(count=int(count), join=-1, original=tier, base_rate=round(rate, 2), protected=-1, cohort_id=cid)
    comp_by_gym = {s["gym_id"]: [c for c in competitors if c["gym_id"] == s["gym_id"]] for s in sites}
    competitor_rows, monthly, ledger, history, assignments = [], [], [], [], []
    cohort_meta = {}
    season = np.asarray(cfg["monthly_demand_seasonality"])
    season = season / season.mean()

    def add_price_event(site, spec, m, pair_id=None):
        old = site["_initial_price"]
        site["_event"] = dict(month=m, increase=spec["increase_gross"], event_id=spec["event_id"], old=old)
        history.append(dict(gym_id=site["gym_id"], event_id=spec["event_id"], effective_date=date_str(months, m), notification_date=date_str(months, m),
                            existing_member_effective_date=date_str(months, m+1), old_price=old, new_price=round(old + spec["increase_gross"], 2),
                            change_amount=spec["increase_gross"], change_pct=spec["increase_gross"] / old,
                            reason="Historical matched-pair pilot" if pair_id else "Targeted increase using preceding six months' observed performance",
                            test_group="Treatment" if pair_id else "Targeted", control_group_flag=False, selection_method=spec["selection"], pair_id=pair_id))

    for m, month in enumerate(months):
        spec = next((e for e in cfg["historical_events"] if e["month_index"] == m), None)
        if spec:
            past = pd.DataFrame(monthly)
            eligible = [s for s in sites if s["_event"] is None]
            if spec["selection"] == "commercially_targeted":
                recent = past[past["month"] >= date_str(months, m-6)].groupby("gym_id").agg(competitor_price_gap=("competitor_price_gap", "mean"), peak_utilisation_pct=("peak_utilisation_pct", "mean"), acquisition_rate=("acquisition_rate", "mean"), churn_rate=("churn_rate", "mean"))
                z = (recent - recent.mean()) / recent.std(ddof=0)
                score = z["competitor_price_gap"] * 0.4 + z["peak_utilisation_pct"] * 0.25 + z["acquisition_rate"] * 0.2 - z["churn_rate"] * 0.15
                ranked = sorted(eligible, key=lambda s: (-score.loc[s["gym_id"]], s["gym_id"]))
                for site in ranked[:spec["gym_count"]]:
                    add_price_event(site, spec, m)
            else:
                recent = past[(past["month"] >= "2025-01-01") & (past["month"] <= "2025-03-01")]
                features = recent.groupby("gym_id").agg(price=("standard_price", "mean"), members=("average_members", "mean"), utilisation=("peak_utilisation_pct", "mean"), acquisition=("acquisition_rate", "mean"), churn=("churn_rate", "mean"), competition=("competitor_count_3km", "mean"))
                growth = recent.groupby("gym_id").apply(lambda f: f.iloc[-1]["closing_members"] / f.iloc[0]["opening_members"] - 1)
                features["historical_growth"] = growth
                z = (features - features.mean()) / features.std(ddof=0)
                candidates = {}
                for region in REGIONS:
                    group = [s for s in eligible if s["region"] == region]
                    pairs = []
                    while len(group) >= 2:
                        distances = [(float(np.sqrt(np.mean((z.loc[a["gym_id"]] - z.loc[b["gym_id"]]) ** 2))) + (0.25 if a["location_type"] != b["location_type"] else 0), a, b) for ia, a in enumerate(group) for b in group[ia+1:]]
                        distance, a, b = min(distances, key=lambda x: (x[0], x[1]["gym_id"], x[2]["gym_id"]))
                        pairs.append((distance, a, b))
                        group = [s for s in group if s["gym_id"] not in {a["gym_id"], b["gym_id"]}]
                    candidates[region] = pairs
                selected = [ps[0] for ps in candidates.values() if ps]
                remaining = sorted([p for ps in candidates.values() for p in ps[1:]], key=lambda x: x[0])
                selected += remaining[:spec["pair_count"]-len(selected)]
                for p, (distance, a, b) in enumerate(selected, 1):
                    pair_id = f"PAIR{p:02d}"
                    treatment, control = (a, b) if assignment_rng.integers(0,2) else (b, a)
                    add_price_event(treatment, spec, m, pair_id)
                    for site, arm in [(treatment, "Treatment"), (control, "Control")]:
                        row = dict(experiment_id=spec["event_id"], pair_id=pair_id, gym_id=site["gym_id"], test_group=arm, control_group_flag=arm == "Control", assignment_date=date_str(months,m), matching_window_start="2025-01-01", matching_window_end="2025-03-31", region=site["region"], location_type=site["location_type"], matching_distance=distance)
                        row.update({f"pre_{key}": float(value) for key, value in features.loc[site["gym_id"]].items()})
                        assignments.append(row)

        for site in sites:
            gid, rng = site["gym_id"], behaviours[site["gym_id"]]
            event = site["_event"]
            current_standard = site["_initial_price"] + (event["increase"] if event else 0)
            prices = {"Standard": current_standard, "Off-Peak": site["_initial_price"] - 5, "Plus": site["_initial_price"] + 5}
            active_comps = []
            for comp in comp_by_gym[gid]:
                if m < comp["start"]:
                    continue
                price = comp["initial_price"] + (comp["delta"] if m >= comp["change_month"] else 0)
                cr = {k: comp[k] for k in ("gym_id", "competitor_id", "competitor_name", "competitor_type", "distance_km", "joining_fee", "estimated_quality_score")}
                cr.update(month=date_str(months,m), competitor_standard_price=round(price,2), promotion_active=m in comp["promo_months"], promotion_value=5.0 if m in comp["promo_months"] else 0.0)
                competitor_rows.append(cr)
                active_comps.append(cr)
            comp_price = float(np.mean([c["competitor_standard_price"] for c in active_comps]))
            initial_comp_price = float(np.mean([c["initial_price"] for c in comp_by_gym[gid] if c["start"] == 0]))
            comp_effective = comp_price - float(np.mean([c["promotion_value"] for c in active_comps])) / 6
            opening_members = sum(p["count"] for p in pools[gid].values())
            promo = m in site["_promo_months"]
            discount = cfg["new_standard_promotion_discount"] if promo else 0.0
            marketing = round(site["_marketing_base"] * season[month.month-1] * float(rng.lognormal(0, 0.12)) * (1.15 if promo else 1), 2)
            student_season = 1 + site["student_population_pct"] * (1.2 if month.month == 9 else -0.7 if month.month in (6,7,8) else 0)
            leads_expected = site["_opening"] * site["_churn"] / site["_conversion"] * season[month.month-1] * student_season * (marketing / site["_marketing_base"]) ** 0.18 * (site["_opening"] / opening_members) ** 0.55 * (1 + 0.001 * m)
            entries = sum(c["start"] > 0 and c["start"] <= m for c in comp_by_gym[gid])
            leads = int(rng.poisson(leads_expected * (0.93 ** entries) * rng.lognormal(0,0.06)))
            share = np.array([0.68, 0.13 + site["student_population_pct"] * 0.10, 0.19 - site["student_population_pct"] * 0.10])
            relative_ratio = (current_standard / comp_effective) / (site["_initial_price"] / initial_comp_price)
            base_standard = site["_conversion"] * share[0] * np.clip((site["_initial_price"] / initial_comp_price) ** site["_elasticity"], 0.8, 1.2)
            standard_prob = standard_conversion(base_standard, relative_ratio, site["_elasticity"], discount)
            # Some prospects substitute into unchanged tiers instead of leaving the funnel.
            diversion = max(0, base_standard - standard_prob) * 0.25
            probabilities = [standard_prob, site["_conversion"] * share[1] + diversion, site["_conversion"] * share[2]]
            noise = float(rng.lognormal(0, 0.045))
            probabilities = [p * noise for p in probabilities]
            new_by_tier = rng.multinomial(leads, probabilities + [1 - sum(probabilities)])[:3]
            start_pools = {key: dict(p) for key, p in pools[gid].items() if p["count"] > 0}
            flow = {key: dict(opening=p["count"], new=0, old_cancel=0, new_cancel=0, incoming=0, outgoing=0) for key,p in start_pools.items()}
            for tier, count in zip(TIERS, new_by_tier):
                cid = f"{gid}_{month.strftime('%Y%m')}_{tier.replace('-', '').upper()}"
                key = (cid, tier)
                protected = m + cfg["promotion_protection_months"] - 1 if promo and tier == "Standard" else -1
                pool = dict(count=int(count), join=m, original=tier, base_rate=round(prices[tier],2), protected=protected, cohort_id=cid)
                pools[gid][key] = pool
                flow[key] = dict(opening=0, new=int(count), old_cancel=0, new_cancel=0, incoming=0, outgoing=0)
                cohort_meta[cid] = dict(gym_id=gid, cohort_id=cid, join_month=date_str(months,m), membership_type=tier, price_at_join=prices[tier], first_month_price=round(prices[tier]*(1-discount if protected >= m else 1),2), customers_joined=int(count), _join=m)
            for key, fl in list(flow.items()):
                pool = pools[gid][key]
                base_churn = site["_churn"] * (1.12 if pool["join"] >= 0 and m-pool["join"] < 3 else 1.0)
                if month.month in (6,7,8):
                    base_churn += site["student_population_pct"] * 0.009
                old_eligible = event and pool["join"] < event["month"] and key[1] == "Standard"
                lag = m-event["month"] if old_eligible else -1
                fraction = event["increase"] / pool["base_rate"] if old_eligible else 0
                if old_eligible and pool["protected"] >= m:
                    lag = 0
                p_cancel = churn_probability(base_churn, fraction, site["_churn_sensitivity"], lag)
                p_cancel = float(np.clip(p_cancel * rng.lognormal(0,0.06),0,0.20))
                fl["old_cancel"] = int(rng.binomial(fl["opening"], p_cancel))
                fl["new_cancel"] = int(rng.binomial(fl["new"], cfg["same_month_exit_probability"]))
                remaining = fl["opening"] + fl["new"] - fl["old_cancel"] - fl["new_cancel"]
                switch_prob = cfg["standard_monthly_downgrade_probability"] + (fraction * 0.055 if old_eligible and m >= event["month"] + 1 else 0)
                moved = int(rng.binomial(remaining, switch_prob)) if key[1] == "Standard" else 0
                if moved:
                    fl["outgoing"] = moved
                    destination = (key[0], "Off-Peak")
                    if destination not in pools[gid]:
                        pools[gid][destination] = dict(pool, count=0, base_rate=prices["Off-Peak"], protected=-1)
                    if destination not in flow:
                        flow[destination] = dict(opening=0,new=0,old_cancel=0,new_cancel=0,incoming=0,outgoing=0)
                    flow[destination]["incoming"] += moved
            month_rows = []
            for key, fl in flow.items():
                pool = pools[gid][key]
                closing = fl["opening"] + fl["new"] - fl["old_cancel"] - fl["new_cancel"] + fl["incoming"] - fl["outgoing"]
                pool["count"] = closing
                average = (fl["opening"] + closing) / 2
                eligible = bool(event and key[1] == "Standard" and pool["join"] < event["month"])
                applied = bool(eligible and m >= event["month"] + 1 and pool["protected"] < m)
                paid = pool["base_rate"] + (event["increase"] if applied else 0)
                actual_discount = cfg["new_standard_promotion_discount"] if key[1] == "Standard" and pool["protected"] >= m else 0
                paid = round(paid * (1-actual_discount),2)
                row = dict(gym_id=gid, month=date_str(months,m), cohort_id=key[0], join_month=date_str(months,pool["join"]) if pool["join"] >= 0 else None,
                           original_membership_type=pool["original"], membership_type=key[1], billing_bucket_id=f"{key[0]}_{key[1].replace('-', '').upper()}",
                           opening_members=fl["opening"], new_members=fl["new"], opening_base_cancellations=fl["old_cancel"], same_month_cancellations=fl["new_cancel"],
                           transfers_in=fl["incoming"], transfers_out=fl["outgoing"], closing_members=closing, average_members=average,
                           headline_price=round(prices[key[1]],2), base_billed_price=pool["base_rate"], billed_price=paid, promotion_discount_pct=actual_discount,
                           price_protected_until=date_str(months,pool["protected"]+1) if pool["protected"] >= 0 else None,
                           repricing_event_id=event["event_id"] if eligible else None, price_increment_applied=applied,
                           subscription_revenue=round(average * paid / (1+cfg["vat_rate"]),2))
                ledger.append(row)
                month_rows.append(row)
            cancelled = sum(r["opening_base_cancellations"] + r["same_month_cancellations"] for r in month_rows)
            old_cancel = sum(r["opening_base_cancellations"] for r in month_rows)
            new_cancel = sum(r["same_month_cancellations"] for r in month_rows)
            new_total = int(new_by_tier.sum())
            closing = sum(r["closing_members"] for r in month_rows)
            average = (opening_members + closing)/2
            subscription = round(sum(r["subscription_revenue"] for r in month_rows),2)
            fee_payers = int(rng.binomial(new_total, 0.15 if promo else 0.85))
            fee_revenue = round(fee_payers * cfg["joining_fee_gross"] / (1+cfg["vat_rate"]),2)
            ancillary = round((1200 + site["floor_space_sqft"]*0.085) * (0.97 + 0.03 * season[month.month-1]) / (1+cfg["vat_rate"]),2)
            total = round(subscription + fee_revenue + ancillary,2)
            visits = int(round(average * site["_visit_frequency"] * rng.lognormal(0,0.045)))
            opening_minutes = calendar.monthrange(month.year,month.month)[1] * 24 * 60
            avg_occupancy = visits * cfg["average_visit_duration_minutes"] / opening_minutes
            peak_occupancy = int(np.ceil(avg_occupancy * site["_peak_factor"]))
            complaints = int(rng.poisson(average / 1000 * (0.3 + (1.7 if event and 0 <= m-event["month"] <= 2 else 0))))
            row = dict(gym_id=gid,month=date_str(months,m),opening_members=opening_members,new_members=new_total,cancelled_members=cancelled,
                       opening_base_cancellations=old_cancel,same_month_cancellations=new_cancel,closing_members=closing,average_members=average,
                       standard_price=round(current_standard,2),offpeak_price=prices["Off-Peak"],premium_price=prices["Plus"],headline_price=round(current_standard,2),
                       subscription_revenue=subscription,joining_fee_revenue=fee_revenue,ancillary_revenue=ancillary,monthly_revenue=total,
                       realised_ARPMM=total/average,subscription_yield=subscription/average,acquisition_rate=new_total/opening_members,churn_rate=old_cancel/opening_members,
                       retention_rate=1-old_cancel/opening_members,conversion_rate=new_total/leads,qualified_prospects=leads,website_leads=int(round(leads*0.82)),
                       trial_visits=int(round(leads*0.18)),gym_visits=visits,visits_per_member=visits/average,utilisation_pct=avg_occupancy/site["capacity_proxy"],
                       peak_utilisation_pct=peak_occupancy/site["capacity_proxy"],average_concurrent_attendance=avg_occupancy,peak_concurrent_attendance=peak_occupancy,
                       opening_minutes=opening_minutes,average_visit_duration_minutes=cfg["average_visit_duration_minutes"],marketing_spend=marketing,promotion_active=promo,
                       promotion_discount_pct=discount,joining_fee=cfg["joining_fee_gross"],joining_fee_payers=fee_payers,pricing_complaints=complaints,
                       pricing_complaints_per_1000_members=complaints/average*1000,competitor_count_3km=len(active_comps),nearest_competitor_distance_km=min(c["distance_km"] for c in active_comps),
                       local_competitor_avg_price=comp_price,competitor_price_gap=comp_price-current_standard)
            for tier, prefix in zip(TIERS,("standard","offpeak","premium")):
                tr = [r for r in month_rows if r["membership_type"] == tier]
                av = sum(r["average_members"] for r in tr)
                row[f"{prefix}_members"] = sum(r["closing_members"] for r in tr)
                row[f"average_{prefix}_members"] = av
                row[f"{prefix}_subscription_revenue"] = round(sum(r["subscription_revenue"] for r in tr),2)
                row[f"{prefix}_realised_yield"] = row[f"{prefix}_subscription_revenue"]/av
            monthly.append(row)

    frames = dict(monthly_performance=pd.DataFrame(monthly),competitor_prices=pd.DataFrame(competitor_rows),pricing_history=pd.DataFrame(history),
                  membership_ledger=pd.DataFrame(ledger),experiment_assignments=pd.DataFrame(assignments),market_events=pd.DataFrame(market_events))
    observations = frames["membership_ledger"].groupby(["cohort_id","month"])[["closing_members","average_members","subscription_revenue"]].sum()
    cohorts = []
    for cid, meta in cohort_meta.items():
        cohort = {k:v for k,v in meta.items() if not k.startswith("_")}
        j, n = meta["_join"], meta["customers_joined"]
        obs = observations.loc[cid]
        cohort["observation_months"] = 24-j
        for label, age in [("30d",1),("90d",3),("180d",6)]:
            cohort[f"customers_remaining_{label}"] = int(obs.loc[date_str(months,j+age),"closing_members"]) if j+age < 24 else None
        cohort["average_tenure"] = float(obs["average_members"].sum()/n) if n else None
        for horizon in (6,12):
            cohort[f"revenue_{horizon}_month"] = round(float(obs.iloc[:horizon]["subscription_revenue"].sum()),2) if 24-j >= horizon else None
        cohorts.append(cohort)
    frames["cohorts"] = pd.DataFrame(cohorts)
    snapshot = frames["monthly_performance"].query("month == '2025-12-01'").set_index("gym_id")
    master = []
    for site in sites:
        row = {k:v for k,v in site.items() if not k.startswith("_")}
        s = snapshot.loc[site["gym_id"]]
        row.update(gym_age_years=round((pd.Timestamp("2025-12-31")-pd.Timestamp(site["opening_date"])).days/365.25,2), snapshot_date="2025-12-31")
        for field in ("competitor_count_3km","nearest_competitor_distance_km","local_competitor_avg_price","competitor_price_gap","utilisation_pct","peak_utilisation_pct"):
            row[field] = int(s[field]) if field == "competitor_count_3km" else float(s[field])
        row.update(current_standard_price=float(s["standard_price"]),current_offpeak_price=float(s["offpeak_price"]),current_premium_price=float(s["premium_price"]))
        local = frames["competitor_prices"][(frames["competitor_prices"]["gym_id"] == site["gym_id"]) & (frames["competitor_prices"]["month"] == "2025-12-01")]
        row["PureGym_equivalent_price"] = float(local.loc[local["competitor_type"] == "National value","competitor_standard_price"].iloc[0])
        row["JD_equivalent_price"] = float(local.loc[local["competitor_type"] == "National full-service","competitor_standard_price"].iloc[0])
        row["market_competitiveness"] = "High" if row["competitor_count_3km"] >= 5 else "Medium" if row["competitor_count_3km"] >= 3 else "Low"
        master.append(row)
    frames["gym_master"] = pd.DataFrame(master)
    for name, frame in frames.items():
        keys = {"gym_master":["gym_id"],"monthly_performance":["gym_id","month"],"competitor_prices":["gym_id","competitor_id","month"],"pricing_history":["gym_id","event_id"],"cohorts":["gym_id","join_month","membership_type"],"membership_ledger":["gym_id","month","billing_bucket_id"],"experiment_assignments":["experiment_id","gym_id"],"market_events":["gym_id","competitor_id","event_date","event_type"]}[name]
        frames[name] = frame.sort_values(keys,kind="stable").reset_index(drop=True)
    return frames


def validate(frames, cfg):
    """Independent table-level reconciliation and boundary checks; failures stop delivery."""
    checks = []
    def check(name, condition):
        passed = bool(condition)
        checks.append(dict(check=name,passed=passed))
        if not passed:
            raise AssertionError(name)
    m, l, g, c, h, a, e, k = (frames[n] for n in ("monthly_performance","membership_ledger","gym_master","cohorts","pricing_history","experiment_assignments","market_events","competitor_prices"))
    keys = {"gym_master":["gym_id"],"monthly_performance":["gym_id","month"],"competitor_prices":["gym_id","competitor_id","month"],"pricing_history":["gym_id","event_id"],"cohorts":["gym_id","join_month","membership_type"],"membership_ledger":["gym_id","month","billing_bucket_id"],"experiment_assignments":["experiment_id","gym_id"],"market_events":["gym_id","competitor_id","event_date","event_type"]}
    check("80 unique gyms and 1,920 complete consecutive gym-months",len(g)==80 and g.gym_id.nunique()==80 and len(m)==1920 and all(m.groupby("gym_id").month.apply(list).apply(lambda v:v==list(pd.date_range(cfg['start_month'],periods=24,freq='MS').strftime('%Y-%m-%d')))))
    check("Every gym mature at observation start",(pd.to_datetime(g.opening_date) < pd.Timestamp("2022-01-01")).all())
    check("Unique non-null declared primary keys",all(not f.duplicated(keys[n]).any() and f[keys[n]].notna().all().all() for n,f in frames.items()))
    check("All foreign gym keys exist",all(set(f.gym_id).issubset(set(g.gym_id)) for f in frames.values()))
    check("Exact 400,000 opening members",m.loc[m.month==cfg['start_month'],'opening_members'].sum()==cfg['opening_estate_members'])
    check("Estate member stock remains within 300,000–500,000",m.groupby('month').closing_members.sum().between(300000,500000).all())
    check("Gym member bridges and monthly continuity",(m.closing_members==m.opening_members+m.new_members-m.cancelled_members).all() and (m.groupby('gym_id').closing_members.shift(1).dropna().to_numpy()==m.loc[m.month!='2024-01-01','opening_members'].to_numpy()).all())
    check("Ledger bridges and exposures",(l.closing_members==l.opening_members+l.new_members-l.opening_base_cancellations-l.same_month_cancellations+l.transfers_in-l.transfers_out).all() and (l.average_members==(l.opening_members+l.closing_members)/2).all())
    check("Cancellations eligible and member counts non-negative",(l.opening_base_cancellations<=l.opening_members).all() and (l.same_month_cancellations<=l.new_members).all() and (l[['opening_members','new_members','closing_members','transfers_in','transfers_out']]>=0).all().all())
    previous=l.groupby('billing_bucket_id').closing_members.shift(1).fillna(0)
    legacy_first=(l.month=='2024-01-01') & l.join_month.isna()
    check("Every billing bucket carries its own closing membership forward",np.array_equal(previous.loc[~legacy_first].to_numpy(),l.loc[~legacy_first,'opening_members'].to_numpy()))
    count_fields=['opening_members','new_members','opening_base_cancellations','same_month_cancellations','closing_members','transfers_in','transfers_out']
    check("Member movement counts are integers",np.equal(l[count_fields],np.floor(l[count_fields])).all().all())
    sums = l.groupby(['gym_id','month'])[['opening_members','new_members','closing_members','average_members','opening_base_cancellations','same_month_cancellations','transfers_in','transfers_out','subscription_revenue']].sum()
    mi = m.set_index(['gym_id','month']).loc[sums.index]
    check("Ledger rolls up to gym member counts",all(np.array_equal(sums[col].to_numpy(),mi[col].to_numpy()) for col in ('opening_members','new_members','closing_members','average_members','opening_base_cancellations','same_month_cancellations')) and (sums.transfers_in==sums.transfers_out).all())
    check("Tier member totals and tier subscription revenue reconcile",(m[['standard_members','offpeak_members','premium_members']].sum(axis=1)==m.closing_members).all() and np.allclose(m[['standard_subscription_revenue','offpeak_subscription_revenue','premium_subscription_revenue']].sum(axis=1),m.subscription_revenue,atol=.011,rtol=0))
    check("Ledger subscription revenue reconciles",np.allclose(sums.subscription_revenue,mi.subscription_revenue,atol=.011,rtol=0))
    check("Revenue components, VAT and ARPMM reconcile",np.allclose(m.subscription_revenue+m.joining_fee_revenue+m.ancillary_revenue,m.monthly_revenue,atol=.011,rtol=0) and np.allclose(m.realised_ARPMM*m.average_members,m.monthly_revenue,atol=.011,rtol=0) and np.allclose(l.average_members*l.billed_price/(1+cfg['vat_rate']),l.subscription_revenue,atol=.00501,rtol=0))
    check("Acquisition, conversion and opening-base churn rates reconcile",np.allclose(m.new_members/m.qualified_prospects,m.conversion_rate) and np.allclose(m.opening_base_cancellations/m.opening_members,m.churn_rate) and np.allclose(m.new_members/m.opening_members,m.acquisition_rate) and np.allclose(m.retention_rate,1-m.churn_rate) and (m.new_members<=m.qualified_prospects).all() and (m.trial_visits<=m.website_leads).all() and (m.website_leads<=m.qualified_prospects).all())
    check("Attendance utilisation derived from visits and capacity",np.allclose(m.average_concurrent_attendance,m.gym_visits*m.average_visit_duration_minutes/m.opening_minutes) and np.allclose(m.utilisation_pct,m.average_concurrent_attendance/m.gym_id.map(g.set_index('gym_id').capacity_proxy)) and (m.peak_utilisation_pct>=m.utilisation_pct).all())
    check("32 actual price events; no zero changes or repeated site events",len(h)==32 and h.gym_id.nunique()==32 and (h.change_amount>0).all() and np.allclose(h.new_price-h.old_price,h.change_amount) and np.allclose(h.change_pct,h.change_amount/h.old_price))
    hm = h.set_index('gym_id')
    for _, row in h.iterrows():
        site_months = m[m.gym_id==row.gym_id]
        assert (site_months.loc[site_months.month<row.effective_date,'standard_price']==row.old_price).all()
        assert (site_months.loc[site_months.month>=row.effective_date,'standard_price']==row.new_price).all()
        assert pd.Timestamp(row.existing_member_effective_date)==pd.Timestamp(row.effective_date)+pd.DateOffset(months=1)
    check("Headline changes and one-month notice match event history",True)
    elig = l[l.repricing_event_id.notna()].copy()
    hist = hm.loc[elig.gym_id]
    expected_applied = (elig.month.to_numpy()>=hist.existing_member_effective_date.to_numpy()) & (elig.price_protected_until.isna().to_numpy() | (elig.month.to_numpy()>=elig.price_protected_until.fillna('').to_numpy()))
    check("Existing-member repricing eligibility and protected promotions",np.array_equal(elig.price_increment_applied.to_numpy(),expected_applied) and ((l.month>=l.price_protected_until.fillna('')) | ~l.price_increment_applied).all())
    expected = l.base_billed_price.to_numpy().copy()
    ids = l.price_increment_applied
    expected[ids] += l.loc[ids,'gym_id'].map(hm.change_amount).to_numpy()
    expected = np.round(expected*(1-l.promotion_discount_pct.to_numpy()),2)
    check("Billed rate applies eligible cash increase exactly once",np.allclose(expected,l.billed_price,atol=.001,rtol=0) and not l.loc[l.join_month.notna() & l.gym_id.isin(h.gym_id)].apply(lambda row: row.join_month>=hm.loc[row.gym_id,'effective_date'] and row.price_increment_applied,axis=1).any())
    check("12 randomised matched treatment/control pairs",len(a)==24 and a.test_group.value_counts().to_dict()=={'Treatment':12,'Control':12} and (a.groupby('pair_id').size()==2).all() and (a.groupby('pair_id').test_group.nunique()==2).all() and (a.matching_window_end<a.assignment_date).all())
    controls=set(a.loc[a.control_group_flag,'gym_id'])
    check("Historical controls remain unrepriced",not controls.intersection(set(h.gym_id)))
    cohort_joins=c.groupby(['gym_id','join_month']).customers_joined.sum()
    check("Cohort acquisitions reconcile and all three origin tiers present",len(c)==5760 and np.array_equal(cohort_joins.to_numpy(),m.set_index(['gym_id','month']).loc[cohort_joins.index,'new_members'].to_numpy()))
    co = l[l.join_month.notna()].groupby(['cohort_id','month']).closing_members.sum()
    check("Cohort survivors never rise after joining",(co.groupby(level=0).diff().dropna()<=0).all())
    cohort_obs=l[l.join_month.notna()].groupby(['cohort_id','month'])[['closing_members','subscription_revenue','average_members']].sum()
    for _, row in c.iterrows():
        j = pd.Timestamp(row.join_month)
        obs=cohort_obs.loc[row.cohort_id]
        for label,age in [('30d',1),('90d',3),('180d',6)]:
            target=(j+pd.DateOffset(months=age)).strftime('%Y-%m-%d')
            value=row[f'customers_remaining_{label}']
            assert (pd.isna(value) if target>'2025-12-01' else value==obs.loc[target,'closing_members'])
        for horizon in (6,12):
            value=row[f'revenue_{horizon}_month']
            assert pd.isna(value) if row.observation_months<horizon else abs(value-obs.iloc[:horizon].subscription_revenue.sum())<.011
    check("Observed cohort milestones and revenues reconcile; immature outputs blank",True)
    snap=m[m.month=='2025-12-01'].set_index('gym_id').loc[g.gym_id]
    check("December master snapshot matches monthly records",np.allclose(g.current_standard_price,snap.standard_price) and np.allclose(g.competitor_price_gap,snap.competitor_price_gap) and np.allclose(g.utilisation_pct,snap.utilisation_pct) and np.array_equal(g.competitor_count_3km,snap.competitor_count_3km))
    for _,row in e.iterrows():
        cr=k[(k.competitor_id==row.competitor_id)&(k.month==row.event_date)]
        assert len(cr)==1
        if row.event_type=='Competitor entry':
            assert not (k[(k.competitor_id==row.competitor_id)].month<row.event_date).any()
        if row.event_type in ('Price cut','Price increase','Competitor entry'):
            assert cr.iloc[0].competitor_standard_price==row.new_price
        if row.event_type=='Promotion':
            assert cr.iloc[0].promotion_active and cr.iloc[0].promotion_value==row.promotion_value
    check("Competitor entry, prices and promotional events align",True)
    check("No analyst-facing assumed elasticity or opportunity rankings",all(not any('elasticity' in col.lower() or 'headroom' in col.lower() or 'recommendation' in col.lower() for col in f.columns) for f in frames.values()))
    check("Controlled higher-price conversion response",standard_conversion(.20,1.10,-.8,0)<standard_conversion(.20,1,-.8,0))
    check("Controlled promotion improves conversion",standard_conversion(.20,1,-.8,.2)>standard_conversion(.20,1,-.8,0))
    check("Controlled existing-member price response increases churn",churn_probability(.04,.08,.008,2)>churn_probability(.04,0,.008,2))
    check("Lagged churn is distinct from notification response",churn_probability(.04,.08,.008,2)>churn_probability(.04,.08,.008,0))
    check("Equivalent relative price rise from competitor cut reduces conversion",standard_conversion(.20,25/23,-.8,0)<standard_conversion(.20,1,-.8,0))
    return checks


DESCRIPTIONS = {
    'gym_id':'Stable Northstar home-gym identifier; foreign key to Gym Master.', 'gym_name':'Fictional Northstar site name.', 'city':'Real UK city name; every associated demographic and commercial value is synthetic.', 'region':'UK regional market; Midlands is a combined region.', 'location_type':'Commercial catchment type.',
    'opening_date':'Fictional site opening date; before January 2022.', 'gym_age_years':'Age at 31 December 2025, using days divided by 365.25.', 'floor_space_sqft':'Synthetic total floor space.', 'capacity_proxy':'Comfortable simultaneous attendance proxy; not a legal or hard occupancy limit.', 'local_population':'Synthetic catchment population, not official census data.', 'median_income':'Synthetic annual local median income, not a sourced statistic.', 'student_population_pct':'Synthetic proportion of students in the local population.',
    'competitor_count_3km':'Active fictional low-cost competitors within 3km in this observation month or master snapshot.', 'nearest_competitor_distance_km':'Distance to nearest active fictional competitor.', 'market_competitiveness':'High for five or more competitors, Medium for three or four, Low for fewer than three; snapshot description, not pricing-opportunity segmentation.',
    'current_standard_price':'December 2025 advertised Standard recurring consumer price.', 'current_offpeak_price':'December 2025 advertised Off-Peak recurring consumer price.', 'current_premium_price':'December 2025 advertised Plus recurring consumer price; premium is the compatibility column label.', 'PureGym_equivalent_price':'Fictional PulseFit proxy price; contains no actual PureGym observation.', 'JD_equivalent_price':'Fictional Forge Fitness proxy price; contains no actual JD Gyms observation.', 'local_competitor_avg_price':'Arithmetic mean of active fictional low-cost recurring Standard prices within 3km; excludes joining fees and introductory promotions.', 'competitor_price_gap':'Comparable competitor recurring price mean minus Northstar advertised Standard price; positive means Northstar is cheaper.',
    'snapshot_date':'Master pricing and competition as-of date; utilisation represents December monthly attendance.', 'month':'First day of observation month; monthly key.', 'opening_members':'Active memberships at start of month.', 'new_members':'Activations during month; includes rejoiners but excludes tier transfers.', 'cancelled_members':'All exits effective in month, including same-month join-and-exit members; excludes transfers.', 'opening_base_cancellations':'Exits among members active at the start of month; churn numerator.', 'same_month_cancellations':'Members joining and exiting in the same month; excluded from opening-base churn.', 'closing_members':'Active memberships at end of month.', 'average_members':'Midpoint of opening and closing memberships; approximate member-month exposure.',
    'standard_members':'Closing Standard memberships.', 'offpeak_members':'Closing Off-Peak memberships.', 'premium_members':'Closing Plus memberships.', 'standard_price':'Advertised Standard recurring consumer price in observation month.', 'offpeak_price':'Advertised Off-Peak recurring consumer price.', 'premium_price':'Advertised Plus recurring consumer price.', 'headline_price':'Standard advertised price in Monthly Performance; current tier advertised price in Membership Ledger.', 'realised_ARPMM':'Total net revenue divided by average members; includes fees and ancillary revenue.', 'subscription_yield':'Net subscription revenue divided by average members; excludes fees and ancillary revenue.', 'monthly_revenue':'Total net subscription, joining-fee and ancillary revenue for the gym-month.', 'subscription_revenue':'Net subscription revenue: midpoint membership exposure times billed consumer price divided by 1.20, rounded per ledger row.', 'joining_fee_revenue':'Net joining fee revenue; recognised in joining month as a portfolio simplification.', 'ancillary_revenue':'Synthetic net ancillary revenue driven by site floor area and seasonality; separately disclosed.',
    'acquisition_rate':'New members divided by opening members.', 'churn_rate':'Opening-base cancellations divided by opening members.', 'retention_rate':'One minus opening-base churn; not joiner cohort retention.', 'conversion_rate':'New members divided by qualified prospects.', 'qualified_prospects':'Unique prospects covering all joining channels and all new activations in the monthly funnel.', 'website_leads':'Website subset of qualified prospects; not the conversion denominator.', 'trial_visits':'Trial subset of website leads; do not add to leads or prospects.', 'gym_visits':'Member visits during month.', 'visits_per_member':'Gym visits divided by average members.', 'utilisation_pct':'Average concurrent attendance divided by comfortable concurrent capacity proxy.', 'peak_utilisation_pct':'Estimated peak concurrent attendance divided by same proxy; values above 100% indicate pressure on comfortable capacity.', 'average_concurrent_attendance':'Visits times visit duration divided by opening minutes.', 'peak_concurrent_attendance':'Average concurrent attendance times a site-specific peak multiplier, rounded upward.', 'opening_minutes':'24-hour opening minutes in calendar month.', 'average_visit_duration_minutes':'Assumed mean duration of each attendance visit.',
    'marketing_spend':'Synthetic monthly marketing spend; expense, not a revenue deduction in this dataset.', 'promotion_active':'Northstar new-joiner promotion active in observation month, or competitor first-month offer active in Competitor Pricing.', 'promotion_discount_pct':'20% discount on two protected billing months for Standard joiners in a Northstar promotional month; Ledger shows actual applicable discount.', 'joining_fee':'Advertised consumer joining fee; waivers reflected in payer count or competitor promotion disclosures.', 'joining_fee_payers':'Number of new members paying the joining fee; other joiners receive a fee waiver.', 'pricing_complaints':'Pricing-related complaints recorded in month; no missing collection months in this clean synthetic dataset.', 'pricing_complaints_per_1000_members':'Pricing complaints divided by average members times 1,000.',
    'competitor_id':'Stable fictional competitor identifier within a gym catchment.', 'competitor_name':'Fictional competitor brand or local site label.', 'competitor_type':'National value, National full-service or Local low-cost archetype; all treated as comparable low-cost alternatives.', 'distance_km':'Synthetic distance from Northstar gym; constant per competitor.', 'competitor_standard_price':'Advertised recurring Standard consumer price, excluding joining fees and introductory offers.', 'promotion_value':'Competitor first-month monetary discount; not a recurring monthly reduction.', 'estimated_quality_score':'Synthetic relative quality score on a ten-point scale.',
    'event_id':'Stable historical Northstar price intervention ID; may cover multiple gyms.', 'effective_date':'First day new joiners face increased Standard headline price.', 'notification_date':'Date existing eligible members are notified; coincides with headline intervention.', 'existing_member_effective_date':'Earliest existing-member implementation date, one full month after notification; promotions may postpone it.', 'old_price':'Pre-change recurring consumer price; Market Events leaves it blank for entry or promotion.', 'new_price':'Post-change recurring consumer price; Market Events leaves it blank for promotion-only events.', 'change_amount':'Monthly Standard consumer cash increment.', 'change_pct':'Cash increment divided by old headline price.', 'reason':'Commercial rationale or controlled-pilot description; not a final project recommendation.', 'test_group':'Treatment or Control in pilot; Targeted for commercially selected historical changes.', 'control_group_flag':'True only for unchanged historical pilot control assignments; actual Pricing History rows are all false.', 'selection_method':'Commercially targeted using pre-event data, or randomised within matched pairs.', 'pair_id':'Historical matched-pair ID; blank for targeted interventions.',
    'cohort_id':'Stable original gym–joining month–original tier identity; legacy identity has unknown join date.', 'join_month':'Original join month; blank only for opening legacy members in Ledger.', 'membership_type':'Current tier in Ledger, original joining tier in Cohorts. Plus is the premium product.', 'original_membership_type':'Tier at original acquisition; unchanged after tier migration.', 'price_at_join':'Advertised recurring consumer tier price before introductory discount.', 'first_month_price':'Actual consumer recurring price during first promotional or full-price month, excluding joining fee.', 'customers_joined':'Original number of acquisitions in joining cohort; all later switches remain assigned to this origin cohort.', 'customers_remaining_30d':'Survivors one calendar month after joining month; monthly approximation, not exact-day retention.', 'customers_remaining_90d':'Survivors three calendar months after joining month; monthly approximation.', 'customers_remaining_180d':'Survivors six calendar months after joining month; monthly approximation.', 'average_tenure':'Observed midpoint member-month exposure summed over all tiers divided by original joins; censored restricted mean, not completed lifetime tenure.', 'revenue_6_month':'Observed net subscription revenue over joining month and next five months; blank if incomplete.', 'revenue_12_month':'Observed net subscription revenue over joining month and next eleven months; blank if incomplete.', 'observation_months':'Available observation months from joining month through December 2025 inclusive.',
    'billing_bucket_id':'Stable cohort–current-tier billing state; all members in bucket share applicable billed-rate rules.', 'transfers_in':'Internal membership-tier arrivals; excluded from acquisitions.', 'transfers_out':'Internal tier departures; excluded from cancellations.', 'base_billed_price':'Gross recurring rate before protected discount and eligible historical cash increase; includes initial legacy discount or joining-date headline rate.', 'billed_price':'Applicable gross recurring paid rate after discount and eligible cash increase, per full member-month.', 'price_protected_until':'Exclusive month-start expiry of protected introductory price; blank if no protection.', 'repricing_event_id':'Historical event affecting members acquired before its headline date and still on Standard; blank otherwise.', 'price_increment_applied':'Whether eligible existing members have completed notice and protection periods; does not denote a new monthly compounding increment.',
    'experiment_id':'Historical matched-pair pilot identifier.', 'assignment_date':'Date of treatment/control random assignment and intervention.', 'matching_window_start':'First day of pre-assignment matching window.', 'matching_window_end':'Last day of matching window, before assignment.', 'matching_distance':'Root-mean-square distance across standardised matching features, plus 0.25 for different location types; descriptive, not a test result.', 'event_date':'Effective date of competitor market event.', 'event_type':'Competitor entry, recurring price change or introductory promotion.', 'description':'Plain-language fictional market event description.',
}


def dictionary(frames):
    rows=[]
    grain = {'gym_master':'Gym snapshot','monthly_performance':'Gym-month','competitor_prices':'Gym-competitor-month','pricing_history':'Gym-event','cohorts':'Gym-join month-original tier','membership_ledger':'Gym-month-original cohort-current tier-billing bucket','experiment_assignments':'Experiment-gym','market_events':'Gym-competitor-date-event type'}
    derived = {'average_members','realised_ARPMM','subscription_yield','monthly_revenue','acquisition_rate','churn_rate','retention_rate','conversion_rate','visits_per_member','utilisation_pct','peak_utilisation_pct','average_concurrent_attendance','competitor_price_gap','change_amount','change_pct','average_tenure','pricing_complaints_per_1000_members','gym_age_years'}
    price_fields={'median_income','current_standard_price','current_offpeak_price','current_premium_price','PureGym_equivalent_price','JD_equivalent_price','local_competitor_avg_price','competitor_price_gap','standard_price','offpeak_price','premium_price','headline_price','billed_price','base_billed_price','price_at_join','first_month_price','joining_fee','competitor_standard_price','promotion_value','old_price','new_price','change_amount'}
    for table,frame in frames.items():
        for col in frame.columns:
            desc=DESCRIPTIONS.get(col)
            if col.startswith('pre_'):
                label=col.removeprefix('pre_')
                desc=f"January–March 2025 pre-assignment {label.replace('_',' ')}; price and rates are monthly means, members are mean average members, competition is mean competitor count, growth is March closing / January opening minus one."
            if col.startswith('average_') and col.endswith('_members'):
                desc=f"Average {col[8:-8]} tier membership exposure; premium means Plus."
            if col.endswith('_subscription_revenue'):
                desc=f"Net subscription revenue of {col.split('_')[0]} tier; premium means Plus."
            if col.endswith('_realised_yield'):
                desc=f"Net {col.split('_')[0]} subscription revenue divided by matching average tier members."
            if not desc:
                raise ValueError(f"Missing dictionary description: {table}.{col}")
            kind='boolean' if pd.api.types.is_bool_dtype(frame[col]) else 'date' if col in {'month','join_month','opening_date','snapshot_date','effective_date','notification_date','existing_member_effective_date','price_protected_until','assignment_date','matching_window_start','matching_window_end','event_date'} else 'integer' if pd.api.types.is_integer_dtype(frame[col]) or col.startswith('customers_remaining_') else 'decimal' if pd.api.types.is_numeric_dtype(frame[col]) else 'text'
            unit='GBP gross' if col in price_fields else 'GBP net' if 'revenue' in col else 'decimal fraction' if col.endswith('_pct') or col.endswith('_rate') or col=='pre_historical_growth' or col in {'pre_churn','pre_acquisition','pre_utilisation'} else 'months' if col in {'average_tenure','observation_months'} else 'km' if col.endswith('_km') else 'sq ft' if col=='floor_space_sqft' else 'years' if col=='gym_age_years' else 'minutes' if 'minutes' in col else 'GBP spend' if col=='marketing_spend' else 'GBP gross' if col=='pre_price' else 'score / 10' if col=='estimated_quality_score' else 'count' if kind in {'integer','decimal'} else 'date' if kind=='date' else 'none'
            provenance='Derived from synthetic inputs' if col in derived or col.startswith(('average_','pre_')) or col.endswith(('_realised_yield','_subscription_revenue')) or col.startswith('customers_remaining_') or col in {'revenue_6_month','revenue_12_month'} else 'Synthetic observation / identifier'
            if col in {'realised_ARPMM','subscription_yield'} or col.endswith('_realised_yield'):
                unit='GBP net per member-month'
            null='Not available: retention horizon or revenue window not fully observed.' if table=='cohorts' and (col.startswith('customers_remaining_') or col in {'revenue_6_month','revenue_12_month'}) else 'Unknown joining month for legacy population.' if table=='membership_ledger' and col=='join_month' else 'Not applicable: no protected offer or eligible repricing event.' if col in {'price_protected_until','repricing_event_id'} else 'Not applicable to this intervention or event type.' if col in {'pair_id','old_price','new_price'} else 'No nulls permitted.'
            rows.append(dict(table=table,field=col,data_type=kind,unit=unit,grain=grain[table],provenance=provenance,null_meaning=null,definition=desc))
    return pd.DataFrame(rows)


def main():
    cfg=json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    frames=generate(cfg)
    checks=validate(frames,cfg)
    second=generate(cfg)
    hashes={name:hashlib.sha256(csv_bytes(frame)).hexdigest() for name,frame in frames.items()}
    assert all(hashes[name]==hashlib.sha256(csv_bytes(second[name])).hexdigest() for name in frames)
    checks.append(dict(check='Two complete generations produce identical CSV SHA-256 hashes',passed=True))
    data=ROOT/'data'
    data.mkdir(exist_ok=True)
    for name,frame in frames.items():
        (data/f'{name}.csv').write_bytes(csv_bytes(frame))
    dd=dictionary(frames)
    (ROOT/'analysis'/'data_dictionary.csv').write_bytes(csv_bytes(dd))
    # Typed values for the workbook builder; JSON nulls remain distinct from zeros.
    payload={name:json.loads(frame.to_json(orient='split',index=False,double_precision=12)) for name,frame in frames.items()}
    payload['data_dictionary']=json.loads(dd.to_json(orient='split',index=False))
    (ROOT/'analysis'/'workbook_data.json').write_text(json.dumps(payload,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
    m=frames['monthly_performance']
    monthly_stocks=m.groupby('month').closing_members.sum()
    result=dict(seed=cfg['seed'],period='January 2024–December 2025',rows={name:len(f) for name,f in frames.items()},checks=checks,csv_sha256=hashes,
                opening_members=int(m.loc[m.month=='2024-01-01','opening_members'].sum()),closing_members=int(monthly_stocks.iloc[-1]),minimum_monthly_closing_members=int(monthly_stocks.min()),maximum_monthly_closing_members=int(monthly_stocks.max()),
                ranges={col:[float(m[col].min()),float(m[col].max())] for col in ['standard_price','churn_rate','conversion_rate','utilisation_pct','peak_utilisation_pct','realised_ARPMM']},
                cohort_censoring={col:int(frames['cohorts'][col].isna().sum()) for col in ['customers_remaining_30d','customers_remaining_90d','customers_remaining_180d','revenue_6_month','revenue_12_month']})
    (ROOT/'analysis'/'validation_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines=['# Phase 2 — Dataset validation', '', DISCLAIMER, '', f"Period: {result['period']}. Seed: {cfg['seed']}.", '', '## Dataset sizes', '', '| Table | Rows |','| --- | ---: |']
    lines += [f'| {name} | {len(frame):,} |' for name,frame in frames.items()]
    lines += ['',f"Opening estate members: **{result['opening_members']:,}**. December 2025 closing estate members: **{result['closing_members']:,}**.",f"Monthly closing stock ranges from {result['minimum_monthly_closing_members']:,} to {result['maximum_monthly_closing_members']:,}. These are stocks, not unique people or a sum across months.",'','## Observed data ranges','','| Metric | Minimum | Maximum |','| --- | ---: | ---: |']
    lines += [f'| {col} | {low:.4f} | {high:.4f} |' for col,(low,high) in result['ranges'].items()]
    lines += ['','Rates and utilisation above are decimal fractions. Prices include VAT; ARPMM is net of VAT. Peak occupancy may exceed the comfortable-capacity proxy.','','## Automated checks','']
    lines += [f"- PASS: {check['check']}" for check in checks]
    lines += ['','## Right-censored cohorts','']+[f'- {col}: {n:,} unavailable observations.' for col,n in result['cohort_censoring'].items()]
    lines += ['','## Workbook verification','', 'Pending workbook build and visual review. This section is updated by the workbook verifier.','','## Limits','', 'Monthly member exposure and retention ages are approximations. All causal mechanisms are assumed by the generator. Behavioural noise, competitor events and commercial selection complicate later observational estimation. The historical pilot is synthetic and its outcome has not been interpreted. Cohort revenue excludes fees and ancillary income. Contribution profit and completed lifetime value are not available.','','Phase 3 baseline analysis has not started.','',LONG_DISCLAIMER,'']
    (ROOT/'analysis'/'validation_report.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in {'checks','csv_sha256'}},indent=2))
    print(f"PASS: {len(checks)} automated checks; all CSVs reproducible.")


if __name__=='__main__':
    main()
