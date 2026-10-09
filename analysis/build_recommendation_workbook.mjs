import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile,FileBlob} from '@oai/artifact-tool';
const dir=path.dirname(fileURLToPath(import.meta.url)),pre=path.join(dir,'.workbook_previews','phase7');
const p=JSON.parse(await fs.readFile(path.join(pre,'payload.json'),'utf8'));
const refresh=process.argv.includes('--refresh')?JSON.parse(await fs.readFile(path.join(pre,'refresh_inputs.json'),'utf8')):null;
if(process.argv.includes('--style-only')){
 const book=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(pre,'recommendation_parts.xlsx'))),r=book.worksheets.getItem('Recommendations'),s=book.worksheets.getItem('Recommendation Summary');
 const layout=JSON.parse(await fs.readFile(path.join(pre,'layout.json'),'utf8'));
 r.getRange('B:B').format.columnWidth=32;r.getRange('H:H').format.columnWidth=40;r.getRange('O:O').format.columnWidth=35;
 r.getRange('H351:H430').format={wrapText:true,rowHeight:32};r.getRange('O1101:O1500').format.wrapText=true;r.getRange('U1101:U1500').setNumberFormat('0');
 r.getRange('C901:H1060').setNumberFormat('"£"#,##0;("£"#,##0);"-"');r.getRange('E351:E430').setNumberFormat('0.00');
 s.getRange('B:F').format.columnWidth=34;s.getRange('B351:F430').format={wrapText:true,rowHeight:35};
 s.getRange('A130').values=[['Annual net revenue (£)']];s.getRange('G130').values=[['Opening-member months']];s.getRange('H130').values=[['Average-member months']];
 const col=i=>{let x='';for(let n=i+1;n;n=Math.floor((n-1)/26))x=String.fromCharCode(65+(n-1)%26)+x;return x;};
 for(const[f,label]of [['monthly_revenue','Annual net revenue (£)'],['opening_members','Opening-member months'],['average_members','Average-member months']])r.getRange(col(layout.pc.indexOf(f))+'1600').values=[[label]];
 const guides=JSON.parse(await fs.readFile(path.join(pre,'guide_updates.json'),'utf8'));guides['Dataset Overview'].E5='80 site recommendations';guides['Dataset Overview'].E10='Conditional recommendations';
 for(const[name,changes]of Object.entries(guides))for(const[a,text]of Object.entries(changes))book.worksheets.getItem(name).getRange(a).values=[[text]];
 await fs.writeFile(path.join(pre,'guide_updates.json'),JSON.stringify(guides));book.recalculate();
 for(const[sheetName,range,file]of [['Recommendations','A350:K359','context'],['Recommendations','M1100:U1109','rules'],['Recommendations','A900:H909','sensitivity_inputs'],['Recommendation Summary','A350:F363','action_changes'],['Recommendation Summary','A130:L136','portfolio']]){const b=await book.render({sheetName,range,scale:1.2,format:'png'});await fs.writeFile(path.join(pre,file+'.png'),new Uint8Array(await b.arrayBuffer()));}
 await (await SpreadsheetFile.exportXlsx(book)).save(path.join(pre,'recommendation_parts.xlsx'));console.log('Targeted layout and guidance repairs authored; business formulas unchanged.');process.exit(0);
}
const wb=Workbook.create();
const names=['Recommendations','Recommendation Summary',...Object.keys(p.sources)];
for(const name of names)wb.worksheets.add(name);
const col=i=>{let s='';for(let n=i+1;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const objects=f=>f.data.map(r=>Object.fromEntries(f.columns.map((c,i)=>[c,r[i]])));
const recs=objects(p.recommendations),sens=objects(p.sensitivity),ports=objects(p.portfolio);
const get=s=>wb.worksheets.getItem(s),R=get('Recommendations'),S=get('Recommendation Summary');
const gbp='"£"#,##0;("£"#,##0);"-"',pct='0.00%;(0.00%);"-"',num='#,##0.0;(#,##0.0);"-"';
const cell=(s,a,v)=>s.getRange(a).values=[[v]],form=(s,a,f)=>s.getRange(a).formulas=[[f]];
const norm=x=>String(x).toLowerCase().replace(/[^a-z0-9]/g,'');
// Read-only dependency sheets contain actual saved values, not another model.
for(const [name,source]of Object.entries(p.sources)){
 let maxR=1,maxC=1;for(const a of Object.keys(source)){const m=a.match(/^([A-Z]+)(\d+)$/);let c=0;for(const ch of m[1])c=c*26+ch.charCodeAt(0)-64;maxR=Math.max(maxR,+m[2]);maxC=Math.max(maxC,c);}
 const matrix=Array.from({length:maxR},()=>Array(maxC).fill(null));for(const[a,v]of Object.entries(source)){const m=a.match(/^([A-Z]+)(\d+)$/);let c=0;for(const ch of m[1])c=c*26+ch.charCodeAt(0)-64;matrix[+m[2]-1][c-1]=v;}
 get(name).getRange(`A1:${col(maxC-1)}${maxR}`).values=matrix;
}
const cap=p.source_layout.captureColumns;
const cc=f=>col(cap.indexOf(f));
const head=p.headroom_columns;
const hcol=f=>col(head.indexOf(f));
const bh={};for(const[a,v]of Object.entries(p.sources.Baseline))if(a.match(/^[A-Z]+8$/))bh[norm(v)]=a.replace('8','');
const blocks={};for(let row=31;row<=990;row+=80){const a=p.sources['Scenario Comparison'];blocks[a['C'+row]+'|'+a['B'+row]]=row;}
function lookup(gid,inc,caseName,field,numeric=true){
 const start=blocks[caseName+'|'+inc];if(!start)throw Error('Block '+caseName+inc);
 const range=`'Scenario Comparison'!$${cc(field)}$${start}:$${cc(field)}$${start+79}`,ids=`'Scenario Comparison'!$A$${start}:$A$${start+79}`;
 const ix=`INDEX(${range},MATCH(${gid},${ids},0))`;
 return `IF(COUNTIFS(${ids},${gid})<>1,"",IF(${numeric?`COUNT(${ix})=1`:`COUNTA(${ix})=1`},${ix},""))`;
}
function context(field,gid){
 const c=bh[norm(field)];const sheet=c?'Baseline':'Headroom Score',column=c??hcol(field);
 if(!column||column==='')throw Error('Unknown context '+field);
 const ix=`INDEX('${sheet}'!$${column}$9:$${column}$88,MATCH(${gid},'${sheet}'!$A$9:$A$88,0))`;
 return `IF(COUNTIFS('${sheet}'!$A$9:$A$88,${gid})<>1,"",${field==='pilot_pair_id'?`IF(${ix}="","",${ix})`:ix})`;
}
function title(s,t){s.showGridLines=false;s.getRange('A2:H2').merge();cell(s,'A2',t);s.getRange('A2:H2').format={font:{name:'Arial',size:14,bold:true,color:'#243B53'},rowHeight:28};}
function table(s,start,columns,vals,forms,name){
 const end=start+vals.length-1;s.getRange(`A${start-1}:${col(columns.length-1)}${end}`).format={font:{name:'Arial',size:10,color:'#243B53'},rowHeight:24,verticalAlignment:'center',columnWidth:20};
 s.getRange(`A${start-1}:${col(columns.length-1)}${start-1}`).values=[columns.map(x=>x.replaceAll('_',' '))];s.getRange(`A${start-1}:${col(columns.length-1)}${start-1}`).format={fill:'#243B53',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:66};
 s.getRange(`A${start}:${col(columns.length-1)}${end}`).values=vals;
 if(forms)s.getRange(`A${start}:${col(columns.length-1)}${end}`).formulas=forms;
 s.tables.add(`A${start-1}:${col(columns.length-1)}${end}`,true,name);
 for(let i=0;i<columns.length;i++){
 const f=columns[i],range=s.getRange(`${col(i)}${start}:${col(i)}${end}`);
 if(/_pp/.test(f))range.setNumberFormat('0.000" pp"');
 else if(/impact|mix|rate|frequency|limit|fraction|utilisation|uplift|population_pct/.test(f)&&!/_price|paid_rate|run_rate/.test(f))range.setNumberFormat(pct);
 else if(/price|gap/.test(f))range.setNumberFormat('"£"0.00;("£"0.00);"-"');
 else if(/revenue|marketing_spend/.test(f))range.setNumberFormat(gbp);
 else if(/members|joins|difference|exposure/.test(f))range.setNumberFormat(num);
 }
}
title(R,'Northstar Fitness — conditional gym recommendations');
cell(R,'A4','Downside December member-loss limit');cell(R,'B4',refresh?.member_loss_limit??p.config.member_loss_limit);
cell(R,'A5','Minimum post-increase competitor gap (£)');cell(R,'B5',refresh?.minimum_gap??p.config.minimum_post_increase_competitor_gap);
cell(R,'A6','Test repeat repricing first (1=yes, 0=no)');cell(R,'B6',refresh?.test_repeats===false?0:refresh?.test_repeats===true?1:1);
R.getRange('A4:A6').format={font:{name:'Arial',size:10,color:'#243B53'},wrapText:true,rowHeight:32,columnWidth:33};R.getRange('B4:B6').format={fill:'#FFF3CD',font:{name:'Arial',size:10,color:'#0000FF'},columnWidth:25,rowHeight:32};R.getRange('B4').setNumberFormat(pct);R.getRange('B5').setNumberFormat(gbp);
R.getRange('B4').dataValidation={rule:{type:'decimal',operator:'between',formula1:0,formula2:1}};R.getRange('B5').dataValidation={rule:{type:'decimal',operator:'greaterThanOrEqual',formula1:0}};R.getRange('B6').dataValidation={rule:{type:'whole',operator:'between',formula1:0,formula2:1}};
form(R,'E4',`=IF(AND(COUNT(B4:B6)=3,B4>=0,B4<=1,B5>=0,OR(B6=0,B6=1)),"VALID POLICY","INVALID POLICY")`);
form(R,'E5',`=IF(AND('Scenario Comparison'!$D$3="CURRENT",'Scenario Inputs'!$E$23=0,COUNT('Scenario Inputs'!$I$9:$I$17)=0),"CURRENT EVIDENCE","UNAVAILABLE EVIDENCE")`);
form(R,'E6',`=CHOOSE('Scenario Inputs'!B3,"Base","Downside","Upside")`);cell(R,'D6','Displayed scenario case');R.getRange('D4:H6').format={font:{name:'Arial',size:10,color:'#243B53'},rowHeight:32,wrapText:true,columnWidth:21};
for(const[a,text]of [['A9','Hypothetical Jan–Dec 2026. Conditional raises require controlled testing before wider implementation.'],['A10','The 5% member limit and financial gates are policy assumptions. Revenue is not profit.'],['A11','Edit the three yellow policy cells. Portfolio uncertainty requires refresh after a selected mix changes.'],['A12',p.disclaimers[0]],['A13',p.disclaimers[1]]]){R.getRange(`${a}:H${a.replace(/\D/g,'')}`).merge();cell(R,a,text);R.getRange(`${a}:H${a.replace(/\D/g,'')}`).format={wrapText:true,rowHeight:a==='A13'?42:29,font:{name:'Arial',size:10,color:'#52667A'}};}
// Six observed sensitivity values per candidate, intact prepared inputs.
const obscols=['gym_id','price_increment',...p.config.nonzero_sensitivities];
const obs= recs.flatMap(h=>[1,2].map(i=>[h.gym_id,i,...p.config.nonzero_sensitivities.map(v=>{const f=p.scenario_sensitivity,c=f.columns;return f.data.find(r=>r[c.indexOf('gym_id')]===h.gym_id&&r[c.indexOf('price_increment')]===i&&r[c.indexOf('variant')]===v)[c.indexOf('incremental_revenue')];})]));
table(R,901,obscols,obs,null,'RecommendationSensitivityInputs7');cell(R,'A898','Prepared Phase 6 nonzero sensitivity annual revenue (£ net). Source records remain unchanged.');R.getRange('A898:H898').merge();
const candcols=['gym_id','price_increment','base_revenue','downside_revenue','downside_member_impact','revenue_lower','revenue_upper','post_competitor_gap','worst_sensitivity_revenue','complete','financial_gates_pass','repeated_repricing','base_member_impact','current_standard_price','sensitivity_coverage'];
const cidx=Object.fromEntries(candcols.map((f,i)=>[f,i]));const C=(f,row)=>col(cidx[f])+row;
const cv=[],cf=[];
for(let j=0;j<80;j++)for(const inc of[1,2]){
 const row=131+j*2+inc-1,orow=901+j*2+inc-1,v=Array(candcols.length).fill(null),f=Array(candcols.length).fill(null);v[0]=recs[j].gym_id;v[1]=inc;
 const links={base_revenue:['incremental_revenue','Base'],downside_revenue:['incremental_revenue','Downside'],downside_member_impact:['member_impact','Downside'],revenue_lower:['incremental_revenue_lower','Base'],revenue_upper:['incremental_revenue_upper','Base'],post_competitor_gap:['post_increase_competitor_gap','Base'],repeated_repricing:['repeated_repricing','Base'],base_member_impact:['member_impact','Base'],current_standard_price:['old_standard_price','Base']};
 for(const[field,[source,cas]]of Object.entries(links))f[cidx[field]]='='+lookup('$A'+row,inc,cas,source,field!=='repeated_repricing');
 f[cidx.sensitivity_coverage]=`=COUNT(C${orow}:H${orow})`;f[cidx.worst_sensitivity_revenue]=`=IF(O${row}=6,MIN(C${orow}:H${orow}),"")`;
 f[cidx.complete]=`=AND(COUNT(C${row}:I${row})=7,ISLOGICAL(L${row}),COUNT(M${row}:N${row})=2,O${row}=6)`;
 f[cidx.financial_gates_pass]=`=AND(J${row},C${row}>0,D${row}>0,F${row}>0,I${row}>0)`;
 cv.push(v);cf.push(f);
}
table(R,131,candcols,cv,cf,'RecommendationCandidateEvidence7');
// All historical context remains source-linked and is not used to manufacture site effects.
const contextcols=['gym_id',...p.recommendations.columns.filter(f=>f!=='gym_id'&&p.headroom_columns.includes(f))];
const hx=Object.fromEntries(contextcols.map((f,i)=>[f,i]));const H=(f,j)=>col(hx[f])+(351+j);
table(R,351,contextcols,recs.map(r=>contextcols.map(f=>f==='gym_id'?r.gym_id:null)),recs.map((r,j)=>contextcols.map(f=>f==='gym_id'?null:'='+context(f,'$A'+(351+j)))),'RecommendationContext7');
const rulescols=['gym_id','variant','member_loss_limit','minimum_gap','test_repeats','caution_count','flags_complete','complete','plus1_plausible','plus2_plausible','plus1_qualified','plus2_qualified','preferred_qualified_increment','assessment_increment','action','proposed_increment','provisional_test_increment','rule_id','status','captured_increment','capture_mix_matches'];
const ri=Object.fromEntries(rulescols.map((f,i)=>[f,i]));const Q=(f,row)=>col(ri[f])+row;
const rv=[],rf=[];
for(let k=0;k<400;k++){
 const r=1101+k,j=k%80,varn=p.config.variants[Math.floor(k/80)],c1=131+j*2,c2=c1+1;const v=Array(rulescols.length).fill(null),f=Array(rulescols.length).fill(null);v[0]=recs[j].gym_id;v[1]=varn;
 f[2]=varn==='member_limit_3pct'?'=0.03':varn==='member_limit_7pct'?'=0.07':'=$B$4';f[3]=varn==='competitor_buffer_1gbp'?'=1':'=$B$5';f[4]=varn==='allow_repeat_repricing'?'=0':'=$B$6';
 const flags=['high_churn_exception','weak_conversion_exception','declining_acquisition_exception','peak_capacity_exception'].map(x=>H(x,j));
 f[5]='='+flags.join('+');f[6]=`=AND(${flags.map(x=>'ISLOGICAL('+x+')').join(',')})`;f[7]=`=AND(G${r},J${c1},J${c2})`;
 f[8]=`=AND(J${c1},C${c1}>0,H${c1}>=D${r})`;f[9]=`=AND(J${c2},C${c2}>0,H${c2}>=D${r})`;
 f[10]=`=AND(I${r},K${c1},E${c1}>=-C${r})`;f[11]=`=AND(J${r},K${c2},E${c2}>=-C${r})`;
 f[12]=`=IF(AND(K${r},L${r}),IF(C${c2}>C${c1},2,1),IF(K${r},1,IF(L${r},2,0)))`;
 f[13]=`=IF(OR(NOT(H${r}),F${r}>0),0,IF(M${r}>0,M${r},IF(I${r},1,IF(J${r},2,0))))`;
 f[14]=`=IF(S${r}<>"READY","",IF(OR(NOT(H${r}),F${r}>0),"DEFENSIVE / INVESTIGATE",IF(N${r}=0,"HOLD PRICE",IF(OR(M${r}=0,AND(E${r}=1,IF(N${r}=1,L${c1},L${c2}))),"TEST FIRST",IF(N${r}=2,"RAISE £2","RAISE £1")))))`;
 f[15]=`=IF(OR(O${r}="RAISE £1",O${r}="RAISE £2"),N${r},0)`;f[16]=`=IF(O${r}="TEST FIRST",N${r},0)`;
 f[17]=`=IF(S${r}<>"READY","",IF(NOT(H${r}),"R1_MISSING",IF(F${r}>0,"R1_CAUTION",IF(N${r}=0,"R3_NO_PLAUSIBLE",IF(M${r}=0,"R6_FAILED_QUALIFICATION",IF(O${r}="TEST FIRST","R6_REPEAT_REPRICING","R7_CONDITIONAL_RAISE"))))))`;
 f[18]=`=IF($E$4<>"VALID POLICY","INVALID POLICY",IF($E$5<>"CURRENT EVIDENCE","UNAVAILABLE EVIDENCE","READY"))`;
 v[19]=refresh?.captures?.[varn]?.[recs[j].gym_id]??sens[k].proposed_increment;f[20]=`=IF(AND(S${r}="READY",P${r}=T${r}),1,0)`;
 rv.push(v);rf.push(f);
}
table(R,1101,rulescols,rv,rf,'RecommendationRuleVariants7');
// Primary output is fully formula-derived; it never depends on the audit area.
const primary=['gym_id','city','region','action','proposed_increment','provisional_test_increment','current_standard_price','proposed_standard_price','selected_incremental_revenue','selected_downside_member_impact','selected_downside_revenue','selected_incremental_revenue_lower','selected_incremental_revenue_upper','score','band','caution_flag_count','rule_id','explanation',...p.recommendations.columns.filter(f=>!['gym_id','city','region','action','proposed_increment','provisional_test_increment','current_standard_price','proposed_standard_price','selected_incremental_revenue','selected_downside_member_impact','selected_downside_revenue','selected_incremental_revenue_lower','selected_incremental_revenue_upper','score','band','caution_flag_count','rule_id','explanation'].includes(f))];
const mi=Object.fromEntries(primary.map((f,i)=>[f,i]));const M=(f,r)=>col(mi[f])+r;
const pv=[],pf=[];
for(let j=0;j<80;j++){
 const row=21+j,q=1101+j,c1=131+j*2,c2=c1+1,v=primary.map(f=>recs[j][f]??null),f=Array(primary.length).fill(null);const assign=(key,formula)=>f[mi[key]]='='+formula;
 for(const k of primary)if(hx[k]!==undefined&&k!=='gym_id')assign(k,k==='pilot_pair_id'?`IF(${H(k,j)}="","",${H(k,j)})`:H(k,j));
 for(const k of ['action','proposed_increment','provisional_test_increment','rule_id','assessment_increment'])assign(k,Q(k,q));
 assign('current_standard_price',`N${c1}`);assign('proposed_standard_price',`${M('current_standard_price',row)}+${M('proposed_increment',row)}`);
 assign('provisional_test_price',`IF(${M('provisional_test_increment',row)}>0,${M('current_standard_price',row)}+${M('provisional_test_increment',row)},"")`);
 assign('member_loss_limit','$B$4');assign('minimum_post_increase_competitor_gap','$B$5');assign('test_repeat_repricing','$B$6=1');assign('repeated_repricing',`L${c1}`);
 for(const k of primary.filter(x=>x.startsWith('selected_'))){
 let field=k.slice(9),cas='Base';if(k==='selected_downside_revenue'){field='incremental_revenue';cas='Downside';}if(k==='selected_downside_member_impact'){field='member_impact';cas='Downside';}
 const expr=i=>lookup('$A'+row,i,cas,field);assign(k,`IF(S${q}<>"READY","",IF(N${q}=2,${expr(2)},IF(N${q}=1,${expr(1)},${expr(0)})))`);
 }
 for(const[k,field]of [['counterfactual_revenue','monthly_revenue'],['counterfactual_month12_members','month12_members']])assign(k,lookup('$A'+row,0,'Base',field));
 for(const inc of[1,2]){
 const cr=inc===1?c1:c2,prefix='plus'+inc+'_';
 const mapped={complete:C('complete',cr),plausible:Q('plus'+inc+'_plausible',q),qualified:Q('plus'+inc+'_qualified',q),base_revenue:C('base_revenue',cr),downside_revenue:C('downside_revenue',cr),downside_member_impact:C('downside_member_impact',cr),revenue_lower:C('revenue_lower',cr),revenue_upper:C('revenue_upper',cr),post_competitor_gap:C('post_competitor_gap',cr),worst_sensitivity_revenue:C('worst_sensitivity_revenue',cr),base_member_impact:C('base_member_impact',cr)};
 for(const[k,expr]of Object.entries(mapped))assign(prefix+k,expr);
 const gates=[[`C${cr}>0`,'Base revenue positive'],[`H${cr}>=$B$5`,'Post-increase competitor gap'],[`D${cr}>0`,'Downside revenue positive'],[`E${cr}>=-$B$4`,'Downside member limit'],[`F${cr}>0`,'Conditional lower bound positive'],[`I${cr}>0`,'Every nonzero sensitivity positive']];
 assign(prefix+'failed_gates',`IF(NOT(J${cr}),"Missing candidate evidence",${gates.map(([expr,label])=>`IF(${expr},"","${label}; ")`).join('&')})`);
 }
 assign('plus3_base_revenue',lookup('$A'+row,3,'Base','incremental_revenue'));assign('plus3_base_member_impact',lookup('$A'+row,3,'Base','member_impact'));assign('plus3_standard_price',lookup('$A'+row,3,'Base','new_standard_price'));
 const gp=Object.entries(p.sources['Gym Master']).find(([a,value])=>a.match(/^[A-Z]+1$/)&&value==='current_premium_price')[0].replace('1','');
 assign('unchanged_plus_price',`INDEX('Gym Master'!$${gp}$2:$${gp}$81,MATCH($A${row},'Gym Master'!$A$2:$A$81,0))`);assign('plus3_standard_plus_parity',`ABS(${M('plus3_standard_price',row)}-${M('unchanged_plus_price',row)})<0.000000001`);
 assign('explanation',`IF(S${q}<>"READY",S${q},IF(R${q}="R1_MISSING","Restore missing decision evidence before repricing",IF(R${q}="R1_CAUTION",${M('investigation_needed',row)},IF(R${q}="R3_NO_PLAUSIBLE","Neither £1 nor £2 preserves the required competitor gap with positive base revenue",IF(R${q}="R6_FAILED_QUALIFICATION","Provisional test £"&Q${q}&". Failed gates: "&IF(Q${q}=1,${M('plus1_failed_gates',row)},${M('plus2_failed_gates',row)}),IF(R${q}="R6_REPEAT_REPRICING","£"&Q${q}&" passes financial gates. Repeat repricing requires controlled evidence","Conditional £"&P${q}&" gives the higher qualifying base revenue. Downside member loss "&TEXT(ABS(${M('selected_downside_member_impact',row)}),"0.00%")))))))`);
 pv.push(v);pf.push(f);
}
table(R,21,primary,pv,pf,'GymRecommendations7');R.freezePanes.freezeRows(20);R.freezePanes.freezeColumns(3);
R.getRange('D:D').format.columnWidth=31;R.getRange('R:R').format.columnWidth=75;R.getRange('R21:R100').format={wrapText:true,rowHeight:44};
// Point portfolio inputs use one unchanged captured record per gym/case.
const sumFields=['monthly_revenue','subscription_revenue','joining_fee_revenue','ancillary_revenue','month12_members','period_opening_members','opening_members','average_members','new_members','standard_joins','qualified_prospects','opening_base_cancellations','same_month_cancellations','incumbent_standard_opening','incumbent_standard_cancellations','incumbent_standard_downgrades','standard_average_members','standard_subscription_revenue','offpeak_average_members','plus_average_members','pricing_complaints','annualised_exit_run_rate','incremental_revenue','member_difference','acquisition_difference','counterfactual_revenue'];
const pc=['gym_id','variant','case','selected_increment',...sumFields,'counterfactual_month12_members'];const ix=Object.fromEntries(pc.map((f,i)=>[f,i]));
const pointV=[],pointF=[];
for(let v=0;v<5;v++)for(let c=0;c<3;c++)for(let j=0;j<80;j++){
 const row=1601+v*240+c*80+j,q=1101+v*80+j,vals=Array(pc.length).fill(null),forms=Array(pc.length).fill(null);vals[0]=recs[j].gym_id;vals[1]=p.config.variants[v];vals[2]=p.config.cases[c];forms[3]=`=P${q}`;
 for(const field of sumFields)forms[ix[field]]=`=IF(S${q}<>"READY","",IF(D${row}=2,${lookup('$A'+row,2,p.config.cases[c],field)},IF(D${row}=1,${lookup('$A'+row,1,p.config.cases[c],field)},${lookup('$A'+row,0,p.config.cases[c],field)})))`;
 forms[ix.counterfactual_month12_members]='='+lookup('$A'+row,0,'Base','month12_members');pointV.push(vals);pointF.push(forms);
}
table(R,1601,pc,pointV,pointF,'RecommendationPortfolioInputs7');
title(S,'Northstar Fitness — conditional recommendation summary');
form(S,'B4',`='Recommendations'!E5`);cell(S,'A4','Scenario evidence');form(S,'E4',`='Recommendations'!E6`);cell(S,'D4','Displayed case');
form(S,'B5',`=IF(AND('Recommendations'!E4="VALID POLICY",'Recommendations'!E5="CURRENT EVIDENCE"),"READY","UNAVAILABLE")`);cell(S,'A5','Recommendation status');
form(S,'E5',`=IF(B5<>"READY","UNAVAILABLE",IF(COUNTIFS('Recommendations'!$U$1101:$U$1500,0)=0,"CURRENT","STALE — REFRESH PORTFOLIO"))`);cell(S,'D5','Captured portfolio uncertainty');
S.getRange('A4:H5').format={font:{name:'Arial',size:10,color:'#243B53'},wrapText:true,rowHeight:32,columnWidth:22};
for(const[a,text]of [['A7','Conditional RAISE portfolio only. TEST FIRST remains at current prices.'],['A15','Intervals describe shared pilot-parameter uncertainty, excluding future shocks and transport. Positive draws are not rollout probabilities.'],['A17','Phase 7 complete. Phase 8: controlled experiment design and prospective implementation conditions.'],['A19',p.disclaimers[0]],['A20',p.disclaimers[1]]]){S.getRange(`${a}:H${a.replace(/\D/g,'')}`).merge();cell(S,a,text);S.getRange(`${a}:H${a.replace(/\D/g,'')}`).format={wrapText:true,rowHeight:a==='A20'?44:33,font:{name:'Arial',size:10,color:'#52667A'}};}
const portfolioCols=p.portfolio.columns,spi=Object.fromEntries(portfolioCols.map((f,i)=>[f,i]));
const vPort=[],fPort=[];
const psum=(field,v,c)=>`SUMIFS('Recommendations'!$${col(ix[field])}$1601:$${col(ix[field])}$2800,'Recommendations'!$B$1601:$B$2800,"${v}",'Recommendations'!$C$1601:$C$2800,"${c}")`;
const rate=(n,d)=>`IF(${d}=0,"",${n}/${d})`;
for(let k=0;k<15;k++){
 const row=131+k,v=p.config.variants[Math.floor(k/3)],cas=p.config.cases[k%3],vals=portfolioCols.map(f=>ports[k][f]??null),forms=Array(portfolioCols.length).fill(null);const assign=(f,e)=>forms[spi[f]]='='+e;
 const local=f=>col(spi[f])+row;
 for(const f of [...sumFields,'counterfactual_month12_members'])assign(f,`IF($B$5<>"READY","",${psum(f,v,cas)})`);
 for(const[field,label]of [['raise_1_sites','RAISE £1'],['raise_2_sites','RAISE £2'],['test_sites','TEST FIRST'],['hold_sites','HOLD PRICE'],['investigate_sites','DEFENSIVE / INVESTIGATE']])assign(field,`IF($B$5<>"READY","",COUNTIFS('Recommendations'!$B$1101:$B$1500,"${v}",'Recommendations'!$O$1101:$O$1500,"${label}"))`);
 assign('raise_sites',`${local('raise_1_sites')}+${local('raise_2_sites')}`);
 const ratios={member_impact:['member_difference','counterfactual_month12_members'],revenue_uplift:['incremental_revenue','counterfactual_revenue'],churn_rate:['opening_base_cancellations','opening_members'],incumbent_churn_rate:['incumbent_standard_cancellations','incumbent_standard_opening'],incumbent_downgrade_rate:['incumbent_standard_downgrades','incumbent_standard_opening'],conversion_rate:['new_members','qualified_prospects'],arpmm:['monthly_revenue','average_members'],subscription_yield:['subscription_revenue','average_members'],standard_yield:['standard_subscription_revenue','standard_average_members'],standard_mix:['standard_average_members','average_members'],offpeak_mix:['offpeak_average_members','average_members'],plus_mix:['plus_average_members','average_members']};
 for(const[f,[n,d]]of Object.entries(ratios))assign(f,`IF($B$5<>"READY","",${rate(local(n),local(d))})`);assign('retention_rate',`IF($B$5<>"READY","",1-${local('churn_rate')})`);assign('complaints_per_1000_member_months',`IF($B$5<>"READY","",${rate(local('pricing_complaints')+'*1000',local('average_members'))})`);
 const qstart=1101+Math.floor(k/3)*80,qend=qstart+79;const current=`AND($B$5="READY",COUNTIFS('Recommendations'!$U$${qstart}:$U$${qend},0)=0)`;
 const capture=refresh?.portfolio?.find(r=>r.variant===v&&r.case===cas)??ports[k];
 for(const f of portfolioCols.filter(f=>/_lower$|_upper$|positive_revenue_draw_fraction/.test(f)))assign(f,`IF(${current},${capture[f]??'""'},"")`);
 for(const[f,source]of [['excluded_test_first_base_revenue','incremental_revenue'],['excluded_test_first_base_member_difference','member_difference']]){
 const expressions=Array.from({length:80},(_,j)=>{const q=qstart+j;return `IF('Recommendations'!O${q}="TEST FIRST",IF('Recommendations'!Q${q}=2,${lookup(`'Recommendations'!A${q}`,2,'Base',source)},${lookup(`'Recommendations'!A${q}`,1,'Base',source)}),0)`;});assign(f,`IF($B$5<>"READY","",${expressions.join('+')})`);
 }
 assign('member_loss_limit',v==='member_limit_3pct'?'0.03':v==='member_limit_7pct'?'0.07':`'Recommendations'!B4`);assign('minimum_post_increase_competitor_gap',v==='competitor_buffer_1gbp'?'1':`'Recommendations'!B5`);assign('test_repeat_repricing',v==='allow_repeat_repricing'?'FALSE':`'Recommendations'!B6=1`);
 vPort.push(vals);fPort.push(forms);
}
table(S,131,portfolioCols,vPort,fPort,'RecommendationPortfolioSummary7');
const execCols=['case','incremental_revenue','member_difference','member_impact','incremental_revenue_lower','incremental_revenue_upper','raise_sites'];
table(S,10,execCols,p.config.cases.map(c=>[c,...Array(execCols.length-1).fill(null)]),p.config.cases.map((c,j)=>execCols.map((f,i)=>i?'='+col(spi[f])+(131+j):null)),'RecommendationExecutive7');
const actionCols=['action','gym_count','conditional_raise_base_revenue','conditional_raise_december_member_difference','excluded_test_base_revenue'];
table(S,25,actionCols,p.config.actions.map(a=>[a,0,0,0,0]),p.config.actions.map((a,j)=>{
 const actionRange=`'Recommendations'!$${col(mi.action)}$21:$${col(mi.action)}$100`,revrange=`'Recommendations'!$${col(mi.selected_incremental_revenue)}$21:$${col(mi.selected_incremental_revenue)}$100`,memrange=`'Recommendations'!$${col(mi.selected_member_difference)}$21:$${col(mi.selected_member_difference)}$100`;
 return [null,`=IF($B$5<>"READY","",COUNTIFS(${actionRange},A${25+j}))`,`=IF($B$5<>"READY","",${a.startsWith('RAISE')?`SUMIFS(${revrange},${actionRange},A${25+j})`:0})`,`=IF($B$5<>"READY","",${a.startsWith('RAISE')?`SUMIFS(${memrange},${actionRange},A${25+j})`:0})`,`=IF($B$5<>"READY","",${a==='TEST FIRST'?`SUMIFS(${revrange},${actionRange},A${25+j})`:0})`];
}),'RecommendationActions7');
S.getRange('A:A').format.columnWidth=32;
const matrixCols=['gym_id',...p.config.variants];
table(S,351,matrixCols,recs.map(r=>[r.gym_id,...Array(5).fill(null)]),recs.map((r,j)=>[null,...p.config.variants.map((v,k)=>`='Recommendations'!O${1101+k*80+j}`)]),'RecommendationActionSensitivity7');
const colors=['#187D73','#4BA3A0','#D59428','#8795A1','#B24D4D'];
function chart(type,range,title,a,b,format){const c=S.charts.add(type,typeof range==='string'?S.getRange(range):range);c.title=title;c.setPosition(a,b);c.titleTextStyle.typeface='Arial';c.titleTextStyle.fontSize=11;c.legend={position:'bottom',textStyle:{typeface:'Arial',fontSize:9}};c.xAxis={axisType:type==='scatter'?'valueAxis':'textAxis',numberFormatCode:type==='scatter'?'0.0%':undefined,numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:9}};c.yAxis={numberFormatCode:format,numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:9}};c.series.items.forEach((x,i)=>{x.fill=colors[i%5];x.line={fill:colors[i%5],width:type==='scatter'?0:1.5};});return c;}
chart('bar','A24:B29','Gyms by conditional action','J8','R25','0');
const chartColumns=['action','Base annual net gain (£)','December member difference'];
table(S,41,chartColumns,p.config.actions.map(a=>[a,0,0]),p.config.actions.map((a,j)=>[null,`=C${25+j}`,`=D${25+j}`]),'RecommendationActionExposure7');
chart('bar','A40:B45','Conditional RAISE net revenue','J28','R45',gbp);
chart('bar',[S.getRange('A40:A45'),S.getRange('C40:C45')],'Conditional RAISE December members','J48','R65',num);
// Numeric action code matrix supports a native heatmap without creating new rankings.
table(S,451,matrixCols,recs.map(r=>[r.gym_id,...Array(5).fill(null)]),recs.map((r,j)=>[null,...p.config.variants.map((v,k)=>`=IF(${col(k+1)}${351+j}="","",MATCH(${col(k+1)}${351+j},$A$25:$A$29,0))`)]),'RecommendationSensitivityCodes7');
for(let i=0;i<5;i++)S.getRange('B451:F530').conditionalFormats.add('cellIs',{operator:'equal',formula:i+1,format:{fill:['#C8E5DF','#D5EEEB','#F8E4BA','#E0E5E9','#E8BBBB'][i]}});
cell(S,'A448','Action codes: 1 £2, 2 £1, 3 Test, 4 Hold, 5 Investigate. These are categories, not scores.');S.getRange('A448:H448').merge();S.getRange('A448:H448').format={wrapText:true,rowHeight:30};
// Independent audit controls observe results and never feed recommendations.
cell(S,'A550','Independent verification');cell(S,'A551','Recommendation count minus 80');form(S,'B551',`=COUNTA('Recommendations'!A21:A100)-80`);cell(S,'A552','Action count minus 80');form(S,'B552','=SUM(B25:B29)-80');cell(S,'A553','Component reconciliation (£)');form(S,'B553',`=${col(spi.monthly_revenue)}131-${col(spi.subscription_revenue)}131-${col(spi.joining_fee_revenue)}131-${col(spi.ancillary_revenue)}131`);
const tradecols=['gym_id','assessment_member_impact','assessment_base_revenue'];
table(S,601,tradecols,recs.map(r=>[r.gym_id,null,null]),recs.map((r,j)=>[null,`=IF($B$5<>"READY","",IF('Recommendations'!${M('assessment_increment',21+j)}=2,'Recommendations'!${M('plus2_base_member_impact',21+j)},'Recommendations'!${M('plus1_base_member_impact',21+j)}))`,`=IF($B$5<>"READY","",IF('Recommendations'!${M('assessment_increment',21+j)}=2,'Recommendations'!${M('plus2_base_revenue',21+j)},'Recommendations'!${M('plus1_base_revenue',21+j)}))`]),'RecommendationSiteTradeoffs7');
chart('scatter','B600:C680','Site trade-offs; hold/investigate at £1 context','J68','R89',gbp);
const guides={'Dataset Overview':{'D5':'Phase 7 complete','E5':'80 site recommendations','E7':'Phase 8: controlled experiment design','E10':'Conditional recommendations'},'README':{'B20':'Phase 7 complete. Phase 8 next: experiment design and prospective implementation conditions.'}};
for(const[name,changes]of Object.entries(guides))for(const[a,text]of Object.entries(changes))cell(get(name),a,text);
// Guidance preview mirrors only the affected original values and layout.
for(const name of['Dataset Overview','README']){get(name).getRange('A:F').format.columnWidth=24;get(name).getRange('A1:F30').format={font:{name:'Arial',size:10,color:'#243B53'},wrapText:true,rowHeight:35};}
// Column widths are shared across every table on the sheet: set them after all tables.
R.getRange('A:A').format.columnWidth=33;R.getRange('B:C').format.columnWidth=24;R.getRange('D:D').format.columnWidth=35;R.getRange('R:R').format.columnWidth=75;
R.getRange('D21:D100').format.wrapText=true;R.getRange('R21:R100').format={wrapText:true,rowHeight:60};R.getRange(`${col(mi.score)}21:${col(mi.score)}100`).setNumberFormat('0.00');
for(const f of['investigation_needed','evidence_limitations','explanation','plus1_failed_gates','plus2_failed_gates']){R.getRange(`${col(mi[f])}:${col(mi[f])}`).format.columnWidth=75;R.getRange(`${col(mi[f])}21:${col(mi[f])}100`).format.wrapText=true;}
S.getRange('A:A').format.columnWidth=36;R.getRange('E6').format.font={color:'#008000'};S.getRange('E4').format.font={color:'#008000'};
R.getRange('B:B').format.columnWidth=32;R.getRange('H:H').format.columnWidth=40;R.getRange('O:O').format.columnWidth=35;R.getRange('H351:H430').format={wrapText:true,rowHeight:32};R.getRange('O1101:O1500').format.wrapText=true;R.getRange('U1101:U1500').setNumberFormat('0');R.getRange('C901:H1060').setNumberFormat(gbp);R.getRange('E351:E430').setNumberFormat('0.00');
S.getRange('B:F').format.columnWidth=34;S.getRange('B351:F430').format={wrapText:true,rowHeight:35};S.getRange('A130').values=[['Annual net revenue (£)']];S.getRange('G130').values=[['Opening-member months']];S.getRange('H130').values=[['Average-member months']];
for(const[f,label]of [['monthly_revenue','Annual net revenue (£)'],['opening_members','Opening-member months'],['average_members','Average-member months']])R.getRange(col(ix[f])+'1600').values=[[label]];
wb.recalculate();
let compared=0,maxDifference=0;
const verify=()=>{
 for(let j=0;j<80;j++)for(const f of['action','proposed_increment','provisional_test_increment','rule_id','selected_incremental_revenue','selected_downside_revenue','selected_downside_member_impact','selected_incremental_revenue_lower','selected_incremental_revenue_upper']){
 const v=R.getRange(M(f,21+j)).values[0][0],e=refresh?null:recs[j][f];if(e!==null){if(typeof e==='number'){maxDifference=Math.max(maxDifference,Math.abs(v-e));if(typeof v!=='number'||Math.abs(v-e)>Math.max(1e-7,Math.abs(e)*2e-11))throw Error(`Parity ${f} ${j}: ${v} vs ${e}`);}else if(v!==e)throw Error(`Parity ${f} ${j}: ${v} vs ${e}`);compared++;}
 }
 if(!refresh)for(let k=0;k<15;k++)for(const f of portfolioCols){const v=S.getRange(col(spi[f])+(131+k)).values[0][0],e=ports[k][f];if(typeof e==='number'){maxDifference=Math.max(maxDifference,Math.abs(v-e));if(typeof v!=='number'||Math.abs(v-e)>Math.max(1e-7,Math.abs(e)*2e-11))throw Error(`Portfolio ${f}/${k}: ${v} vs ${e}`);}else if(v!==e)throw Error(`Portfolio ${f}/${k}: ${v} vs ${e}`);compared++;}
};verify();
const tests=[];
if(!refresh){
 const before=R.getRange('D21:F100').values;cell(R,'B4',.03);if(JSON.stringify(R.getRange('D21:F100').values)===JSON.stringify(before))throw Error('Member policy failed to propagate');if(S.getRange('E5').values[0][0]==='CURRENT')throw Error('Mix changes did not stale');if(S.getRange('E10').values[0][0]!==''&&S.getRange('E10').values[0][0]!==null)throw Error('Stale interval visible');tests.push('Member policy changes action mix and stales uncertainty');cell(R,'B4',.05);
 cell(R,'B6',0);if(JSON.stringify(R.getRange('D21:F100').values)===JSON.stringify(before))throw Error('Repeat policy failed');tests.push('Zero repeat policy is valid and changes actions');cell(R,'B6',1);
 const cas=get('Scenario Inputs').getRange('B3').values[0][0];cell(get('Scenario Inputs'),'B3',3);if(JSON.stringify(R.getRange('D21:F100').values)!==JSON.stringify(before))throw Error('Displayed case affects actions');tests.push('Displayed case does not alter Base/Downside rule assessment');cell(get('Scenario Inputs'),'B3',cas);
 cell(get('Scenario Comparison'),'D3','STALE');if(R.getRange('D21').values[0][0]!==''||S.getRange('B10').values[0][0]!=='')throw Error('Stale evidence still authoritative');cell(get('Scenario Comparison'),'D3','CURRENT');tests.push('Stale scenarios suppress actions and portfolio');
 cell(get('Scenario Inputs'),'I9',0);if(R.getRange('D21').values[0][0]!=='')throw Error('Zero behavioural override remains authoritative');cell(get('Scenario Inputs'),'I9',null);tests.push('Manual zero override suppresses evidence-derived decisions');
 cell(R,'B4',null);if(R.getRange('D21').values[0][0]!=='')throw Error('Missing policy accepted as zero');cell(R,'B4',.05);tests.push('Missing policy distinct from zero');
 verify();
}
wb.recalculate();const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:10},summary:'Phase 7 formula-error scan'});
console.log('Parity and edit tests',JSON.stringify({compared,maxDifference,tests,errors:errors.ndjson}));
const ranges={'Recommendations':`A1:${col(primary.length-1)}2800`,'Recommendation Summary':`A1:${col(portfolioCols.length-1)}680`};const values={},formulas={};
for(const[name,range]of Object.entries(ranges)){values[name]={range,values:get(name).getRange(range).values};formulas[name]=get(name).getRange(range).formulas;}
await fs.writeFile(path.join(pre,'final_values.json'),JSON.stringify(values));await fs.writeFile(path.join(pre,'final_formulas.json'),JSON.stringify(formulas));await fs.writeFile(path.join(pre,'guide_updates.json'),JSON.stringify(guides));await fs.writeFile(path.join(pre,'layout.json'),JSON.stringify({primary,portfolioCols,candcols,rulescols,contextcols,pc,views:ranges}));
await fs.writeFile(path.join(pre,'build_verification.json'),JSON.stringify({compared,maxDifference,tests,errors:errors.ndjson,refresh:!!refresh,selectedCase:p.sources['Scenario Inputs'].B3,selectedPrice:p.sources['Scenario Inputs'].B4},null,2));
const views=[['Recommendations','A1:H13','controls'],['Recommendations','A20:F29','actions'],['Recommendations','I20:R29','financial'],['Recommendations','A130:O139','candidate'],['Recommendations','A350:K359','context'],['Recommendations','A900:H909','sensitivity_inputs'],['Recommendations','A1100:U1109','rules'],['Recommendation Summary','A1:H29','summary'],['Recommendation Summary','A130:L136','portfolio'],['Recommendation Summary','A350:F363','action_changes'],['Recommendation Summary','J8:R25','chart_counts'],['Recommendation Summary','J28:R45','chart_revenue'],['Recommendation Summary','J48:R65','chart_members'],['Recommendation Summary','J68:R89','chart_tradeoffs'],['Dataset Overview','A1:F10','overview'],['README','A16:F24','readme']];
for(const[sheetName,range,file]of views){const blob=await wb.render({sheetName,range,scale:1.2,format:'png'});await fs.writeFile(path.join(pre,file+'.png'),new Uint8Array(await blob.arrayBuffer()));}
// Export only this bounded dependency segment, never the large 25-sheet workbook.
// Packaging takes the two new authored sheets and retains the original source sheets.
const file='recommendation_parts.xlsx';await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(pre,file));
const segments=['Recommendations','Recommendation Summary'].map(name=>({name,file}));
await fs.writeFile(path.join(pre,'segments.json'),JSON.stringify(segments));console.log('Phase 7 authored and exported two bounded segments.');
