import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile,FileBlob} from '@oai/artifact-tool';

const dir=path.dirname(fileURLToPath(import.meta.url)), root=path.dirname(dir);
const previews=path.join(dir,'.workbook_previews','phase3');
await fs.mkdir(previews,{recursive:true});
const p=JSON.parse(await fs.readFile(path.join(dir,'.workbook_previews','phase3_payload.json'),'utf8'));
const names={gym_master:'Gym Master',monthly_performance:'Monthly Performance',pricing_history:'Historical Pricing',experiment_assignments:'Pilot Assignments'};
const added=['Baseline','Estate Trends','Baseline Summary'];
const col=i=>{let s='';for(let n=i+1;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const rng=(table,field)=>{const c=col(p[table].columns.indexOf(field));if(p[table].columns.indexOf(field)<0)throw Error(field);return `'${names[table]}'!$${c}$2:$${c}$${p[table].data.length+1}`;};
const src=(field,row)=>`'Monthly Performance'!${col(p.monthly_performance.columns.indexOf(field))}${row}`;
const B=(field,row)=>`'Baseline'!${col(p.gym_baseline.columns.indexOf(field))}${row}`;
const BR=field=>`'Baseline'!$${col(p.gym_baseline.columns.indexOf(field))}$9:$${col(p.gym_baseline.columns.indexOf(field))}$88`;
const T=(field,row)=>`'Estate Trends'!${col(p.estate_monthly_trend.columns.indexOf(field))}${row}`;
const base=(s,a)=>{s.showGridLines=false;s.getRange(a).format.font={name:'Arial',size:10,color:'#243B53'};s.getRange(a).format.verticalAlignment='center';s.getRange(a).format.rowHeight=22;};
const header=(s,a)=>{s.getRange(a).format={fill:'#243B53',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:60,horizontalAlignment:'center',verticalAlignment:'center'};};
const title=(s,t)=>{s.getRange('A2').values=[[t]];s.getRange('A2').format.font={name:'Arial',size:14,bold:true};s.getRange('A3:H3').format.borders={bottom:{style:'thin',color:'#829AB1'}};};
const quot=ref=>`'${ref}'`;
const ratio=(a,b)=>`IF((${b})=0,"",(${a})/(${b}))`;
const sumFields={member_months:'average_members',opening_member_months:'opening_members',subscription_revenue:'subscription_revenue',joining_fee_revenue:'joining_fee_revenue',ancillary_revenue:'ancillary_revenue',total_revenue:'monthly_revenue',standard_member_months:'average_standard_members',standard_subscription_revenue:'standard_subscription_revenue',new_members:'new_members',opening_base_cancellations:'opening_base_cancellations',same_month_cancellations:'same_month_cancellations',all_cancellations:'cancelled_members',qualified_prospects:'qualified_prospects',opening_minutes:'opening_minutes',promotion_gym_months:'promotion_active',pricing_complaints:'pricing_complaints',marketing_spend:'marketing_spend'};
const periodIndex={'2025':0,'2024':1,'q4_2025':2,'q4_2024':3};
const periods=Object.keys(periodIndex);
const dateRef=(w,end=false)=>`'Baseline Summary'!$${col(periodIndex[w]+1)}$${end?5:4}`;
const dateRange=rng('monthly_performance','month'), idRange=rng('monthly_performance','gym_id');
const aggSum=(field,criteria)=>`SUMIFS(${rng('monthly_performance',field)},${criteria})`;
const styleFormat=(s,c,first,last,field)=>{
  const area=s.getRange(`${col(c)}${first}:${col(c)}${last}`);
  let fmt='#,##0.00;(#,##0.00);"-"';
  if(field==='month')fmt='mmm-yy';
  else if(field==='year')fmt='0';
  else if(field.includes('change_pp'))fmt='0.00" pp";(0.00)" pp";"-"';
  else if(/rate|growth|mix|utilisation|monthly_peak|promotion_frequency/.test(field)&&!field.includes('rank'))fmt='0.0%;(0.0%);"-"';
  else if(/revenue|yield|arpmm|price|cash_increase|marketing_spend|competitor_gap/.test(field)&&!field.includes('rank'))fmt='"£"#,##0.00;("£"#,##0.00);"-"';
  else if(/members|months|minutes|prospects|complaints$|events|count|rank|capacity_proxy|year/.test(field))fmt='#,##0;(#,##0);"-"';
  if(/exception|gym_id|gym_name|city|region|location_type|pilot_assignment|pilot_pair/.test(field))fmt='General';
  area.setNumberFormat(fmt);
};
const label=f=>f.replaceAll('_',' ').replace('q4 2025','Q4 2025').replace('q4 2024','Q4 2024').replace('arpmm','ARPMM').replace('dec2025','Dec 2025').replace('yoy','YoY');

if(process.argv.includes('--probe')){
 const test=Workbook.create(),sheet=test.worksheets.add('Probe');sheet.getRange('A1:A3').values=[[true],[false],[true]];
 sheet.getRange('B1:E1').formulas=[['=COUNTIF(A1:A3,TRUE)','=COUNTIF(A1:A3,"TRUE")','=SUMPRODUCT(A1:A3*1)','=SUMPRODUCT((A1:A3=TRUE)*1)']];test.recalculate();console.log(JSON.stringify(sheet.getRange('B1:E1').values));process.exit(0);
}
if(process.argv.includes('--probe-import')){
 const file=process.argv[process.argv.indexOf('--probe-import')+1];
 const test=await SpreadsheetFile.importXlsx(await FileBlob.load(file));
 console.log((await test.inspect({kind:'sheet',include:'name',maxChars:500})).ndjson);process.exit(0);
}
if(process.argv.includes('--style-repairs')){
 const test=Workbook.create(),sheet=test.worksheets.add('Baseline Summary');base(sheet,'A20:C42');sheet.getRange('A20:A42').format.columnWidth=38;sheet.getRange('B20:C42').format.columnWidth=20;
 for(const [row,key,window] of [[20,'churn_rate','annual'],[21,'conversion_rate','annual'],[27,'churn_rate','q4'],[28,'conversion_rate','q4']]){
  sheet.getRange(`A${row}:C${row}`).values=[[label(key),p.result[window]['2024'][key],p.result[window]['2025'][key]]];sheet.getRange(`B${row}:C${row}`).setNumberFormat('0.00%');
 }
 sheet.getRange('A42:B42').values=[['Bridge reconciliation difference',0]];sheet.getRange('B42').setNumberFormat('0.00;(0.00);0.00');test.recalculate();
 const blob=await test.render({sheetName:sheet.name,range:'A20:C42',scale:1.3,format:'png'});await fs.writeFile(path.join(previews,'rate_precision_repair.png'),new Uint8Array(await blob.arrayBuffer()));
 const output=await SpreadsheetFile.exportXlsx(test);await output.save(path.join(previews,'style_repairs.xlsx'));console.log('Artifact Tool authored targeted rate precision and reconciliation formats.');process.exit(0);
}

function metricFormula(field,criteria,ref,firstCriteria,lastCriteria,capacity,mask,helper=false){
  const sum=f=>aggSum(f,criteria);
  if(field==='promotion_gym_months')return helper?`SUMPRODUCT((${dateRange}=$A${helper})*${rng('monthly_performance','promotion_active')})`:`SUMPRODUCT(${mask}*${rng('monthly_performance','promotion_active')})`;
  if(field in sumFields)return sum(sumFields[field]);
  if(field==='months')return helper?'1':`COUNTIFS(${criteria})`;
  if(field==='opening_members')return aggSum('opening_members',firstCriteria);
  if(field==='closing_members')return aggSum('closing_members',lastCriteria);
  if(field==='average_members')return ratio(ref('member_months'),ref('months'));
  if(field==='average_monthly_revenue')return ratio(ref('total_revenue'),ref('months'));
  if(field==='arpmm')return ratio(ref('total_revenue'),ref('member_months'));
  if(field==='subscription_yield')return ratio(ref('subscription_revenue'),ref('member_months'));
  if(field==='standard_yield')return ratio(ref('standard_subscription_revenue'),ref('standard_member_months'));
  if(field==='average_monthly_joins')return ratio(ref('new_members'),ref('months'));
  if(field==='acquisition_rate')return ratio(ref('new_members'),ref('opening_member_months'));
  if(field==='churn_rate')return ratio(ref('opening_base_cancellations'),ref('opening_member_months'));
  if(field==='retention_rate')return `IF(${ref('churn_rate')}="","",1-${ref('churn_rate')})`;
  if(field==='conversion_rate')return ratio(ref('new_members'),ref('qualified_prospects'));
  if(field==='member_growth')return `IF(${ref('opening_members')}=0,"",${ref('closing_members')}/${ref('opening_members')}-1)`;
  if(field==='occupancy_minutes')return helper?`SUMIFS($E$49:$E$1968,$B$49:$B$1968,$A${helper})`:`SUMPRODUCT(${mask}*${rng('monthly_performance','gym_visits')}*${rng('monthly_performance','average_visit_duration_minutes')})`;
  if(field==='capacity_minutes')return helper?`SUMIFS($D$49:$D$1968,$B$49:$B$1968,$A${helper})`:`${ref('opening_minutes')}*${capacity}`;
  if(field==='average_utilisation')return ratio(ref('occupancy_minutes'),ref('capacity_minutes'));
  if(field==='average_monthly_peak')return helper?ratio(`SUMIFS($F$49:$F$1968,$B$49:$B$1968,$A${helper})`,ref('capacity_minutes')):ratio(`SUMPRODUCT(${mask}*${rng('monthly_performance','peak_utilisation_pct')}*${rng('monthly_performance','opening_minutes')})`,ref('opening_minutes'));
  if(field==='max_monthly_peak')return `_xlfn.MAXIFS(${rng('monthly_performance','peak_utilisation_pct')},${criteria})`;
  if(field==='promotion_frequency')return ratio(ref('promotion_gym_months'),helper?`COUNTIFS(${criteria})`:ref('months'));
  if(['standard_mix','offpeak_mix','plus_mix'].includes(field))return ratio(sum({standard_mix:'average_standard_members',offpeak_mix:'average_offpeak_members',plus_mix:'average_premium_members'}[field]),ref('member_months'));
  if(field==='complaints_per_1000_member_months')return ratio(`${ref('pricing_complaints')}*1000`,ref('member_months'));
  throw Error(`Unmapped metric ${field}`);
}

function verify(wb,stage){
  let cells=0,maxDifference=0;
  for(const [name,key,start] of [['Baseline','gym_baseline',9],['Estate Trends','estate_monthly_trend',9],['Baseline Summary','region_year_baseline',105]]){
    const expected=p[key],s=wb.worksheets.getItem(name);
    const actual=s.getRange(`A${start}:${col(expected.columns.length-1)}${start+expected.data.length-1}`).values;
    for(let r=0;r<actual.length;r++)for(let c=0;c<expected.columns.length;c++){
      let v=actual[r][c],e=expected.data[r][c];
      if(v instanceof Date)v=(v.getTime()-Date.UTC(1899,11,30))/86400000;
      if(key==='estate_monthly_trend'&&c===0)e=(Date.parse(e+'T00:00:00Z')-Date.UTC(1899,11,30))/86400000;
      if(typeof e==='number'){
        const d=Math.abs(v-e);maxDifference=Math.max(maxDifference,d);
        if(typeof v!=='number'||d>Math.max(.00002,Math.abs(e)*2e-12))throw Error(`${stage} ${name} ${col(c)}${start+r} ${expected.columns[c]}: ${v} vs ${e}`);
      }else if(e===null){if(v!==null&&v!=='')throw Error(`Nonblank null ${name}`);}
      else if(v!==e)throw Error(`${stage} ${name} ${col(c)}${start+r}: ${v} vs ${e}`);
      cells++;
    }
  }
  const s=wb.worksheets.getItem('Baseline Summary');
  for(const [address,e] of Object.entries({'B37':p.result.bridge['2024_revenue'],'B38':p.result.bridge.member_volume_contribution,'B39':p.result.bridge.total_arpmm_contribution,'B40':p.result.bridge['2025_revenue']})){
    const v=s.getRange(address).values[0][0];if(Math.abs(v-e)>.01)throw Error('Bridge '+address);
  }
  if(Math.abs(s.getRange('B42').values[0][0])>.01)throw Error('Revenue bridge reconciliation');
  return {cellsCompared:cells,maxAbsoluteDifference:maxDifference};
}

if(process.argv.includes('--verify-final')){
  const workbookPath=path.join(root,'excel',process.argv.includes('--candidate')?'gym_pricing_model.xlsx.tmp':'gym_pricing_model.xlsx');
  const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
  wb.recalculate();const info=verify(wb,'saved workbook');
  const checks=wb.worksheets.getItem('Checks');
  if(Math.abs(checks.getRange('C5').values[0][0])>.01||checks.getRange('C8:H1927').values.some(r=>r.some(v=>Math.abs(v)>1e-8)))throw Error('Original source checks');
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1500});
  info.formulaErrorScan=errors.ndjson;
  info.savedWorkbookRecalculated=true;info.originalReconciliationsPassed=true;
  info.nativeExcelApplication='Not automated; verification uses Artifact Tool and saved OOXML';
  await fs.writeFile(path.join(dir,'baseline_workbook_verification.json'),JSON.stringify(info,null,2));
  const cell=wb.worksheets.getItem('Monthly Performance').getRange(col(p.monthly_performance.columns.indexOf('monthly_revenue'))+'14');
  const old=cell.values[0][0],oldResult=wb.worksheets.getItem('Baseline').getRange(col(p.gym_baseline.columns.indexOf('total_revenue_2025'))+'9').values[0][0];
  cell.values=[[old+120]];
  const newResult=wb.worksheets.getItem('Baseline').getRange(col(p.gym_baseline.columns.indexOf('total_revenue_2025'))+'9').values[0][0];
  if(Math.abs(newResult-oldResult-120)>.001)throw Error('Baseline input-change proof');
  cell.values=[[old]];
  info.inputChangeProof='A GBP 120 January 2025 source-revenue change propagated to the site annual result; original source restored';
  const guideUpdates={'Dataset Overview':{D5:'Phase 3',E5:'Commercial baseline',E7:'Pricing headroom'},README:{B20:'Phase 3 completed: annual baseline and Q4 comparisons. Next: Phase 4 pricing-headroom analysis.'}};
  for(const [name,updates] of Object.entries(guideUpdates))for(const [address,value] of Object.entries(updates))wb.worksheets.getItem(name).getRange(address).values=[[value]];
  wb.recalculate();
  verify(wb,'restored');
  const caches={};for(const name of added){const sheet=wb.worksheets.getItem(name);const range=name==='Baseline'?`A1:${col(p.gym_baseline.columns.length-1)}88`:name==='Estate Trends'?`A1:${col(p.estate_monthly_trend.columns.length-1)}1968`:`A1:${col(p.region_year_baseline.columns.length-1)}124`;caches[name]={values:sheet.getRange(range).values.map(r=>r.map(v=>v instanceof Date?(v.getTime()-Date.UTC(1899,11,30))/86400000:v))};}
  await fs.writeFile(path.join(previews,'final_values.json'),JSON.stringify(caches));
  await fs.writeFile(path.join(previews,'guide_updates.json'),JSON.stringify(guideUpdates));
  for(const [sheetName,range,file] of [['Dataset Overview','A1:F24','overview_updated'],['README','A18:B22','readme_updated']]){const blob=await wb.render({sheetName,range,scale:1.3,format:'png'});await fs.writeFile(path.join(previews,file+'.png'),new Uint8Array(await blob.arrayBuffer()));}
  await fs.writeFile(path.join(dir,'baseline_workbook_verification.json'),JSON.stringify(info,null,2));
  console.log(JSON.stringify(info));process.exit(0);
}

