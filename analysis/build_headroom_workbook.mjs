import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile,FileBlob} from '@oai/artifact-tool';
const dir=path.dirname(fileURLToPath(import.meta.url)),root=path.dirname(dir),pre=path.join(dir,'.workbook_previews','phase4');
const p=JSON.parse(await fs.readFile(path.join(pre,'payload.json'),'utf8'));
const col=i=>{let s='';for(let n=i+1;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const hc=p.gym_headroom.columns,sc=p.headroom_sensitivity.columns,ind=p.config.indicators,variants=Object.keys(p.config.weights);
const flags=['high_churn_exception','weak_conversion_exception','declining_acquisition_exception','peak_capacity_exception'];
const H=(f,r)=>`${col(hc.indexOf(f))}${r}`,HR=f=>`$${col(hc.indexOf(f))}$9:$${col(hc.indexOf(f))}$88`;
const S=(f,r)=>`${col(sc.indexOf(f))}${r}`,SR=(f,start,end)=>`$${col(sc.indexOf(f))}$${start}:$${col(sc.indexOf(f))}$${end}`;
const srcNames={gym_baseline:'Baseline',gym_master:'Gym Master',competitor_prices:'Competitors',monthly_performance:'Monthly Performance'};
const srcRange=(table,f)=>{const i=p[table].columns.indexOf(f);if(i<0)throw Error(f);return `'${srcNames[table]}'!$${col(i)}$2:$${col(i)}$${p[table].data.length+1}`;};
const linked=(table,f,row,start=2)=>`'${srcNames[table]}'!${col(p[table].columns.indexOf(f))}${row+start}`;
const B=(f,row)=>linked('gym_baseline',f,row,9);
const control=(c,r)=>`'Headroom Summary'!$${col(c)}$${r}`;
const eps=p.config.comparison_tolerance;
const normal=(value,range,reverse=false)=>`IF(NOT(ISNUMBER(${value})),"",IF(COUNT(${range})<=1,50,${reverse?'100-':''}100*(COUNTIFS(${range},"<"&(${value}-${eps}))+(COUNTIFS(${range},">="&(${value}-${eps}),${range},"<="&(${value}+${eps}))-1)/2)/(COUNT(${range})-1)))`;
const band=(score,shift='0')=>`IF(NOT(ISNUMBER(${score})),"",IF(${score}>=${control(1,17)}+(${shift}),"High",IF(${score}>=${control(1,18)}+(${shift}),"Medium","Low")))`;
const rank=(score,scores,id,ids)=>`IF(NOT(ISNUMBER(${score})),"",COUNTIFS(${scores},">"&(${score}+${eps}))+COUNTIFS(${scores},">="&(${score}-${eps}),${scores},"<="&(${score}+${eps}),${ids},"<"&${id})+1)`;
const seg=(band,gap,caution)=>`IF(${caution}>0,"Investigation priority",IF(OR(${band}="",NOT(ISNUMBER(${gap}))),"Unavailable",IF(AND(${band}="High",${gap}>0),"Stronger headroom indicators",IF(OR(${band}="Low",${gap}<=0),"Limited headroom indicators","Mixed indicators"))))`;
function verify(wb,stage){
 let cells=0,maxDifference=0;
 const sheet=wb.worksheets.getItem('Headroom Score');
 for(const [key,start] of [['gym_headroom',9],['headroom_sensitivity',111]]){
  const expected=p[key],actual=sheet.getRange(`A${start}:${col(expected.columns.length-1)}${start+expected.data.length-1}`).values;
  for(let r=0;r<actual.length;r++)for(let c=0;c<expected.columns.length;c++){
   const e=expected.data[r][c],v=actual[r][c];
   if(typeof e==='number'){const d=Math.abs(v-e);maxDifference=Math.max(maxDifference,d);if(typeof v!=='number'||d>Math.max(2e-8,Math.abs(e)*2e-12))throw Error(`${stage} ${key} ${col(c)}${start+r} ${expected.columns[c]}: ${v} vs ${e}`);}
   else if(e===null){if(v!==null&&v!=='')throw Error(`Nonblank ${key} ${r} ${c}`);}
   else if(v!==e)throw Error(`${stage} ${key} ${col(c)}${start+r} ${expected.columns[c]}: ${v} vs ${e}`);
   cells++;
  }
 }
 const summary=wb.worksheets.getItem('Headroom Summary');
 for(const [cell,e] of Object.entries({B23:80,B24:p.result.sensitive_sites,B25:p.result.threshold_sensitive_sites,B26:p.result.high_score_with_cautions})){if(summary.getRange(cell).values[0][0]!==e)throw Error('Summary '+cell);}
 return {cellsCompared:cells,maxAbsoluteDifference:maxDifference};
}
const renderViews=[['Headroom Score','A1:I14','score_primary'],['Headroom Score','Q8:Z14','score_context'],['Headroom Score','AM8:AU14','score_components'],['Headroom Score','A109:H117','sensitivity_detail'],['Headroom Score','A608:E617','benchmark_detail'],['Headroom Summary','A1:G27','summary_controls'],['Headroom Summary','A29:G57','summary_counts'],['Headroom Summary','A59:H72','summary_leaders'],['Headroom Summary','J7:R24','chart_contributions'],['Headroom Summary','J27:R45','chart_gap'],['Headroom Summary','J48:R68','chart_stability']];
async function renders(wb,views=renderViews){for(const [sheetName,range,file]of views){const blob=await wb.render({sheetName,range,scale:1.2,format:'png'});await fs.writeFile(path.join(pre,file+'.png'),new Uint8Array(await blob.arrayBuffer()));}}
if(process.argv.includes('--style-repairs')){
 const wb=Workbook.create(),s=wb.worksheets.add('Headroom Score'),summary=wb.worksheets.add('Headroom Summary');
 s.getRange(`A8:${col(hc.length-1)}8`).values=[hc.map(label=>label.replaceAll('_',' '))];s.getRange(`A9:${col(hc.length-1)}88`).values=p.gym_headroom.data;
 s.getRange(`A8:${col(hc.length-1)}88`).format={font:{name:'Arial',size:10,color:'#243B53'},verticalAlignment:'center',columnWidth:22,rowHeight:25};
 s.getRange(`A8:${col(hc.length-1)}8`).format={font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},fill:'#243B53',wrapText:true,rowHeight:64};
 const selections={'Headroom Score':[],'Headroom Summary':[]};
 for(const [field,format]of [['competitor_mean_first_month_discount_dec2025','"£"0.00;("£"0.00);"-"'],['complaints_per_1000_member_months_2025','0.00'],['competitor_gap_input','"£"0.00;("£"0.00);"-"']]){
  const c=col(hc.indexOf(field));s.getRange(`${c}9:${c}88`).setNumberFormat(format);for(let r=9;r<=88;r++)selections['Headroom Score'].push(c+r);
 }
 s.getRange('E9:E88').format.horizontalAlignment='center';for(let r=9;r<=88;r++)selections['Headroom Score'].push('E'+r);
 summary.getRange('D60:D69').values=p.result.top10.map(r=>[r.band]);summary.getRange('D60:D69').format={font:{name:'Arial',size:10,color:'#243B53'},horizontalAlignment:'center',verticalAlignment:'center'};for(let r=60;r<=69;r++)selections['Headroom Summary'].push('D'+r);
 summary.getRange('A180:G260').format={font:{name:'Arial',size:10,color:'#243B53'},columnWidth:22,rowHeight:23};
 summary.getRange('A180:G180').values=[['Gym in base-rank order',...variants.map(v=>v.replaceAll('_',' '))]];
 const idIndex=hc.indexOf('gym_id'),rankIndex=hc.indexOf('rank'),sid=sc.indexOf('gym_id'),sv=sc.indexOf('variant'),sr=sc.indexOf('rank');
 summary.getRange('A181:G260').values=p.gym_headroom.data.slice().sort((a,b)=>a[rankIndex]-b[rankIndex]).map(row=>[row[idIndex],...variants.map(v=>p.headroom_sensitivity.data.find(x=>x[sid]===row[idIndex]&&x[sv]===v)[sr])]);
 summary.getRange('B181:G260').conditionalFormats.add('colorScale',{colors:['#EDF2F7','#D9E2EC','#BCCCDC'],thresholds:['min',{type:'percentile',value:50},'max']});
 wb.recalculate();await fs.writeFile(path.join(pre,'repair_cells.json'),JSON.stringify(selections));const out=await SpreadsheetFile.exportXlsx(wb);await out.save(path.join(pre,'style_repairs.xlsx'));
 await renders(wb,[['Headroom Score','AN8:AP14','discount_format_repair'],['Headroom Score','W8:W14','complaints_format_repair'],['Headroom Summary','D60:D69','band_alignment_repair'],['Headroom Summary','A180:G190','matrix_first'],['Headroom Summary','A250:G260','matrix_last']]);console.log('Targeted display repairs authored.');process.exit(0);
}
if(process.argv.includes('--verify-final')){
 const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(root,'excel','gym_pricing_model.xlsx')));
 wb.recalculate();const info=verify(wb,'saved workbook');console.log('Saved workbook parity',JSON.stringify(info));
 const summary=wb.worksheets.getItem('Headroom Summary'),scores=wb.worksheets.getItem('Headroom Score');
 const weight=summary.getRange('B8'),old=weight.values[0][0],original=scores.getRange(H('score',9)).values[0][0];
 weight.values=[[old+.01]];const changed=scores.getRange(H('score',9)).values[0][0];
 // Invalid weight totals must be unavailable rather than silently renormalized.
 if(changed!==''&&changed!==null)throw Error('Invalid weight total accepted');weight.values=[[old]];
 const high=summary.getRange('B17'),oldHigh=high.values[0][0];high.values=[[101]];
 if(summary.getRange('B30').values[0][0]!==0)throw Error('Threshold change did not update High count');high.values=[[oldHigh]];
 // Changing one valid component weight and offsetting another changes the model and ranking lists.
 const oldChurn=summary.getRange('B9').values[0][0];weight.values=[[old+.05]];summary.getRange('B9').values=[[oldChurn-.05]];
 const changedValid=scores.getRange(H('score',9)).values[0][0];if(Math.abs(changedValid-original)<1e-8)throw Error('Weight input did not affect score');
 const leader=summary.getRange('A60').values[0][0];if(!leader)throw Error('Ranking list lost leader');
 weight.values=[[old]];summary.getRange('B9').values=[[oldChurn]];
 const defaults=summary.getRange('B8:B13').values;
 summary.getRange('B8:B13').values=[[1],[0],[0],[0],[0],[0]];
 const gapIndex=hc.indexOf('competitor_gap_input'),gymIndex=hc.indexOf('gym_id');
 const gapLeader=p.gym_headroom.data.slice().sort((a,b)=>b[gapIndex]-a[gapIndex]||a[gymIndex].localeCompare(b[gymIndex]))[0][gymIndex];
 if(summary.getRange('A60').values[0][0]!==gapLeader||summary.getRange('A83').values[0][0]!==gapLeader)throw Error('Ranking list or chart schedule did not react to weights');
 summary.getRange('B8:B13').values=defaults;
 const gapCell=wb.worksheets.getItem('Baseline').getRange(col(p.gym_baseline.columns.indexOf('competitor_gap_dec2025'))+'9');
 const oldGap=gapCell.values[0][0];gapCell.values=[['']];if(scores.getRange(H('score',9)).values[0][0]!=='')throw Error('Missing score input was imputed');gapCell.values=[[oldGap]];
 const guideUpdates={'Dataset Overview':{D5:'Phase 4',E5:'Pricing headroom assessment',E7:'Historical price response'},README:{B20:'Phase 4 completed: headroom scores, caution flags and sensitivity. Next: Phase 5 historical price response.'},'Headroom Score':{A5:'Sensitivity starts at row 110; Q4 benchmarks at row 609. Boolean flags: 1 = yes, 0 = no.'}};
 for(const [name,updates]of Object.entries(guideUpdates))for(const [address,value]of Object.entries(updates))wb.worksheets.getItem(name).getRange(address).values=[[value]];
 wb.recalculate();verify(wb,'restored');
 const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1500});
 console.log(errors.ndjson);info.formulaErrorScan=errors.ndjson;
 const checks=wb.worksheets.getItem('Checks');if(Math.abs(checks.getRange('C5').values[0][0])>.01||checks.getRange('C8:H1927').values.some(row=>row.some(v=>Math.abs(v)>1e-8)))throw Error('Existing checks failed');
 const cache={};for(const [name,range]of [['Headroom Score',`A1:${col(hc.length-1)}850`],['Headroom Summary','A1:R264']])cache[name]={values:wb.worksheets.getItem(name).getRange(range).values.map(row=>row.map(v=>v instanceof Date?(v.getTime()-Date.UTC(1899,11,30))/86400000:v))};
 await fs.writeFile(path.join(pre,'final_values.json'),JSON.stringify(cache));await fs.writeFile(path.join(pre,'guide_updates.json'),JSON.stringify(guideUpdates));
 await renders(wb,[['Dataset Overview','A1:F24','overview_updated'],['README','A18:B22','readme_updated']]);
 info.savedWorkbookRecalculated=true;info.originalReconciliationsPassed=true;info.inputChangeTests=['Invalid weight total blocked scores','Editable threshold changed count','Valid weight transfer changed score','Ranking list and chart schedule reacted to competitor-only weights','Missing required input produced unavailable score'];info.nativeExcelApplication='Not automated; recalculation uses Artifact Tool and saved OOXML verification';
 await fs.writeFile(path.join(dir,'headroom_workbook_verification.json'),JSON.stringify(info,null,2));console.log(JSON.stringify(info));process.exit(0);
}

