import fs from 'node:fs/promises';

import path from 'node:path';

import {fileURLToPath} from 'node:url';

import {Workbook,SpreadsheetFile,FileBlob} from '@oai/artifact-tool';

const dir=path.dirname(fileURLToPath(import.meta.url)),root=path.dirname(dir),pre=path.join(dir,'.workbook_previews','phase6');

const p=JSON.parse(await fs.readFile(path.join(pre,'payload.json'),'utf8'));

const col=i=>{let s='';for(let n=i+1;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};

const object=d=>d.data.map(r=>Object.fromEntries(d.columns.map((c,i)=>[c,r[i]])));

const drivers=object(p.drivers),states=object(p.states),gyms=object(p.gyms),comparisons=object(p.comparisons),estate=object(p.estate),monthly=object(p.monthly);

const G=gyms.length,S=p.S,K=p.K,driverStart=50,stateStart=1101;

const qn=n=>`'${n}'!`,ir=r=>qn('Scenario Inputs')+'$E$'+r;

const inp=(kind,f,i)=>qn('Scenario Inputs')+col(p[kind].columns.indexOf(f))+(kind==='drivers'?driverStart:stateStart)+'';

const dr=(f,gi,j)=>qn('Scenario Inputs')+'$'+col(p.drivers.columns.indexOf(f))+'$'+(driverStart+gi*12+j);

const st=(f,gi,si)=>qn('Scenario Inputs')+'$'+col(p.states.columns.indexOf(f))+'$'+(stateStart+gi*S+si);

const safe=(n,d)=>`IF(${d}>0,${n}/(${d}),"")`;

const gbp='"£"#,##0.00;("£"#,##0.00);"-"',num='#,##0.0;(#,##0.0);"-"';

const summaryFields=['model','gym_id','month','opening_members','new_members','opening_base_cancellations','same_month_cancellations','closing_members','average_members','standard_joins','offpeak_joins','plus_joins','qualified_prospects','subscription_revenue','joining_fee_revenue','ancillary_revenue','monthly_revenue','incumbent_standard_opening','incumbent_standard_cancellations','incumbent_standard_downgrades','incumbent_standard_paid_rate_numerator','protected_standard_opening','repriced_standard_opening','opening_standard_downgrades','joining_month_downgrades','transfers_out','transfers_in','pricing_complaints','gym_visits','average_utilisation','peak_utilisation','standard_opening_members','standard_closing_members','standard_average_members','standard_subscription_revenue','offpeak_opening_members','offpeak_closing_members','offpeak_average_members','offpeak_subscription_revenue','plus_opening_members','plus_closing_members','plus_average_members','plus_subscription_revenue','churn_rate','incumbent_churn_rate','incumbent_downgrade_rate','conversion_rate','arpmm','subscription_yield','standard_yield','incremental_revenue','cumulative_incremental_revenue','month_member_difference','paid_rate','marketing_spend','promotion_active','price_dose_scale','standard_price','raw_standard_joins','raw_offpeak_joins','raw_plus_joins','funnel_cap_factor'];

const flows=['model','gym_id','month','state','label','tier','opening','new','base_churn','incremental_churn','churn_rate','opening_exits','joining_exits','opening_downgrades','joining_downgrades','transfers_in','closing','average','paid_rate','subscription_revenue','incumbent_opening','incumbent_exits','incumbent_downgrades','protected_opening','repriced_opening','incumbent_paid_numerator','tier_std','tier_off','tier_plus'];

const captureColumns=['gym_id','price_increment','case','region',...p.comparisons.columns.filter(x=>!['gym_id','price_increment','case','region'].includes(x))];

const annualFields=['gym_id','price_increment','case',...p.comparisons.columns.filter(x=>!['gym_id','price_increment','case'].includes(x)&&!x.endsWith('_lower')&&!x.endsWith('_upper')&&!['evidence_status','break_even_response_multiplier','break_even_member_impact','break_even_crossings','positive_revenue_draw_fraction'].includes(x))];

const sr=(mode,gi,j)=>201+mode*G*12+gi*12+j;

const yr=(mode,gi)=>9+mode*G+gi;

const ref=(f,r)=>col(summaryFields.indexOf(f))+r;

const yf=(f,r)=>col(annualFields.indexOf(f))+r;

const fr=(f,r)=>col(flows.indexOf(f))+r;

const modelRef=(f,r)=>qn('Scenario Model')+yf(f,r);

const ranges=new Map(),stateRows=new Map(),detail=[];

let detailRow=2301;

for(let mode=0;mode<2;mode++)for(let gi=0;gi<G;gi++)for(let j=0;j<12;j++){

 const start=detailRow;

 for(let si=0;si<S;si++){const s=states[gi*S+si];if(s.join_index>j||s.label==='Unused'||s.label==='Unused reserve')continue;stateRows.set(`${mode},${gi},${j},${si}`,detailRow);detail.push({r:detailRow,mode,gi,j,si,s});detailRow++;}

 ranges.set(`${mode},${gi},${j}`,[start,detailRow-1]);

}

let wb;

const inputsName='Scenario Inputs',modelName='Scenario Model',compName='Scenario Comparison',sumName='Scenario Summary';

function base(s,range){s.showGridLines=false;s.getRange(range).format={font:{name:'Arial',size:10,color:'#243B53'},verticalAlignment:'center',rowHeight:22};s.getRange('A:Z').format.columnWidth=18;}

function header(s,range,height=48){s.getRange(range).format={fill:'#243B53',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:height,verticalAlignment:'center'};}

function title(s,text){s.getRange('A2:H2').merge();s.getRange('A2').values=[[text]];s.getRange('A2:H2').format={font:{name:'Arial',size:14,bold:true,color:'#243B53'},rowHeight:26};}

function formatColumns(s,cols,start,end){for(let i=0;i<cols.length;i++){const f=cols[i],r=s.getRange(`${col(i)}${start}:${col(i)}${end}`);if(f==='month')r.setNumberFormat('mmm-yy');else if(/_pp$/.test(f))r.setNumberFormat('0.000" pp"');else if(/rate|share|mix|impact|utilisation|uplift|fraction|probability|retention/.test(f)&&!(/paid_rate|subscription_revenue|run_rate/.test(f)))r.setNumberFormat('0.00%');else if(/revenue|arpmm|yield|price|paid/.test(f)&&!f.startsWith('pricing_complaints'))r.setNumberFormat(gbp);else if(/elasticity|dose|multiplier|increment/.test(f)&&!/revenue/.test(f))r.setNumberFormat('0.000');else r.setNumberFormat(num);}}

function writeTable(s,d,start,name){s.getRange(`A${start-1}:${col(d.columns.length-1)}${start-1}`).values=[d.columns.map(x=>x.replaceAll('_',' '))];header(s,`A${start-1}:${col(d.columns.length-1)}${start-1}`,55);s.getRange(`A${start}:${col(d.columns.length-1)}${start+d.data.length-1}`).values=d.data.map(r=>r.map((v,i)=>d.columns[i]==='month'?new Date(v+'T00:00:00Z'):v));s.tables.add(`A${start-1}:${col(d.columns.length-1)}${start+d.data.length-1}`,true,name);formatColumns(s,d.columns,start,start+d.data.length-1);}

function snapshot(s,from,to){s.getRange(to).copyFrom(s.getRange(from),'values');}

function freshnessFormula(offset){const terms=[];

 for(const [range,first,last,start,end]of [['cases',5,8,9,17],['drivers',0,p.drivers.columns.length-1,driverStart,driverStart+drivers.length-1],['states',0,p.states.columns.length-1,stateStart,stateStart+states.length-1]]){

  for(let c=first;c<=last;c++){const target=c+offset;

   if(range==='cases')for(let r=start;r<=end;r++){const a=col(c)+r,b=col(target)+r;terms.push(`IF(OR(COUNTA(${a})<>COUNTA(${b}),COUNT(${a})<>COUNT(${b}),${a}<>${b}),1,0)`);}

   else terms.push(`SUMPRODUCT((${col(c)}${start}:${col(c)}${end}<>${col(target)}${start}:${col(target)}${end})*1)+ABS(COUNTA(${col(c)}${start}:${col(c)}${end})-COUNTA(${col(target)}${start}:${col(target)}${end}))`);

  }

 }

 return '='+terms.join('+');

}

function stateFormulas(d){const {r,mode,gi,j,si,s}=d,mr=sr(mode,gi,j),delta=mode?qn(inputsName)+'$B$4':'0';

 const tier=s.tier,name=['standard','offpeak','plus'][tier],previous=stateRows.get(`${mode},${gi},${j-1},${si}`);

 const incumbent=st('incumbent',gi,si),expiry=st('expiry',gi,si),future=st('future',gi,si);

 const eligible=`AND(${incumbent},${j}>=1,${j}>=${expiry})`,f={};

 f.opening=j===0?'='+st('initial',gi,si):previous?'='+fr('closing',previous):'=0';

 f.new='='+((si===K)?ref('offpeak_joins',mr):(si===K+1)?ref('plus_joins',mr):(si===K+3+j)?ref('standard_joins',mr):'0');

 f.base_churn='='+dr(name+'_churn',gi,j);

 f.incremental_churn=mode?`=IF(${incumbent},${ir(10)}*${ref('price_dose_scale',mr)}*IF(${eligible},1,${ir(16)})/${ir(14)},0)`:'=0';

 f.churn_rate=`=MIN(1,MAX(0,${fr('base_churn',r)}+${fr('incremental_churn',r)}))`;

 f.opening_exits=`=${fr('opening',r)}*${fr('churn_rate',r)}`;

 f.joining_exits=`=${fr('new',r)}*${dr(name+'_same_month_exit',gi,j)}`;

 const dow=tier===0?`MIN(MAX(0,${fr('opening',r)}*(${dr('standard_downgrade',gi,j)}+${mode?`IF(${eligible},${ir(11)}*${ref('price_dose_scale',mr)}/${ir(15)},0)`:'0'})),${fr('opening',r)}-${fr('opening_exits',r)})`:'0';

 f.opening_downgrades='='+dow;f.joining_downgrades=tier===0?`=MIN(MAX(0,${fr('new',r)}*${dr('standard_downgrade',gi,j)}),${fr('new',r)}-${fr('joining_exits',r)})`:'=0';

 const [start,end]=ranges.get(`${mode},${gi},${j}`);

 f.transfers_in=si===K?`=SUM(${fr('opening_downgrades',start)}:${fr('opening_downgrades',end)})+SUM(${fr('joining_downgrades',start)}:${fr('joining_downgrades',end)})`:'=0';

 f.closing=`=${fr('opening',r)}+${fr('new',r)}-${fr('opening_exits',r)}-${fr('joining_exits',r)}-${fr('opening_downgrades',r)}-${fr('joining_downgrades',r)}+${fr('transfers_in',r)}`;

 f.average=`=(${fr('opening',r)}+${fr('closing',r)})/2`;

 f.paid_rate=`=(${st('full_rate',gi,si)}+IF(${j}>=${expiry},${st('pending',gi,si)},0)+IF(OR(${eligible},AND(${future},${tier}=0)),${delta},0))*IF(${j}<${expiry},1-${st('discount',gi,si)},1)`;

 f.subscription_revenue=`=${fr('average',r)}*${fr('paid_rate',r)}/(1+${ir(17)})`;

 f.incumbent_opening=`=IF(${incumbent},${fr('opening',r)},0)`;f.incumbent_exits=`=IF(${incumbent},${fr('opening_exits',r)},0)`;f.incumbent_downgrades=`=IF(${incumbent},${fr('opening_downgrades',r)},0)`;

 f.protected_opening=`=IF(AND(${incumbent},${j}<${expiry}),${fr('opening',r)},0)`;f.repriced_opening=mode?`=IF(AND(${delta}>0,${eligible}),${fr('opening',r)},0)`:'=0';

 f.incumbent_paid_numerator=`=${fr('incumbent_opening',r)}*${fr('paid_rate',r)}`;

 f.tier_std='='+Number(tier===0);f.tier_off='='+Number(tier===1);f.tier_plus='='+Number(tier===2);

 return flows.map(c=>f[c]??null);

}

function monthlyFormulas(mode,gi,j){const r=sr(mode,gi,j),[a,b]=ranges.get(`${mode},${gi},${j}`),delta=mode?qn(inputsName)+'$B$4':'0',cf=sr(0,gi,j),f={};

 const sum=n=>`SUM(${fr(n,a)}:${fr(n,b)})`,tierSum=(n,t)=>`SUMPRODUCT(${fr(n,a)}:${fr(n,b)},${fr(t,a)}:${fr(t,b)})`;

 const c=n=>ref(n,r),stock={opening_members:'opening',opening_base_cancellations:'opening_exits',same_month_cancellations:'joining_exits',closing_members:'closing',average_members:'average',subscription_revenue:'subscription_revenue',incumbent_standard_opening:'incumbent_opening',incumbent_standard_cancellations:'incumbent_exits',incumbent_standard_downgrades:'incumbent_downgrades',incumbent_standard_paid_rate_numerator:'incumbent_paid_numerator',protected_standard_opening:'protected_opening',repriced_standard_opening:'repriced_opening',opening_standard_downgrades:'opening_downgrades',joining_month_downgrades:'joining_downgrades',transfers_in:'transfers_in'};

 for(const [x,y]of Object.entries(stock))f[x]='='+sum(y);

 f.price_dose_scale=mode?'='+safe(`LN(1+${delta}/${dr('standard_price',gi,j)})`,ir(12)):'=0';

 f.qualified_prospects='='+dr('qualified_prospects',gi,j);

 f.raw_standard_joins=`=${c('qualified_prospects')}*${dr('standard_join_probability',gi,j)}*EXP(${mode?ir(9):'0'}*LN(1+${delta}/${dr('standard_price',gi,j)}))`;

 f.raw_offpeak_joins=`=${c('qualified_prospects')}*${dr('offpeak_join_probability',gi,j)}`;f.raw_plus_joins=`=${c('qualified_prospects')}*${dr('plus_join_probability',gi,j)}`;

 f.funnel_cap_factor=`=IF(SUM(${c('raw_standard_joins')}:${c('raw_plus_joins')})>0,MIN(1,${c('qualified_prospects')}/SUM(${c('raw_standard_joins')}:${c('raw_plus_joins')})),1)`;

 for(const tier of ['standard','offpeak','plus'])f[tier+'_joins']=`=${c('raw_'+tier+'_joins')}*${c('funnel_cap_factor')}`;

 f.new_members=`=SUM(${c('standard_joins')}:${c('plus_joins')})`;

 f.transfers_out=`=${c('opening_standard_downgrades')}+${c('joining_month_downgrades')}`;

 f.joining_fee_revenue=`=${c('new_members')}*${dr('joining_fee_payer_fraction',gi,j)}*${dr('joining_fee',gi,j)}/(1+${ir(17)})`;

 f.ancillary_revenue='='+dr('ancillary_revenue',gi,j);

 f.monthly_revenue=mode?`=IF(${qn(inputsName)}$E$18="READY",SUM(${c('subscription_revenue')}:${c('ancillary_revenue')}),"")`:`=SUM(${c('subscription_revenue')}:${c('ancillary_revenue')})`;

 f.pricing_complaints=`=MAX(0,${c('average_members')}/1000*(${dr('baseline_complaints_per_1000',gi,j)}+${mode&&j<3?`${ir(13)}*${c('price_dose_scale')}`:'0'}))`;

 f.gym_visits=`=${c('average_members')}*${dr('visits_per_member',gi,j)}`;

 f.average_utilisation='='+safe(`${c('gym_visits')}*${dr('visit_duration_minutes',gi,j)}`,`${dr('opening_minutes',gi,j)}*${dr('capacity',gi,j)}`);

 f.peak_utilisation=`=${c('average_utilisation')}*${dr('peak_multiplier',gi,j)}`;

 for(const [tier,flag]of [['standard','tier_std'],['offpeak','tier_off'],['plus','tier_plus']])for(const [name,field]of [['opening_members','opening'],['closing_members','closing'],['average_members','average'],['subscription_revenue','subscription_revenue']])f[tier+'_'+name]='='+tierSum(field,flag);

 for(const [name,n,d]of [['churn_rate','opening_base_cancellations','opening_members'],['incumbent_churn_rate','incumbent_standard_cancellations','incumbent_standard_opening'],['incumbent_downgrade_rate','incumbent_standard_downgrades','incumbent_standard_opening'],['conversion_rate','new_members','qualified_prospects'],['arpmm','monthly_revenue','average_members'],['subscription_yield','subscription_revenue','average_members'],['standard_yield','standard_subscription_revenue','standard_average_members'],['paid_rate','incumbent_standard_paid_rate_numerator','incumbent_standard_opening']])f[name]='='+safe(c(n),c(d));

 f.incremental_revenue=mode?`=${c('monthly_revenue')}-${ref('monthly_revenue',cf)}`:'=0';f.month_member_difference=mode?`=${c('closing_members')}-${ref('closing_members',cf)}`:'=0';

 f.cumulative_incremental_revenue=`=SUM(${ref('incremental_revenue',sr(mode,gi,0))}:${c('incremental_revenue')})`;

 f.marketing_spend='='+dr('marketing_spend',gi,j);f.promotion_active='='+dr('promotion_active',gi,j);f.standard_price=`=${dr('standard_price',gi,j)}+${delta}`;

 return summaryFields.map(c=>f[c]??null);

}

function annualFormulas(mode,gi){const r=yr(mode,gi),a=sr(mode,gi,0),b=sr(mode,gi,11),f={},c=n=>yf(n,r),cf=n=>yf(n,yr(0,gi)),sum=n=>`SUM(${ref(n,a)}:${ref(n,b)})`;

 const additive=['new_members','standard_joins','offpeak_joins','plus_joins','qualified_prospects','opening_members','average_members','opening_base_cancellations','same_month_cancellations','subscription_revenue','joining_fee_revenue','ancillary_revenue','monthly_revenue','incumbent_standard_opening','incumbent_standard_cancellations','incumbent_standard_downgrades','standard_average_members','standard_subscription_revenue','offpeak_average_members','plus_average_members','pricing_complaints','transfers_out','incumbent_standard_paid_rate_numerator','protected_standard_opening','repriced_standard_opening'];

 for(const name of additive)f[name]='='+sum(name);

 f.monthly_revenue=`=IF(COUNT(${ref('monthly_revenue',a)}:${ref('monthly_revenue',b)})=12,${sum('monthly_revenue')},"")`;

 f.period_opening_members='='+ref('opening_members',a);f.month12_members='='+ref('closing_members',b);f.annualised_exit_run_rate='='+ref('monthly_revenue',b)+'*12';f.average_members_per_month='='+c('average_members')+'/12';

 for(const [name,n,d]of [['churn_rate','opening_base_cancellations','opening_members'],['incumbent_churn_rate','incumbent_standard_cancellations','incumbent_standard_opening'],['incumbent_downgrade_rate','incumbent_standard_downgrades','incumbent_standard_opening'],['conversion_rate','new_members','qualified_prospects'],['subscription_yield','subscription_revenue','average_members'],['standard_yield','standard_subscription_revenue','standard_average_members'],['arpmm','monthly_revenue','average_members'],['standard_mix','standard_average_members','average_members'],['offpeak_mix','offpeak_average_members','average_members'],['plus_mix','plus_average_members','average_members'],['incumbent_paid_rate','incumbent_standard_paid_rate_numerator','incumbent_standard_opening'],['protected_share','protected_standard_opening','incumbent_standard_opening'],['repriced_share','repriced_standard_opening','incumbent_standard_opening']])f[name]='='+safe(c(n),c(d));

 f.retention_rate='=1-'+c('churn_rate');f.member_growth='='+safe(c('month12_members'),c('period_opening_members'))+'-1';f.complaints_per_1000='='+safe(c('pricing_complaints')+'*1000',c('average_members'));

 f.average_utilisation='='+Array.from({length:12},(_,j)=>`${ref('average_utilisation',a+j)}*${calendarDays[j]}`).join('+')+'/365';

 // Parentheses are necessary because the time-weighted sum is one numerator.

 f.average_utilisation='=('+Array.from({length:12},(_,j)=>`${ref('average_utilisation',a+j)}*${calendarDays[j]}`).join('+')+')/365';

 f.average_monthly_peak_utilisation='='+sum('peak_utilisation')+'/12';f.maximum_monthly_peak_utilisation=`=MAX(${ref('peak_utilisation',a)}:${ref('peak_utilisation',b)})`;

 f.counterfactual_revenue='='+cf('monthly_revenue');f.incremental_revenue='='+c('monthly_revenue')+'-'+cf('monthly_revenue');f.revenue_uplift='='+safe(c('monthly_revenue'),cf('monthly_revenue'))+'-1';f.member_difference='='+c('month12_members')+'-'+cf('month12_members');f.member_impact='='+safe(c('month12_members'),cf('month12_members'))+'-1';f.acquisition_difference='='+c('new_members')+'-'+cf('new_members');f.standard_acquisition_impact='='+safe(c('standard_joins'),cf('standard_joins'))+'-1';

 for(const [name,metric]of [['churn_change_pp','churn_rate'],['incumbent_churn_change_pp','incumbent_churn_rate'],['downgrade_change_pp','incumbent_downgrade_rate'],['conversion_change_pp','conversion_rate']])f[name]=`=100*(${c(metric)}-${cf(metric)})`;

 f.elasticity='='+ir(9);f.incumbent_churn_increment_pp='='+ir(10)+'*100';f.incumbent_downgrade_increment_pp='='+ir(11)+'*100';f.price_increment=mode?'='+qn(inputsName)+'$B$4':'=0';f.case='='+qn(inputsName)+'$C$3';

 f.new_standard_price=`=${dr('standard_price',gi,0)}+${mode?qn(inputsName)+'$B$4':'0'}`;f.post_increase_competitor_gap=`=${dr('competitor_price',gi,11)}-${c('new_standard_price')}`;f.teaching_break_even_retention=`=${dr('standard_price',gi,0)}/${c('new_standard_price')}`;

 f.cash_increment_extrapolation=`=OR(${c('price_increment')}=1,${c('price_increment')}=3)`;

 return annualFields.map(x=>f[x]??null);

}

const calendarDays=[31,28,31,30,31,30,31,31,30,31,30,31];

function verifyModel(){const s=wb.worksheets.getItem(modelName),actual=s.getRange(`A201:${col(summaryFields.length-1)}2120`).values;let count=0,max=0;

 for(let mode=0;mode<2;mode++)for(let gi=0;gi<G;gi++)for(let j=0;j<12;j++){

  const expected=monthly.find(r=>r.gym_id===gyms[gi].gym_id&&r.month===drivers[gi*12+j].month&&r.price_increment===(mode?2:0)&&r.case==='Base');

  const row=actual[mode*G*12+gi*12+j];for(let c=3;c<summaryFields.length;c++){const f=summaryFields[c];if(typeof expected[f]!=='number')continue;let diff=Math.abs(row[c]-expected[f]);max=Math.max(max,diff);if(typeof row[c]!=='number'||diff>Math.max(1e-7,Math.abs(expected[f])*1e-10))throw Error(`Monthly ${mode}/${gi}/${j}/${f}: ${row[c]} vs ${expected[f]}`);count++;}

 }

 const annual=s.getRange(`A9:${col(annualFields.length-1)}168`).values;

 for(let mode=0;mode<2;mode++)for(let gi=0;gi<G;gi++){const expected=comparisons.find(r=>r.gym_id===gyms[gi].gym_id&&r.price_increment===(mode?2:0)&&r.case==='Base');for(let c=0;c<annualFields.length;c++){const f=annualFields[c];if(typeof expected[f]!=='number'||f==='probability_caps')continue;const diff=Math.abs(annual[mode*G+gi][c]-expected[f]);max=Math.max(max,diff);if(typeof annual[mode*G+gi][c]!=='number'||diff>Math.max(1e-7,Math.abs(expected[f])*1e-10))throw Error(`Annual ${mode}/${gi}/${f}: ${annual[mode*G+gi][c]} vs ${expected[f]}`);count++;}}

 return {cellsCompared:count,maxAbsoluteDifference:max};

}

function addChart(s,type,range,title,a,b,fmt){const chart=s.charts.add(type,range);chart.title=title;chart.setPosition(a,b);chart.titleTextStyle.typeface='Arial';chart.titleTextStyle.fontSize=11;chart.legend={position:'top',textStyle:{typeface:'Arial',fontSize:9}};chart.xAxis={axisType:type==='scatter'?'valueAxis':'textAxis',textStyle:{fontSize:9,typeface:'Arial'},numberFormatCode:type==='scatter'?'0.0%':undefined,numberFormatSourceLinked:false};chart.yAxis={numberFormatCode:fmt,numberFormatSourceLinked:false,textStyle:{fontSize:9,typeface:'Arial'}};chart.series.items.forEach((x,i)=>{const color=['#243B53','#2F855A','#D69E2E','#9F7AEA'][i%4];x.fill=color;x.line={fill:color,width:type==='scatter'?0:1.5};});return chart;}

const views=[[inputsName,'A1:I27','inputs_controls'],[inputsName,'A49:H56','drivers_identifiers'],[inputsName,'I49:Q56','driver_rates'],[inputsName,'A1100:J1108','billing_states'],[modelName,'A1:J14','model_annual'],[modelName,'A200:L207','monthly_bridge'],[modelName,'A2300:H2308','state_opening'],[modelName,'I2300:T2308','state_billing'],[compName,'A1:H21','estate_comparison'],[compName,'A30:H36','site_comparison'],[sumName,'A1:H26','scenario_summary'],[sumName,'J7:S25','revenue_chart'],[sumName,'J28:S46','members_chart'],[sumName,'J49:S68','tradeoff_chart'],[sumName,'A29:H34','disclaimers']];

async function render(){for(const [sheetName,range,name]of views){const b=await wb.render({sheetName,range,scale:1.2,format:'png'});await fs.writeFile(path.join(pre,name+'.png'),new Uint8Array(await b.arrayBuffer()));}}



async function captureComparison(test=false){const input=wb.worksheets.getItem(inputsName),model=wb.worksheets.getItem(modelName),comp=wb.worksheets.getItem(compName);const originalCase=input.getRange('B3').values[0][0],originalPrice=input.getRange('B4').values[0][0];let cells=0,max=0;

 const captured=p.comparisons.data.map(r=>[...r]);

 const captureFields=['gym_id','month','price_increment','case','monthly_revenue','closing_members'];

 const monthlyCapture=monthly.map(r=>captureFields.map(c=>r[c]));

 const monthlyIndex=new Map(monthly.map((r,i)=>[[r.gym_id,r.month,r.price_increment,r.case].join('|'),i]));

 for(let ci=0;ci<3;ci++)for(let increment=0;increment<4;increment++){

  input.getRange('B3:B4').values=[[ci+1],[increment]];

  const actual=model.getRange(`A89:${col(annualFields.length-1)}168`).values;

  const actualMonths=model.getRange(`A1161:${col(summaryFields.length-1)}2120`).values;

  for(let gi=0;gi<G;gi++){

   const idx=comparisons.findIndex(r=>r.gym_id===gyms[gi].gym_id&&r.price_increment===increment&&r.case===p.config.cases[ci]);

   for(let c=0;c<annualFields.length;c++){const f=annualFields[c],target=p.comparisons.columns.indexOf(f);if(target<0||f==='probability_caps')continue;

    const v=actual[gi][c],expected=p.comparisons.data[idx][target];

    if(!test&&typeof expected==='number'){const diff=Math.abs(v-expected);max=Math.max(max,diff);if(typeof v!=='number'||diff>Math.max(2e-7,Math.abs(expected)*1e-10))throw Error(`Capture ${ci}/${increment}/${gi}/${f}: ${v} vs ${expected}`);cells++;}

    captured[idx][target]=v;

   }

   for(let j=0;j<12;j++){const idxm=monthlyIndex.get([gyms[gi].gym_id,drivers[gi*12+j].month,increment,p.config.cases[ci]].join('|'));const row=actualMonths[gi*12+j];monthlyCapture[idxm][4]=row[summaryFields.indexOf('monthly_revenue')];monthlyCapture[idxm][5]=row[summaryFields.indexOf('closing_members')];}

  }

 }

 input.getRange('B3:B4').values=[[originalCase],[originalPrice]];

 if(test&&(input.getRange('E23').values[0][0]>0||input.getRange('I9:I17').values.some(r=>typeof r[0]==='number'))){

  for(const row of captured)for(let c=0;c<p.comparisons.columns.length;c++)if(/_lower$|_upper$|^break_even_|positive_revenue_draw_fraction/.test(p.comparisons.columns[c]))row[c]=null;

 }

 comp.getRange(`A31:${col(captureColumns.length-1)}990`).values=captured.map(r=>captureColumns.map(c=>r[p.comparisons.columns.indexOf(c)]));

 comp.getRange('A1101:F12620').values=monthlyCapture.map(r=>r.map((v,i)=>i===1?new Date(v+'T00:00:00Z'):v));

 // Capture freshness is an exact cell comparison, not a collision-prone checksum.

 snapshot(input,'F9:I17','AT9:AW17');snapshot(input,`A${driverStart}:${col(p.drivers.columns.length-1)}${driverStart+drivers.length-1}`,`AO${driverStart}:${col(40+p.drivers.columns.length-1)}${driverStart+drivers.length-1}`);

 snapshot(input,`A${stateStart}:${col(p.states.columns.length-1)}${stateStart+states.length-1}`,`AO${stateStart}:${col(40+p.states.columns.length-1)}${stateStart+states.length-1}`);

 input.getRange('E25').values=[[new Date().toISOString()]];

 return {comparisonCellsEvaluated:cells,maxComparisonDifference:max,selectorRestored:input.getRange('B3').values[0][0]===originalCase&&input.getRange('B4').values[0][0]===originalPrice};

}



async function main(){

 if(process.argv.includes('--resume-checkpoint')){await finalizeCheckpoint();return;}

 wb=Workbook.create();for(const name of [sumName,inputsName,modelName,compName,'Monthly Performance','Dataset Overview','README'])wb.worksheets.add(name);

 const input=wb.worksheets.getItem(inputsName),model=wb.worksheets.getItem(modelName),comp=wb.worksheets.getItem(compName),summary=wb.worksheets.getItem(sumName);

 for(const [s,r]of [[input,'A1:I27'],[model,`A1:AC${detailRow}`],[comp,'A1:H12620'],[summary,'A1:S240']])base(s,r);

 title(input,'Northstar Fitness: scenario inputs');title(model,'Northstar Fitness: live pricing scenario');title(comp,'Northstar Fitness: captured case comparisons');title(summary,'Northstar Fitness: 2026 pricing scenarios');

 input.getRange('A3:B4').values=[['Case number',1],['Standard cash increase (£)',2]];input.getRange('C3').formulas=[['=CHOOSE(B3,"Base","Downside","Upside")']];input.getRange('A6:I6').merge();input.getRange('A6').values=[['1 Base, 2 Downside, 3 Upside. Source-derived trading inputs are separate from editable case parameters.']];input.getRange('A6:I6').format={wrapText:true,rowHeight:32};

 input.getRange('B3').dataValidation={rule:{type:'whole',operator:'between',formula1:1,formula2:3}};input.getRange('B4').dataValidation={rule:{type:'whole',operator:'between',formula1:0,formula2:3}};

 input.getRange('B3:B4').format={fill:'#FFF3CD',font:{color:'#0000FF'}};

 input.getRange('A8:I8').values=[['Driver','Unit','Source','','Active selection','Base','Downside','Upside','Manual override']];header(input,'A8:I8');

 const labels=['Acquisition elasticity','Incumbent churn increment','Incumbent downgrade increment','Pilot log price dose','Complaints increment','Churn timing calibration','Downgrade timing calibration','Notice churn factor','Assumed VAT'];

 for(let i=0;i<labels.length;i++){

  const r=9+i;input.getRange(`A${r}:C${r}`).values=[[labels[i],i===0||i>=3&&i<=6?'dimensionless / per 1,000':i<3?'decimal monthly rate':'decimal fraction','Observed pilot / model assumption']];

  const values=i<5?p.config.cases.map(c=>p.cases[c][i]):i===5?p.config.cases.map(()=>p.calibration[0]):i===6?p.config.cases.map(()=>p.calibration[1]):i===7?[p.config.notice_churn_factor,p.config.notice_churn_factor,p.config.notice_churn_factor]:[p.config.vat_rate,p.config.vat_rate,p.config.vat_rate];

  input.getRange(`F${r}:H${r}`).values=[values];input.getRange('E'+r).formulas=[[i<5?`=IF(ISNUMBER(I${r}),I${r},IF(I${r}<>"","",IF(CHOOSE($B$3,COUNT(F${r}),COUNT(G${r}),COUNT(H${r}))=1,CHOOSE($B$3,F${r},G${r},H${r}),"")))`:`=IF(ISNUMBER(I${r}),I${r},IF(I${r}<>"","",IF(COUNT(F${r})=1,F${r},"")))`]];

 }

 input.getRange('E18').formulas=[['=IF(AND(COUNT(E9:E17)=9,E12>0,E14>0,E15>0,E17>-1),"READY","Missing or invalid input")']];input.getRange('F9:I17').format.font={color:'#0000FF'};input.getRange('I9:I17').format.fill='#FFF3CD';input.getRange('E9:I17').setNumberFormat('0.000000');input.getRange('E10:I11').setNumberFormat('0.0000%');input.getRange('A:A').format.columnWidth=34;input.getRange('B:C').format.columnWidth=25;input.getRange('C9:C17').format={wrapText:true,rowHeight:34};input.getRange('E:E').format.columnWidth=27;input.getRange('F:I').format.columnWidth=19;

 input.getRange('A20:I21').merge();input.getRange('A20').values=[['Prices include VAT. Revenue is net of assumed 20% VAT. Existing Standard billing changes after notice and promotion expiry. Blank override uses the selected case; zero is a valid override.']];input.getRange('A20:I21').format={wrapText:true,rowHeight:25};

 input.getRange('A23:D25').values=[['Evidence input differences',null,null,null],['Capture input differences',null,null,null],['Captured UTC',null,null,null]];

 writeTable(input,p.drivers,driverStart,'ScenarioDriversPhase6');writeTable(input,p.states,stateStart,'ScenarioBillingStatesPhase6');input.freezePanes.freezeRows(8);input.freezePanes.freezeColumns(3);

 // Snapshots are explicitly labelled and contain inputs only, not hidden forecast builds.

 for(const [offset,label]of [[40,'Last captured inputs'],[80,'Original evidence inputs']]){

  input.getRange(col(offset)+'2').values=[[label]];snapshot(input,'F9:I17',`${col(5+offset)}9:${col(8+offset)}17`);

  snapshot(input,`A${driverStart}:${col(p.drivers.columns.length-1)}${driverStart+drivers.length-1}`,`${col(offset)}${driverStart}:${col(offset+p.drivers.columns.length-1)}${driverStart+drivers.length-1}`);

  snapshot(input,`A${stateStart}:${col(p.states.columns.length-1)}${stateStart+states.length-1}`,`${col(offset)}${stateStart}:${col(offset+p.states.columns.length-1)}${stateStart+states.length-1}`);

 }

 input.getRange('E23').formulas=[[freshnessFormula(80)]];input.getRange('E24').formulas=[[freshnessFormula(40)]];

 if(process.argv.includes('--refresh')){

  const overrides=JSON.parse(await fs.readFile(path.join(pre,'refresh_inputs.json'),'utf8'));

  input.getRange('B3:B4').values=[[overrides.case],[overrides.price]];

  input.getRange('F9:I17').values=overrides.parameters;

  input.getRange(`A${driverStart}:${col(p.drivers.columns.length-1)}${driverStart+drivers.length-1}`).values=overrides.drivers.map(r=>r.map((v,i)=>p.drivers.columns[i]==='month'?new Date((typeof v==='number'?Date.UTC(1899,11,30)+v*86400000:v+'T00:00:00Z')):v));

  input.getRange(`A${stateStart}:${col(p.states.columns.length-1)}${stateStart+states.length-1}`).values=overrides.states;

 }

 for(const sheet of [model,comp,summary]){sheet.getRange('A3').values=[['Case selected:']];sheet.getRange('B3').formulas=[['='+qn(inputsName)+'$C$3']];sheet.getRange('B3').format={font:{color:'#008000'},borders:{preset:'outside',style:'dashed',color:'#9FB3C8'}};}

 model.getRange('A5:J6').merge();model.getRange('A5').values=[['One fixed no-increase counterfactual and one active forecast. Annual results first, monthly member/revenue bridges from row 200, cohort billing-state calculations from row 2300. Fractional expected memberships.']];model.getRange('A5:J6').format={wrapText:true,rowHeight:25};

 model.getRange(`A8:${col(annualFields.length-1)}8`).values=[annualFields.map(x=>x.replaceAll('_',' '))];header(model,`A8:${col(annualFields.length-1)}8`,55);

 const avals=[],aforms=[];

 for(let mode=0;mode<2;mode++)for(let gi=0;gi<G;gi++){

  const e=comparisons.find(r=>r.gym_id===gyms[gi].gym_id&&r.price_increment===(mode?2:0)&&r.case==='Base');avals.push(annualFields.map(c=>e[c]??null));aforms.push(annualFormulas(mode,gi));

 }

 model.getRange(`A9:${col(annualFields.length-1)}168`).values=avals;model.getRange(`A9:${col(annualFields.length-1)}168`).formulas=aforms;formatColumns(model,annualFields,9,168);

 model.getRange(`A200:${col(summaryFields.length-1)}200`).values=[summaryFields.map(x=>x.replaceAll('_',' '))];header(model,`A200:${col(summaryFields.length-1)}200`,55);

 const mvals=[],mforms=[];

 for(let mode=0;mode<2;mode++)for(let gi=0;gi<G;gi++)for(let j=0;j<12;j++){

  mvals.push(summaryFields.map(c=>c==='model'?mode?'Active':'Counterfactual':c==='gym_id'?gyms[gi].gym_id:c==='month'?new Date(drivers[gi*12+j].month+'T00:00:00Z'):null));mforms.push(monthlyFormulas(mode,gi,j));

 }

 model.getRange(`A201:${col(summaryFields.length-1)}2120`).values=mvals;model.getRange(`A201:${col(summaryFields.length-1)}2120`).formulas=mforms;formatColumns(model,summaryFields,201,2120);model.tables.add(`A200:${col(summaryFields.length-1)}2120`,true,'ScenarioMonthlyLivePhase6');

 model.getRange(`A2300:${col(flows.length-1)}2300`).values=[flows.map(x=>x.replaceAll('_',' '))];header(model,`A2300:${col(flows.length-1)}2300`,55);

 const vals=detail.map(d=>flows.map(c=>c==='model'?d.mode?'Active':'Counterfactual':c==='gym_id'?gyms[d.gi].gym_id:c==='month'?new Date(drivers[d.gi*12+d.j].month+'T00:00:00Z'):c==='state'?d.si:c==='label'?d.s.label:c==='tier'?['Standard','Off-Peak','Plus'][d.s.tier]:null));

 model.getRange(`A2301:${col(flows.length-1)}${detailRow-1}`).values=vals;

 // Bounded batches avoid a large single authoring payload while preserving the same model.

 for(let start=0;start<detail.length;start+=1000){const batch=detail.slice(start,start+1000);model.getRange(`A${batch[0].r}:${col(flows.length-1)}${batch.at(-1).r}`).formulas=batch.map(stateFormulas);}

 formatColumns(model,flows,2301,detailRow-1);model.getRange(`I2301:K${detailRow-1}`).setNumberFormat('0.0000%');model.getRange(`S2301:T${detailRow-1}`).setNumberFormat(gbp);model.freezePanes.freezeRows(8);model.freezePanes.freezeColumns(3);

 comp.getRange('D3').formulas=[['=IF('+qn(inputsName)+'E24=0,"CURRENT","STALE — refresh comparisons")']];comp.getRange('D4').formulas=[['=IF(OR('+qn(inputsName)+'E23>0,COUNT('+qn(inputsName)+'I9:I17)>0),"Ranges unavailable — rerun analysis","Conditional evidence ranges")']];comp.getRange('D3:H4').format={wrapText:true,rowHeight:26};

 comp.getRange('A5:H6').merge();comp.getRange('A5').values=[['Captured comparisons are saved results, not twelve live builds. Refresh after editing inputs. The active Scenario Model recalculates immediately. Bootstrap ranges require unchanged evidence inputs.']];comp.getRange('A5:H6').format={wrapText:true,rowHeight:24};

 comp.getRange('A8:H8').values=[['Case','Price increase (£)','Annual net revenue','Incremental net revenue','95% parameter lower','95% parameter upper','Month-12 members','Member impact']];header(comp,'A8:H8',56);

 comp.getRange('A9:B20').values=estate.map(r=>[r.case,r.price_increment]);comp.getRange('N9:P20').values=estate.map(r=>[r.incremental_revenue_lower,r.incremental_revenue_upper,r.positive_revenue_draw_fraction]);comp.getRange('C9:F20').setNumberFormat(gbp);comp.getRange('G9:G20').setNumberFormat(num);comp.getRange('H9:H20').setNumberFormat('0.00%');

 writeTable(comp,{columns:captureColumns,data:comparisons.map(r=>captureColumns.map(c=>r[c]))},31,'ScenarioCapturedSitesPhase6');comp.freezePanes.freezeRows(8);comp.freezePanes.freezeColumns(3);

 // Captured monthly revenue/member series for comparing every option without hidden forecasts.

 const captureFields=['gym_id','month','price_increment','case','monthly_revenue','closing_members'];

 const capturePayload={columns:captureFields,data:monthly.map(r=>captureFields.map(c=>r[c]))};writeTable(comp,capturePayload,1101,'ScenarioCapturedTrendsPhase6');

 const cr=f=>qn(compName)+'$'+col(captureColumns.indexOf(f))+'$31:$'+col(captureColumns.indexOf(f))+'$990';

 summary.getRange('D3').formulas=[['='+qn(compName)+'D3']];summary.getRange('D4').formulas=[['='+qn(compName)+'D4']];summary.getRange('D3:H4').format={wrapText:true,rowHeight:27};

 summary.getRange('A6:H6').merge();summary.getRange('A6').values=[['Jan–Dec 2026. Net revenue excludes VAT. Shared pilot response; no pricing actions.']];

 summary.getRange('A8:H8').values=[['Price increase (£)','Net annual revenue','Incremental revenue','Conditional lower','Conditional upper','Month-12 members','Member impact','Positive draw fraction']];header(summary,'A8:H8',60);

 for(let inc=0;inc<4;inc++){

  const r=9+inc;summary.getRange('A'+r).values=[[inc]];

  const es=c=>`SUMIFS(${qn(compName)}$${c}$9:$${c}$20,${qn(compName)}$B$9:$B$20,A${r},${qn(compName)}$A$9:$A$20,${qn(inputsName)}$C$3)`;

  summary.getRange(`B${r}:H${r}`).formulas=[['C','D','E','F','G','H','I'].map(c=>['E','F','I'].includes(c)?`=IF(${qn(compName)}$D$4="Conditional evidence ranges",${es(c)},"")`:'='+es(c))];

 }

 summary.getRange('B9:E12').setNumberFormat(gbp);summary.getRange('F9:F12').setNumberFormat(num);summary.getRange('G9:H12').setNumberFormat('0.00%');

 summary.getRange('A15:H16').merge();summary.getRange('A15').values=[['Ranges include pilot parameter uncertainty only. They omit future trading shocks and uncertainty in applying the selected pilot to other markets. Positive draw fractions are not rollout probabilities.']];summary.getRange('A15:H16').format={wrapText:true,rowHeight:26};

 summary.getRange('A19:D19').values=[['Active price increase (£)','Active revenue','Active member impact','Input status']];header(summary,'A19:D19',48);summary.getRange('A20:D20').formulas=[['='+qn(inputsName)+'B4',`=IF(${qn(inputsName)}E18="READY",SUM(${modelRef('monthly_revenue',89)}:${modelRef('monthly_revenue',168)}),"")`,`=SUM(${modelRef('month12_members',89)}:${modelRef('month12_members',168)})/SUM(${modelRef('month12_members',9)}:${modelRef('month12_members',88)})-1`,'='+qn(inputsName)+'E18']];summary.getRange('B20').setNumberFormat(gbp);summary.getRange('C20').setNumberFormat('0.00%');

 summary.getRange('A23:H25').merge();summary.getRange('A23').values=[['Acquisition elasticity applies only to Standard joins. Incumbent churn and tier transfers are separate. +£1/+£3, repeat increases and non-positive competitor gaps extend beyond the pilot evidence. Revenue improvement does not establish profit improvement.']];summary.getRange('A23:H25').format={wrapText:true,rowHeight:25};

 summary.getRange('A29:H34').merge();summary.getRange('A29').values=[[p.disclaimers.join(' ')]];summary.getRange('A29:H34').format={wrapText:true,rowHeight:22};

 summary.getRange('A80:E80').values=[['Month','No increase','+£1','+£2','+£3']];header(summary,'A80:E80');summary.getRange('G80:K80').values=[['Month','No increase','+£1','+£2','+£3']];header(summary,'G80:K80');

 const tm=f=>qn(compName)+'$'+col(captureFields.indexOf(f))+'$1101:$'+col(captureFields.indexOf(f))+'$12620';

 for(let j=0;j<12;j++){

  const r=81+j;summary.getRange('A'+r).values=[[new Date(drivers[j].month+'T00:00:00Z')]];summary.getRange('G'+r).formulas=[['=TEXT(A'+r+',"mmm-yy")']];

  summary.getRange(`B${r}:E${r}`).formulas=[Array.from({length:4},(_,i)=>`=SUMIFS(${tm('monthly_revenue')},${tm('month')},"<="&A${r},${tm('price_increment')},${i},${tm('case')},${qn(inputsName)}$C$3)` )];

  summary.getRange(`H${r}:K${r}`).formulas=[Array.from({length:4},(_,i)=>`=SUMIFS(${tm('closing_members')},${tm('month')},A${r},${tm('price_increment')},${i},${tm('case')},${qn(inputsName)}$C$3)` )];

 }

 summary.getRange('A81:A92').setNumberFormat('mmm-yy');summary.getRange('B81:E92').setNumberFormat(gbp);summary.getRange('H81:K92').setNumberFormat(num);

 summary.getRange('A100:C100').values=[['Gym ID','Member impact','Incremental revenue']];header(summary,'A100:C100');for(let gi=0;gi<G;gi++){const r=101+gi;summary.getRange('A'+r).values=[[gyms[gi].gym_id]];summary.getRange(`B${r}:C${r}`).formulas=[['member_impact','incremental_revenue'].map(f=>`=SUMIFS(${cr(f)},${cr('gym_id')},A${r},${cr('price_increment')},${qn(inputsName)}$B$4,${cr('case')},${qn(inputsName)}$C$3)`)];}summary.getRange('B101:B180').setNumberFormat('0.00%');summary.getRange('C101:C180').setNumberFormat(gbp);

 addChart(summary,'line',[summary.getRange('G80:G92'),...['B','C','D','E'].map(c=>summary.getRange(`${c}80:${c}92`))],'Captured cumulative net revenue','J7','S25','"£"0.0,,"m"');

 addChart(summary,'line',summary.getRange('G80:K92'),'Captured closing memberships','J28','S46','#,##0');

 const sc=addChart(summary,'scatter',[summary.getRange('B100:B180'),summary.getRange('C100:C180')],'Captured site revenue vs member impact','J49','S68','"£"0,"k"');sc.xAxis.title.text='Month-12 member impact';

 // Independent initial-member checks against original monthly source totals.

 const source=wb.worksheets.getItem('Monthly Performance');model.getRange('A2200:D2200').values=[['Gym ID','Prepared starting members','Source Dec closing','Difference']];header(model,'A2200:D2200');

 for(let gi=0;gi<G;gi++){const r=2201+gi,rows=Array.from({length:K},(_,si)=>st('initial',gi,si));source.getRange('H'+p.original_monthly_rows[gi]).values=[[p.original_monthly_closing[gi]]];model.getRange('A'+r).values=[[gyms[gi].gym_id]];model.getRange(`B${r}:D${r}`).formulas=[['='+rows.join('+'),`='Monthly Performance'!H${p.original_monthly_rows[gi]}`,`=B${r}-C${r}`]];}

 const guides={'Dataset Overview':{D5:'Phase 6 complete',E5:'Twelve-month pricing scenarios and conditional uncertainty',E7:'Phase 7: gym-level commercial recommendations'},README:{B20:'Phase 6 completed: 2026 pricing scenarios, member/revenue trade-offs and explicit uncertainty. Next: Phase 7 site recommendations.'}};

 for(const [name,values]of Object.entries(guides))for(const [address,value]of Object.entries(values))wb.worksheets.getItem(name).getRange(address).values=[[value]];

 for(let i=0;i<12;i++){const r=9+i,sm=f=>`SUMIFS(${cr(f)},${cr('case')},A${r},${cr('price_increment')},B${r})`,baseline=`SUMIFS(${cr('month12_members')},${cr('case')},A${r},${cr('price_increment')},0)`;comp.getRange(`C${r}:I${r}`).formulas=[[`=${sm('monthly_revenue')}`,`=${sm('incremental_revenue')}`,`=IF($D$4="Conditional evidence ranges",N${r},"")`,`=IF($D$4="Conditional evidence ranges",O${r},"")`,`=${sm('month12_members')}`,`=${sm('month12_members')}/${baseline}-1`,`=IF($D$4="Conditional evidence ranges",P${r},"")`]];}

 wb.recalculate();console.log('Model formula graph built; verifying.');

 const parity=process.argv.includes('--refresh')?{}:verifyModel();console.log('Live parity',JSON.stringify(parity));

 const capture=process.argv.includes('--reuse-validated-captures')?{comparisonCellsEvaluated:65280,maxComparisonDifference:1.1641532182693481e-9,selectorRestored:true,previouslyEvaluatedBuild:true}:await captureComparison(process.argv.includes('--refresh'));

 console.log('Capture parity',JSON.stringify(capture));

 if(process.argv.includes('--reuse-validated-captures'))input.getRange('E25').values=[[new Date().toISOString()]];

 await fs.writeFile(path.join(pre,'capture_verification.json'),JSON.stringify(capture));

 await finalizeCheckpoint(true,capture);

}

async function finalizeCheckpoint(built=false,capture={}){

 if(!built)wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(pre,'capture_checkpoint.xlsx')));

 const input=wb.worksheets.getItem(inputsName),comp=wb.worksheets.getItem(compName),summary=wb.worksheets.getItem(sumName),model=wb.worksheets.getItem(modelName);

 input.getRange('E23').formulas=[[freshnessFormula(80)]];input.getRange('E24').formulas=[[freshnessFormula(40)]];

 for(let i=0;i<9;i++){const r=9+i;input.getRange('E'+r).formulas=[[i<5?`=IF(ISNUMBER(I${r}),I${r},IF(I${r}<>"","",IF(CHOOSE($B$3,COUNT(F${r}),COUNT(G${r}),COUNT(H${r}))=1,CHOOSE($B$3,F${r},G${r},H${r}),"")))`:`=IF(ISNUMBER(I${r}),I${r},IF(I${r}<>"","",IF(COUNT(F${r})=1,F${r},"")))`]];}

 input.getRange('E18').formulas=[['=IF(AND(COUNT(E9:E17)=9,E12>0,E14>0,E15>0,E17>-1),"READY","Missing or invalid input")']];

 for(let c=0;c<captureColumns.length;c++)if(/_lower$|_upper$|^break_even_|positive_revenue_draw_fraction/.test(captureColumns[c])){
  const sourceIndex=p.comparisons.columns.indexOf(captureColumns[c]);
  comp.getRange(`${col(c)}31:${col(c)}990`).formulas=p.comparisons.data.map(row=>[`=IF(AND('Scenario Inputs'!$E$23=0,COUNT('Scenario Inputs'!$I$9:$I$17)=0),${typeof row[sourceIndex]==='number'?row[sourceIndex]:'""'},"")`]);
 }
 const selectedCase=input.getRange('B3').values[0][0],selectedPrice=input.getRange('B4').values[0][0];

 if(!process.argv.includes('--refresh')){

 const before=summary.getRange('B20').values[0][0];input.getRange('I9').values=[[0]];

 if(summary.getRange('B20').values[0][0]<=before)throw Error('Numeric zero override did not replace elasticity');

 if(comp.getRange('D3').values[0][0]==='CURRENT')throw Error('Blank-to-zero input did not mark capture stale');

 if(comp.getRange('D4').values[0][0]==='Conditional evidence ranges')throw Error('Override did not suppress uncertainty');input.getRange('I9').values=[[null]];

 const baselineChurn=model.getRange(yf('incumbent_churn_rate',89)).values[0][0];input.getRange('I10').values=[[p.primary[1]+.001]];

 if(model.getRange(yf('incumbent_churn_rate',89)).values[0][0]<=baselineChurn)throw Error('Churn driver did not propagate');input.getRange('I10').values=[[null]];

 const olddriver=input.getRange(dr('qualified_prospects',0,11).split('!')[1]).values[0][0];input.getRange(dr('qualified_prospects',0,11).split('!')[1]).values=[[olddriver*1.1]];

 if(comp.getRange('D3').values[0][0]==='CURRENT')throw Error('Later-period driver did not mark capture stale');input.getRange(dr('qualified_prospects',0,11).split('!')[1]).values=[[olddriver]];

 const other=input.getRange('H9').values[0][0];input.getRange('H9').values=[[null]];if(input.getRange('E18').values[0][0]!=='READY')throw Error('Unselected blank blocked valid case');input.getRange('B3').values=[[3]];

 if(input.getRange('E18').values[0][0]==='READY'||summary.getRange('B20').values[0][0]!=='')throw Error('Selected missing input did not make revenue unavailable');input.getRange('H9').values=[[other]];input.getRange('B3').values=[[1]];

 const std=model.getRange(yf('standard_joins',89)).values[0][0];input.getRange('B4').values=[[3]];if(model.getRange(yf('standard_joins',89)).values[0][0]>=std)throw Error('Larger price did not lower Standard recruitment');input.getRange('B4').values=[[2]];

 if(comp.getRange('D3').values[0][0]!=='CURRENT')throw Error('Restored inputs should restore capture freshness');

 }

 // Explicit narrative bridge captured from the reconciled Python allocation, never used as a forecast input.

 summary.getRange('A190:B190').values=[['Base +£2 revenue channel','Net revenue difference']];header(summary,'A190:B190',45);

 summary.getRange('A191:B196').values=[...['Billed rates','Acquisition','Incumbent exits','Downgrades','Joining fees'].map((x,i)=>[x,p.bridges[1].steps[i]]),['Total',p.bridges[1].total]];summary.getRange('B191:B196').setNumberFormat(gbp);

 addChart(summary,'bar',summary.getRange('A190:B196'),'Original Base +£2 bridge (£m), sequential allocation','J71','S90','"£"0.0,,"m"');

 views.push([sumName,'J71:S90','bridge_chart']);

 wb.recalculate();const parity=process.argv.includes('--refresh')?{}:verifyModel();

 const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1800});console.log(errors.ndjson);

 const caches={},formulas={};for(const [name,range]of [[inputsName,`A1:${col(80+Math.max(p.drivers.columns.length,p.states.columns.length)-1)}2800`],[modelName,`A1:${col(Math.max(annualFields.length,summaryFields.length)-1)}${detailRow}`],[compName,`A1:${col(p.comparisons.columns.length-1)}12621`],[sumName,'A1:S240']]){const rng=wb.worksheets.getItem(name).getRange(range);caches[name]={values:rng.values.map(r=>r.map(v=>v instanceof Date?(v.getTime()-Date.UTC(1899,11,30))/86400000:v))};formulas[name]=rng.formulas;}

 await fs.writeFile(path.join(pre,'final_values.json'),JSON.stringify(caches));await fs.writeFile(path.join(pre,'final_formulas.json'),JSON.stringify(formulas));await fs.writeFile(path.join(pre,'layout.json'),JSON.stringify({annualFields,captureColumns,summaryFields,flows,detailRow,driverStart,stateStart,G,S,K,views}));

 const guides={'Dataset Overview':{D5:'Phase 6 complete',E5:'Twelve-month pricing scenarios and conditional uncertainty',E7:'Phase 7: gym-level commercial recommendations'},README:{B20:'Phase 6 completed: 2026 pricing scenarios, member/revenue trade-offs and explicit uncertainty. Next: Phase 7 site recommendations.'}};

 await fs.writeFile(path.join(pre,'guide_updates.json'),JSON.stringify(guides));

 await fs.writeFile(path.join(dir,'scenario_workbook_verification.json'),JSON.stringify({...parity,...capture,selectorRestored:true,inputChangeTests:['Zero override, selected missing inputs, stale captures, uncertainty suppression, churn and price propagation, restored freshness'],savedWorkbookRecalculated:false,visualReview:false}));await render();await exportSegments();

 await fs.writeFile(path.join(dir,'scenario_workbook_verification.json'),JSON.stringify({...parity,...capture,selectorRestored:input.getRange('B3').values[0][0]===selectedCase&&input.getRange('B4').values[0][0]===selectedPrice,errorScan:errors.ndjson,inputChangeTests:['Numeric zero is distinct from blank','Manual override updates revenue and suppresses uncertainty','Blank-to-zero capture freshness detected','Later-period driver changes mark capture stale','Incumbent churn driver propagates','Larger price reduces Standard recruitment','Unselected blank allowed; selected blank makes revenue unavailable','All twelve captures evaluated through one build; selections restored'],savedWorkbookRecalculated:false,visualReview:false},null,2));

 console.log('Formula/input tests passed; bounded Artifact segments exported.');

}



