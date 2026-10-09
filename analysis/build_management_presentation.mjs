import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const skill='C:/Users/prave/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const runtimePython='C:/Users/prave/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const build=path.join(root,'analysis/.presentation_build');
const out=path.join(root,'presentation');
await fs.mkdir(out,{recursive:true});
const data=JSON.parse(await fs.readFile(path.join(build,'inputs.json'),'utf8'));
const {resolvePresentationFont,applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const font=resolvePresentationFont({fontFamily:'Arial'});
const C={navy:'#18344B',teal:'#008E87',red:'#B54452',amber:'#9B6700',muted:'#536674',light:'#E7EFF2',white:'#FFFFFF'};
const p=Presentation.create({slideSize:{width:1280,height:720}});
const money=x=>new Intl.NumberFormat('en-GB',{style:'currency',currency:'GBP',maximumFractionDigits:0}).format(x);
const num=x=>new Intl.NumberFormat('en-GB',{maximumFractionDigits:0}).format(x);
const pct=(x,d=2)=>`${(x*100).toFixed(d)}%`;
const signed=(x,d=2)=>`${x>0?'+':''}${pct(x,d)}`;
const k=x=>`£${(x/1000).toFixed(0)}k`;
const million=x=>`£${(x/1e6).toFixed(2)}m`;
const notes=[];
const titles=[];
function text(s,str,x,y,w,h,size=24,color=C.navy,bold=false){
 const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=str;sh.text.style={typeface:font,fontSize:size,color,bold,autoFit:'none',verticalAlignment:'top',wrap:'square',insets:{left:0,right:0,top:0,bottom:0}};
 return sh;
}
function slide(title,footer,note){
 const s=p.slides.add();s.background.fill=C.white;
 text(s,title,64,46,1152,110,43,C.navy,true);
 text(s,footer,64,655,1116,42,16,C.muted);
 text(s,String(p.slides.items.length).padStart(2,'0'),1190,661,35,28,16,C.muted);
 s.speakerNotes.textFrame.setText(note);notes.push(note);titles.push(title);return s;
}
function table(s,values,x,y,widths,height,size=24,padding=7){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:widths.reduce((a,b)=>a+b,0),height,columnWidths:widths,values});
 t.borders.assign({style:'solid',fill:C.light,width:.7});
 t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({margins:{left:12,right:12,top:padding,bottom:padding}});
 for(let r=0;r<values.length;r++){
   t.rows[r].height=height/values.length;
   for(let c=0;c<values[0].length;c++){
     const cell=t.getCell(r,c);cell.fill=r===0?C.navy:(r%2===0?'#F1F5F6':C.white);
     cell.text.style={typeface:font,fontSize:size,color:r===0?C.white:C.navy,bold:r===0,verticalAlignment:'middle',autoFit:'none'};
   }
 }
 return t;
}
function chart(s,type,config){
 // Twelve significant digits preserve displayed precision and fit Excel's 15-digit limit.
 config={...config,series:config.series.map(sr=>({...sr,values:sr.values?.map(v=>Number(v.toPrecision(12))),xValues:sr.xValues?.map(v=>Number(v.toPrecision(12)))}))};
 const ch=s.charts.add(type,{chartFill:C.white,plotAreaFill:C.white,chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0},...config});
 applyPresentationChartFont(ch,{fontFamily:font});return ch;
}
const hist=m=>data.history.find(r=>r.metric===m);
const exp=m=>data.experiment_primary.find(r=>r.metric===m);
const portfolio=data.portfolio.find(r=>r.variant==='base'&&r.case==='Base');
const a24=data.baseline['2024'],a25=data.baseline['2025'];

