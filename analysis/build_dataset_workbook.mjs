import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile, FileBlob } from '@oai/artifact-tool';

const dir = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(dir);
const payload = JSON.parse(await fs.readFile(path.join(dir,'workbook_data.json'),'utf8'));
const config = JSON.parse(await fs.readFile(path.join(dir,'generation_config.json'),'utf8'));
const result = JSON.parse(await fs.readFile(path.join(dir,'validation_results.json'),'utf8'));
const dictionary = payload.data_dictionary.data.map(r=>Object.fromEntries(payload.data_dictionary.columns.map((c,i)=>[c,r[i]])));
const previewDir = path.join(dir,'.workbook_previews');
await fs.mkdir(previewDir,{recursive:true});
await fs.mkdir(path.join(root,'excel'),{recursive:true});

const wb = Workbook.create();
const overview = wb.worksheets.add('Dataset Overview');
const assumptions = wb.worksheets.add('Assumptions');
const names = {
  gym_master:'Gym Master',monthly_performance:'Monthly Performance',competitor_prices:'Competitors',pricing_history:'Historical Pricing',
  cohorts:'Customer Cohorts',membership_ledger:'Membership Ledger',experiment_assignments:'Pilot Assignments',market_events:'Market Events',
};
const sheets = {};
for(const [key,name] of Object.entries(names)) sheets[key]=wb.worksheets.add(name);
const dictSheet=wb.worksheets.add('Data Dictionary');
const checks=wb.worksheets.add('Checks');
const readme=wb.worksheets.add('README');
const blockSize=6000;
const partsDir=path.join(previewDir,'parts');
await fs.mkdir(partsDir,{recursive:true});