const wb=Workbook.create();
const sheets=Object.fromEntries(added.map(n=>[n,wb.worksheets.add(n)]));
for(const [table,name] of Object.entries(names)){
  const s=wb.worksheets.add(name),v=p[table];
  s.getRange(`A1:${col(v.columns.length-1)}${v.data.length+1}`).values=[v.columns,...v.data.map(r=>r.map((x,i)=>x!==null&&v.dates.includes(v.columns[i])?new Date(x+'T00:00:00Z'):x))];
}
const s=sheets['Baseline Summary'];base(s,'A1:R100');title(s,'Northstar Fitness commercial baseline');s.tabColor='#243B53';
s.getRange('A1:A100').format.columnWidth=38;s.getRange('B1:E100').format.columnWidth=20;s.getRange('F1:R100').format.columnWidth=13;
s.getRange('A4:A5').values=[['First observed month'],['Last observed month']];
s.getRange('B3:E3').values=[['2025','2024','Q4 2025','Q4 2024']];
s.getRange('B4:E5').values=[['2025-01-01','2024-01-01','2025-10-01','2024-10-01'],['2025-12-01','2024-12-01','2025-12-01','2024-12-01']].map(r=>r.map(d=>new Date(d+'T00:00:00Z')));
s.getRange('B4:E5').setNumberFormat('mmm-yy');
s.getRange('A7').values=[['Net revenue excludes assumed 20% VAT. Consumer prices include VAT.']];
s.getRange('A7').format.font={name:'Arial',size:10,italic:true};

