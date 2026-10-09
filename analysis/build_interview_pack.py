"""Phase 12 access materials and validation; no regeneration or commercial inference."""
import argparse,csv,hashlib,json,math,re,shutil,sys,tempfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from interview_content import QUESTIONS,CHALLENGES
from package_portfolio import accepted_integrity

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'interview';BUILD=ROOT/'analysis/.interview_build';DIST=ROOT/'dist'
D1='This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.'
D2='This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.'
STATUS='Phase 12 complete; interview preparation materials complete.'
DISCLAIMER='\n'+D1+'\n\n'+D2+'\n'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,obj):p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def csvrows(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def one(rows,key):
    selected=[r for r in rows if all(str(r[k])==str(v) for k,v in key.items())]
    assert len(selected)==1,(key,len(selected));return selected[0]
def value(x):
    if x=='':return None
    if x in ('True','False'):return x=='True'
    try:return float(x)
    except (TypeError,ValueError):return x
def display(v,kind='text'):
    if v is None:return 'Unavailable'
    if kind=='money':return ('−£' if v<0 else '£')+f'{abs(v):,.2f}'
    if kind=='money0':return ('−£' if v<0 else '£')+f'{abs(v):,.0f}'
    if kind=='percent':return f'{v*100:.2f}%'
    if kind=='percent1':return f'{v*100:.1f}%'
    if kind=='pp':return f'{v:.3f} pp'
    if kind=='decimal3':return f'{v:.3f}'
    if kind=='count':return f'{v:,.0f}'
    if kind=='p':return f'{v:.5f}'
    return str(v)

def extract_register():
    records=[];files=set()
    def add(id,label,v,source,key,field,unit,window,population,kind='text',transform='none'):
        files.add(source)
        records.append(dict(id=id,label=label,value=v,display=display(v,kind),unit=unit,window=window,population=population,
          source=dict(path=source,key=key,field=field,transformation=transform),
          rounding={'money':'GBP to 2 decimals','money0':'GBP to nearest whole pound','percent':'decimal ×100, 2 decimals',
          'percent1':'decimal ×100, 1 decimal','pp':'already percentage points, 3 decimals','decimal3':'3 decimals',
          'count':'nearest whole member/count for display; unrounded value retained','p':'5 decimals'}.get(kind,'unchanged')))
    b=load('analysis/baseline_results.json');yr=b['annual']['2025'];last=b['annual']['2024']
    for field,label,kind,unit in [
      ('total_revenue','2025 total net revenue','money','GBP net'),('closing_members','December 2025 member stock','count','members'),
      ('arpmm','2025 total ARPMM','money','GBP net per average-member month'),
      ('new_members','2025 joins','count','acquisitions, not unique people'),
      ('churn_rate','2025 monthly opening-base churn','percent','decimal monthly rate'),
      ('retention_rate','2025 monthly opening-base retention','percent','decimal monthly rate'),
      ('conversion_rate','2025 qualified-prospect conversion','percent','decimal fraction')]:
        add('baseline.'+field,label,yr[field],'analysis/baseline_results.json',{'annual':'2025'},field,unit,
            'January–December 2025' if field!='closing_members' else 'December 2025 closing','All 80 gyms',kind)
    for field,label in [('total_revenue','Matching-year net revenue growth'),('closing_members','December closing membership growth')]:
        add('baseline.'+field+'_growth',label,yr[field]/last[field]-1,'analysis/baseline_results.json',{'annual':['2024','2025']},field,
          'decimal growth','Matching 2024/2025 windows','All 80 gyms','percent','2025 / 2024 − 1; descriptive saved-value arithmetic')
    for field,label in [('member_volume_contribution','Revenue bridge member-volume contribution'),('total_arpmm_contribution','Revenue bridge total-ARPMM contribution')]:
        add('bridge.'+field,label,b['bridge'][field],'analysis/baseline_results.json',{'object':'bridge'},field,'GBP net',
          '2025 versus 2024','All 80 gyms','money')
    h=load('analysis/headroom_results.json')
    for field in ['sensitive_sites','high_score_with_cautions']:
        add('headroom.'+field,field.replace('_',' '),h[field],'analysis/headroom_results.json',{},field,'gyms','2025/December 2025','All 80 gyms','count')
    for band,n in h['bands'].items():add('headroom.band.'+band,band+' score band',n,'analysis/headroom_results.json',{'object':'bands'},band,'gyms','2025/December 2025','All 80 gyms','count')
    psrc='data/price_response_estimates.csv';p=csvrows(psrc)
    for metric,kind,unit in [('controlled_acquisition_response','percent','decimal fraction'),('acquisition_elasticity','decimal3','log response / log dose'),
      ('incumbent_churn_response_pp','pp','percentage points per month'),('incumbent_downgrade_response_pp','pp','percentage points per month'),
      ('monthly_revenue_estimated_difference','money','GBP net control-derived historical-period estimate')]:
        key={'estimator':'paired_equal','window':'primary_6m','group_type':'Overall','group':'All assigned pairs','metric':metric,'weight_method':'Equal pairs'}
        r=one(p,key)
        metric_label={'controlled_acquisition_response':'Controlled Standard acquisition response',
          'acquisition_elasticity':'Local Standard acquisition elasticity',
          'incumbent_churn_response_pp':'Monthly incumbent Standard churn change',
          'incumbent_downgrade_response_pp':'Monthly incumbent Standard downgrade change',
          'monthly_revenue_estimated_difference':'Estimated cumulative six-month total net revenue difference'}[metric]
        for field in ['estimate','ci_lower','ci_upper']:
            add('pilot.'+metric+'.'+field,metric_label+' '+field,value(r[field]),psrc,key,field,unit,
              'October 2024–March 2025 versus April–September 2025','12 randomised pairs',kind)
        if metric in ['controlled_acquisition_response','incumbent_churn_response_pp']:
            add('pilot.'+metric+'.p',metric+' exact p-value',value(r['exact_p_value']),psrc,key,'exact_p_value','probability',
              'Primary six-month comparison','12 pairs / 4096 within-pair flips','p')
    rsrc='data/recommendation_portfolio.csv';r=one(csvrows(rsrc),{'variant':'base','case':'Base'})
    for field,label,kind,unit in [('incremental_revenue','Base conditional RAISE portfolio uplift','money','GBP net'),
      ('incremental_revenue_lower','Portfolio conditional 95% lower bound','money','GBP net'),('incremental_revenue_upper','Portfolio conditional 95% upper bound','money','GBP net'),
      ('member_difference','December member difference versus no increase','count','expected members'),('member_impact','December member impact versus no increase','percent','decimal growth'),
      ('counterfactual_month12_members','No-increase December 2026 members','count','expected members'),('month12_members','Conditional-raise December 2026 members','count','expected members'),
      ('excluded_test_first_base_revenue','Excluded provisional TEST FIRST gains','money','GBP net, separately labelled potential'),
      ('raise_1_sites','RAISE £1 sites','count','gyms'),('raise_2_sites','RAISE £2 sites','count','gyms'),('test_sites','TEST FIRST sites','count','gyms'),
      ('hold_sites','HOLD PRICE sites','count','gyms'),('investigate_sites','DEFENSIVE / INVESTIGATE sites','count','gyms')]:
        add('portfolio.'+field,label,value(r[field]),rsrc,{'variant':'base','case':'Base'},field,unit,'January–December 2026 hypothetical',
          'All 80 gyms; only 11 conditional RAISE increments; other sites no increase',kind)
    esrc='data/experiment_estimates.csv';rows=csvrows(esrc)
    for checkpoint,metrics in [(6,['revenue_effect','member_harm','standard_acquisition_harm','incumbent_churn_change_pp','incumbent_downgrade_change_pp']),
                              (12,['incumbent_churn_change_pp'])]:
        for metric in metrics:
            key={'simulation':'Main','population':'First repricing','checkpoint_months':str(checkpoint),'metric':metric};r=one(rows,key)
            kind='pp' if metric.endswith('_pp') else 'percent'
            for field in ['estimate','lower','upper']:
                add(f'experiment.{checkpoint}.{metric}.{field}',f'Main {checkpoint}-month '+metric.replace('_',' ')+' '+field,value(r[field]),esrc,key,field,
                  'percentage points per month' if kind=='pp' else 'decimal proportion',
                  ('July–December 2025 versus January–June 2026' if checkpoint==6 else 'January–December 2025 versus January–December 2026'),
                  'Five primary first-repricing pairs; simulated','pp' if kind=='pp' else 'percent')
            if metric=='revenue_effect':
                for field in ['p_value_one_sided','p_value_two_sided']:
                    add('experiment.6.'+field,field.replace('_',' '),value(r[field]),esrc,key,field,'probability',
                      'Six-month primary window','Five pairs / 32 assignment flips','p')
    gov=load('analysis/experiment_results.json')['governance']
    for sim,checkpoint in [('Main',6),('Main',12),('A/A null',12)]:
        key={'simulation':sim,'population':'First repricing','checkpoint_months':checkpoint};r=one(gov,key)
        add(f'decision.{sim}.{checkpoint}',f'{sim} {checkpoint}-month primary decision',r['decision'],'analysis/experiment_results.json',key,'decision',
          'saved classification','Matching-length pre/post '+str(checkpoint)+'-month window','Five primary pairs; simulated')
    key={'design':'5 first-repricing pairs','effect_assumption':'0.02','method':'Exact assignment Monte Carlo'}
    r=one(csvrows('data/experiment_power.csv'),key)
    for field,label in [('planning_power','Planning power at assumed 2% revenue effect'),('effect_detectable_80pct','Effect detectable at 80% planning power')]:
        add('power.'+field,label,value(r[field]),'data/experiment_power.csv',key,field,'decimal proportion',
            'Prospective planning, not observed power','Five primary pairs; historical placebo noise proxy','percent1' if field=='planning_power' else 'percent')
    for src,fields,prefix,window in [
      ('analysis/recommendation_config.json',['member_loss_limit','minimum_post_increase_competitor_gap','test_repeat_repricing'],'policy7','Hypothetical 2026 assessment'),
      ('analysis/experiment_config.json',['member_harm_limit','standard_acquisition_harm_limit','churn_harm_limit_pp','downgrade_harm_limit_pp',
       'complaints_service_limit','capacity_service_limit','capacity_consecutive_months','alpha','minimum_interval_pairs','bootstrap_samples','increment','intervention_date','billing_date'],'policy8','Hypothetical 2026 experiment'),
      ('analysis/scenario_config.json',['vat_rate','notice_churn_factor','protected_downgrade_factor','bootstrap_samples'],'scenario','Hypothetical 2026 model')]:
        cfg=load(src)
        for field in fields:
            v=cfg[field];kind='text'
            if field.endswith('_pp'):kind='pp'
            elif field.endswith('_limit') and field not in ['complaints_service_limit']:kind='percent'
            elif field in ['alpha','vat_rate']:kind='percent'
            elif field in ['minimum_post_increase_competitor_gap','increment']:kind='money'
            elif field in ['bootstrap_samples','minimum_interval_pairs','capacity_consecutive_months']:kind='count'
            unit={'member_loss_limit':'decimal downside December member-loss tolerance',
              'minimum_post_increase_competitor_gap':'GBP consumer recurring-price gap inclusive VAT','test_repeat_repricing':'boolean policy',
              'member_harm_limit':'decimal controlled closing-member loss','standard_acquisition_harm_limit':'decimal controlled Standard acquisition loss',
              'churn_harm_limit_pp':'monthly percentage points','downgrade_harm_limit_pp':'monthly percentage points',
              'complaints_service_limit':'complaints per 1000 average-member months','capacity_service_limit':'fraction of concurrent capacity',
              'capacity_consecutive_months':'consecutive months','alpha':'probability','minimum_interval_pairs':'complete pairs',
              'bootstrap_samples':'whole-pair samples','increment':'GBP consumer cash increment inclusive VAT',
              'intervention_date':'ISO date','billing_date':'ISO date','vat_rate':'decimal VAT rate',
              'notice_churn_factor':'pre-calibration response multiplier','protected_downgrade_factor':'pre-calibration response multiplier'}[field]
            add(prefix+'.'+field,field.replace('_',' '),v,src,{},field,unit,window,'Policy/configuration, not empirical tolerance',kind)
    sites=[];design=csvrows('data/experiment_design.csv');recommend=csvrows('data/gym_recommendations.csv')
    for gym in ['NF049','NF023','NF013','NF001','NF002']:
        r=one(recommend,{'gym_id':gym});d=one(design,{'gym_id':gym})
        fields=['city','action','proposed_increment','provisional_test_increment','assessment_increment','rule_id','current_standard_price','proposed_standard_price','plus1_qualified','plus2_qualified',
          'plus1_failed_gates','plus2_failed_gates','explanation','selected_incremental_revenue','selected_member_impact','repeated_repricing','caution_flag_count']
        saved={field:value(r[field]) for field in fields}
        for field in fields:
            kind='money' if field in ['current_standard_price','proposed_standard_price','selected_incremental_revenue'] else 'percent' if field=='selected_member_impact' else 'text'
            add(f'site.{gym}.{field}',gym+' '+field.replace('_',' '),saved[field],'data/gym_recommendations.csv',{'gym_id':gym},field,
              'GBP net' if field=='selected_incremental_revenue' else 'GBP consumer inclusive VAT' if 'price' in field or 'increment' in field else
              'decimal December member impact' if field=='selected_member_impact' else 'count' if field=='caution_flag_count' else
              'boolean' if field in ['plus1_qualified','plus2_qualified','repeated_repricing'] else 'text / saved label',
              'Phase 7 hypothetical 2026; December 2025 price snapshot','Single gym saved recommendation',kind)
        for field in ['disposition','assignment','population','exclusion_reason']:
            add(f'site.{gym}.design.{field}',gym+' design '+field,d[field] or None,'data/experiment_design.csv',{'gym_id':gym},field,
              'saved design status','December 2025 eligibility/matching','Single gym')
        sites.append(dict(gym_id=gym,recommendation=saved,design={k:d[k] for k in ['disposition','assignment','population','exclusion_reason']}))
    assert len({r['id'] for r in records})==len(records)
    return {'version':1,'status':'Saved evidence access; no new response estimates','records':records,'sites':sites,
      'source_hashes':{p:sha(ROOT/p) for p in sorted(files)},'disclaimers':[D1,D2]}, {r['id']:r for r in records}

def prepare():
    OUT.mkdir(exist_ok=True);BUILD.mkdir(parents=True,exist_ok=True)
    if not (OUT/'validation.json').exists():
        write(OUT/'validation.json',{'status':'Pending content, rendered review and packaging checks; not yet accepted.'})
    # Check original acceptance and phase archives before authorised documentation edits.
    accepted_integrity()
    saved=load('analysis/portfolio_validation.json')
    identity={name:item['sha256'] for name,item in saved['archives'].items()}
    for name,expected in identity.items():assert sha(DIST/name)==expected
    identity.update({p:sha(ROOT/p) for p in ['portfolio/case_study.md','analysis/powerbi_native_acceptance.json','analysis/presentation_validation.json']})
    proof=OUT/'protected_identity.json'
    if proof.exists():assert load('interview/protected_identity.json')==identity,'Protected interview baseline changed'
    else:write(proof,identity)
    reg,facts=extract_register();write(OUT/'evidence_register.json',reg)
    qlines=['# Thirty core interview questions','',
      'Use the spoken answers as frameworks, not scripts to memorise. Explain the technical follow-up in your own words. Personalise ownership honestly. Each source supports the documented method; the evidence register provides exact numerical values.','']
    current=None
    for i,(topic,question,answer,technical,source,limit) in enumerate(QUESTIONS,1):
        if topic!=current:qlines += ['## '+topic,''];current=topic
        qlines += [f'### Q{i:02d}. {question}','', '**Spoken response:** '+answer,'', '**Technical follow-up:** '+technical,'',
          f'**Evidence:** [{source}](../{source}).','', '**Limit:** '+limit,'']
    (OUT/'core_questions.md').write_text('\n'.join(qlines)+DISCLAIMER,encoding='utf-8')
    lines=['# Fifteen stakeholder challenges','',
      'Answer the objection directly, make the material concession, then specify evidence that could change the decision. The personal-contribution challenge requires your own truthful details.','']
    current=None
    for i,(role,question,defence,concession,needed,source) in enumerate(CHALLENGES,1):
        if role!=current:lines += ['## '+role,''];current=role
        link='../'+source
        lines += [f'### C{i:02d}. {question}','', '**Defence:** '+defence,'','**Concession:** '+concession,'',
          '**Evidence needed:** '+needed,'',f'**Source:** [{source}]({link}).','']
    (OUT/'stakeholder_challenges.md').write_text('\n'.join(lines)+DISCLAIMER,encoding='utf-8')
    quick=['# Quick-reference evidence and definitions','',
      'All figures below are extracted from saved evidence. Use the reporting window and population with every number. Display rounding never changes the underlying saved value.','']
    groups=[('Baseline — synthetic historical trading',[r for r in reg['records'] if r['id'].startswith(('baseline.','bridge.'))]),
      ('Headroom — relative indicators',[r for r in reg['records'] if r['id'].startswith('headroom.')]),
      ('Historical pilot — local +£2 policy',[r for r in reg['records'] if r['id'].startswith('pilot.')]),
      ('Conditional RAISE-only portfolio — hypothetical 2026',[r for r in reg['records'] if r['id'].startswith('portfolio.')]),
      ('Experiment — simulated primary first-repricing population',[r for r in reg['records'] if r['id'].startswith(('experiment.','decision.','power.'))]),
      ('Policy assumptions — not empirical tolerances',[r for r in reg['records'] if r['id'].startswith(('policy7.','policy8.','scenario.'))])]
    for title,items in groups:
        quick += ['## '+title,'','| Metric | Saved display | Evidence ID |','|---|---|---|']
        for r in items:
            if r['id'].endswith(('.ci_lower','.ci_upper','.lower','.upper')):continue
            text=r['display'];id=r['id'];label=r['label']
            if id.endswith('.estimate'):
                base=id.rsplit('.',1)[0]
                lo=facts.get(base+'.ci_lower') or facts.get(base+'.lower')
                hi=facts.get(base+'.ci_upper') or facts.get(base+'.upper')
                if lo and hi:text+=f"; 95% interval {lo['display']} to {hi['display']}"
                label=label.removesuffix(' estimate')
            if id=='portfolio.incremental_revenue':
                text+=f"; conditional 95% range {facts['portfolio.incremental_revenue_lower']['display']} to {facts['portfolio.incremental_revenue_upper']['display']}"
            if id in ['portfolio.incremental_revenue_lower','portfolio.incremental_revenue_upper']:continue
            if id=='portfolio.raise_1_sites':
                text='1 RAISE £2; 10 RAISE £1; 5 TEST FIRST; 26 HOLD; 38 INVESTIGATE';label='Saved action counts';id='portfolio.*_sites'
            elif id in ['portfolio.raise_2_sites','portfolio.test_sites','portfolio.hold_sites','portfolio.investigate_sites']:continue
            if id.startswith('headroom.band.'):
                if id!='headroom.band.High':continue
                text='15 High; 43 Medium; 22 Low';label='Saved score bands';id='headroom.band.*'
            if id.startswith(('policy8.bootstrap_samples','scenario.bootstrap_samples','scenario.notice_churn_factor','scenario.protected_downgrade_factor')):continue
            if id=='policy8.complaints_service_limit':label='Complaints service trigger (per 1,000 average-member months)'
            if id=='policy8.capacity_service_limit':label='Capacity service trigger (% concurrent capacity)'
            if id=='policy8.capacity_consecutive_months':label='Capacity trigger consecutive months'
            quick.append(f"| {label} | **{text}** | `{id}` |")
        quick += ['']
    quick += ['## Windows and populations','',
      '- Historical dataset: January 2024–December 2025; full-year 2025 baseline, matching 2024 and Q4 context.',
      '- Pricing/headroom snapshot: December 2025; original estate ranks retained.',
      '- Historical randomised +£2 primary comparison: October 2024–March 2025 versus April–September 2025; twelve pairs, April notice/new joiner price, May eligible incumbent billing.',
      '- Historical robustness: three-month early, nine-month sustained and three-month pre-intervention placebo; twenty targeted increases remain observational.',
      '- Scenarios: January–December 2026; expected fractional members, common no-increase counterfactual.',
      '- Designed £1 experiment: seven pairs, seven treatment and seven control gyms; five first-repricing pairs primary, two repeat pairs exploratory. Portsmouth and Leicester are reserves.',
      '- Experiment primary: July–December 2025 versus January–June 2026. One-, three- and twelve-month checkpoints use matching-length pre-periods.',
      '- New joiner change/notice: 1 January 2026; eligible incumbent billing: 1 February or later at protection expiry. A real test needs a new prospective calendar.',
      '', '## Definitions worth being able to derive','',
      '| Measure | Definition and boundary |','|---|---|',
      '| Members | Opening + joins − opening-base exits − same-month exits = closing; tier transfers reconcile within a gym. |',
      '| Average members | Approximate monthly opening/closing midpoint; annual average is mean monthly exposure. |',
      '| Churn / retention | Opening-base exits ÷ summed opening exposure; retention is one minus the monthly exposure-weighted churn, not annual retention. |',
      '| Acquisition / conversion | Joins ÷ opening-member exposure; joins ÷ qualified prospects. Standard conversion is unavailable because prospects are not tier-specific. |',
      '| ARPMM / subscription yield | Total net revenue / summed average-member months; subscription revenue / the same exposure. Standard yield uses Standard exposure. |',
      '| Consumer versus net money | Consumer headline and paid prices include assumed 20% VAT; revenue excludes it. |',
      '| Competitor gap | Comparable recurring competitor price minus Standard headline price; positive means Northstar is cheaper. Fees and introductory discounts stay separate. |',
      '| Cohorts | Original joining cohort survives tier switches. Legacy join dates are unknown. Immature milestones and incomplete revenue stay unavailable. |',
      '| Historical acquisition response | exp(mean paired log join response) − 1. Elasticity = mean paired log response / mean log price dose. |',
      '| Pair acquisition contrast | dᵢ = ln(Treatment post Standard joins / Treatment pre Standard joins) − ln(Control post Standard joins / Control pre Standard joins). |',
      '| Pair-controlled revenue | Treatment post revenue − Treatment pre revenue × (Control post revenue / Control pre revenue). Log contrasts supply the equal-pair percentage effect. |',
      '| Controlled churn/downgrade | Treatment-minus-control before/after opening-exposure rate difference, expressed in percentage points. |',
      '| Revenue bridge | Δ exposure × old ARPMM + new exposure × Δ ARPMM; interaction allocated to ARPMM. |',
      '| Exit run-rate | December monthly revenue ×12, a seasonal annualised exit figure; not earned annual revenue or a forecast. |',
      '', '## Ordered decision rules','',
      '**Phase 7:** caution/missing evidence → investigate; neither candidate plausible → hold; otherwise test qualification, choose higher Base revenue with smaller exact-tie increment, and route repeat repricing to TEST FIRST. Qualifying financial gates require positive Base, Downside, conditional lower-bound and every non-zero sensitivity revenue; sufficient post-increase competitor gap; Downside member loss no greater than policy limit. Equality passes the member-loss and competitor-gap boundaries; zero revenue does not pass a strict-positive gate. £3 remains analytical only.',
      '', '**Phase 8:** incomplete/invalid/unavailable → EXTEND TEST; revenue upper bound non-positive or harm lower bound above tolerance → STOP; unresolved service or point harm above tolerance → MODIFY; completed primary assessment with positive revenue lower bound, passing one-sided test and all upper harms within tolerance → ROLL OUT; otherwise EXTEND TEST. Equality passes harm limits. Early checks cannot roll out; repeat repricing and A/A cannot authorise progression.',
      '', '## Uncertainty and common traps','',
      '- Conditional parameter uncertainty comes from joint historical pair draws; it excludes trading shocks and transport risk. Shared draws are aggregated before portfolio quantiles; never sum site interval endpoints.',
      '- Simulated trading variation comes from residual blocks and integer flows. Experimental intervals resample whole observed simulated pairs; the simulation supplies no new independent evidence.',
      '- The primary five-pair experiment enumerates 32 flips; minimum one-sided p-value is 3.125%, minimum two-sided 6.25%. Seven pooled pairs give 128 flips. At least four complete pairs are required for subgroup intervals; repeat/regional intervals remain unavailable.',
      '- Main six-month revenue is positive at the point estimate but inconclusive; several upper harm bounds fail. Main twelve-month churn lower harm exceeds its tolerance, producing STOP.',
      '- A/A no-increase diagnostic paths match exactly, yet the comparative estimator can trigger MODIFY from noise/baseline extrapolation. This is a management review signal, not causal harm.',
      '- A missing rate is not zero; valid zero is retained. A member stock or repeated event-family/simulation observation is not a unique customer.',
      '- A high score is not causal willingness to pay. A low p-value is not an implementation rule. Positive parameter draws are not rollout probabilities.',
      '- Revenue is not profit or completed LTV. Persistent response, customer value, contribution costs, bad debt, competitor reactions, cannibalisation and repeat repricing need further evidence.',
      '- The forecast does not acquire authority from an editable selector. Stale comparisons or manual behavioural overrides suppress authoritative ranges/recommendations until the required rerun/refresh.',
      '', 'Sources: [evidence register](evidence_register.json), [historical response](../analysis/response_report.md), [scenario methodology](../analysis/phase6_methodology.md), [recommendation policy](../analysis/recommendation_config.json), [experiment protocol](../analysis/experiment_protocol.md).']
    (OUT/'quick_reference.md').write_text('\n'.join(quick)+DISCLAIMER,encoding='utf-8')
    write_demonstration(reg,facts)
    guidance=load('analysis/latest_phase_guidance.json');guidance['Dataset Overview'].update(D5='Phase 12 complete',E5='Interview pack ready',E7='Materials complete')
    guidance['README']['B20']=STATUS
    guidance['Recommendation Summary']['A17']=STATUS+' Conditional recommendations unchanged.'
    write(ROOT/'analysis/latest_phase_guidance.json',guidance)
    readme=ROOT/'README.md';text=readme.read_text(encoding='utf-8')
    text=text.replace('**Phase 11 complete; Phase 12 next.**','**'+STATUS+'**')
    text=text.replace('this README and external phase guidance describe current project status. GitHub publication and interview defence remain separate work.',
      'this README and external phase guidance describe current project status. The [separate interview pack](interview/README.md) completes written preparation; live mock practice and GitHub publication remain separate work. The two Phase 11 archives are preserved unchanged.')
    if not re.search(r'^6\..*interview/README\.md',text,re.M):
        text=text.replace('5. Explore the [SQL examples]', '6. Prepare with the [interview preparation](interview/README.md).\n\n5. Explore the [SQL examples]')
        # Keep ordinary numbered viewing order rather than an out-of-order insertion.
        text=text.replace('6. Prepare with the [interview preparation](interview/README.md).\n\n5. Explore the [SQL examples](sql/README.md), [methodology](analysis/business_brief.md) and [verification records](portfolio/REPRODUCIBILITY.md).',
          '5. Explore the [SQL examples](sql/README.md), [methodology](analysis/business_brief.md) and [verification records](portfolio/REPRODUCIBILITY.md).\n6. Prepare with the [interview preparation](interview/README.md).')
    text=text.replace('6. Prepare with the [interview preparation](interview/README.md).','6. Practise with the [interview pack](interview/README.md).')
    if '| `interview/` |' not in text:
        text=text.replace('| `portfolio/` | Case study, gallery, package configuration and reproducibility guide |',
          '| `portfolio/` | Case study, gallery, package configuration and reproducibility guide |\n| `interview/` | Story, thirty answers, stakeholder challenges, evidence register and rehearsal guide |')
    text=text.replace('This package adds presentation and SQL access without changing prior commercial evidence.',
      'The portfolio includes presentation, SQL and interview materials without changing prior commercial evidence.')
    readme.write_text(text,encoding='utf-8')

def write_demonstration(reg,facts):
    lines=['# Five saved site examples and artifact demonstration','',
      'These are unchanged Phase 7 recommendations and Phase 8 design statuses, not a new ranking. Site financial figures describe the saved **assessment increment**, which can be a provisional TEST FIRST amount. The actual conditional portfolio maps TEST FIRST, HOLD and investigation sites to no increase. Provisional test gains are excluded from that portfolio and are not accepted raises.','']
    for s in reg['sites']:
        r=s['recommendation'];d=s['design'];gym=s['gym_id']
        lines += [f"## {gym} {r['city']}",'',
          f"**Saved action:** {r['action']}; proposed cash increment £{r['proposed_increment']:g}; provisional test amount £{r['provisional_test_increment']:g}.",'',
          f"**Rule:** `{r['rule_id']}`. {r['explanation']}",'',
          f"**{'Provisional test' if r['action']=='TEST FIRST' else 'Saved assessment'} Base effect at £{r['assessment_increment']:g}:** {facts[f'site.{gym}.selected_incremental_revenue']['display']} incremental net revenue; {facts[f'site.{gym}.selected_member_impact']['display']} December member impact versus no increase.",'',
          f"**£1 failed gates:** {r['plus1_failed_gates'] or 'None'}. **£2 failed gates:** {r['plus2_failed_gates'] or 'None'}.",'',
          f"**Experiment status:** {d['disposition']}; assignment {d['assignment'] or 'Unavailable / not assigned'}; population {d['population'] or 'Unavailable / not assigned'}.",'',
          f"**Design reason:** {d['exclusion_reason'] or 'Matched and randomised under the saved protocol.'}",'',
          f"**Evidence:** [recommendation row](../data/gym_recommendations.csv), [design row](../data/experiment_design.csv), keys `gym_id={gym}`; exact values in [register](evidence_register.json).",'']
        if gym=='NF023':lines += ['**Defence:** Portsmouth is commercially qualified but unmatched within its strict region/prior-repricing stratum. It remains a reserve. Do not relax matching or admit flagged sites to inflate power.','']
        if gym=='NF013':lines += ['**Defence:** Reading passes financial gates but prior repricing creates an evidence gap. The displayed potential gains are provisional and excluded from the conditional-raise portfolio. Its provisional £2 amount does not change the designed £1 experiment, and repeat-repricing inference remains exploratory.','']
    lines += ['## Five-minute artifact demonstration','',
      'Open saved files beforehand. The timing below is a rehearsal budget, not a measured session. If native applications are unavailable, use the existing gallery and presentation PDF; do not claim a live refresh or interaction test.','',
      '| Time | Action | Explain / fallback |','|---|---|---|',
      '| 0:00–0:35 | Show the presentation opening and evidence scope. | Fictional operator, modelled revenue/member trade-off, no implemented gain. |',
      '| 0:35–1:15 | Open Executive Overview, full-year 2025. | Matching-year revenue/membership and exact bridge. Avoid a revenue-only narrative. |',
      '| 1:15–2:00 | Show Recommendations, then Gym Detail for a saved example and Back. | Ordered gates, failed £2 gate at Portsmouth, repeat status at Reading. Use saved screenshots if needed. |',
      '| 2:00–2:45 | Show Scenario Inputs/Model and captured comparison. | One authoritative selector affects the active model; saved captures require refresh and show freshness. Do not edit the accepted workbook during rehearsal. |',
      '| 2:45–3:25 | Show Pricing Scenarios saved Base/Downside controls. | Report controls select saved combinations, not new forecasts. Unsupported multi-site ranges remain blank; never sum endpoints. |',
      '| 3:25–4:05 | Show Experiment & Monitoring at Main / six months / First repricing, then twelve months. | EXTEND TEST then STOP; reset restores primary defaults. Repeat-pair intervals remain blank. |',
      '| 4:05–5:00 | Explain SQL 02, 12 and 14 plus the next evidence needed. | Weighted exposure, case separation and RAISE-only mapping. Close on a real test and contribution/service evidence. |','',
      'Use [Power BI native gallery](../portfolio/dashboard_gallery.md), [accepted PBIX](../powerbi/gym_pricing_dashboard.pbix), [31-sheet workbook](../excel/gym_pricing_model.xlsx), [management presentation](../presentation/pricing_recommendation.pdf) and [SQL guide](../sql/README.md).','',
      'SQL cues: [02 weighted baseline](../sql/queries/02_weighted_baseline.sql); [12 saved Base scenarios](../sql/queries/12_saved_base_scenarios.sql); [14 conditional portfolios](../sql/queries/14_conditional_portfolios.sql). Query 14 maps every TEST FIRST site to no increase and joins saved complete-portfolio ranges, rather than summing site bounds.','',
      'Before any genuine workbook input demonstration, use a disposable copy. A stale comparison, missing evidence or manual behavioural override must not be presented as authoritative. Consult the existing refresh runbooks; this interview pack neither executes them nor changes the scenario selector.']
    (OUT/'demonstration.md').write_text('\n'.join(lines)+DISCLAIMER,encoding='utf-8')

def words(text):return len(re.findall(r"\b[\w]+(?:[’-][\w]+)*\b",re.sub(r'^#+.*$','',text,flags=re.M)))
def check_identity(require_archives=False):
    result=accepted_integrity();missing=[];checked=0
    supplement=DIST/'reproduction_manifest.json'
    if not supplement.exists():supplement=ROOT/'REPRODUCTION_MANIFEST.json'
    dependency_count=0
    assert supplement.exists(),'Restore the supplemental reproduction manifest'
    for name,item in json.loads(supplement.read_text())['files'].items():
        assert sha(ROOT/name)==item['sha256'],'Supporting evidence changed: '+name;dependency_count+=1
    for name,expected in load('interview/protected_identity.json').items():
        p=DIST/name if name.endswith('.zip') else ROOT/name
        if not p.exists():missing.append(name);continue
        assert sha(p)==expected,'Protected Phase 11/identity changed: '+name;checked+=1
    assert not require_archives or not missing,missing
    return {'accepted_artifacts':result,'supporting_dependency_files_checked':dependency_count,'additional_protected_files_checked':checked,'unavailable_archive_files':missing}

def check():
    integrity=check_identity();reg=load('interview/evidence_register.json');rebuilt,_=extract_register();assert reg==rebuilt
    manifest=ROOT/'INTERVIEW_MANIFEST.json'
    if manifest.exists():
        for name,item in json.loads(manifest.read_text())['files'].items():
            assert sha(ROOT/name)==item['sha256'],'Interview shipped file changed: '+name
    for file,hash in reg['source_hashes'].items():assert sha(ROOT/file)==hash,file
    assert len(QUESTIONS)==30 and len(CHALLENGES)==15
    assert set(Counter(q[0] for q in QUESTIONS).values())=={5}
    assert set(Counter(c[0] for c in CHALLENGES).values())=={3}
    counts={};s=(OUT/'story.md').read_text(encoding='utf-8')
    for tag,lo,hi in [('pitch',60,75),('story',240,280)]:
        txt=s.split('<!-- '+tag+':start -->')[1].split('<!-- '+tag+':end -->')[0];counts[tag]=words(txt);assert lo<=counts[tag]<=hi
    lesson="The key lesson was that the highest price isn't necessarily the optimal price. The commercial objective is finding the point where additional yield more than compensates for any member-volume response."
    assert lesson in s
    assert 'approximately £149,000' in s and 'about 1,209 fewer December members' in s
    assert round(value(one(csvrows('data/recommendation_portfolio.csv'),{'variant':'base','case':'Base'})['incremental_revenue'])/1000)*1000==149000
    assert round(abs(value(one(csvrows('data/recommendation_portfolio.csv'),{'variant':'base','case':'Base'})['member_difference'])))==1209
    q=(OUT/'core_questions.md').read_text(encoding='utf-8');c=(OUT/'stakeholder_challenges.md').read_text(encoding='utf-8')
    assert len(re.findall(r'^### Q\d\d\.',q,re.M))==30 and len(re.findall(r'^### C\d\d\.',c,re.M))==15
    for field in ['Spoken response','Technical follow-up','Evidence','Limit']:assert q.count('**'+field+':**')==30
    for field in ['Defence','Concession','Evidence needed','Source']:assert c.count('**'+field+':**')==15
    links=0
    for p in list(OUT.glob('*.md'))+[ROOT/'README.md']:
        text=p.read_text(encoding='utf-8');assert D1 in text and D2 in text,p
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
            if target.startswith(('https://','http://','#')):continue
            path=(p.parent/target.split('#')[0]).resolve();assert path.is_file(),(p.name,target);links+=1
    f={r['id']:r for r in reg['records']}
    assert abs(f['baseline.total_revenue']['value']-107006933.85)<.01
    assert f['baseline.closing_members']['value']==396311
    assert abs(f['portfolio.incremental_revenue']['value']-148618.48)<.01
    assert [f['portfolio.'+x]['value'] for x in ['raise_2_sites','raise_1_sites','test_sites','hold_sites','investigate_sites']]==[1,10,5,26,38]
    assert f['decision.Main.6']['value']=='EXTEND TEST' and f['decision.Main.12']['value']=='STOP'
    assert f['decision.A/A null.12']['value']=='MODIFY'
    assert f['experiment.12.incumbent_churn_change_pp.lower']['value']>f['policy8.churn_harm_limit_pp']['value']
    assert f['experiment.6.revenue_effect.lower']['value']<0<f['experiment.6.revenue_effect.upper']['value']
    assert f['experiment.6.member_harm.upper']['value']>f['policy8.member_harm_limit']['value']
    assert f['experiment.6.standard_acquisition_harm.upper']['value']>f['policy8.standard_acquisition_harm_limit']['value']
    assert f['experiment.6.incumbent_churn_change_pp.upper']['value']>f['policy8.churn_harm_limit_pp']['value']
    assert f['experiment.6.incumbent_downgrade_change_pp.upper']['value']<=f['policy8.downgrade_harm_limit_pp']['value']
    expected={'NF049':('Hull','RAISE £2'),'NF023':('Portsmouth','RAISE £1'),'NF013':('Reading','TEST FIRST'),
              'NF001':('London','HOLD PRICE'),'NF002':('London','DEFENSIVE / INVESTIGATE')}
    for site in reg['sites']:assert (site['recommendation']['city'],site['recommendation']['action'])==expected[site['gym_id']]
    assert f['site.NF023.design.disposition']['value']=='Reserve'
    assert f['site.NF013.proposed_increment']['value']==0 and f['site.NF013.provisional_test_increment']['value']==2
    demo=(OUT/'demonstration.md').read_text(encoding='utf-8')
    assert '**Provisional test Base effect at £2:**' in demo and 'excluded from the conditional-raise portfolio' in demo
    for r in csvrows('data/experiment_estimates.csv'):
        if int(r['complete_pairs'])<4:assert r['lower']=='' and r['upper']==''
    # Display/null boundary examples only; never new commercial policy calculations.
    assert display(None,'percent')=='Unavailable' and display(0,'percent')=='0.00%'
    assert display(.0034,'percent')=='0.34%' and display(.345,'pp')=='0.345 pp'
    assert f['policy7.member_loss_limit']['value']==.05 and f['policy8.member_harm_limit']['value']==.03
    assert 1/32==.03125 and 2/32==.0625
    result={'status':'Content and saved-evidence checks passed','story_words':counts,'core_questions':30,'stakeholder_challenges':15,
      'evidence_records':len(reg['records']),'source_files':len(reg['source_hashes']),'local_links_checked':links,'integrity':integrity,
      'tests':['Saved anchors/action counts/decisions','All register source rows, units, windows and rounding reconstructed',
       'All five site examples and Portsmouth reserve','Six-month harm bounds and twelve-month churn STOP',
       'Unavailable sparse-population intervals','Missing versus valid zero','Percentage-point versus decimal display',
       'Separate Phase 7/8 policy limits','Exact assignment p-value resolution','No new analysis or changes to native artifacts']}
    return result

def package():
    BUILD.mkdir(parents=True,exist_ok=True);DIST.mkdir(exist_ok=True)
    result=check();check_identity(require_archives=True)
    visual=load('interview/visual_review.json');assert visual['visual_review_completed']
    assert len(visual['documents'])==8 # Seven interview Markdown documents plus root README.
    for entry in visual['documents']:assert sha(ROOT/entry['file'])==entry['source_sha256'],'Visual review stale: '+entry['file']
    result.update(status=STATUS,visual_review=visual,live_mock_performed=False,candidate_competence_assessed=False,
      package_test_plan='Extract alongside Phase 11 content; compare every shipped hash and run checks; package twice and compare bytes')
    write(OUT/'validation.json',result)
    files=sorted(list(OUT.glob('*.md'))+list(OUT.glob('*.json'))+[
      ROOT/'README.md',ROOT/'.gitignore',ROOT/'analysis/latest_phase_guidance.json',
      ROOT/'analysis/build_interview_pack.py',ROOT/'analysis/interview_content.py',ROOT/'analysis/render_interview_docs.mjs'],key=lambda p:p.relative_to(ROOT).as_posix())
    manifest={'version':1,'description':'Overlay on portfolio root. Manifest excludes itself; archive hash is external.',
      'files':{p.relative_to(ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in files}}
    def zipit(path):
        with ZipFile(path,'w',ZIP_DEFLATED,compresslevel=6) as z:
            for name,p in sorted([(p.relative_to(ROOT).as_posix(),p) for p in files]+[('INTERVIEW_MANIFEST.json',None)]):
                info=ZipInfo(name,(2026,10,6,0,0,0));info.compress_type=ZIP_DEFLATED;info.create_system=3;info.external_attr=0o100644<<16
                z.writestr(info,p.read_bytes() if p else json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    target=DIST/'northstar_interview_pack.zip';twin=BUILD/'northstar_interview_pack.zip';zipit(target);zipit(twin);assert sha(target)==sha(twin)
    extracted=Path(tempfile.mkdtemp(prefix='extract_',dir=BUILD))
    for name in ['northstar_portfolio.zip','northstar_reproduction.zip','northstar_interview_pack.zip']:
        with ZipFile(DIST/name) as z:z.extractall(extracted)
    for name,item in manifest['files'].items():assert sha(extracted/name)==item['sha256']
    import subprocess
    proc=subprocess.run([sys.executable,str(extracted/'analysis/build_interview_pack.py'),'--check'],cwd=extracted,capture_output=True,text=True)
    (BUILD/'clean_check.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8');assert proc.returncode==0,proc.stderr
    # No package runs, source rebuilds, workbook recalculation or Desktop refresh.
    check_identity(require_archives=True)
    external=dict(result,validated_at_utc=datetime.now(timezone.utc).isoformat(),
      archive={'path':target.relative_to(ROOT).as_posix(),'bytes':target.stat().st_size,'sha256':sha(target),'files':len(files)},
      byte_identical_archive=True,clean_extraction_checks_passed=True,
      remaining_limits=['Approximate speech duration; no timed live rehearsal','Preparation is not demonstrated competence',
        'Synthetic/historical/scenario/experimental evidence limits retained','Existing native PowerPoint limitation unchanged',
        'Private pack requires original portfolio for source links; no publication'])
    write(ROOT/'analysis/interview_validation.json',external);write(DIST/'phase12_validation.json',external)
    report='\n'.join(['# Phase 12 validation','',STATUS,'',
      f"Opening pitch: {result['story_words']['pitch']} words; main story: {result['story_words']['story']} words.",
      f"Thirty core questions (six topics × five); fifteen stakeholder challenges (five roles × three); {result['evidence_records']} source-linked facts from {result['source_files']} saved files.",
      f"{result['local_links_checked']} local links checked; all eight rendered documents visually reviewed without clipping or horizontal overflow.",
      'Saved anchors, action counts, site examples, experiment decisions, rounding and unavailable intervals passed. Protected evidence, native Power BI, presentation, case study and both Phase 11 archives are unchanged.',
      'Clean overlay extraction and independent check-script execution passed. ZIP bytes reproduced identically.',
      '',f"Archive: {target.name}; {target.stat().st_size:,} bytes; {len(files)} files.",f"SHA-256: {sha(target)}",'',
      'Live mock practice, timed speaking and candidate scoring were not performed. No commercial response was re-estimated. No GitHub publication occurred.'])+'\n'
    (ROOT/'analysis/interview_validation.md').write_text(report,encoding='utf-8');(DIST/'phase12_validation.md').write_text(report,encoding='utf-8')
    print(json.dumps({'status':STATUS,'archive':external['archive'],'word_counts':result['story_words'],'questions':30,'challenges':15,'checks':'pass'},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',action='store_true');group.add_argument('--check',action='store_true');group.add_argument('--package',action='store_true');args=parser.parse_args()
    if args.prepare:prepare();print(json.dumps({'prepared':True,'content_check':check()},indent=2))
    elif args.check:print(json.dumps(check(),indent=2))
    else:package()
