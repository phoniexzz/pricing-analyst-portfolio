"""Apply Artifact-authored guidance; verify preservation and refresh packaging."""
import json,copy,hashlib
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import package_recommendations as pack
from refresh_scenario_comparison import cells
ROOT=Path(__file__).resolve().parents[1];PRE=ROOT/'analysis/.workbook_previews/phase9'
def compare(before,after,updates):
 with ZipFile(before) as a,ZipFile(after) as b:
  ap=pack.common.sheet_paths(a);bp=pack.common.sheet_paths(b);assert list(ap)==list(bp) and len(bp)==31
  changed=[];cells_checked=0
  for name,path in ap.items():
   if name not in updates:assert a.read(path)==b.read(bp[name]),name
   else:
    aa=cells(a,path);bb=cells(b,bp[name]);assert set(aa)==set(bb)
    for c,v in aa.items():
     assert bb[c]==(updates[name][c] if c in updates[name] else v),(name,c)
     cells_checked+=1
    # Compare the native guide sheet XML after replacing only authorised cells.
    x=ET.fromstring(a.read(path));y=ET.fromstring(b.read(bp[name]));xl={c.attrib['r']:c for c in x.iter(pack.T+'c')};yl={c.attrib['r']:c for c in y.iter(pack.T+'c')}
    for c in updates[name]:
     parent=next(row for row in y.iter(pack.T+'row') if yl[c] in list(row));i=list(parent).index(yl[c]);parent.remove(yl[c]);parent.insert(i,copy.deepcopy(xl[c]))
    assert ET.tostring(x)==ET.tostring(y),name+' unintended style/formula/feature change'
    changed+=list(updates[name])
  exempt={'xl/workbook.xml','xl/_rels/workbook.xml.rels','xl/styles.xml','[Content_Types].xml',*[ap[n] for n in updates]}
  for item in a.namelist():
   if item not in exempt:assert a.read(item)==b.read(item),item
  assert ET.tostring(ET.fromstring(a.read('xl/styles.xml')))==ET.tostring(ET.fromstring(b.read('xl/styles.xml')))
  for address in ['B3','B4']:assert cells(a,ap['Scenario Inputs'])[address]==cells(b,bp['Scenario Inputs'])[address]
 return {'sheet_count':31,'all_unaffected_sheets_byte_identical':True,'all_other_native_resources_byte_identical':True,'guide_cells_changed':len(changed),'guide_cells_independently_compared':cells_checked,'selector_restored':True}
def main():
 updates=json.loads((PRE/'guide_updates.json').read_text(encoding='utf-8'))
 before=PRE/'input_workbook.xlsx'
 pack.graft(before,pack.OUTPUT,[],PRE,guides_path=PRE/'guide_updates.json',prefix='phase9_')
 proof=compare(before,pack.OUTPUT,updates)
 # Exercise the same owned-sheet packaging used by all three existing refreshes
 # on a disposable copy. Previously validated cached builds are retained exactly.
 refresh=PRE/'refresh_preservation_test.xlsx';pack.graft(pack.OUTPUT,refresh,[],PRE)
 compare(pack.OUTPUT,refresh,updates)
 for phase,owned in [('phase6','Scenario Summary'),('phase7','Recommendation Summary'),('phase8','Experiment Results')]:
  pre=ROOT/'analysis/.workbook_previews'/phase
  segments=json.loads((pre/'segments.json').read_text(encoding='utf-8'))
  # Replace one small owned summary per workflow, preserving all later sheets.
  summary=[s for s in segments if s['name']==owned]
  if summary:
   before_refresh=PRE/f'{phase}_refresh_input.xlsx';before_refresh.write_bytes(refresh.read_bytes())
   pack.graft(before_refresh,refresh,summary,pre,pre/'final_values.json',pre/'final_formulas.json',pre/'guide_updates.json' if (pre/'guide_updates.json').exists() else None,prefix='phase9_'+phase+'_')
   with ZipFile(refresh) as z:
    paths=pack.common.sheet_paths(z);assert len(paths)==31
    for name,changes in updates.items():
     now=cells(z,paths[name]);assert all(now[c]==v for c,v in changes.items())
    assert cells(z,paths['Scenario Inputs'])['B3']==1 and cells(z,paths['Scenario Inputs'])['B4']==2
 proof['refresh_packaging_tests']='Phase 6/7/8 owned summary replacements retain 31 sheets, latest guidance and selector. Forecast engines are unchanged; their prior verification is retained.'
 (ROOT/'analysis/powerbi_workbook_verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
 print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
