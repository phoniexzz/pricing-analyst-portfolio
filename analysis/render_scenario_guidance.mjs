import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const pre='analysis/.workbook_previews/phase6';
try{const w=await SpreadsheetFile.importXlsx(await FileBlob.load(pre+'/guidance_segment.xlsx'));
for(const [sheetName,range,name]of [['Dataset Overview','A1:F10','overview_final'],['README','A16:F24','readme_final']]){const b=await w.render({sheetName,range,scale:1.3,format:'png'});await fs.writeFile(pre+'/'+name+'.png',new Uint8Array(await b.arrayBuffer()));}
}catch(e){console.error(e.name+': '+e.message);process.exitCode=1;}