function col(index){let s='';for(let n=index+1;n>0;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;}
function address(key,field,row=2){return `'${names[key]}'!${col(payload[key].columns.indexOf(field))}${row}`;}
function range(key,field){const c=col(payload[key].columns.indexOf(field));return `'${names[key]}'!$${c}$2:$${c}$${payload[key].data.length+1}`;}
function base(sheet,area){sheet.showGridLines=false;sheet.getRange(area).format.font={name:'Arial',size:10};sheet.getRange(area).format.verticalAlignment='center';}
function header(sheet,area){sheet.getRange(area).format={fill:'#243B53',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center',verticalAlignment:'center',rowHeight:58};}
function title(sheet,text){sheet.getRange('A2').values=[[text]];sheet.getRange('A2').format.font={name:'Arial',size:14,bold:true};sheet.getRange('A3:F3').format.borders={bottom:{style:'thin',color:'#829AB1'}};}

function populate(sheet,key,data){
  const {columns}=payload[key];
  const metadata=new Map(dictionary.filter(r=>r.table===key).map(r=>[r.field,r]));
  const end=data.length+1;
  sheet.showGridLines=false;
  sheet.getRange(`A1:${col(columns.length-1)}1`).values=[columns];
  // Keep block size bounded while retaining every source row.
  for(let start=0;start<data.length;start+=2500){
    const rows=data.slice(start,start+2500).map(row=>row.map((v,i)=>v!==null&&metadata.get(columns[i]).data_type==='date'?new Date(`${v}T00:00:00Z`):v));
    sheet.getRange(`A${start+2}:${col(columns.length-1)}${start+rows.length+1}`).values=rows;
  }
  base(sheet,`A1:${col(columns.length-1)}${end}`);
  header(sheet,`A1:${col(columns.length-1)}1`);
  sheet.getRange(`A1:${col(columns.length-1)}1`).format.rowHeight=32;
  for(let i=0;i<columns.length;i++){
    const md=metadata.get(columns[i]);
    const c=col(i);
    const maxValueLength=Math.max(0,...data.slice(0,120).map(row=>typeof row[i]==='string'?row[i].length:0));
    const width=md.data_type==='text'?Math.min(65,Math.max(18,maxValueLength+5,columns[i].length+5)):Math.max(17,columns[i].length+5);
    sheet.getRange(`${c}1:${c}${end}`).format.columnWidth=width;
    if(md.data_type==='date')sheet.getRange(`${c}2:${c}${end}`).setNumberFormat('dd/mm/yyyy');
    else if(md.unit==='decimal fraction')sheet.getRange(`${c}2:${c}${end}`).setNumberFormat('0.00%');
    else if(md.unit.startsWith('GBP'))sheet.getRange(`${c}2:${c}${end}`).setNumberFormat('"£"#,##0.00');
    else if(md.data_type==='integer')sheet.getRange(`${c}2:${c}${end}`).setNumberFormat('#,##0');
    else if(md.data_type==='decimal')sheet.getRange(`${c}2:${c}${end}`).setNumberFormat('#,##0.00');
    sheet.getRange(`${c}2:${c}${end}`).format.horizontalAlignment=md.data_type==='text'?'left':'right';
    if(columns[i]==='description'||columns[i]==='reason'){
      sheet.getRange(`${c}2:${c}${end}`).format.wrapText=true;
      sheet.getRange(`A2:${col(columns.length-1)}${end}`).format.rowHeight=36;
    }
  }
  const table=sheet.tables.add(`A1:${col(columns.length-1)}${end}`,true,`Source_${key}`);
  table.showFilterButton=true;
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(2);
}

if(process.argv.includes('--ledger-parts')){
  for(let start=blockSize;start<payload.membership_ledger.data.length;start+=blockSize){
    let part=Workbook.create();
    const sheet=part.worksheets.add('Membership Ledger');
    populate(sheet,'membership_ledger',payload.membership_ledger.data.slice(start,start+blockSize));
    part.recalculate();
    let blob=await SpreadsheetFile.exportXlsx(part);
    await blob.save(path.join(partsDir,`ledger_${start}.xlsx`));
    blob=null;part=null;globalThis.gc?.();
    console.log(`Exported ledger block ${start}–${Math.min(start+blockSize,payload.membership_ledger.data.length)-1}`);
  }
  process.exit(0);
}

if(process.argv.includes('--verify-assembled')){
  const final=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(root,'excel','gym_pricing_model.xlsx')));
  final.recalculate();
  const view=final.worksheets.getItem('Dataset Overview');
  const audit=final.worksheets.getItem('Checks');
  if(Math.abs(audit.getRange('C5').values[0][0])>.011)throw new Error('Assembled ledger revenue failed recalculation');
  if(view.getRange('B17').values[0][0]!==payload.membership_ledger.data.length)throw new Error('Assembled ledger count failed recalculation');
  if(view.getRange('B8').values[0][0]!==result.opening_members||view.getRange('B9').values[0][0]!==result.closing_members)throw new Error('Assembled member stocks failed');
  const rows=audit.getRange('C8:H1927').values;
  if(rows.some(r=>r.some(v=>typeof v!=='number'||Math.abs(v)>1e-8)))throw new Error('Assembled monthly checks failed');
  const source=final.worksheets.getItem('Monthly Performance');
  const cell=source.getRange(col(payload.monthly_performance.columns.indexOf('closing_members'))+'2');
  const old=cell.values[0][0];cell.values=[[old+1]];final.recalculate();
  if(audit.getRange('C8').values[0][0]!==1)throw new Error('Assembled member-change test failed');
  cell.values=[[old]];final.recalculate();
  const errors=await final.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:2500});
  for(const [sheetName,renderRange,filename] of [
    ['Dataset Overview','A1:F24','01_Dataset_Overview.png'],
    ['Checks','A1:H12','12_Checks.png'],
    ['Membership Ledger','A1:H10','08_Membership_Ledger.png'],
    ['Membership Ledger','P1:W9','08_Membership_Ledger_values.png'],
    ['Membership Ledger',`P${payload.membership_ledger.data.length-7}:W${payload.membership_ledger.data.length+1}`,'08_Membership_Ledger_tail.png'],
  ]){
    const preview=await final.render({sheetName,range:renderRange,scale:1.5,format:'png'});
    await fs.writeFile(path.join(previewDir,filename),new Uint8Array(await preview.arrayBuffer()));
  }
  await fs.writeFile(path.join(dir,'final_formula_cache.json'),JSON.stringify({'Dataset Overview':{B17:view.getRange('B17').values[0][0]},Checks:{C5:audit.getRange('C5').values[0][0]}}));
  const info=JSON.parse(await fs.readFile(path.join(dir,'workbook_verification.json'),'utf8'));
  info.ledgerReconciliation=audit.getRange('C5').values[0][0];info.formulaErrorScan=errors.ndjson;
  info.assembledWorkbookRecalculation='Full saved workbook re-imported and recalculated in Artifact Tool; all 1,920 monthly reconciliations and full-ledger total passed.';
  info.exportMethod='All sheets and ledger blocks authored by Artifact Tool; XML packaging combines ledger blocks to avoid the exporter string-size limit.';
  await fs.writeFile(path.join(dir,'workbook_verification.json'),JSON.stringify(info,null,2));
  console.log(info.assembledWorkbookRecalculation);console.log(errors.ndjson);
  process.exit(0);
}