// 1. Executive recommendation, which also serves as the project cover.
{
 const title='UK Gym Pricing & Revenue Optimisation';
 const note=`Executive recommendation: evaluate a controlled £1 pilot before wider implementation. Phase 7 identifies 11 conditional raises: 10 at £1 and one at £2. Their January–December 2026 Base scenario produces ${money(portfolio.incremental_revenue)} incremental net revenue and ${num(portfolio.member_difference)} December members versus the same no-increase counterfactual. The 95% conditional parameter range is ${money(portfolio.incremental_revenue_lower)} to ${money(portfolio.incremental_revenue_upper)}. TEST FIRST gains are excluded. The planned £1 experiment tests five first-repricing pairs as primary and two repeat pairs as exploratory. Its simulated results do not establish new evidence or authorise implementation. Sources: data/gym_recommendations.csv; data/recommendation_portfolio.csv; data/experiment_estimates.csv; analysis/experiment_report.md.`;
 const s=p.slides.add();s.background.fill=C.navy;
 text(s,'NORTHSTAR FITNESS',64,46,1100,36,23,'#72D3C9',true);
 text(s,'UK Gym Pricing &\nRevenue Optimisation',64,117,1110,174,64,C.white,true);
 text(s,'Identifying Site-Level Pricing Headroom Across an 80-Gym Estate',64,305,1090,60,25,'#D8E8EE');
 text(s,'A controlled £1 pilot precedes wider price increases',64,402,1120,86,40,C.white,true);
 text(s,`${k(portfolio.incremental_revenue)} modelled annual uplift across 11 conditional raises`,64,510,1110,55,31,'#72D3C9');
 text(s,'Hypothetical 2026 assessment. Controlled testing remains a condition of implementation.',64,600,1110,55,22,'#D8E8EE');
 s.speakerNotes.textFrame.setText(note+'\n\n'+data.disclaimers.join('\n'));notes.push(note);titles.push(title);
}

// 2. Baseline and exact descriptive bridge.
{
 const note=`2025 net revenue ${money(a25.total_revenue)} versus ${money(a24.total_revenue)} in 2024, a ${pct(a25.total_revenue/a24.total_revenue-1)} increase. December member stock fell from ${num(a24.closing_members)} to ${num(a25.closing_members)}, ${signed(a25.closing_members/a24.closing_members-1)}. The bridge uses mean monthly average members and total ARPMM. It allocates the interaction to ARPMM: member volume ${money(data.bridge.member_volume_contribution)}, total ARPMM ${money(data.bridge.total_arpmm_contribution)}, total change ${money(a25.total_revenue-a24.total_revenue)}. Total ARPMM includes membership mix, joining fees and ancillary income. This is descriptive accounting, not a causal estimate of repricing. Churn is monthly opening-exposure-weighted, and members are stocks rather than unique people. Sources: analysis/baseline_results.json; data/estate_monthly_trend.csv.`;
 const s=slide('2025 revenue grew 2.37% as members fell 0.67%','2025 versus matching 2024 months. Revenue excludes assumed 20% VAT. Bridge interaction belongs to total ARPMM.',note);
 text(s,'Change in annual net revenue, £m',64,177,730,38,25,C.navy,true);
 chart(s,'bar',{position:{left:65,top:223,width:720,height:318},categories:['Member volume','Total ARPMM','Net change'],series:[{name:'Net revenue change',values:[data.bridge.member_volume_contribution/1e6,data.bridge.total_arpmm_contribution/1e6,(a25.total_revenue-a24.total_revenue)/1e6],fill:C.teal,points:[{idx:0,fill:C.red},{idx:2,fill:C.navy}],valuesFormatCode:'0.000'}],barOptions:{direction:'column',grouping:'clustered',gapWidth:90},hasLegend:false,xAxis:{tickLabelPosition:'low',textStyle:{fontSize:21,fill:C.navy},majorGridlines:null},yAxis:{min:-1,max:3.5,majorUnit:1,numberFormatCode:'0.0',textStyle:{fontSize:18,fill:C.muted},majorGridlines:{fill:C.light,width:.7}},dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:22,bold:true,fill:C.navy}}});
 const facts=[[million(a25.total_revenue),'2025 earned net revenue'],[num(a25.closing_members),'December closing members'],[`£${a25.arpmm.toFixed(2)}`,'Total ARPMM, +2.79%'],[num(a25.new_members),'Annual joins, −0.13%']];
 facts.forEach((f,i)=>{text(s,f[0],865,185+i*97,345,47,38,C.navy,true);text(s,f[1],865,233+i*97,345,36,23,C.muted);});
 text(s,'Q4 recruitment weakened further: acquisitions fell 1.32% while revenue rose 2.05%.',64,578,1140,56,25,C.navy);
}