// Source-linked gym baseline, with complete annual and Q4 comparison schedules.
const b=sheets.Baseline,bc=p.gym_baseline.columns;base(b,`A1:${col(bc.length-1)}88`);title(b,'Gym baseline: 2025, 2024 and matching Q4 periods');b.tabColor='#486581';
b.getRange('A4').values=[['Annual baseline January–December 2025. Q4 uses October–December. Scroll across for denominators and prior periods.']];
b.getRange('A5').values=[['Prices gross VAT. Revenue net VAT. Retention is a monthly exposure-weighted rate. Flags identify investigation, not pricing actions.']];
b.getRange(`A8:${col(bc.length-1)}8`).values=[bc.map(label)];header(b,`A8:${col(bc.length-1)}8`);
for(let c=0;c<bc.length;c++){b.getRange(`${col(c)}8:${col(c)}88`).format.columnWidth=c===1?30:Math.min(30,Math.max(18,label(bc[c]).length*.55));styleFormat(b,c,9,88,bc[c]);}
b.getRange('A9:A88').values=p.gym_baseline.data.map(r=>[r[bc.indexOf('gym_id')]]);
const baselineFormRows=[];
for(let i=0;i<80;i++){
  const row=i+9;const ref=f=>col(bc.indexOf(f))+row;
  const forms=bc.map(field=>{
    if(field==='gym_id')return '';
    if(['gym_name','city','region','location_type','capacity_proxy'].includes(field))return `=INDEX(${rng('gym_master',field)},MATCH($A${row},${rng('gym_master','gym_id')},0))`;
    if(field==='standard_price_dec2025'||field==='competitor_price_dec2025'||field==='competitor_count_dec2025'||field==='december_annualised_revenue'){
      const target={standard_price_dec2025:'standard_price',competitor_price_dec2025:'local_competitor_avg_price',competitor_count_dec2025:'competitor_count_3km',december_annualised_revenue:'monthly_revenue'}[field];
      return '='+aggSum(target,`${idRange},$A${row},${dateRange},${dateRef('2025',true)}`)+(field==='december_annualised_revenue'?'*12':'');
    }
    if(field==='competitor_gap_dec2025')return `=${ref('competitor_price_dec2025')}-${ref('standard_price_dec2025')}`;
    if(field==='historical_price_events')return `=COUNTIF(${rng('pricing_history','gym_id')},$A${row})`;
    if(field==='historical_cash_increase')return `=SUMIF(${rng('pricing_history','gym_id')},$A${row},${rng('pricing_history','change_amount')})`;
    if(field==='pilot_assignment'||field==='pilot_pair_id')return `=IF(COUNTIF(${rng('experiment_assignments','gym_id')},$A${row})=0,"${field==='pilot_assignment'?'Not in pilot':''}",INDEX(${rng('experiment_assignments',field==='pilot_assignment'?'test_group':'pair_id')},MATCH($A${row},${rng('experiment_assignments','gym_id')},0)))`;
    if(field==='high_churn_exception')return `=${ref('churn_rate_2025')}>='Baseline Summary'!$B$46`;
    if(field==='weak_conversion_exception')return `=${ref('conversion_rate_2025')}<='Baseline Summary'!$B$47`;
    if(field==='declining_acquisition_exception')return `=AND(${ref('acquisition_growth_yoy')}<0,${ref('acquisition_growth_yoy')}<='Baseline Summary'!$B$48)`;
    if(field==='peak_capacity_exception')return `=${ref('max_monthly_peak_2025')}>=1`;
    if(field.includes('_rank_')){
      const metric=field.split('_rank_')[1],op=field.startsWith('highest')?'>':'<';
      return `=COUNTIF(${BR(metric)},"${op}"&${ref(metric)})+COUNTIFS(${BR(metric)},${ref(metric)},${BR('gym_id')},"<"&$A${row})+1`;
    }
    for(const [suffix,now,old] of [['q4_yoy','q4_2025','q4_2024'],['yoy','2025','2024']]){
      if(field.endsWith('_'+suffix)){
        const key=field.slice(0,-suffix.length-1);
        if(key.endsWith('_change_pp')){const metric=key.replace('_change_pp','_rate');return `=100*(${ref(metric+'_'+now)}-${ref(metric+'_'+old)})`;}
        const metric={revenue_growth:'total_revenue',acquisition_growth:'new_members',closing_member_growth:'closing_members'}[key];
        if(metric)return `=IF(${ref(metric+'_'+old)}=0,"",${ref(metric+'_'+now)}/${ref(metric+'_'+old)}-1)`;
      }
    }
    for(const w of ['q4_2025','q4_2024','2025','2024'])if(field.endsWith('_'+w)){
      const metric=field.slice(0,-w.length-1),start=dateRef(w),end=dateRef(w,true);
      const criteria=`${idRange},$A${row},${dateRange},">="&${start},${dateRange},"<="&${end}`;
      const mask=`(${idRange}=$A${row})*(${dateRange}>=${start})*(${dateRange}<=${end})`;
      return '='+metricFormula(metric,criteria,k=>ref(k+'_'+w),`${idRange},$A${row},${dateRange},${start}`,`${idRange},$A${row},${dateRange},${end}`,ref('capacity_proxy'),mask);
    }
    throw Error(field);
  });
  baselineFormRows.push(forms.slice(1));
}
b.getRange(`B9:${col(bc.length-1)}88`).formulas=baselineFormRows;
b.tables.add(`A8:${col(bc.length-1)}88`,true,'BaselineMetrics');b.freezePanes.freezeRows(8);b.freezePanes.freezeColumns(2);
for(const field of ['high_churn_exception','weak_conversion_exception','declining_acquisition_exception','peak_capacity_exception']){
 const c=col(bc.indexOf(field));b.getRange(`${c}9:${c}88`).conditionalFormats.add('cellIs',{operator:'equal',formula:'TRUE',format:{fill:'#FFF1D6',font:{color:'#92400E'}}});
}

