import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {SpreadsheetFile,FileBlob} from '@oai/artifact-tool';
const dir=path.dirname(fileURLToPath(import.meta.url)),pre=path.join(dir,'.workbook_previews','phase6');
const p=JSON.parse(await fs.readFile(path.join(pre,'payload.json'),'utf8')),layout=JSON.parse(await fs.readFile(path.join(pre,'layout.json'),'utf8'));
const col=i=>{let s='';for(let n=i+1;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const gbp='"£"#,##0.00;("£"#,##0.00);"-"',num='#,##0.0;(#,##0.0);"-"';
function base(s,range){s.showGridLines=false;s.getRange(range).format={font:{name:'Arial',size:10,color:'#243B53'},verticalAlignment:'center',rowHeight:22};s.getRange('A:Z').format.columnWidth=18;}
function header(s,range,height=48){s.getRange(range).format={fill:'#243B53',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:height,verticalAlignment:'center'};}
function title(s,text){s.getRange('A2:H2').merge();s.getRange('A2').values=[[text]];s.getRange('A2:H2').format={font:{name:'Arial',size:14,bold:true,color:'#243B53'},rowHeight:26};}
function formatColumns(s,cols,start,end){for(let i=0;i<cols.length;i++){const f=cols[i],r=s.getRange(`${col(i)}${start}:${col(i)}${end}`);if(f==='month')r.setNumberFormat('mmm-yy');else if(/_pp$/.test(f))r.setNumberFormat('0.000" pp"');else if(/rate|share|mix|impact|utilisation|uplift|fraction|probability|retention/.test(f)&&!(/paid_rate|subscription_revenue|run_rate/.test(f)))r.setNumberFormat('0.00%');else if(/revenue|arpmm|yield|price|paid/.test(f)&&!f.startsWith('pricing_complaints'))r.setNumberFormat(gbp);else if(/elasticity|dose|multiplier|increment/.test(f)&&!/revenue/.test(f))r.setNumberFormat('0.000');else r.setNumberFormat(num);}}

async function main(){
 for(const seg of JSON.parse(await fs.readFile(path.join(pre,'segments.json'),'utf8'))){
  if(process.argv.includes('--comparison-only')&&seg.name!=='Scenario Comparison')continue;
  if(process.argv.includes('--summary-only')&&seg.name!=='Scenario Summary')continue;
  const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(pre,seg.file))),s=wb.worksheets.getItem(seg.name);
  s.showGridLines=false;s.getRange('A:Z').format.columnWidth=18;
  if(seg.name==='Scenario Inputs'){
   base(s,'A1:I27');base(s,`A49:${col(p.drivers.columns.length-1)}1009`);base(s,`A1100:${col(p.states.columns.length-1)}2700`);
   header(s,'A8:I8');header(s,`A49:${col(p.drivers.columns.length-1)}49`,60);header(s,`A1100:${col(p.states.columns.length-1)}1100`,60);
   formatColumns(s,p.drivers.columns,50,1009);formatColumns(s,p.states.columns,1101,2700);s.getRange('I50:O1009').setNumberFormat('0.00%');s.getRange('P50:P1009').setNumberFormat(gbp);s.getRange('D50:D1009').setNumberFormat('0');s.getRange('E1101:E2700').setNumberFormat(gbp);s.getRange('H1101:H2700').setNumberFormat(gbp);s.getRange('G1101:G2700').setNumberFormat('0.00%');
   s.getRange(`A:${col(p.drivers.columns.length-1)}`).format.columnWidth=18;s.getRange('A:A').format.columnWidth=34;s.getRange('B:C').format.columnWidth=25;s.getRange('E:E').format.columnWidth=27;s.getRange('F:I').format.columnWidth=19;
   s.getRange('A6:I6').format={wrapText:true,rowHeight:34};s.getRange('C9:C17').format={wrapText:true,rowHeight:34};s.getRange('A20:I21').format={wrapText:true,rowHeight:26};
   s.getRange('F9:I17').format.font={color:'#0000FF'};s.getRange('I9:I17').format.fill='#FFF3CD';s.getRange('B3:B4').format={fill:'#FFF3CD',font:{color:'#0000FF'}};
   s.getRange('B9').values=[['dimensionless']];s.getRange('B12').values=[['natural-log ratio']];s.getRange('B13').values=[['complaints / 1,000 member-months']];s.getRange('B14:B15').values=[['dimensionless'],['dimensionless']];s.getRange('B9:C17').format={wrapText:true,rowHeight:36};s.getRange('E25').setNumberFormat('yyyy-mm-dd hh:mm');s.getRange('E9:I17').setNumberFormat('0.000000');s.getRange('E10:I11').setNumberFormat('0.0000%');s.getRange('B3').dataValidation={rule:{type:'whole',operator:'between',formula1:1,formula2:3}};s.getRange('B4').dataValidation={rule:{type:'whole',operator:'between',formula1:0,formula2:3}};
  }else if(seg.name==='Scenario Model'){
   if(seg.file.includes('front')){
    s.getRange(`A:${col(layout.annualFields.length-1)}`).format.columnWidth=18;base(s,`A1:${col(layout.annualFields.length-1)}168`);base(s,`A200:${col(layout.summaryFields.length-1)}2120`);base(s,'A2200:D2280');base(s,'A2300:AC13000');
    header(s,`A8:${col(layout.annualFields.length-1)}8`,70);header(s,`A200:${col(layout.summaryFields.length-1)}200`,70);header(s,'A2200:D2200');header(s,'A2300:AC2300',70);
    for(const [f,label]of [['opening_members','Opening-member months'],['average_members','Average-member months']])s.getRange(col(layout.annualFields.indexOf(f))+'8').values=[[label]];formatColumns(s,layout.annualFields,9,168);formatColumns(s,layout.summaryFields,201,2120);s.getRange('A5:J6').format={wrapText:true,rowHeight:26};formatColumns(s,layout.flows,2301,13000);
   }else{base(s,`A13001:AC${layout.detailRow-1}`);formatColumns(s,layout.flows,13001,layout.detailRow-1);}
   s.getRange(`I${seg.file.includes('front')?2301:13001}:K${seg.file.includes('front')?13000:layout.detailRow-1}`).setNumberFormat('0.0000%');s.getRange(`S${seg.file.includes('front')?2301:13001}:T${seg.file.includes('front')?13000:layout.detailRow-1}`).setNumberFormat(gbp);
  }else if(seg.name==='Scenario Comparison'){
   const source=wb.worksheets.add('Scenario Inputs');source.getRange('E23').values=[[0]];
   const authored=JSON.parse(await fs.readFile(path.join(pre,'final_formulas.json'),'utf8'));
   for(let c=0;c<layout.captureColumns.length;c++)if(/_lower$|_upper$|^break_even_|positive_revenue_draw_fraction/.test(layout.captureColumns[c])){
    const src=p.comparisons.columns.indexOf(layout.captureColumns[c]);const forms=p.comparisons.data.map(row=>[`=IF(AND('Scenario Inputs'!$E$23=0,COUNT('Scenario Inputs'!$I$9:$I$17)=0),${typeof row[src]==='number'?row[src]:'""'},"")`]);
    s.getRange(`${col(c)}31:${col(c)}990`).formulas=forms;
    for(let i=0;i<960;i++)authored[seg.name][30+i][c]=forms[i][0];
   }
   await fs.writeFile(path.join(pre,'final_formulas.json'),JSON.stringify(authored));
   s.getRange(`A:${col(layout.captureColumns.length-1)}`).format.columnWidth=18;base(s,'A1:I21');base(s,`A30:${col(layout.captureColumns.length-1)}990`);base(s,'A1100:F12620');
   for(const [f,label]of [['opening_members','Opening-member months'],['average_members','Average-member months']])s.getRange(col(layout.captureColumns.indexOf(f))+'30').values=[[label]];s.getRange('I8').values=[['Positive draw fraction']];header(s,'A8:I8',66);header(s,`A30:${col(layout.captureColumns.length-1)}30`,70);header(s,'A1100:F1100',58);
   s.getRange('D3:H4').format={wrapText:true,rowHeight:30};s.getRange('A5:H6').format={wrapText:true,rowHeight:26};
   s.getRange('C9:F20').setNumberFormat(gbp);s.getRange('G9:G20').setNumberFormat(num);s.getRange('H9:I20').setNumberFormat('0.00%');formatColumns(s,layout.captureColumns,31,990);formatColumns(s,['gym_id','month','price_increment','case','monthly_revenue','closing_members'],1101,12620);
  }else{
   if(s.charts.items.length===4)for(const series of s.charts.items[3].series.items)series.fill='#C9D8E8';base(s,'A1:S240');for(const [r,h]of [['A8:H8',65],['A19:D19',52],['A80:E80',55],['G80:K80',55],['A100:C100',52],['A190:B190',65]])header(s,r,h);
   s.getRange('D3:H4').format={wrapText:true,rowHeight:30};s.getRange('A15:H16').format={wrapText:true,rowHeight:26};s.getRange('A23:H25').format={wrapText:true,rowHeight:26};s.getRange('A29:H34').format={wrapText:true,rowHeight:24};
   s.getRange('B9:E12').setNumberFormat(gbp);s.getRange('F9:F12').setNumberFormat(num);s.getRange('G9:H12').setNumberFormat('0.00%');s.getRange('B20').setNumberFormat(gbp);s.getRange('C20').setNumberFormat('0.00%');s.getRange('A81:A92').setNumberFormat('mmm-yy');s.getRange('B81:E92').setNumberFormat(gbp);s.getRange('H81:K92').setNumberFormat(num);s.getRange('B101:B180').setNumberFormat('0.00%');s.getRange('C101:C180').setNumberFormat(gbp);s.getRange('B191:B196').setNumberFormat(gbp);
  }
  if(!seg.file.includes('tail')){s.getRange('A2:H2').format={font:{name:'Arial',size:14,bold:true,color:'#243B53'},rowHeight:28};s.getRange('B3').format.font={color:'#008000'};}
  console.log('Styling bounded segment',seg.file);await(await SpreadsheetFile.exportXlsx(wb)).save(path.join(pre,seg.file));
  const views=seg.name==='Scenario Inputs'?[['A1:I27','inputs_final'],['I49:Q56','rates_final'],['A1100:J1108','states_final']]:seg.file.includes('front')?[['A1:J14','model_final'],['I2300:T2308','billing_final']]:seg.file.includes('tail')?[['A13001:H13008','model_tail_final']]:seg.name==='Scenario Comparison'?[['A1:I21','comparison_final'],['A30:H36','capture_final']]:[['A1:H26','summary_final'],['J7:S25','revenue_final'],['J28:S46','members_final'],['J49:S68','tradeoff_final'],['J71:S90','bridge_final']];
  for(const [range,name]of views){const b=await wb.render({sheetName:seg.name,range,scale:1.2,format:'png'});await fs.writeFile(path.join(pre,name+'.png'),new Uint8Array(await b.arrayBuffer()));}
 }
}
try{await main();}catch(e){console.error(e.name+': '+e.message);process.exitCode=1;}