// 3. Recurring-price and retention landscape.
{
 const s=slide('31 gyms have no current recurring-price advantage','Competitor recurring prices include VAT. December 2025 snapshot. Churn uses full-year 2025 opening exposure.',`December 2025 competitor recurring price minus Northstar Standard headline price is positive when Northstar is cheaper. ${data.nonpositive_gaps} of 80 sites have a non-positive gap. ${data.headroom_segments['Investigation priority']} sites retain at least one baseline caution. The scatter is descriptive and does not estimate elasticity. Competitors and national-equivalent benchmarks are fictional proxies under the documented comparability assumption. Joining fees and introductory discounts remain separate. Sources: data/gym_headroom.csv; analysis/headroom_report.md.`);
 const series=[{name:'No baseline caution',rows:data.headroom.filter(r=>r.caution_flag_count===0),color:C.teal},{name:'Baseline caution',rows:data.headroom.filter(r=>r.caution_flag_count>0),color:C.red}].map(g=>({name:g.name,xValues:g.rows.map(r=>r.competitor_gap_dec2025),values:g.rows.map(r=>r.churn_rate_2025),fill:g.color,line:{fill:'none',width:0},marker:{symbol:'circle',size:7}}));
 chart(s,'scatter',{position:{left:58,top:185,width:745,height:398},series,scatterOptions:{style:'marker'},hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:20,fill:C.muted}},xAxis:{title:{text:'Competitor gap, £',textStyle:{fontSize:20,fill:C.navy}},min:-5,max:4,majorUnit:1,numberFormatCode:'£0',textStyle:{fontSize:19,fill:C.muted},majorGridlines:{fill:C.light,width:.6}},yAxis:{title:{text:'Monthly opening-base churn',textStyle:{fontSize:20,fill:C.navy}},min:.025,max:.065,majorUnit:.01,numberFormatCode:'0.0%',textStyle:{fontSize:19,fill:C.muted},majorGridlines:{fill:C.light,width:.6}}});
 text(s,'31',865,205,340,55,48,C.navy,true);text(s,'Sites with gap ≤ £0',865,268,340,65,27,C.muted);
 text(s,'38',865,355,340,55,48,C.red,true);text(s,'Sites with baseline caution',865,418,340,75,27,C.muted);
 text(s,'Median Standard price £25.99',865,540,340,62,27,C.navy,true);
}

// 4. Explain why relative score is supporting context only.
{
 const s=slide('High scores still require behavioural evidence','Headroom scores preserve Phase 4 ranks. Cautions remain separate from the 0–100 relative score.',`The weighted percentile score uses competitor gap 30%, low churn 25%, qualified conversion 15%, acquisition growth 15%, average monthly peak utilisation 10% and synthetic income 5%. Bands are High at 65, Medium 40 to less than 65, Low below 40. ${data.headroom_bands.High} sites have High scores and ${data.high_with_caution} of those retain caution flags. ${data.sensitive_sites} sites change band or move at least ten ranks under an alternative. Segment precedence gives investigation priority to caution flags. This score does not estimate willingness to pay. Sources: data/gym_headroom.csv; data/headroom_sensitivity.csv; analysis/headroom_config.json.`);
 const seg=['Stronger headroom indicators','Mixed indicators','Limited headroom indicators','Investigation priority'];
 chart(s,'bar',{position:{left:58,top:198,width:728,height:370},categories:seg.map(x=>x.replace(' indicators','')),series:[{name:'Gyms',values:seg.map(x=>data.headroom_segments[x]),fill:C.teal,points:[{idx:1,fill:'#597286'},{idx:2,fill:C.amber},{idx:3,fill:C.red}]}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:70},hasLegend:false,xAxis:{textStyle:{fontSize:20,fill:C.navy},majorGridlines:null},yAxis:{min:0,max:45,majorUnit:10,numberFormatCode:'0',textStyle:{fontSize:19,fill:C.muted},majorGridlines:{fill:C.light,width:.6}},dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:25,bold:true,fill:C.navy}}});
 text(s,'15',870,193,330,60,48,C.navy,true);text(s,'High scores across the estate',870,256,330,73,27,C.muted);
 text(s,'5',870,354,330,55,48,C.red,true);text(s,'High-score sites retain cautions',870,417,330,75,27,C.muted);
 text(s,'51 of 80 sites are sensitive to score specification',64,588,1136,42,27,C.navy,true);
}