// Explicit capacity calculations allow correctly weighted multi-site utilisation.
const t=sheets['Estate Trends'],tc=p.estate_monthly_trend.columns;base(t,`A1:${col(tc.length-1)}1968`);title(t,'Estate monthly trading: January 2024–December 2025');t.tabColor='#486581';
t.getRange('A4').values=[['Member figures are stocks and monthly exposure, not unique customers. Average occupancy and peak estimates are separate.']];
t.getRange(`A8:${col(tc.length-1)}8`).values=[tc.map(label)];header(t,`A8:${col(tc.length-1)}8`);
for(let c=0;c<tc.length;c++){t.getRange(`${col(c)}8:${col(c)}32`).format.columnWidth=Math.max(18,Math.min(30,label(tc[c]).length*.65));styleFormat(t,c,9,32,tc[c]);}
t.getRange('A9:A32').values=p.estate_monthly_trend.data.map(r=>[new Date(r[0]+'T00:00:00Z')]);t.getRange('A9:A32').setNumberFormat('mmm-yy');
t.getRange('A46').values=[['Capacity and attendance calculation schedule']];
t.getRange('A48:F48').values=[['gym_id','month','Concurrent capacity','Capacity minutes','Occupancy minutes','Peak capacity minutes']];header(t,'A48:F48');
const helper=p.monthly_performance.data.map((_,i)=>{const r=i+49,sr=i+2;return [`=${src('gym_id',sr)}`,`=${src('month',sr)}`,`=INDEX(${rng('gym_master','capacity_proxy')},MATCH(A${r},${rng('gym_master','gym_id')},0))`,`=C${r}*${src('opening_minutes',sr)}`,`=${src('gym_visits',sr)}*${src('average_visit_duration_minutes',sr)}`,`=D${r}*${src('peak_utilisation_pct',sr)}`];});
t.getRange('A49:F1968').formulas=helper;t.getRange('B49:B1968').setNumberFormat('mmm-yy');t.getRange('C49:F1968').setNumberFormat('#,##0.00');
for(let i=0;i<24;i++){
  const row=i+9,criteria=`${dateRange},$A${row}`,ref=f=>col(tc.indexOf(f))+row;
  t.getRange(`B${row}:${col(tc.length-1)}${row}`).formulas=[tc.slice(1).map(f=>'='+metricFormula(f,criteria,ref,criteria,criteria,'','',row))];
}
t.tables.add(`A8:${col(tc.length-1)}32`,true,'EstateMonthlyMetrics');t.freezePanes.freezeRows(8);t.freezePanes.freezeColumns(1);

