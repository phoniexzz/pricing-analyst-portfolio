import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook} from '@oai/artifact-tool';
const pre=path.join(path.dirname(fileURLToPath(import.meta.url)),'.workbook_previews','phase7');
const p=JSON.parse(await fs.readFile(path.join(pre,'saved_graph.json'),'utf8'));
const canonical=Object.fromEntries(Object.keys(p.graphs).sort().map(n=>[n,Object.fromEntries(Object.entries(p.graphs[n].formulas).sort(([a],[b])=>a<b?-1:a>b?1:0))]));
const formulaGraphHash=createHash('sha256').update(JSON.stringify(canonical),'utf8').digest('hex');
const wb=Workbook.create(),col=i=>{let s='';for(let n=i+1;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const load=(sheet,data,isFormula=false)=>{
 let rows=1,cols=1;for(const a of Object.keys(data)){const m=a.match(/([A-Z]+)(\d+)/);let c=0;for(const ch of m[1])c=c*26+ch.charCodeAt(0)-64;rows=Math.max(rows,+m[2]);cols=Math.max(cols,c);}
 const matrix=Array.from({length:rows},()=>Array(cols).fill(null));for(const[a,v]of Object.entries(data)){const m=a.match(/([A-Z]+)(\d+)/);let c=0;for(const ch of m[1])c=c*26+ch.charCodeAt(0)-64;matrix[+m[2]-1][c-1]=v;}
 const r=sheet.getRange(`A1:${col(cols-1)}${rows}`);if(isFormula)r.formulas=matrix;else r.values=matrix;
};
const created=new Set();for(const name of [...Object.keys(p.sources),...Object.keys(p.graphs)])if(!created.has(name)){wb.worksheets.add(name);created.add(name);}
for(const[name,values]of Object.entries(p.sources))load(wb.worksheets.getItem(name),values);
for(const[name,g]of Object.entries(p.graphs))load(wb.worksheets.getItem(name),g.values);
for(const[name,g]of Object.entries(p.graphs))load(wb.worksheets.getItem(name),g.formulas,true);
console.log('Actual saved Phase 7 formula graph loaded.');wb.recalculate();
const R=wb.worksheets.getItem('Recommendations'),S=wb.worksheets.getItem('Recommendation Summary'),I=wb.worksheets.getItem('Scenario Inputs'),C=wb.worksheets.getItem('Scenario Comparison');
const mi=Object.fromEntries(p.layout.primary.map((f,i)=>[f,i]));let checked=0,maxDiff=0;
const primary=p.expected.data.map(r=>Object.fromEntries(p.expected.columns.map((f,i)=>[f,r[i]])));
const verify=()=>{
 for(let j=0;j<80;j++)for(const f of ['action','proposed_increment','provisional_test_increment','rule_id','selected_incremental_revenue','selected_downside_member_impact','selected_downside_revenue','plus1_qualified','plus2_qualified']){
 const actual=R.getRange(col(mi[f])+(21+j)).values[0][0],expected=primary[j][f];if(typeof expected==='number'){const d=Math.abs(actual-expected);maxDiff=Math.max(maxDiff,d);if(typeof actual!=='number'||d>Math.max(1e-7,Math.abs(expected)*2e-11))throw Error('Saved recalculation '+f+'/'+j);}else if(actual!==expected)throw Error('Saved recalculation '+f+'/'+j);checked++;
 }
 const pc=p.layout.portfolioCols;
 for(let j=0;j<15;j++)for(const f of['incremental_revenue','monthly_revenue','member_difference','member_impact','conversion_rate','churn_rate','arpmm','incremental_revenue_lower','incremental_revenue_upper']){
 const actual=S.getRange(col(pc.indexOf(f))+(131+j)).values[0][0],expected=p.expected_portfolio.data[j][p.expected_portfolio.columns.indexOf(f)];const d=Math.abs(actual-expected);maxDiff=Math.max(maxDiff,d);if(typeof actual!=='number'||d>Math.max(1e-7,Math.abs(expected)*2e-11))throw Error('Saved portfolio '+f+'/'+j);checked++;
 }
};verify();
const tests=[];const put=(s,a,v)=>s.getRange(a).values=[[v]];
const before=R.getRange('D21:F100').values;
put(R,'B4',.03);if(JSON.stringify(R.getRange('D21:F100').values)===JSON.stringify(before)||S.getRange('E5').values[0][0]==='CURRENT')throw Error('Saved policy edit stale failed');if(S.getRange('E10').values[0][0]!=='')throw Error('Saved stale interval visible');tests.push('Actual saved member-policy edit changes mix and hides stale interval');put(R,'B4',.05);
put(R,'B6',0);if(JSON.stringify(R.getRange('D21:F100').values)===JSON.stringify(before))throw Error('Zero repeat failed');tests.push('Saved zero repeat setting valid');put(R,'B6',1);
put(R,'B5',1);if(JSON.stringify(R.getRange('D21:F100').values)===JSON.stringify(before))throw Error('Competitor policy failed');tests.push('Saved competitor buffer changes actions');put(R,'B5',0);
const cas=I.getRange('B3').values[0][0];put(I,'B3',3);if(JSON.stringify(R.getRange('D21:F100').values)!==JSON.stringify(before))throw Error('Displayed case changed recommendations');put(I,'B3',cas);tests.push('Actual saved case selector independent of named Base/Downside rules');
put(C,'D3','STALE');if(R.getRange('D21').values[0][0]!==''||S.getRange('B10').values[0][0]!=='')throw Error('Stale comparisons failed to suppress');put(C,'D3','CURRENT');tests.push('Saved stale evidence suppresses authority');
put(I,'I9',0);if(R.getRange('D21').values[0][0]!=='')throw Error('Zero manual override should suppress');put(I,'I9',null);tests.push('Manual behavioural zero suppresses evidence-derived authority');
put(R,'B4',null);if(R.getRange('D21').values[0][0]!=='')throw Error('Blank policy accepted');put(R,'B4',0);if(R.getRange('E4').values[0][0]!=='VALID POLICY')throw Error('Valid zero member tolerance rejected');put(R,'B4',.05);tests.push('Blank versus valid zero policy distinguished');
const old=R.getRange('F131').formulas[0][0];put(R,'F131',null);if(R.getRange('Q21').values[0][0]!=='R1_MISSING')throw Error('Missing candidate did not investigate');R.getRange('F131').formulas=[[old]];tests.push('Missing conditional interval leads to investigation');
wb.recalculate();verify();const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:10},maxChars:1000});
await fs.writeFile(path.join(pre,'saved_recalculation.json'),JSON.stringify({savedWorkbookRecalculated:true,formula_graph_sha256:formulaGraphHash,engine:'Artifact Tool recalculation of actual saved Phase 7 formulas with unchanged saved source caches; native Excel not automated',independent_cells_checked:checked,max_difference:maxDiff,tests,error_scan:errors.ndjson,selected_case_restored:I.getRange('B3').values[0][0]===cas,policy_restored:R.getRange('B4:B6').values},null,2));
console.log('Saved formula recalculation, independent parity and edit tests passed.',JSON.stringify({checked,maxDiff,tests,error_scan:errors.ndjson}));