// 5. Historical local response, with unabridged behavioural distinction.
{
 const s=slide('The historical £2 pilot gained revenue and lost joins','12 randomised pairs. Baseline Oct 2024–Mar 2025 versus Apr–Sep 2025. Monthly incumbent effects use percentage points.',`All twelve randomised pairs remain in the primary equal-pair analysis. Acquisition elasticity is ${hist('acquisition_elasticity').estimate.toFixed(3)}, with a 95% whole-pair interval ${hist('acquisition_elasticity').ci_lower.toFixed(3)} to ${hist('acquisition_elasticity').ci_upper.toFixed(3)}. It applies locally to Standard joining demand around the historical £2 policy, not to the entire member base. Cancellations and Standard-to-Off-Peak transfers are separate incumbent responses. Revenue is a control-derived six-month estimate across treated gyms. All pairs had positive pre-period gaps. Pre-trend imbalance, contemporary marketing, promotions and competitor changes limit transport. The 20 commercially selected increases stay observational and separate. Source: data/price_response_estimates.csv; analysis/response_report.md.`);
 const acq=hist('controlled_acquisition_response'),ch=hist('incumbent_churn_response_pp'),dg=hist('incumbent_downgrade_response_pp'),rev=hist('monthly_revenue_estimated_difference');
 table(s,[['Historical response','Point estimate','95% whole-pair interval'],['Standard acquisition',signed(acq.estimate),`${pct(acq.ci_lower)} to ${pct(acq.ci_upper)}`],['Incumbent monthly churn',`+${ch.estimate.toFixed(3)} pp`,`${ch.ci_lower.toFixed(3)} to ${ch.ci_upper.toFixed(3)} pp`],['Incumbent monthly downgrades',`+${dg.estimate.toFixed(3)} pp`,`${dg.ci_lower.toFixed(3)} to ${dg.ci_upper.toFixed(3)} pp`],['Estimated six-month net revenue',k(rev.estimate),`${k(rev.ci_lower)} to ${k(rev.ci_upper)}`]],64,190,[485,245,422],290,25);
 text(s,`Standard acquisition elasticity: ${hist('acquisition_elasticity').estimate.toFixed(2)}`,64,514,1130,52,32,C.navy,true);
 text(s,'The evidence covers one £2 policy in positive-gap markets. Repeat repricing and precise site responses remain uncertain.',64,580,1130,62,25,C.muted);
}

// 6. Conditional all-estate scenario comparisons.
{
 const s=slide('Estate-wide increases trade yield for fewer members','Jan–Dec 2026 Base scenarios across all 80 gyms. Same counterfactual. Ranges reflect conditional parameter uncertainty.',`The four scenarios start from December 2025's 396,311 ledger members. New Standard joiners see the increment on 1 January; eligible incumbents see it on 1 February or later at protection expiry. Legacy differences, promotional protection and historical obligations carry forward. Q4 site levels and observed regional seasonal drivers define the common trading counterfactual. Shared historical pilot responses affect acquisition, incumbent churn and downgrades separately. The ranges preserve joint whole-pair draws and exclude future shocks and transport uncertainty. Off-Peak and Plus headline prices stay unchanged. £3 is outside the action vocabulary and gives Standard/Plus headline equality at twenty previously +£2 sites. December ×12 is a separate seasonal run-rate, not earned annual revenue. Source: data/estate_scenarios.csv; analysis/scenario_report.md.`);
 const rows=data.scenarios.map(r=>[r.price_increment===0?'No increase':`+£${r.price_increment}`,million(r.incremental_revenue),`${million(r.incremental_revenue_lower)} to ${million(r.incremental_revenue_upper)}`,pct(r.member_impact),num(r.month12_members)]);
 table(s,[['Standard\nincrease','12-month\nnet uplift','95% parameter\nrange','December\nmember impact','December\nexpected members'],...rows],64,188,[150,235,320,205,242],318,23);
 text(s,'Higher modelled revenue accompanies fewer December members at every increase.',64,546,1130,55,28,C.navy,true);
 text(s,'+£3 is an analytical comparison. Standard reaches the unchanged Plus price at 20 gyms.',64,605,1130,43,23,C.muted);
}