// Summary reads finished schedules. Check results never drive this output.
const sumB=(f,w)=>`SUM(${BR(f+'_'+w)})`;
const annualRef=(f,w)=>{
  if(f==='average_members')return `${sumB('member_months',w)}/${w.startsWith('q4')?3:12}`;
  if(f==='arpmm')return ratio(sumB('total_revenue',w),sumB('member_months',w));
  if(f==='subscription_yield')return ratio(sumB('subscription_revenue',w),sumB('member_months',w));
  if(f==='standard_yield')return ratio(sumB('standard_subscription_revenue',w),sumB('standard_member_months',w));
  if(f==='churn_rate')return ratio(sumB('opening_base_cancellations',w),sumB('opening_member_months',w));
  if(f==='conversion_rate')return ratio(sumB('new_members',w),sumB('qualified_prospects',w));
  return sumB(f,w);
};
const summaryFields=['total_revenue','subscription_revenue','joining_fee_revenue','ancillary_revenue','average_members','closing_members','new_members','arpmm','subscription_yield','standard_yield','churn_rate','conversion_rate'];
s.getRange('A9:D9').values=[['Annual estate metric','2024','2025','Change']];header(s,'A9:D9');s.getRange('A9:D9').format.rowHeight=26;
summaryFields.forEach((f,i)=>{const r=i+10;s.getRange(`A${r}`).values=[[label(f)]];s.getRange(`B${r}:D${r}`).formulas=[[`=${annualRef(f,'2024')}`,`=${annualRef(f,'2025')}`,f.endsWith('_rate')?`=100*(C${r}-B${r})`:`=IF(B${r}=0,"",C${r}/B${r}-1)`]];styleFormat(s,1,r,r,f);styleFormat(s,2,r,r,f);s.getRange(`D${r}`).setNumberFormat(f.endsWith('_rate')?'0.00" pp"':'0.0%');});
s.getRange('A24:D24').values=[['Q4 estate metric','Q4 2024','Q4 2025','Change']];header(s,'A24:D24');s.getRange('A24:D24').format.rowHeight=26;
['total_revenue','new_members','churn_rate','conversion_rate'].forEach((f,i)=>{const r=25+i;s.getRange(`A${r}`).values=[[label(f)]];s.getRange(`B${r}:D${r}`).formulas=[[`=${annualRef(f,'q4_2024')}`,`=${annualRef(f,'q4_2025')}`,f.endsWith('_rate')?`=100*(C${r}-B${r})`:`=IF(B${r}=0,"",C${r}/B${r}-1)`]];styleFormat(s,1,r,r,f);styleFormat(s,2,r,r,f);s.getRange(`D${r}`).setNumberFormat(f.endsWith('_rate')?'0.00" pp"':'0.0%');});
s.getRange('A31').values=[['December annualised revenue']];s.getRange('B31').formulas=[[`=SUM(${BR('december_annualised_revenue')})`]];styleFormat(s,1,31,31,'revenue');
s.getRange('A32').values=[['December × 12 is seasonal. It is not a forecast.']];
s.getRange('A36:B36').values=[['Revenue bridge','Net GBP']];header(s,'A36:B36');s.getRange('A36:B36').format.rowHeight=26;
s.getRange('A37:A40').values=[['2024 revenue'],['Member volume contribution'],['Total ARPMM contribution'],['2025 revenue']];
s.getRange('B37:B40').formulas=[['=B10'],['=12*(C14-B14)*B17'],['=12*C14*(C17-B17)'],['=C10']];s.getRange('B37:B42').setNumberFormat('"£"#,##0.00;("£"#,##0.00);"-"');
s.getRange('A42').values=[['Bridge reconciliation difference']];s.getRange('B42').formulas=[['=B37+B38+B39-B40']];
s.getRange('B42').conditionalFormats.add('cellIs',{operator:'notBetween',formula:[-.01,.01],format:{fill:'#FCE4D6',font:{color:'#9C0006'}}});
s.getRange('A44').values=[['Interaction allocated to ARPMM. Yield includes mix, joining fees and ancillary revenue.']];
s.getRange('A46:A48').values=[['Upper-quartile churn'],['Lower-quartile conversion'],['Lower-quartile acquisition growth']];
s.getRange('B46:B48').formulas=[[`=PERCENTILE.INC(${BR('churn_rate_2025')},0.75)`],[`=PERCENTILE.INC(${BR('conversion_rate_2025')},0.25)`],[`=PERCENTILE.INC(${BR('acquisition_growth_yoy')},0.25)`]];s.getRange('B46:B48').setNumberFormat('0.00%');
['high_churn_exception','weak_conversion_exception','declining_acquisition_exception','peak_capacity_exception'].forEach((f,i)=>{s.getRange(`A${50+i}`).values=[[label(f)]];s.getRange(`B${50+i}`).formulas=[[`=SUMPRODUCT(${BR(f)}*1)`]];});
s.getRange('A55').values=[['Flags overlap. These indicators do not assign pricing actions.']];
// Six formula-backed top/bottom lists remain responsive to source edits and ties.
let rankRow=59;
for(const metric of ['total_revenue_2025','revenue_growth_yoy','member_growth_2025'])for(const direction of ['highest','lowest']){
 s.getRange(`A${rankRow}:D${rankRow}`).values=[[`${direction} five: ${label(metric)}`,'gym_id','city','Result']];header(s,`A${rankRow}:D${rankRow}`);s.getRange(`A${rankRow}:D${rankRow}`).format.rowHeight=34;
 for(let j=1;j<=5;j++){
  const r=rankRow+j,match=`MATCH(${j},${BR(direction+'_rank_'+metric)},0)`;
  s.getRange(`A${r}:D${r}`).formulas=[[`=INDEX(${BR('gym_name')},${match})`,`=INDEX(${BR('gym_id')},${match})`,`=INDEX(${BR('city')},${match})`,`=INDEX(${BR(metric)},${match})`]];
  styleFormat(s,3,r,r,metric);
 }
 rankRow+=7;
}
// Regional schedule owns the 16-row export; ratios use pooled exposures.
const rc=p.region_year_baseline.columns;base(s,`A103:${col(rc.length-1)}120`);s.getRange(`A104:${col(rc.length-1)}104`).values=[rc.map(label)];header(s,`A104:${col(rc.length-1)}104`);
s.getRange('A103').values=[['Regional annual baseline']];
for(let i=0;i<16;i++){
 const row=i+105,expected=p.region_year_baseline.data[i],year=String(expected[1]);s.getRange(`A${row}:B${row}`).values=[[expected[0],expected[1]]];
 const ref=f=>col(rc.indexOf(f))+row,regionalSum=f=>`SUMIF(${BR('region')},$A${row},${BR(f+'_'+year)})`;
 s.getRange(`C${row}:${col(rc.length-1)}${row}`).formulas=[rc.slice(2).map(f=>{
  if(f==='gym_count')return `=COUNTIF(${BR('region')},$A${row})`;
  if(f==='months')return '=12';
  if(['average_members','average_monthly_revenue','average_monthly_joins'].includes(f))return '='+ratio(ref({average_members:'member_months',average_monthly_revenue:'total_revenue',average_monthly_joins:'new_members'}[f]),ref('months'));
  const pairs={arpmm:['total_revenue','member_months'],subscription_yield:['subscription_revenue','member_months'],standard_yield:['standard_subscription_revenue','standard_member_months'],acquisition_rate:['new_members','opening_member_months'],churn_rate:['opening_base_cancellations','opening_member_months'],conversion_rate:['new_members','qualified_prospects'],average_utilisation:['occupancy_minutes','capacity_minutes']};
  if(f in pairs)return '='+ratio(ref(pairs[f][0]),ref(pairs[f][1]));
  if(f==='retention_rate')return `=1-${ref('churn_rate')}`;
  if(f==='member_growth')return `=${ref('closing_members')}/${ref('opening_members')}-1`;
  if(f==='average_monthly_peak')return '='+ratio(`SUMPRODUCT((${BR('region')}=$A${row})*${BR('average_monthly_peak_'+year)}*${BR('capacity_minutes_'+year)})`,ref('capacity_minutes'));
  if(f==='max_monthly_peak')return `=_xlfn.MAXIFS(${BR('max_monthly_peak_'+year)},${BR('region')},$A${row})`;
  if(f==='promotion_frequency')return '='+ratio(ref('promotion_gym_months'),`${ref('months')}*${ref('gym_count')}`);
  if(['standard_mix','offpeak_mix','plus_mix'].includes(f))return '='+ratio(`SUMPRODUCT((${BR('region')}=$A${row})*${BR(f+'_'+year)}*${BR('member_months_'+year)})`,ref('member_months'));
  if(f==='complaints_per_1000_member_months')return '='+ratio(`${ref('pricing_complaints')}*1000`,ref('member_months'));
  return '='+regionalSum(f);
 })];
}
for(let c=0;c<rc.length;c++){s.getRange(`${col(c)}104:${col(c)}120`).format.columnWidth=c===0?38:Math.max(18,Math.min(28,label(rc[c]).length*.6));styleFormat(s,c,105,120,rc[c]);}
s.tables.add(`A104:${col(rc.length-1)}120`,true,'RegionalAnnualMetrics');
// Restore summary layout widths after sizing the regional table.
s.getRange('A1:A100').format.columnWidth=38;s.getRange('B1:E100').format.columnWidth=20;s.getRange('F1:R100').format.columnWidth=13;
s.getRange('A122').values=[['This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.']];
s.getRange('A124').values=[['This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.']];

