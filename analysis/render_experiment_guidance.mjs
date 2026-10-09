import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const pre='analysis/.workbook_previews/phase8';
const w=await SpreadsheetFile.importXlsx(await FileBlob.load(pre+'/guidance_segment.xlsx'));
for(const[sheetName,range,name]of [['Dataset Overview','A1:F10','overview'],['README','A16:H24','readme'],['Recommendation Summary','A16:H18','recommendation_guidance']]){const b=await w.render({sheetName,range,scale:1.3,format:'png'});await fs.writeFile(pre+'/'+name+'.png',new Uint8Array(await b.arrayBuffer()));}
console.log('Rendered all three affected guidance areas from current saved styles and caches.');