// 7. Saved actions with all eleven conditional raise sites visible.
{
 const s=slide('Only 11 gyms qualify for conditional raises','Saved Phase 7 actions. Every increase remains conditional on controlled testing. TEST FIRST gains stay outside the raise portfolio.',`Apply the ordered Phase 7 rules using unrounded evidence. Baseline caution or missing decision evidence gives DEFENSIVE / INVESTIGATE. Plausibility needs positive Base revenue and a non-negative post-increase competitor gap. Qualification additionally needs positive Downside revenue, a positive 95% conditional lower revenue bound, no more than 5% Downside December member loss and positive revenue in every non-zero-behaviour sensitivity. Select the qualifying increment with higher Base revenue, preferring £1 on ties. Repeat repricing sends a qualifying candidate to TEST FIRST. If neither increment is plausible, HOLD PRICE. The 5% gate is a policy assumption, distinct from experimental limits. All eighty actions remain in data/gym_recommendations.csv. Sources: data/gym_recommendations.csv; analysis/recommendation_config.json.`);
 const labels=['RAISE £2','RAISE £1','TEST FIRST','HOLD PRICE','DEFENSIVE / INVESTIGATE'];
 chart(s,'bar',{position:{left:56,top:188,width:665,height:332},categories:['Raise £2','Raise £1','Test first','Hold price','Investigate'],series:[{name:'Gyms',values:labels.map(x=>data.action_counts[x]),fill:C.teal,points:[{idx:2,fill:C.amber},{idx:3,fill:'#597286'},{idx:4,fill:C.red}]}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:68},hasLegend:false,xAxis:{textStyle:{fontSize:23,fill:C.navy},majorGridlines:null},yAxis:{min:0,max:45,majorUnit:10,numberFormatCode:'0',textStyle:{fontSize:19,fill:C.muted},majorGridlines:{fill:C.light,width:.6}},dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:25,bold:true,fill:C.navy}}});
 const one=data.raise_sites.filter(r=>r.proposed_increment===1),two=data.raise_sites.find(r=>r.proposed_increment===2);
 const siteRows=[];for(let i=0;i<one.length;i+=2)siteRows.push(['£1',one.slice(i,i+2).map(r=>`${r.gym_id} ${r.city}`).join('\n')]);
 siteRows.push(['£2',`${two.gym_id} ${two.city}`]);
 table(s,[['Raise','Conditional sites'],...siteRows],768,188,[90,356],414,22,3);
 text(s,'Qualification tests downside revenue, member loss, lower-bound revenue and behavioural sensitivities.',64,551,650,79,25,C.navy);
}

// 8. Joint portfolio uncertainty and policy sensitivity.
{
 const s=slide('The £149k portfolio depends on management policy','Jan–Dec 2026 conditional RAISE portfolios. TEST FIRST excluded. Ranges exclude future shocks and transport uncertainty.',`The Base conditional-raise portfolio sums only saved RAISE increments. Every other gym uses the no-increase path. Base net uplift ${money(portfolio.incremental_revenue)}, December member difference ${num(portfolio.member_difference)} (${pct(portfolio.member_impact)}), conditional 95% range ${money(portfolio.incremental_revenue_lower)} to ${money(portfolio.incremental_revenue_upper)}. Portfolio ranges aggregate each selected site outcome within the same one of 10,000 joint draws before calculating quantiles; they never sum site endpoints. Downside and Upside use coherent shared parameter vectors, not every site's own best/worst outcome. Policy sensitivity changes judgement assumptions rather than re-estimating behaviour. TEST FIRST's provisional Base gains of ${money(portfolio.excluded_test_first_base_revenue)} remain excluded. Source: data/recommendation_portfolio.csv; analysis/recommendation_report.md.`);
 const policies=[['base','Agreed policy: 5% member gate'],['member_limit_3pct','3% downside member gate'],['member_limit_7pct','7% downside member gate'],['competitor_buffer_1gbp','£1 post-increase competitor buffer'],['allow_repeat_repricing','Repeat repricing permitted with warning']];
 const rows=policies.map(([variant,label])=>{const r=data.portfolio.find(x=>x.variant===variant&&x.case==='Base');return [label,String(r.raise_sites),k(r.incremental_revenue),pct(r.member_impact)];});
 table(s,[['Policy assumption','Raise sites','Annual net uplift','December\nmember impact'],...rows],64,187,[530,150,245,227],336,24);
 text(s,`Base portfolio: ${num(Math.abs(portfolio.member_difference))} fewer December members (${pct(portfolio.member_impact)})`,64,557,1140,46,29,C.navy,true);
 text(s,`95% parameter range ${k(portfolio.incremental_revenue_lower)} to ${k(portfolio.incremental_revenue_upper)}. Downside ${k(data.portfolio.find(r=>r.variant==='base'&&r.case==='Downside').incremental_revenue)}. Upside ${k(data.portfolio.find(r=>r.variant==='base'&&r.case==='Upside').incremental_revenue)}.`,64,609,1140,40,23,C.muted);
}