for(const [key,sheet] of Object.entries(sheets)){
  const data=key==='membership_ledger'?payload[key].data.slice(0,blockSize):payload[key].data;
  populate(sheet,key,data);
  console.log(`Populated ${sheet.name}: ${data.length.toLocaleString()} rows${key==='membership_ledger'?' (first export block)':''}`);
}

base(overview,'A1:F25');overview.tabColor='#243B53';
overview.getRange('A1:A25').format.columnWidth=36;overview.getRange('B1:B25').format.columnWidth=26;
overview.getRange('C1:C25').format.columnWidth=4;overview.getRange('D1:F25').format.columnWidth=22;
title(overview,'Northstar Fitness dataset');
overview.getRange('A5:B5').values=[['Historical window','Jan 2024 – Dec 2025']];
overview.getRange('A6:B6').values=[['Gym count',null]];
overview.getRange('B6').formulas=[[`=COUNTA(${range('gym_master','gym_id')})`]];
overview.getRange('A7').values=[['Gym-month records']];overview.getRange('B7').formulas=[[`=COUNTA(${range('monthly_performance','gym_id')})`]];
overview.getRange('A8').values=[['Opening estate memberships']];overview.getRange('B8').formulas=[[`=SUMIFS(${range('monthly_performance','opening_members')},${range('monthly_performance','month')},Assumptions!$B$6)`]];
overview.getRange('A9').values=[['December closing memberships']];overview.getRange('B9').formulas=[[`=SUMIFS(${range('monthly_performance','closing_members')},${range('monthly_performance','month')},Assumptions!$B$7)`]];
overview.getRange('A11:B11').values=[['Source table','Rows']];header(overview,'A11:B11');overview.getRange('A11:B11').format.rowHeight=24;
let summaryRow=12;
for(const key of Object.keys(names)){
  overview.getRange(`A${summaryRow}`).values=[[names[key]]];
  overview.getRange(`B${summaryRow}`).formulas=[[`=COUNTA(${range(key,payload[key].columns[0])})`]];
  summaryRow++;
}
overview.getRange('B6:B19').setNumberFormat('#,##0');
overview.getRange('D5:F5').values=[['Phase 2','Synthetic history','']];
overview.getRange('D7:F10').values=[['Next phase','Baseline analysis',''],['Revenue basis','Net of assumed VAT',''],['Member figures','Monthly stocks',''],['Recommendations','Not calculated','']];
overview.getRange('A22:F23').format.wrapText=true;
overview.getRange('A22').values=[['All observations are synthetic.']];
overview.getRange('A23').values=[['See README for definitions and limits.']];

