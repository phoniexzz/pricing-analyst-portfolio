import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const dir=path.dirname(fileURLToPath(import.meta.url)),pre=path.join(dir,'.workbook_previews','phase6');
const p=JSON.parse(await fs.readFile(path.join(pre,'payload.json'),'utf8')),l=JSON.parse(await fs.readFile(path.join(pre,'layout.json'),'utf8'));
const inputsName='Scenario Inputs',modelName='Scenario Model',compName='Scenario Comparison',sumName='Scenario Summary';
const col=i=>{let s='';for(let n=i+1;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const annualFields=l.annualFields,summaryFields=l.summaryFields,captureColumns=l.captureColumns,detailRow=l.detailRow;
const comparisons=p.comparisons.data,monthly=p.monthly.data;
function addChart(s,type,range,title,a,b,fmt){const chart=s.charts.add(type,range);chart.title=title;chart.setPosition(a,b);chart.titleTextStyle.typeface='Arial';chart.titleTextStyle.fontSize=11;chart.legend={position:'top',textStyle:{typeface:'Arial',fontSize:9}};chart.xAxis={axisType:type==='scatter'?'valueAxis':'textAxis',textStyle:{fontSize:9,typeface:'Arial'},numberFormatCode:type==='scatter'?'0.0%':undefined,numberFormatSourceLinked:false};chart.yAxis={numberFormatCode:fmt,numberFormatSourceLinked:false,textStyle:{fontSize:9,typeface:'Arial'}};chart.series.items.forEach((x,i)=>{const color=['#243B53','#2F855A','#D69E2E','#9F7AEA'][i%4];x.fill=color;x.line={fill:color,width:type==='scatter'?0:1.5};});return chart;}
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

try{await exportSegments();}catch(e){console.error(e.name+': '+e.message);process.exitCode=1;}
