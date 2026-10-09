"""Make a bounded read-only guidance segment for Artifact Tool authoring."""
import copy,json
import xml.etree.ElementTree as ET
from zipfile import ZipFile,ZIP_DEFLATED
from pathlib import Path
import append_scenario_sheets as x
ROOT=Path(__file__).resolve().parents[1];PRE=ROOT/'analysis/.workbook_previews/phase9'
def prepare():
 PRE.mkdir(parents=True,exist_ok=True)
 current=ROOT/'excel/gym_pricing_model.xlsx';(PRE/'input_workbook.xlsx').write_bytes(current.read_bytes())
 updates={'Dataset Overview':{'D5':'Phase 9 build-ready','E5':'Six Power BI pages','E7':'Phase 10 next'},'README':{'B20':'Phase 9 build-ready; native verification pending. Phase 10 next.'},'Recommendation Summary':{'A17':'Phase 9 build-ready; native verification pending. Phase 10 next.'}}
 (PRE/'requested_guidance.json').write_text(json.dumps(updates,indent=2),encoding='utf-8')
 with ZipFile(current) as z:
  paths=x.sheet_paths(z);book=ET.fromstring(z.read('xl/workbook.xml'));sheets=book.find(x.T+'sheets');ids=set()
  for s in list(sheets):
   if s.attrib['name'] not in updates:sheets.remove(s)
   else:ids.add(s.attrib['{'+x.RID+'}id'])
  defs=book.find(x.T+'definedNames')
  if defs is not None:book.remove(defs)
  rel=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
  for r in list(rel):
   if r.attrib['Type'].endswith('/worksheet') and r.attrib['Id'] not in ids:rel.remove(r)
   if r.attrib['Type'].endswith(('/calcChain','/externalLink')):rel.remove(r)
  repl={'xl/workbook.xml':x.xml(book),'xl/_rels/workbook.xml.rels':x.xml(rel)}
  for name in updates:
   part=paths[name];tree=ET.fromstring(z.read(part));data=tree.find(x.T+'sheetData');limit={'Dataset Overview':14,'README':23,'Recommendation Summary':18}[name]
   for row in list(data):
    if int(row.attrib['r'])>limit:data.remove(row)
    else:
     for cell in row:
      f=cell.find(x.T+'f')
      if f is not None:cell.remove(f) # cached values in this audit-only segment
   for tag in ['drawing','tableParts','conditionalFormatting','dataValidations']:
    for node in list(tree.findall(x.T+tag)):tree.remove(node)
   repl[part]=x.xml(tree)
  ct=ET.fromstring(z.read('[Content_Types].xml'))
  for c in list(ct):
   if '/worksheets/' in c.attrib.get('PartName','') and c.attrib['PartName'].lstrip('/') not in [paths[n] for n in updates]:ct.remove(c)
  repl['[Content_Types].xml']=x.xml(ct)
  with ZipFile(PRE/'guidance_segment.xlsx','w',ZIP_DEFLATED) as out:
   for item in z.infolist():
    if item.filename.startswith('xl/worksheets/') and item.filename not in [paths[n] for n in updates]:continue
    out.writestr(copy.copy(item),repl.get(item.filename,z.read(item.filename)))
 print('Read-only guidance segment prepared from fresh 31-sheet workbook')
if __name__=='__main__':prepare()