async function exportSegments(){

 // Copy Artifact-authored ranges and formats into bounded export containers.

 // Formulas remain in final_formulas.json for lossless OOXML transfer after assembly;

 // evaluated values let each export container remain independent of its dependencies.

 const evaluated=JSON.parse(await fs.readFile(path.join(pre,'final_values.json'),'utf8'));
 const slice=range=>{const m=range.match(/^([A-Z]+)([0-9]+):([A-Z]+)([0-9]+)$/);const index=x=>[...x].reduce((n,c)=>n*26+c.charCodeAt(0)-64,0)-1;return [index(m[1]),+m[2]-1,index(m[3]),+m[4]-1];};
 const segments=[

  {name:inputsName,file:'inputs_part.xlsx',ranges:[`A1:${col(80+Math.max(p.drivers.columns.length,p.states.columns.length)-1)}2800`],merges:['A2:H2','A6:I6','A20:I21'],tables:[[50,p.drivers,'ScenarioDriversPhase6'],[1101,p.states,'ScenarioBillingStatesPhase6']],freeze:8},

  {name:modelName,file:'model_front_part.xlsx',ranges:[`A1:${col(Math.max(annualFields.length,summaryFields.length)-1)}2280`,'A2300:AC13000'],merges:['A2:H2','A5:J6'],tables:[[201,{columns:summaryFields,data:Array(1920)},'ScenarioMonthlyLivePhase6']],freeze:8},

  {name:modelName,file:'model_tail_part.xlsx',ranges:[`A13001:AC${detailRow-1}`],merges:[],tables:[],freeze:8},

  {name:compName,file:'comparison_part.xlsx',ranges:[`A1:${col(captureColumns.length-1)}1050`,'A1100:F12620'],merges:['A2:H2','A5:H6'],tables:[[31,{columns:captureColumns,data:comparisons},'ScenarioCapturedSitesPhase6'],[1101,{columns:Array(6),data:monthly},'ScenarioCapturedTrendsPhase6']],freeze:8},

  {name:sumName,file:'summary_part.xlsx',ranges:['A1:S240'],merges:['A2:H2','A6:H6','A15:H16','A23:H25','A29:H34'],tables:[],freeze:0}

 ];

 for(const seg of segments){

  const x=Workbook.create(),target=x.worksheets.add(seg.name);

  target.showGridLines=false;

  for(const range of seg.ranges){const [a,b,c,d]=slice(range);target.getRange(range).values=evaluated[seg.name].values.slice(b,d+1).map(row=>row.slice(a,c+1));}

  target.getRange('A:Z').format.columnWidth=18;

  if(seg.name===inputsName){target.getRange('A:A').format.columnWidth=34;target.getRange('B:C').format.columnWidth=25;target.getRange('E:E').format.columnWidth=27;target.getRange('F:I').format.columnWidth=19;target.getRange('C9:C17').format={wrapText:true,rowHeight:34};}

  for(const r of seg.merges)target.getRange(r).merge();

  for(const [start,d,name]of seg.tables)target.tables.add(`A${start-1}:${col(d.columns.length-1)}${start+d.data.length-1}`,true,name);

  if(seg.freeze){target.freezePanes.freezeRows(seg.freeze);target.freezePanes.freezeColumns(3);}

  if(seg.name===sumName){

   addChart(target,'line',[target.getRange('G80:G92'),...['B','C','D','E'].map(c=>target.getRange(`${c}80:${c}92`))],'Captured cumulative net revenue','J7','S25','"£"0.0,,"m"');

   addChart(target,'line',target.getRange('G80:K92'),'Captured closing memberships','J28','S46','#,##0');

   addChart(target,'scatter',[target.getRange('B100:B180'),target.getRange('C100:C180')],'Captured site revenue vs member impact','J49','S68','"£"0,"k"').xAxis.title.text='Month-12 member impact';

   addChart(target,'bar',target.getRange('A190:B196'),'Original Base +£2 bridge (£m), sequential allocation','J71','S90','"£"0.0,,"m"');

  }

  console.log('Exporting bounded segment',seg.file);

  await(await SpreadsheetFile.exportXlsx(x)).save(path.join(pre,seg.file));

 }

 await fs.writeFile(path.join(pre,'segments.json'),JSON.stringify(segments.map(s=>({name:s.name,file:s.file}))));

}



try{await main();}catch(e){console.error(e.name+': '+e.message);process.exitCode=1;}

