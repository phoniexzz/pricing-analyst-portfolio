// Optional local Markdown visual QA; no accepted report or workbook is modified.
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const modules=process.env.CODEX_NODE_MODULES || path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const {marked}=await import(pathToFileURL(path.join(modules,'marked/lib/marked.esm.js')));
const {chromium}=await import(pathToFileURL(path.join(modules,'playwright/index.mjs')));
const out=path.join(root,'analysis/.portfolio_build/docs');await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1280,height:960},deviceScaleFactor:1});
const reports=[];
for(const file of ['README.md','portfolio/case_study.md','portfolio/dashboard_gallery.md','portfolio/REPRODUCIBILITY.md','sql/README.md']){
 const absolute=path.join(root,file),text=await fs.readFile(absolute,'utf8');
 const name=file.replaceAll('/','_').replace('.md','');
 const html=`<!doctype html><html><head><meta charset="utf-8"><base href="${pathToFileURL(path.dirname(absolute)+path.sep)}"><style>
 body{margin:40px auto;max-width:1060px;padding:0 28px;color:#18334a;font:17px/1.6 Arial,sans-serif}h1{font-size:34px;line-height:1.25}h2{margin-top:32px;color:#076a70}a{color:#007479}img{max-width:100%;height:auto;border:1px solid #dde4e8}table{border-collapse:collapse;width:100%;font-size:15px}td,th{border:1px solid #cdd7dd;padding:10px;text-align:left;vertical-align:top}th{background:#e6f1f1}code{background:#edf1f4;font-size:14px}pre{padding:16px;background:#edf1f4;overflow:auto}p{margin:14px 0}</style></head><body>${marked.parse(text)}</body></html>`;
 const target=path.join(out,name+'.html');await fs.writeFile(target,html);
 await page.goto(pathToFileURL(target).href);await page.evaluate(()=>Promise.all([...document.images].map(im=>im.complete?Promise.resolve():new Promise(resolve=>{im.onload=resolve;im.onerror=resolve}))));
 const findings=await page.evaluate(()=>({brokenImages:[...document.images].filter(i=>!i.naturalWidth).map(i=>i.src),horizontalOverflow:document.documentElement.scrollWidth>innerWidth,height:document.documentElement.scrollHeight}));
 if(findings.brokenImages.length||findings.horizontalOverflow)throw new Error(JSON.stringify({file,...findings}));
 await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});
 // Recruiter-facing opening viewport and lower README screenshot detail.
 if(file==='README.md'){
  await page.screenshot({path:path.join(out,'README_opening.png')});
  await page.locator('h2').filter({hasText:'Findings and conditional decisions'}).scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(out,'README_findings.png')});
 }
 reports.push({file,...findings});
}
await browser.close();await fs.writeFile(path.join(out,'render_validation.json'),JSON.stringify(reports,null,2));
console.log(JSON.stringify(reports,null,2));