base(assumptions,'A1:C21');assumptions.tabColor='#486581';
assumptions.getRange('A1:A21').format.columnWidth=43;assumptions.getRange('B1:B21').format.columnWidth=27;assumptions.getRange('C1:C21').format.columnWidth=85;
title(assumptions,'Generation assumptions');
const assumptionRows=[
  ['Parameter','Value','Meaning'],
  ['Random seed',config.seed,'Fixed generation seed; assumed mechanisms are not measured elasticity.'],
  ['First observation month',new Date('2024-01-01T00:00:00Z'),'First day of monthly historical key.'],
  ['Last observation month',new Date('2025-12-01T00:00:00Z'),'December observation includes the full calendar month.'],
  ['VAT modelling convention',config.vat_rate,'Uniform assumed VAT rate on all included receipts.'],
  ['Opening estate members',config.opening_estate_members,'Allocated once; future closing stocks are not rescaled.'],
  ['Existing-member notice, months',1,'First implementation is month after headline intervention.'],
  ['Introductory protection, months',config.promotion_protection_months,'Standard new-joiner discount protected for two billing months.'],
  ['Introductory Standard discount',config.new_standard_promotion_discount,'Honour until exclusive protection expiry.'],
  ['Average visit duration, minutes',config.average_visit_duration_minutes,'Average attendance derives from visits and total opening minutes.'],
  ['Advertised joining fee',config.joining_fee_gross,'Consumer amount; waivers captured in number of payers.'],
  ['Future decision horizon, months',12,'Used in later phases; this workbook contains history only.'],
];
assumptions.getRange('A4:C16').values=[...assumptionRows,['Revenue convention','Net GBP','Consumer prices gross; revenue excludes assumed VAT.']];
header(assumptions,'A4:C4');assumptions.getRange('A4:C4').format.rowHeight=24;
assumptions.getRange('B6:B7').setNumberFormat('dd/mm/yyyy');assumptions.getRange('B8').setNumberFormat('0%');assumptions.getRange('B9').setNumberFormat('#,##0');assumptions.getRange('B12').setNumberFormat('0%');assumptions.getRange('B14').setNumberFormat('"£"0.00');
assumptions.getRange('C5:C16').format.wrapText=true;assumptions.getRange('A5:C16').format.rowHeight=30;
assumptions.getRange('A19:C20').format.wrapText=true;
assumptions.getRange('A19').values=[['Generation parameters are fixed inputs.']];
assumptions.getRange('C19').values=[['Changing a value here does not regenerate source records. Rerun the generator to change history.']];

const dd=payload.data_dictionary;
base(dictSheet,`A1:H${dd.data.length+1}`);
dictSheet.getRange(`A1:H${dd.data.length+1}`).values=[dd.columns,...dd.data];
header(dictSheet,'A1:H1');
const widths=[25,35,14,27,45,32,70,100];
widths.forEach((w,i)=>dictSheet.getRange(`${col(i)}1:${col(i)}${dd.data.length+1}`).format.columnWidth=w);
dictSheet.getRange(`A2:H${dd.data.length+1}`).format.wrapText=true;
dictSheet.getRange(`A2:H${dd.data.length+1}`).format.rowHeight=54;
dictSheet.tables.add(`A1:H${dd.data.length+1}`,true,'DictionaryFields');dictSheet.freezePanes.freezeRows(1);dictSheet.freezePanes.freezeColumns(2);

base(checks,'A1:H1930');checks.getRange('A1:A1930').format.columnWidth=20;checks.getRange('B1:B1930').format.columnWidth=20;checks.getRange('C1:H1930').format.columnWidth=24;
title(checks,'Source reconciliations');
checks.getRange('A5').values=[['Ledger versus monthly net subscriptions']];checks.getRange('A5').format.columnWidth=42;
checks.getRange('C5').formulas=[[`=ROUND(SUM(${range('membership_ledger','subscription_revenue')})-SUM(${range('monthly_performance','subscription_revenue')}),2)`]];
checks.getRange('E5:F5').values=[['Expected difference',0]];
checks.getRange('A7:H7').values=[['gym_id','month','Member bridge','Average exposure','Revenue components','Closing tier totals','Tier subscription totals','Opening-base churn']];header(checks,'A7:H7');
const formulaRows=payload.monthly_performance.data.map((row,i)=>{
  const r=i+2,ref=f=>address('monthly_performance',f,r);
  return [`=${ref('gym_id')}`,`=${ref('month')}`,`=${ref('closing_members')}-${ref('opening_members')}-${ref('new_members')}+${ref('cancelled_members')}`,`=${ref('average_members')}-(${ref('opening_members')}+${ref('closing_members')})/2`,
    `=ROUND(${ref('monthly_revenue')}-${ref('subscription_revenue')}-${ref('joining_fee_revenue')}-${ref('ancillary_revenue')},2)`,
    `=${ref('closing_members')}-${ref('standard_members')}-${ref('offpeak_members')}-${ref('premium_members')}`,
    `=ROUND(${ref('subscription_revenue')}-${ref('standard_subscription_revenue')}-${ref('offpeak_subscription_revenue')}-${ref('premium_subscription_revenue')},2)`,
    `=ROUND(${ref('churn_rate')}-${ref('opening_base_cancellations')}/${ref('opening_members')},10)`];
});
checks.getRange(`A8:H${formulaRows.length+7}`).formulas=formulaRows;
checks.getRange(`B8:B${formulaRows.length+7}`).setNumberFormat('dd/mm/yyyy');checks.getRange(`C8:H${formulaRows.length+7}`).setNumberFormat('0.0000');checks.getRange('C5').setNumberFormat('"£"0.00');
checks.getRange(`C8:H${formulaRows.length+7}`).conditionalFormats.add('cellIs',{operator:'notEqual',formula:0,format:{fill:'#FCE4D6',font:{color:'#9C0006',bold:true}}});
checks.getRange('C5').conditionalFormats.add('cellIs',{operator:'notEqual',formula:0,format:{fill:'#FCE4D6',font:{color:'#9C0006',bold:true}}});
checks.freezePanes.freezeRows(7);checks.freezePanes.freezeColumns(2);

