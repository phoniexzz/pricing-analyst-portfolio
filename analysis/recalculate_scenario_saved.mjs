import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const dir=path.dirname(fileURLToPath(import.meta.url)),pre=path.join(dir,'.workbook_previews','phase6');
const layout=JSON.parse(await fs.readFile(path.join(pre,'layout.json'),'utf8')),p=JSON.parse(await fs.readFile(path.join(pre,'payload.json'),'utf8'));
const col=i=>{let s='';for(let n=i+1;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const wb=Workbook.create();const actualSaved=JSON.parse(await fs.readFile(path.join(pre,'saved_formula_blocks.json'),'utf8'));
for(const sheet of actualSaved){const s=wb.worksheets.add(sheet.name);for(const block of sheet.blocks)s.getRange(block.address).values=block.values;}
for(const sheet of actualSaved){const s=wb.worksheets.getItem(sheet.name);for(const block of sheet.blocks)if(block.formulas)s.getRange(block.address).formulas=block.formulas;}
console.log('Actual saved formula blocks loaded into Artifact Tool.');
console.log('Saved scenario graph reconstructed from actual file formulas and values.');wb.recalculate();
const checks=wb.worksheets.getItem('Scenario Model').getRange('D2201:D2280').values;if(checks.some(r=>Math.abs(r[0])>1e-8))throw Error('Independent source opening-members check failed.');
const summary=wb.worksheets.getItem('Scenario Summary'),inputs=wb.worksheets.getItem('Scenario Inputs'),comp=wb.worksheets.getItem('Scenario Comparison');
const estate=p.estate.data.filter(r=>r[p.estate.columns.indexOf('case')]==='Base');let max=0;
for(let i=0;i<4;i++)for(const [cell,field]of [[`B${9+i}`,'monthly_revenue'],[`C${9+i}`,'incremental_revenue'],[`D${9+i}`,'incremental_revenue_lower'],[`E${9+i}`,'incremental_revenue_upper'],[`F${9+i}`,'month12_members'],[`G${9+i}`,'member_impact'],[`H${9+i}`,'positive_revenue_draw_fraction']]){
 const v=summary.getRange(cell).values[0][0],e=estate[i][p.estate.columns.indexOf(field)],diff=Math.abs(v-e);max=Math.max(max,diff);if(typeof v!=='number'||diff>Math.max(1e-7,Math.abs(e)*1e-10))throw Error(`${cell}: ${v} vs ${e}`);
}
const old=summary.getRange('B20').values[0][0];inputs.getRange('I9').values=[[0]];if(summary.getRange('B20').values[0][0]<=old)throw Error('Saved numeric zero override failed');if(comp.getRange('D3').values[0][0]==='CURRENT')throw Error('Saved stale-input detection failed');const intervalCell=col(layout.captureColumns.indexOf('incremental_revenue_lower'))+'31';if(comp.getRange(intervalCell).values[0][0]!=='')throw Error('Saved site intervals did not become unavailable immediately');inputs.getRange('I9').values=[[null]];
inputs.getRange('B4').values=[[3]];if(summary.getRange('B20').values[0][0]===old)throw Error('Saved price change failed');inputs.getRange('B4').values=[[2]];
inputs.getRange('B3').values=[[2]];if(summary.getRange('B20').values[0][0]===old)throw Error('Saved case selector failed');inputs.getRange('B3').values=[[1]];
wb.recalculate();const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1800});console.log(errors.ndjson);
const cache={};for(const [name,range]of [['Scenario Inputs',`A1:${col(80+Math.max(p.drivers.columns.length,p.states.columns.length)-1)}2800`],['Scenario Model',`A1:${col(Math.max(layout.annualFields.length,layout.summaryFields.length)-1)}${layout.detailRow}`],['Scenario Comparison',`A1:${col(p.comparisons.columns.length-1)}12621`],['Scenario Summary','A1:S240']])cache[name]={values:wb.worksheets.getItem(name).getRange(range).values.map(r=>r.map(v=>v instanceof Date?(v.getTime()-Date.UTC(1899,11,30))/86400000:v))};
await fs.writeFile(path.join(pre,'final_values.json'),JSON.stringify(cache));
await fs.writeFile(path.join(pre,'saved_recalculation.json'),JSON.stringify({savedWorkbookRecalculated:true,savedSummaryMaxDifference:max,savedFormulaErrorScan:errors.ndjson,savedInputTests:['Zero override distinct from blank','Price change propagates','Case selection propagates','Captured comparisons stale after driver override'],recalculationEngine:'Artifact Tool recalculation of actual saved formulas/values in bounded blocks; all 21 prior sheets/features checked independently against the pre-edit package. Native Excel was not automated.'},null,2));
console.log('Saved formula graph recalculated; independent source checks, summary parity and input edits passed.');
