"""Read saved formula/value blocks for an Artifact recalculation audit; never writes business formulas."""
import json,re,sys,xml.etree.ElementTree as E
from zipfile import ZipFile
from pathlib import Path
sys.path.insert(0,'analysis');import append_scenario_sheets as pack
from refresh_scenario_comparison import cells,col
pre=pack.PREVIEW;l=json.loads((pre/'layout.json').read_text());p=json.loads((pre/'payload.json').read_text())
ranges={
'Scenario Inputs':[(1,27,80+max(len(p['drivers']['columns']),len(p['states']['columns']))),(49,1009,80+max(len(p['drivers']['columns']),len(p['states']['columns']))),(1100,2700,80+max(len(p['drivers']['columns']),len(p['states']['columns'])))],
'Scenario Model':[(1,168,len(l['annualFields'])),(200,2120,len(l['summaryFields'])),(2200,2280,4),(2300,l['detailRow']-1,len(l['flows']))],
'Scenario Comparison':[(1,21,16),(30,990,len(l['captureColumns'])),(1100,12620,6)],'Scenario Summary':[(1,240,19)],'Monthly Performance':[(1,1921,48)]}
out=[]
with ZipFile(pack.OUTPUT) as z:
 paths=pack.sheet_paths(z)
 for name,rs in ranges.items():
  raw=cells(z,paths[name]);tree=E.fromstring(z.read(paths[name]));forms={c.attrib['r']:'='+c.find(pack.T+'f').text for c in tree.iter(pack.T+'c') if c.find(pack.T+'f') is not None}
  blocks=[]
  for start,end,width in rs:
   for a in range(start,end+1,1000):
    b=min(a+999,end);addresses=[[col(c)+str(r) for c in range(width)] for r in range(a,b+1)]
    values=[[raw.get(x) for x in row] for row in addresses];f=[[forms.get(x) for x in row] for row in addresses]
    blocks.append(dict(address='A'+str(a)+':'+col(width-1)+str(b),values=values,formulas=f if any(v for row in f for v in row) else None))
  out.append(dict(name=name,blocks=blocks))
(pre/'saved_formula_blocks.json').write_text(json.dumps(out,separators=(',',':')),encoding='utf-8')
print('Prepared actual saved formulas and values as bounded audit blocks.')