base(readme,'A1:B24');readme.tabColor='#829AB1';readme.getRange('A1:A24').format.columnWidth=28;readme.getRange('B1:B24').format.columnWidth=110;
readme.getRange('A2').values=[['Dataset guide']];readme.getRange('A2').format.font={name:'Arial',size:14,bold:true};
const guide=[
 ['Project','UK Gym Pricing & Revenue Optimisation. Identifying Site-Level Pricing Headroom Across an 80-Gym Estate.'],
 ['Data disclaimer','This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.'],
 ['Period','January 2024–December 2025. Master fields are a December snapshot; use monthly history for pre-event comparisons.'],
 ['Price and revenue','Prices include VAT. Revenue excludes an assumed uniform 20% VAT. Joining fees are recognised in joining month as a portfolio simplification.'],
 ['Premium label','premium columns refer to Plus memberships. All tiers remain visible even though only Standard prices change.'],
 ['Members','Opening and closing are stocks. average_members is their midpoint. Tier membership columns are closing counts. Do not sum member stocks as unique customers.'],
 ['Acquisition and churn','Acquisition = new / opening members. Churn = opening-base exits / opening members. Same-month joiner exits remain in the member bridge.'],
 ['Conversion','New members / all qualified prospects. Website leads and trials are nested subsets, not additive denominators.'],
 ['Competitors','PulseFit and Forge Fitness are fictional proxies. PureGym_equivalent_price and JD_equivalent_price contain no real brand observations. Recurring gaps exclude fees and introductory offers.'],
 ['Repricing','New joiners pay increased headline prices immediately. Eligible existing Standard rates rise once after one full month notice and promotional protection expiry. Legacy differences remain.'],
 ['Cohorts','Original tier identity survives downgrades. Retention milestones are monthly approximations. Incomplete milestones and revenue windows are blank. average_tenure is censored observed exposure.'],
 ['Legacy population','Unknown join dates remain blank; opening legacy groups are excluded from the joining-cohort summary.'],
 ['Utilisation','Derived from visits, duration and 24-hour opening minutes. Peak uses a within-day concentration factor. Capacity is comfortable occupancy; above 100% means service pressure.'],
 ['Historical evidence','12 targeted +£1 sites in July 2024; eight targeted +£2 sites in February 2025; April 2025 historical pilot has 12 randomised matched treatment/control pairs. Outcomes are not interpreted here.'],
 ['Formula checks','Checks reads sources independently and feeds no business calculations. Python validates all ledger roll-forwards, cohorts and eligibility; workbook checks show monthly bridges and revenue reconciliation.'],
 ['Regeneration','CSV records are fixed synthetic observations. Rerun the generator and workbook builder to change history. Generation parameters must not be used as estimated elasticity.'],
 ['Next phase','Baseline analysis. No headroom rankings, forward scenarios, recommendations or future experiment results are included.'],
 ['Limits','Monthly exposure is approximate. No cash collection, bad debt, fixed terms, freezes, cross-gym movement or upgrades are modelled. Revenue improvement is not profit improvement.'],
 ['Full disclaimer','This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.'],
];
readme.getRange(`A4:B${guide.length+3}`).values=guide;readme.getRange(`A4:B${guide.length+3}`).format.wrapText=true;readme.getRange(`A4:B${guide.length+3}`).format.rowHeight=48;readme.getRange(`A4:A${guide.length+3}`).format.font={name:'Arial',size:10,bold:true};