// 9. Small prospective design and illustrative simulated governance.
{
 const revenue=exp('revenue_effect');
 const pw=data.power.find(x=>Math.abs(x.effect_assumption-.02)<1e-8);
 const s=slide('The simulated £1 pilot is inconclusive at six months','Illustrative simulation. Primary comparison: Jul–Dec 2025 versus Jan–Jun 2026. These results do not add independent evidence.',`Seven matched same-region/same-prior-pricing pairs assign seven treatment gyms and seven controls. Five first-repricing pairs define the primary population, two repeat pairs remain exploratory, with unavailable intervals. NF023 Portsmouth and NF057 Leicester remain reserves. Notice and new-joiner prices start 1 January 2026; protected/eligible incumbent bills change from 1 February. Six-month primary decision EXTEND TEST: revenue effect ${pct(revenue.estimate)}, interval ${pct(revenue.lower)} to ${pct(revenue.upper)}, one-sided exact p ${revenue.p_value_one_sided}, two-sided ${revenue.p_value_two_sided}. Harm upper bounds are compared with management-assumed limits, equality passes. Twelve-month STOP arises because incumbent churn's lower bound ${data.experiment_sustained.find(r=>r.metric==='incumbent_churn_change_pp').lower.toFixed(3)} pp exceeds +0.250 pp. Actual five-pair exact-test planning power is ${pct(pw.planning_power,1)} at a 2% effect; its 80%-power detectable effect is ${pct(pw.effect_detectable_80pct)}. Minimum attainable one-sided p is 3.125%. Sources: data/experiment_estimates.csv; data/experiment_design.csv; data/experiment_power.csv; analysis/experiment_report.md.`);
 text(s,'5 primary pairs. 2 exploratory repeat pairs. 2 unmatched reserves.',64,172,1140,43,25,C.navy);
 text(s,'EXTEND TEST',64,247,430,49,36,C.amber,true);
 text(s,`${signed(revenue.estimate)} revenue`,64,314,440,53,38,C.navy,true);
 text(s,`95% interval ${pct(revenue.lower)} to ${pct(revenue.upper)}\nOne-sided p = ${revenue.p_value_one_sided.toFixed(4)}`,64,379,445,98,26,C.muted);
 const harms=[['Closing-member loss','member_harm',.03,false],['Standard acquisition loss','standard_acquisition_harm',.1,false],['Monthly churn, pp','incumbent_churn_change_pp',.25,true],['Monthly downgrades, pp','incumbent_downgrade_change_pp',.25,true]];
 const rows=harms.map(([label,metric,limit,pp])=>{const e=exp(metric);return [label,pp?`+${e.upper.toFixed(3)}`:pct(e.upper),pp?`+${limit.toFixed(3)}`:pct(limit),e.upper<=limit?'Pass':'Fail'];});
 const t=table(s,[['Controlled harm','95% upper','Limit','Gate'],...rows],548,235,[295,140,140,95],286,22);
 for(let i=1;i<=4;i++)t.getCell(i,3).text.style={typeface:font,fontSize:22,bold:true,color:rows[i-1][3]==='Pass'?C.teal:C.red};
 text(s,'Twelve months: STOP. The churn lower harm bound exceeds the tolerance.',64,542,1136,54,28,C.red,true);
 text(s,`Planning power at a 2% effect: ${pct(pw.planning_power,1)}. Detectable effect at 80% power: ${pct(pw.effect_detectable_80pct)}.`,64,600,1136,43,23,C.muted);
}