// Native chart helpers link only to the owning calculation schedules.
t.getRange('A35:E35').values=[['Month','2024 average members','2025 average members','2024 net revenue','2025 net revenue']];header(t,'A35:E35');t.getRange('A35:E35').format.rowHeight=32;
for(let i=0;i<12;i++){const r=i+36;t.getRange(`A${r}`).values=[[['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][i]]];t.getRange(`B${r}:E${r}`).formulas=[[`=${T('average_members',i+9)}`,`=${T('average_members',i+21)}`,`=${T('total_revenue',i+9)}`,`=${T('total_revenue',i+21)}`]];}
// Helpers end at row 47; capacity schedule starts at row 48.
t.getRange('A46').clear({applyTo:'contents'});
function chartStyle(chart,title,from,to,format){chart.title=title;chart.titleTextStyle.typeface='Arial';chart.titleTextStyle.fontSize=12;chart.setPosition(from,to);chart.legend={position:'top',textStyle:{typeface:'Arial',fontSize:10}};chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10}};chart.yAxis={numberFormatCode:format,numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};chart.series.items.forEach((series,i)=>{series.fill=['#829AB1','#243B53','#D97706'][i%3];series.line={fill:['#829AB1','#243B53','#D97706'][i%3],style:i===0?'dashed':'solid',width:2};});}
const members=s.charts.add('line',[t.getRange('A35:A47'),t.getRange('B35:B47'),t.getRange('C35:C47')]);chartStyle(members,'Matching-month average members','J9','R24','#,##0');
const revenue=s.charts.add('line',[t.getRange('A35:A47'),t.getRange('D35:D47'),t.getRange('E35:E47')]);chartStyle(revenue,'Matching-month net revenue (£m)','J26','R41','"£"0.0,,"m"');
// Bar contributions are editable; the standalone figure supplies the exact waterfall.
const bridgeChart=s.charts.add('bar',s.getRange('A38:B39'));chartStyle(bridgeChart,'Annual revenue change contributions (£m)','J43','R58','"£"0.0,,"m"');bridgeChart.hasLegend=false;
const scatter=s.charts.add('scatter',[b.getRange(`${col(bc.indexOf('acquisition_growth_yoy'))}8:${col(bc.indexOf('acquisition_growth_yoy'))}88`),b.getRange(`${col(bc.indexOf('churn_rate_2025'))}8:${col(bc.indexOf('churn_rate_2025'))}88`)]);
chartStyle(scatter,'Acquisition growth and monthly churn','J60','R80','0.0%');scatter.hasLegend=false;scatter.xAxis={numberFormatCode:'0.0%',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};scatter.xAxis.title.text='Acquisition growth, 2025 vs 2024';scatter.yAxis.title.text='2025 monthly churn';

wb.recalculate();
const info=verify(wb,'authored');
console.log('Derived value parity:',JSON.stringify(info));
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1500})).ndjson);
for(const [name,range,file] of [['Baseline','A1:I13','baseline_primary'],['Baseline','N8:W14','baseline_exceptions'],['Estate Trends','A1:I14','estate_primary'],['Estate Trends','A48:F56','estate_capacity'],['Baseline Summary','A1:E33','summary_metrics'],['Baseline Summary','A36:E57','summary_bridge_flags'],['Baseline Summary','A59:E99','summary_rankings'],['Baseline Summary','A103:H110','summary_regions'],['Baseline Summary','J9:R41','summary_trends'],['Baseline Summary','J43:R80','summary_bridge_scatter']]){
 const blob=await wb.render({sheetName:name,range,scale:1.3,format:'png'});await fs.writeFile(path.join(previews,file+'.png'),new Uint8Array(await blob.arrayBuffer()));
}
const output=await SpreadsheetFile.exportXlsx(wb);await output.save(path.join(previews,'baseline_parts.xlsx'));
await fs.writeFile(path.join(previews,'author_verification.json'),JSON.stringify(info,null,2));
console.log('Artifact Tool sheets exported; append the three analysis sheets to the preserved workbook.');
