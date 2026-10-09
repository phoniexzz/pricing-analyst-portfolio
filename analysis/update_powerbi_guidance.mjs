import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {FileBlob,SpreadsheetFile,Workbook} from '@oai/artifact-tool';
const root=path.dirname(fileURLToPath(import.meta.url)), pre=path.join(root,'.workbook_previews','phase9');
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(pre,'guidance_segment.xlsx')));
const desired=JSON.parse(await fs.readFile(path.join(pre,'requested_guidance.json'),'utf8'));
const ranges={'Dataset Overview':'A1:F14','README':'A16:F23','Recommendation Summary':'A15:H18'};
for(const [name,updates] of Object.entries(desired)){
 const image=await wb.render({sheetName:name,range:ranges[name],scale:1.5,format:'png'});
 await fs.writeFile(path.join(pre,name.replaceAll(' ','_')+'_before.png'),new Uint8Array(await image.arrayBuffer()));
 const sheet=wb.worksheets.getItem(name);
 for(const [cell,text] of Object.entries(updates))sheet.getRange(cell).values=[[text]];
}
wb.recalculate();
const authored={};
for(const[name,updates]of Object.entries(desired)){
 authored[name]={};const sheet=wb.worksheets.getItem(name);
 for(const cell of Object.keys(updates))authored[name][cell]=sheet.getRange(cell).values[0][0];
 const image=await wb.render({sheetName:name,range:ranges[name],scale:1.5,format:'png'});
 await fs.writeFile(path.join(pre,name.replaceAll(' ','_')+'_after.png'),new Uint8Array(await image.arrayBuffer()));
}
await fs.writeFile(path.join(pre,'guide_updates.json'),JSON.stringify(authored,null,2));
await fs.writeFile(path.join(root,'latest_phase_guidance.json'),JSON.stringify(authored,null,2));
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(pre,'guidance_authored.xlsx'));
console.log('Artifact Tool authored and rendered three guidance views. Existing format retained.');
// Disposable input-change cells, authored by the same documented spreadsheet API.
const tests=Workbook.create();
for(const[name,address,value]of [['Zero Override','I9',0],['Policy Edit','B4',.03],['Selector Case','B3',2],['Stale Capture','D3','STALE']]){
 const sheet=tests.worksheets.add(name);sheet.getRange(address).values=[[value]];
}
tests.recalculate();await(await SpreadsheetFile.exportXlsx(tests)).save(path.join(pre,'stale_test_cells.xlsx'));
