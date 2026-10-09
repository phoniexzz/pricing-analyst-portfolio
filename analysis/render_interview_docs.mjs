// Render written interview materials for visual QA, without operating native deliverables.
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const modules=process.env.CODEX_NODE_MODULES || path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const {marked}=await import(pathToFileURL(path.join(modules,'marked/lib/marked.esm.js')));
const {chromium}=await import(pathToFileURL(path.join(modules,'playwright/index.mjs')));
const out=path.join(root,'analysis/.interview_build/rendered');await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1280,height:960},deviceScaleFactor:1});
const reports=[];
for(const file of ['README.md','interview/README.md','interview/story.md','interview/core_questions.md','interview/stakeholder_challenges.md','interview/quick_reference.md','interview/demonstration.md','interview/rehearsal.md']){
 const absolute=path.join(root,file),text=await fs.readFile(absolute,'utf8'),name=file.replaceAll('/','_').replace('.md','');
 const html=`<!doctype html><html><head><meta charset="utf-8"><base href="${pathToFileURL(path.dirname(absolute)+path.sep)}"><style>
 body{margin:40px auto;max-width:1060px;padding:0 28px;color:#18334a;font:17px/1.6 Arial,sans-serif}h1{font-size:34px;line-height:1.25}h2{margin-top:32px;color:#076a70}h3{font-size:21px;margin-top:28px}a{color:#007479;overflow-wrap:anywhere}img{max-width:100%;height:auto;border:1px solid #dde4e8}table{border-collapse:collapse;table-layout:fixed;width:100%;font-size:15px}td,th{border:1px solid #cdd7dd;padding:10px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#e6f1f1}code{background:#edf1f4;font-size:13px;overflow-wrap:anywhere}pre{padding:16px;background:#edf1f4;overflow:auto}p{margin:14px 0}input[type=checkbox]{margin-right:6px}</style></head><body>${marked.parse(text)}</body></html>`;
 const target=path.join(out,name+'.html');await fs.writeFile(target,html);await page.goto(pathToFileURL(target).href);
 await page.evaluate(()=>Promise.all([...document.images].map(im=>im.complete?Promise.resolve():new Promise(resolve=>{im.onload=resolve;im.onerror=resolve}))));
 const findings=await page.evaluate(()=>({brokenImages:[...document.images].filter(i=>!i.naturalWidth).map(i=>i.src),horizontalOverflow:document.documentElement.scrollWidth>innerWidth,
   clippedText:[...document.querySelectorAll('td,th,p,h1,h2,h3')].filter(e=>e.scrollWidth>e.clientWidth+2||e.scrollHeight>e.clientHeight+2).map(e=>e.textContent.slice(0,80)),height:document.documentElement.scrollHeight}));
 if(findings.brokenImages.length||findings.horizontalOverflow||findings.clippedText.length)throw new Error(JSON.stringify({file,...findings}));
 await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});await page.screenshot({path:path.join(out,name+'_opening.png')});
 const sections=await page.locator('h2').allTextContents();const captures=[];
 for(let i=0;i<sections.length;i++){
  const heading=page.locator('h2').nth(i);await heading.evaluate(e=>window.scrollTo(0,Math.max(0,e.getBoundingClientRect().top+scrollY-30)));
  const image=name+`_section_${i+1}.png`;await page.screenshot({path:path.join(out,image)});captures.push({heading:sections[i],image});
 }
 reports.push({file,source_sha256:createHash('sha256').update(text).digest('hex'),...findings,sections:captures});
}
await browser.close();await fs.writeFile(path.join(out,'render_validation.json'),JSON.stringify(reports,null,2));
console.log(JSON.stringify(reports.map(({file,height,horizontalOverflow,clippedText,sections})=>({file,height,horizontalOverflow,clippedText,sections:sections.length})),null,2));