if(process.argv.includes('--resume')){
 const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(pre,'headroom_parts.xlsx'))),sheet=wb.worksheets.getItem('Headroom Score');
 for(const key of ind){sheet.getRange(`${col(hc.indexOf(key+'_component'))}9:${col(hc.indexOf(key+'_component'))}88`).formulas=Array.from({length:80},(_,i)=>['='+normal(H(key+'_input',9+i),HR(key+'_input'),key==='churn')]);}
 sheet.getRange(`${col(hc.indexOf('rank'))}9:${col(hc.indexOf('rank'))}88`).formulas=Array.from({length:80},(_,i)=>['='+rank(H('score',9+i),HR('score'),H('gym_id',9+i),HR('gym_id'))]);
 for(let j=0;j<6;j++){
  const start=111+j*80,end=start+79;
  for(const key of ind){sheet.getRange(`${col(sc.indexOf(key+'_component'))}${start}:${col(sc.indexOf(key+'_component'))}${end}`).formulas=Array.from({length:80},(_,i)=>['='+normal(S(key+'_input',start+i),SR(key+'_input',start,end),key==='churn')]);}
  sheet.getRange(`${col(sc.indexOf('rank'))}${start}:${col(sc.indexOf('rank'))}${end}`).formulas=Array.from({length:80},(_,i)=>['='+rank(S('score',start+i),SR('score',start,end),S('gym_id',start+i),SR('gym_id',start,end))]);
 }
 wb.recalculate();console.log('Resumed parity',JSON.stringify(verify(wb,'resumed')));await renders(wb);const output=await SpreadsheetFile.exportXlsx(wb);await output.save(path.join(pre,'headroom_parts.xlsx'));console.log('Resumed headroom sheets exported.');process.exit(0);
}
const wb=Workbook.create();for(const name of [...Object.values(srcNames),'Headroom Score','Headroom Summary'])wb.worksheets.add(name);
for(const [table,name]of Object.entries(srcNames)){
 const s=wb.worksheets.getItem(name),start=table==='gym_baseline'?8:1,data=p[table];
 s.getRange(`A${start}:${col(data.columns.length-1)}${start}`).values=[data.columns];
 s.getRange(`A${start+1}:${col(data.columns.length-1)}${start+data.data.length}`).values=data.data.map(row=>row.map((v,i)=>['month','opening_date','snapshot_date'].includes(data.columns[i])&&v?new Date(v+'T00:00:00Z'):v));
}
const score=wb.worksheets.getItem('Headroom Score'),summary=wb.worksheets.getItem('Headroom Summary');
const base=(s,area)=>{s.showGridLines=false;s.getRange(area).format.font={name:'Arial',size:10,color:'#243B53'};s.getRange(area).format.verticalAlignment='center';s.getRange(area).format.rowHeight=23;s.getRange(area).format.columnWidth=22;};
const head=(s,area,height=62)=>{s.getRange(area).format={fill:'#243B53',font:{name:'Arial',size:10,color:'#FFFFFF',bold:true},wrapText:true,rowHeight:height,horizontalAlignment:'center',verticalAlignment:'center'};};
const title=(s,text)=>{s.getRange('A2').values=[[text]];s.getRange('A2').format.font={name:'Arial',size:14,bold:true};};
const label=f=>f.replaceAll('_',' ').replaceAll('q4','Q4').replaceAll('dec2025','Dec 2025').replaceAll('pp','pp');
base(score,`A1:${col(hc.length-1)}850`);base(summary,'A1:R264');score.getRange('A:A').format.columnWidth=14;score.getRange('B:B').format.columnWidth=18;score.getRange('F:F').format.columnWidth=36;
title(score,'Pricing headroom: scores, context and sensitivity');title(summary,'Northstar Fitness: pricing headroom summary');
score.getRange('A4:I4').merge();score.getRange('A4').values=[['2025 behaviour and December competitor prices. Score is relative opportunity; caution flags remain separate.']];
score.getRange('A5:I5').merge();score.getRange('A5').values=[['Sensitivity starts at row 110; Q4 benchmarks at row 609. Boolean flags: 1 = yes, 0 = no.']];
summary.getRange('A4:G4').merge();summary.getRange('A4').values=[['Historical price sensitivity remains pending Phase 5. No pricing action or revenue uplift is estimated.']];summary.getRange('A4:G4').format.wrapText=true;summary.getRange('A4:G4').format.rowHeight=32;
summary.getRange('A7:G7').values=[['Indicator',...variants.map(label)]];head(summary,'A7:G7',45);
for(let i=0;i<6;i++){summary.getRange(`A${8+i}:G${8+i}`).values=[[label(ind[i]),...variants.map(v=>p.config.weights[v][i])]];}
summary.getRange('B8:G13').setNumberFormat('0%');summary.getRange('B8:G13').format.font.color='#0000FF';summary.getRange('B8:G13').dataValidation={rule:{type:'decimal',operator:'between',formula1:0,formula2:1}};
summary.getRange('A14').values=[['Weight total']];summary.getRange('B14:G14').formulas=[variants.map((v,i)=>`=SUM(${col(i+1)}8:${col(i+1)}13)`)];summary.getRange('B14:G14').setNumberFormat('0%');
summary.getRange('A17:B21').values=[['High starts at',65],['Medium starts at',40],['Rank sensitivity threshold',10],['Threshold sensitivity shift',5],['Competitor snapshot',new Date('2025-12-01T00:00:00Z')]];
summary.getRange('B17:B20').format.font.color='#0000FF';summary.getRange('B21').setNumberFormat('mmm-yy');
summary.getRange('A23:A26').values=[['Gyms assessed'],['Sensitive to alternatives'],['Sensitive to thresholds'],['High band with caution flags']];
summary.getRange('B23:B26').formulas=[[`=COUNTA('Headroom Score'!${HR('gym_id')})`],[`=SUMPRODUCT('Headroom Score'!${HR('sensitive')}*1)`],[`=SUMPRODUCT('Headroom Score'!${HR('threshold_sensitive')}*1)`],[`=SUMPRODUCT(('Headroom Score'!${HR('band')}="High")*('Headroom Score'!${HR('caution_flag_count')}>0))`]];
score.getRange(`A8:${col(hc.length-1)}8`).values=[hc.map(label)];head(score,`A8:${col(hc.length-1)}8`);score.getRange(`A9:${col(hc.length-1)}88`).values=p.gym_headroom.data;
const compDate=srcRange('competitor_prices','month'),compID=srcRange('competitor_prices','gym_id'),compPrice=srcRange('competitor_prices','competitor_standard_price'),compType=srcRange('competitor_prices','competitor_type');
const benchmarkCount=id=>`COUNTIFS(${compID},${id},${compDate},${control(1,21)})`;
const mean=(f,id)=>`IF(${benchmarkCount(id)}=0,"",SUMIFS(${srcRange('competitor_prices',f)},${compID},${id},${compDate},${control(1,21)})/${benchmarkCount(id)})`;
const benchmarkRows=p.q4_benchmarks.slice().sort((a,b)=>a.gym_id.localeCompare(b.gym_id)||a.month.localeCompare(b.month));
score.getRange('A609:E609').values=[['Gym ID','Month','Competitor average gross GBP','Standard gross GBP','Competitor gap gross GBP']];head(score,'A609:E609',52);
for(let i=0;i<240;i++){
 const r=610+i,v=benchmarkRows[i];score.getRange(`A${r}:B${r}`).values=[[v.gym_id,new Date(v.month+'T00:00:00Z')]];
 const count=`COUNTIFS(${compID},A${r},${compDate},B${r})`,price=`SUMIFS(${srcRange('monthly_performance','standard_price')},${srcRange('monthly_performance','gym_id')},A${r},${srcRange('monthly_performance','month')},B${r})`;
 score.getRange(`C${r}:E${r}`).formulas=[[`=IF(${count}=0,"",SUMIFS(${compPrice},${compID},A${r},${compDate},B${r})/${count})`,`=${price}`,`=IF(ISNUMBER(C${r}),C${r}-D${r},"")`]];
}
score.getRange('B610:B849').setNumberFormat('mmm-yy');score.getRange('C610:E849').setNumberFormat('"£"0.00;("£"0.00);"-"');
const hform=[];
for(let i=0;i<80;i++){
 const r=i+9,id=H('gym_id',r);const f={};
 for(const field of hc){if(p.gym_baseline.columns.includes(field))f[field]=`=IF(ISBLANK(${B(field,i)}),"",${B(field,i)})`;else if(p.gym_master.columns.includes(field)){const ref=linked('gym_master',field,i);f[field]=`=IF(ISBLANK(${ref}),"",${ref})`;}}
 f.competitor_count_dec2025=`=${benchmarkCount(id)}`;
 for(const [field,src]of [['competitor_mean_joining_fee_dec2025','joining_fee'],['competitor_promotion_share_dec2025','promotion_active'],['competitor_mean_first_month_discount_dec2025','promotion_value']]){
  f[field]=src==='promotion_active'?`=IF(${benchmarkCount(id)}=0,"",SUMPRODUCT((${compID}=${id})*(${compDate}=${control(1,21)})*${srcRange('competitor_prices',src)})/${benchmarkCount(id)})`:`=${mean(src,id)}`;
 }
 f.q4_average_competitor_gap=`=IF(COUNTIFS($A$610:$A$849,${id})<>3,"",AVERAGEIFS($E$610:$E$849,$A$610:$A$849,${id}))`;
 const vc=p.config.value_types.map(t=>`COUNTIFS(${compID},${id},${compDate},${control(1,21)},${compType},"${t}")`).join('+'),vs=p.config.value_types.map(t=>`SUMIFS(${compPrice},${compID},${id},${compDate},${control(1,21)},${compType},"${t}")`).join('+');
 f.value_competitor_gap_dec2025=`=IF((${vc})=0,"",(${vs})/(${vc})-${H('standard_price_dec2025',r)})`;
 f.caution_flag_count=`=${flags.map(x=>H(x,r)+'*1').join('+')}`;
 const inputs=['competitor_gap_dec2025','churn_rate_2025','conversion_rate_2025','acquisition_growth_yoy','average_monthly_peak_2025','median_income'];
 for(let j=0;j<6;j++){
  const key=ind[j],ref=H(inputs[j],r);f[key+'_input']=`=IF(ISNUMBER(${ref}),${j===4?'MIN(1,'+ref+')':ref},"")`;
  f[key+'_component']='='+normal(H(key+'_input',r),HR(key+'_input'),j===1);
  f[key+'_contribution']=`=IF(${control(1,8+j)}=0,0,IF(ISNUMBER(${H(key+'_component',r)}),${H(key+'_component',r)}*${control(1,8+j)},""))`;
 }
 const valid=ind.map((x,j)=>`IF(${control(1,j+8)}>0,ISNUMBER(${H(x+'_input',r)}),TRUE)`).join(',');
 f.score=`=IF(AND(ABS(SUM('Headroom Summary'!$B$8:$B$13)-1)<0.000000001,MIN('Headroom Summary'!$B$8:$B$13)>=0,${valid}),${ind.map(x=>H(x+'_contribution',r)).join('+')},"")`;
 f.rank='='+rank(H('score',r),HR('score'),id,HR('gym_id'));f.band='='+band(H('score',r));f.segment='='+seg(H('band',r),H('competitor_gap_dec2025',r),H('caution_flag_count',r));
 const alternatives=[1,2,3,4,5].map(j=>111+j*80+i),movements=alternatives.map(x=>`ABS(${S('rank_movement',x)})`);
 f.max_absolute_rank_movement=`=MAX(${movements.join(',')})`;
 f.alternative_band_change_count=`=${alternatives.map(x=>S('band_changed',x)+'*1').join('+')}`;
 f.sensitive=`=OR(${H('max_absolute_rank_movement',r)}>=${control(1,19)},${H('alternative_band_change_count',r)}>0)`;
 f.band_lower_thresholds='='+band(H('score',r),'-'+control(1,20));f.band_higher_thresholds='='+band(H('score',r),control(1,20));f.threshold_sensitive=`=OR(${H('band',r)}<>${H('band_lower_thresholds',r)},${H('band',r)}<>${H('band_higher_thresholds',r)})`;
 const labels=['High opening-base churn','Weak qualified-prospect conversion','Declining acquisition','Peak service pressure'];
 f.explanation=`=IF(${H('competitor_gap_dec2025',r)}>0,"Positive competitor gap. ","No positive competitor gap. ")&IF(${H('caution_flag_count',r)}=0,"No baseline caution flags. ",${flags.map((x,j)=>`IF(${H(x,r)},"${labels[j]}. ","")`).join('&')})&"Historical sensitivity pending Phase 5."`;
 hform.push(hc.map(x=>f[x]||(()=>{throw Error('No formula '+x);})()));
}
score.getRange(`A9:${col(hc.length-1)}88`).formulas=hform;
score.getRange('A109:H109').merge();score.getRange('A109').values=[['Six sensitivity specifications. Positive rank movement means a lower relative position.']];
score.getRange(`A110:${col(sc.length-1)}110`).values=[sc.map(label)];head(score,`A110:${col(sc.length-1)}110`);
const sform=[];
for(let j=0;j<6;j++)for(let i=0;i<80;i++){
 const r=111+j*80+i,br=i+9,start=111+j*80,end=start+79,v=variants[j],f={gym_id:`=${H('gym_id',br)}`,variant:`="${v}"`};
 for(let k=0;k<6;k++){
  const key=ind[k];let ref=H(key+'_input',br);
  if(j===4){ref=[H('q4_average_competitor_gap',br),B('churn_rate_q4_2025',i),B('conversion_rate_q4_2025',i),B('acquisition_growth_q4_yoy',i),`MIN(1,${B('average_monthly_peak_q4_2025',i)})`,H('income_input',br)][k];}
  if(j===5&&k===0)ref=H('value_competitor_gap_dec2025',br);
  f[key+'_input']=`=IF(ISNUMBER(${ref}),${ref},"")`;
  f[key+'_component']='='+normal(S(key+'_input',r),SR(key+'_input',start,end),k===1);
  f[key+'_contribution']=`=IF(${control(j+1,8+k)}=0,0,IF(ISNUMBER(${S(key+'_component',r)}),${S(key+'_component',r)}*${control(j+1,8+k)},""))`;
 }
 const valid=ind.map((x,k)=>`IF(${control(j+1,k+8)}>0,ISNUMBER(${S(x+'_input',r)}),TRUE)`).join(',');
 f.score=`=IF(AND(ABS(SUM('Headroom Summary'!$${col(j+1)}$8:$${col(j+1)}$13)-1)<0.000000001,MIN('Headroom Summary'!$${col(j+1)}$8:$${col(j+1)}$13)>=0,${valid}),${ind.map(x=>S(x+'_contribution',r)).join('+')},"")`;
 f.rank='='+rank(S('score',r),SR('score',start,end),S('gym_id',r),SR('gym_id',start,end));f.band='='+band(S('score',r));f.segment='='+seg(S('band',r),S('competitor_gap_input',r),H('caution_flag_count',br));
 f.base_score=`=${H('score',br)}`;f.base_rank=`=${H('rank',br)}`;f.rank_movement=`=IF(AND(ISNUMBER(${S('rank',r)}),ISNUMBER(${S('base_rank',r)})),${S('rank',r)}-${S('base_rank',r)},"")`;
 f.band_changed=`=${S('band',r)}<>${H('band',br)}`;f.sensitive=`=OR(ABS(${S('rank_movement',r)})>=${control(1,19)},${S('band_changed',r)})`;
 sform.push(sc.map(x=>f[x]||(()=>{throw Error('No sensitivity formula '+x);})()));
}
score.getRange(`A111:${col(sc.length-1)}590`).formulas=sform;
score.tables.add(`A8:${col(hc.length-1)}88`,true,'GymHeadroomScores');score.tables.add(`A110:${col(sc.length-1)}590`,true,'HeadroomSensitivity');score.freezePanes.freezeRows(8);score.freezePanes.freezeColumns(2);
for(const [columns,start,end]of [[hc,9,88],[sc,111,590]])for(let i=0;i<columns.length;i++){
 const field=columns[i],range=score.getRange(`${col(i)}${start}:${col(i)}${end}`);let fmt='General';
 if(/score|component|contribution/.test(field))fmt='0.00';
 else if(/rank|(^|_)count($|_)|events/.test(field))fmt='0';
 else if(/change_pp/.test(field))fmt='0.00" pp";(0.00)" pp"';
 else if(/rate|growth|mix|frequency|utilisation|monthly_peak|population_pct|share/.test(field))fmt='0.00%;(0.00%)';
 else if(/price|gap|fee|discount|spend|income/.test(field))fmt='"£"#,##0.00;("£"#,##0.00);"-"';
 if(field==='complaints_per_1000_member_months_2025')fmt='0.00';
 if(field.endsWith('_input'))fmt=field==='income_input'?'"£"#,##0':field==='competitor_gap_input'?'"£"0.00;("£"0.00);"-"': '0.00%';
 range.setNumberFormat(fmt);
}
score.getRange(`${col(hc.indexOf('explanation'))}8:${col(hc.indexOf('explanation'))}88`).format.columnWidth=85;score.getRange(`${col(hc.indexOf('explanation'))}9:${col(hc.indexOf('explanation'))}88`).format.wrapText=true;score.getRange('A9:'+col(hc.length-1)+'88').format.rowHeight=48;
score.getRange('E9:E88').format.horizontalAlignment='center';
summary.getRange('A29:B29').values=[['Score band','Gym count']];head(summary,'A29:B29',32);
for(let i=0;i<3;i++){const r=30+i;summary.getRange('A'+r).values=[[['High','Medium','Low'][i]]];summary.getRange('B'+r).formulas=[[`=COUNTIFS('Headroom Score'!${HR('band')},A${r})`]];}
summary.getRange('A35:B35').values=[['Commercial segment','Gym count']];head(summary,'A35:B35',32);
const segments=['Investigation priority','Stronger headroom indicators','Limited headroom indicators','Mixed indicators'];
for(let i=0;i<4;i++){const r=36+i;summary.getRange('A'+r).values=[[segments[i]]];summary.getRange('B'+r).formulas=[[`=COUNTIFS('Headroom Score'!${HR('segment')},A${r})`]];}
summary.getRange('A43:D43').values=[['Variant','Band changes','Maximum rank movement','Sensitive gyms']];head(summary,'A43:D43',45);
for(let j=0;j<6;j++){const r=44+j,start=111+j*80,end=start+79;summary.getRange('A'+r).values=[[label(variants[j])]];summary.getRange(`B${r}:D${r}`).formulas=[[`=SUMPRODUCT('Headroom Score'!${SR('band_changed',start,end)}*1)`,`=MAX(MAX('Headroom Score'!${SR('rank_movement',start,end)}),-MIN('Headroom Score'!${SR('rank_movement',start,end)}))`,`=SUMPRODUCT('Headroom Score'!${SR('sensitive',start,end)}*1)`]];}
summary.getRange('A52:G54').merge();summary.getRange('A52').values=[['Percentile scores are relative to this estate. Competitor prices include VAT; joining fees and first-month discounts remain separate. Peak utilisation at or above comfortable capacity is a service caution.']];summary.getRange('A52:G54').format.wrapText=true;
summary.getRange('A56:G57').merge();summary.getRange('A56').values=[['Weights and band thresholds are business assumptions. Sensitivity shows specification dependence, not statistical confidence. The four baseline flags determine investigation precedence without reducing the score.']];summary.getRange('A56:G57').format.wrapText=true;
summary.getRange('A59:H59').values=[['Gym ID','City','Score','Band','Segment','Largest rank change','Competitor gap','Caution count']];head(summary,'A59:H59',56);
for(let i=0;i<10;i++){const r=60+i;for(let j=0;j<8;j++){const field=['gym_id','city','score','band','segment','max_absolute_rank_movement','competitor_gap_dec2025','caution_flag_count'][j];summary.getRange(col(j)+r).formulas=[[`=INDEX('Headroom Score'!${HR(field)},MATCH(${i+1},'Headroom Score'!${HR('rank')},0))`]];}}
summary.getRange('C60:C69').setNumberFormat('0.00');summary.getRange('G60:G69').setNumberFormat('"£"0.00;("£"0.00)');summary.getRange('A60:H69').format.wrapText=true;summary.getRange('A60:H69').format.rowHeight=42;
summary.getRange('D60:D69').format.horizontalAlignment='center';
summary.getRange('A73:H74').merge();summary.getRange('A73').values=[['This project uses synthetic data and is inspired by the commercial economics of UK subscription fitness businesses.']];summary.getRange('A73:H74').format.wrapText=true;
summary.getRange('A76:H78').merge();summary.getRange('A76').values=[['This project uses synthetic data created for portfolio purposes. It is inspired by the economics of multi-site subscription fitness businesses and does not use confidential information from The Gym Group or any other operator.']];summary.getRange('A76:H78').format.wrapText=true;
// Chart schedules are live links to the owning scoring calculations.
summary.getRange('A82:G82').values=[['Leading site',...ind.map(label)]];head(summary,'A82:G82',40);
for(let i=0;i<10;i++){const r=83+i;summary.getRange('A'+r).formulas=[[`=A${60+i}`]];summary.getRange(`B${r}:G${r}`).formulas=[ind.map(x=>`=INDEX('Headroom Score'!${HR(x+'_contribution')},MATCH(A${r},'Headroom Score'!${HR('gym_id')},0))`)];}
summary.getRange('A96:E96').values=[['Gap gross GBP','No caution churn','Caution churn','Gym ID','Peak service pressure']];head(summary,'A96:E96',42);
for(let i=0;i<80;i++){const r=97+i,br=9+i;summary.getRange(`A${r}:E${r}`).formulas=[[`='Headroom Score'!${H('competitor_gap_dec2025',br)}`,`=IF('Headroom Score'!${H('caution_flag_count',br)}=0,'Headroom Score'!${H('churn_rate_2025',br)},"")`,`=IF('Headroom Score'!${H('caution_flag_count',br)}>0,'Headroom Score'!${H('churn_rate_2025',br)},"")`,`='Headroom Score'!${H('gym_id',br)}`,`='Headroom Score'!${H('peak_capacity_exception',br)}`]];}
summary.getRange('B97:C176').setNumberFormat('0.00%');summary.getRange('A97:A176').setNumberFormat('"£"0.00;("£"0.00)');
summary.getRange('A180:G180').values=[['Gym in base-rank order',...variants.map(label)]];head(summary,'A180:G180',42);
for(let i=0;i<80;i++){const r=181+i;summary.getRange('A'+r).formulas=[[`=INDEX('Headroom Score'!${HR('gym_id')},MATCH(${i+1},'Headroom Score'!${HR('rank')},0))`]];summary.getRange(`B${r}:G${r}`).formulas=[variants.map((v,j)=>`=INDEX('Headroom Score'!${SR('rank',111+j*80,190+j*80)},MATCH(A${r},'Headroom Score'!${SR('gym_id',111+j*80,190+j*80)},0))`)];}
summary.getRange('B181:G260').conditionalFormats.add('colorScale',{colors:['#EDF2F7','#D9E2EC','#BCCCDC'],thresholds:['min',{type:'percentile',value:50},'max']});
summary.getRange('A263:B264').values=[['Weight check (difference from 100%)',null],['Contribution check (maximum difference)',null]];summary.getRange('B263').formulas=[['=SUM(B8:B13)-1']];summary.getRange('B264').formulas=[[`=MAX(${Array.from({length:80},(_,i)=>`ABS('Headroom Score'!${H('score',9+i)}-(${ind.map(x=>`'Headroom Score'!${H(x+'_contribution',9+i)}`).join('+')}))`).join(',')})`]];summary.getRange('B263:B264').setNumberFormat('0.000000');
summary.getRange('A:A').format.columnWidth=34;summary.getRange('E:E').format.columnWidth=30;summary.getRange('A36:A39').format.wrapText=true;summary.getRange('A36:B39').format.rowHeight=34;
function styleChart(chart,title,from,to,fmt){chart.title=title;chart.titleTextStyle.typeface='Arial';chart.titleTextStyle.fontSize=12;chart.setPosition(from,to);chart.legend={position:'top',textStyle:{typeface:'Arial',fontSize:9}};chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:9}};chart.yAxis={numberFormatCode:fmt,numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};chart.series.items.forEach((s,i)=>{s.fill=['#243B53','#486581','#829AB1','#2F855A','#D69E2E','#9F7AEA'][i%6];s.line={fill:['#243B53','#486581','#829AB1','#2F855A','#D69E2E','#9F7AEA'][i%6],style:'solid',width:1.5};});}
const contribution=summary.charts.add('bar',summary.getRange('A82:G92'));styleChart(contribution,'Leading sites: weighted score points','J7','R24','0');
const scatter=summary.charts.add('scatter',[summary.getRange('A96:A176'),summary.getRange('B96:B176'),summary.getRange('C96:C176')]);styleChart(scatter,'Competitor gap and monthly churn','J27','R45','0.0%');scatter.xAxis={numberFormatCode:'"£"0.0',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};scatter.xAxis.title.text='December competitor gap (£ gross)';scatter.yAxis.title.text='2025 monthly churn';scatter.series.items[1].fill='#D97706';scatter.series.items[1].line={fill:'#D97706',width:0};
// Plot all 80 sites across every variant against base-rank order.
const stability=summary.charts.add('line',summary.getRange('A180:G260'));styleChart(stability,'Rank stability: all sites in base order','J48','R68','0');
wb.recalculate();const checkpoint=await SpreadsheetFile.exportXlsx(wb);await checkpoint.save(path.join(pre,'headroom_parts.xlsx'));console.log('Authoring checkpoint saved.');console.log('Authored parity',JSON.stringify(verify(wb,'authored')));
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1200})).ndjson);
await renders(wb);const output=await SpreadsheetFile.exportXlsx(wb);await output.save(path.join(pre,'headroom_parts.xlsx'));console.log('Headroom sheets exported for preserved-workbook assembly.');