wb.recalculate();
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:2500});
console.log('Formula error scan:',errors.ndjson);
const checkValues=checks.getRange(`C8:H${formulaRows.length+7}`).values;
if(checkValues.some(row=>row.some(value=>typeof value!=='number'||Math.abs(value)>1e-8)))throw new Error('Monthly reconciliation failed');
// Full-ledger SUM is verified after block assembly; this intermediate has only the first block.
if(overview.getRange('B8').values[0][0]!==result.opening_members||overview.getRange('B9').values[0][0]!==result.closing_members)throw new Error('Dataset stock totals do not match source');

// Recalculation proof: change source values, observe dependent formulas, then restore.
const closingCell=sheets.monthly_performance.getRange(col(payload.monthly_performance.columns.indexOf('closing_members'))+'2');
const oldClosing=closingCell.values[0][0];closingCell.values=[[oldClosing+1]];wb.recalculate();
if(checks.getRange('C8').values[0][0]!==1)throw new Error('Member bridge failed input-change test');
closingCell.values=[[oldClosing]];
const revenueCell=sheets.monthly_performance.getRange(col(payload.monthly_performance.columns.indexOf('subscription_revenue'))+'2');
const oldRevenue=revenueCell.values[0][0];revenueCell.values=[[oldRevenue+1]];wb.recalculate();
if(checks.getRange('E8').values[0][0]!==-1)throw new Error('Revenue check failed input-change test');
revenueCell.values=[[oldRevenue]];wb.recalculate();
const finalChecks=checks.getRange(`C8:H${formulaRows.length+7}`).values;
if(finalChecks.some(row=>row.some(v=>typeof v!=='number'||Math.abs(v)>1e-8)))throw new Error('Source restoration failed');
await fs.writeFile(path.join(dir,'workbook_verification.json'),JSON.stringify({sourceSheets:names,formulaErrorScan:errors.ndjson,monthlyReconciliationRows:formulaRows.length,ledgerReconciliation:checks.getRange('C5').values[0][0],openingMembers:overview.getRange('B8').values[0][0],closingMembers:overview.getRange('B9').values[0][0],inputChangeTests:'Member bridge and revenue component checks reacted; original inputs restored',renderedSheets:[],excelNativeApplication:'Not automated; recalculation verified in Artifact Tool'},null,2));

let previewIndex=0;
const previewList=[];
for(const sheet of [overview,assumptions,...Object.values(sheets),dictSheet,checks,readme]){
  let renderRange='A1:H10';
  if(sheet===overview)renderRange='A1:F24';
  if(sheet===assumptions)renderRange='A1:C20';
  if(sheet===readme)renderRange='A1:B22';
  if(sheet===dictSheet)renderRange='A1:H7';
  if(sheet===checks)renderRange='A1:H12';
  const blob=await wb.render({sheetName:sheet.name,range:renderRange,scale:1.5,format:'png'});
  const filename=`${String(++previewIndex).padStart(2,'0')}_${sheet.name.replaceAll(' ','_')}.png`;
  await fs.writeFile(path.join(previewDir,filename),new Uint8Array(await blob.arrayBuffer()));
  previewList.push({sheet:sheet.name,file:filename});
  console.log(`Rendered ${sheet.name}`);
}
await fs.writeFile(path.join(previewDir,'manifest.json'),JSON.stringify(previewList,null,2));
console.log('Exporting workbook...');
const output=await SpreadsheetFile.exportXlsx(wb);
await output.save(path.join(partsDir,'core.xlsx'));
const verification=JSON.parse(await fs.readFile(path.join(dir,'workbook_verification.json'),'utf8'));
verification.renderedSheets=previewList.map(p=>p.sheet);
await fs.writeFile(path.join(dir,'workbook_verification.json'),JSON.stringify(verification,null,2));
console.log('Saved intermediate core.xlsx; next export ledger blocks and assemble.');