// 10. Concrete decision and boundaries, with both established disclosures.
{
 const s=slide('New evidence is needed before broader repricing','Hypothetical management proposal. Revenue improvement does not establish profit improvement.',`Decision supported: whether to resource a real controlled £1 test for comparable first-repricing sites and the investigations needed before wider implementation. Refresh site eligibility and competitor comparability using current observations, match prospectively and randomise after fixing pairs. A real calendar must replace the hypothetical 2026 programme. Keep repeat repricing exploratory and retain controls. Conduct approximately 30- and 90-day safety reviews, a six-month primary assessment and twelve-month follow-up. A rollout decision requires complete evidence, revenue lower bound above zero, primary one-sided p no more than 5%, and upper harm bounds within the 3% member, 10% Standard acquisition and +0.25 pp monthly churn/downgrade limits. Service complaints above two per 1,000 member-months or consecutive months at capacity prompt investigation. Excluded markets, repeated repricing, £2/£3 and competitor reactions need separate evidence. Finance should assess contribution costs, bad debt and collection economics before treating revenue as profit. Sources: analysis/experiment_config.json; analysis/experiment_report.md; analysis/recommendation_report.md.\n\n${data.disclaimers.join('\n')}`);
 const items=[
 ['A real £1 pilot needs fresh eligibility and prospective assignment','Comparable first-repricing sites form the primary population. Repeat repricing remains exploratory.'],
 ['Safety reviews precede the six-month commercial assessment','Approximately 30 and 90 days, then six months and twelve months. Study controls remain unchanged.'],
 ['Rollout depends on financial and member confidence bounds','Positive revenue lower bound, one-sided p ≤ 5%, and every harm upper bound within its tolerance.'],
 ['Finance and Operations must assess the remaining business risks','Contribution costs, competitor response, complaints and sustained service pressure need review.']
 ];
 items.forEach((it,i)=>{text(s,it[0],64,179+i*84,1152,38,26,C.navy,true);text(s,it[1],64,221+i*84,1152,36,23,C.muted);});
 text(s,data.disclaimers.join('\n\n'),64,546,1148,104,16,C.muted);
}

// Finalize the editable package, then render every saved slide for review.
const draft=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(draft);
const finalPath=path.join(out,process.argv[2]??'pricing_recommendation.pptx');
const result=await finalizePresentation({
 workspaceDir:root,candidatePath:draft,finalPath,pythonExecutable:runtimePython,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[5,6,7,8,9].flatMap(n=>['--require-native-table-slide',String(n)])],
 explicitTotalSlideCount:10,requiredNativeChartOwnerSlides:[2,3,4,7],requiredNativeTableOwnerSlides:[5,6,7,8,9],
 fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 materializeLiteralChartWorkbooks:true,receiptPath:path.join(build,`validation-${Date.now()}.json`)
});
await fs.writeFile(path.join(build,'latest_validation.json'),JSON.stringify(result,null,2));
await fs.writeFile(path.join(build,'notes.json'),JSON.stringify({titles,notes,font,finalPath},null,2));
const {FileBlob}=await import('@oai/artifact-tool');
const saved=await PresentationFile.importPptx(await FileBlob.load(finalPath));
await fs.mkdir(path.join(build,'rendered'),{recursive:true});
for(let i=0;i<saved.slides.items.length;i++){
 const blob=await saved.export({slide:saved.slides.items[i],format:'png',scale:1.5});
 await fs.writeFile(path.join(build,'rendered',`slide-${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));
}
console.log(JSON.stringify({finalPath,slides:saved.slides.items.length,font,receiptPath:result.receiptPath,layoutWarnings:result.presentationLayout.warnings},null,2));
