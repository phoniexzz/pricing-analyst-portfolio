"""Deterministic snapshot and independent stale-input tests on disposable copies."""
import copy,json,contextlib,io
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import xml.etree.ElementTree as ET
from powerbi_prepare import ROOT,prepare,workbook_status,digest,sources
import append_scenario_sheets as xml
PRE=ROOT/'analysis/.workbook_previews/phase9'
def inject_test(source_name,sheet_name,address,source_address=None):
 destination=PRE/(source_name.replace(' ','_')+'_test.xlsx')
 with ZipFile(ROOT/'excel/gym_pricing_model.xlsx') as original,ZipFile(PRE/'stale_test_cells.xlsx') as authored:
  p=xml.sheet_paths(original)[sheet_name];s=xml.sheet_paths(authored)[source_name]
  tree=ET.fromstring(original.read(p));test=next(c for c in ET.fromstring(authored.read(s)).iter(xml.T+'c') if c.attrib['r']==(source_address or address))
  original_cell=next(c for c in tree.iter(xml.T+'c') if c.attrib['r']==address)
  for child in list(original_cell):original_cell.remove(child)
  original_cell.attrib.pop('t',None)
  if 't' in test.attrib:original_cell.set('t',test.attrib['t'])
  if test.attrib.get('t')=='s':
   # Resolve the Artifact-authored shared string to an inline string for transfer.
   strings=list(ET.fromstring(authored.read('xl/sharedStrings.xml')));i=int(test.find(xml.T+'v').text)
   original_cell.set('t','inlineStr');ET.SubElement(ET.SubElement(original_cell,xml.T+'is'),xml.T+'t').text=''.join(strings[i].itertext())
  else:
   for child in test:original_cell.append(copy.deepcopy(child))
  with ZipFile(destination,'w',ZIP_DEFLATED) as out:
   for item in original.infolist():out.writestr(copy.copy(item),xml.xml(tree) if item.filename==p else original.read(item.filename))
 return destination
def test():
 initial=sources();old=json.loads((ROOT/'powerbi/source_hash_manifest.json').read_text())['snapshot_files']
 with contextlib.redirect_stdout(io.StringIO()):prepare()
 new=json.loads((ROOT/'powerbi/source_hash_manifest.json').read_text())['snapshot_files']
 assert {k:v for k,v in old.items() if k!='EvidenceStatus.csv'}=={k:v for k,v in new.items() if k!='EvidenceStatus.csv'},'Non-deterministic reporting data'
 assert workbook_status()['forward_current']
 zero=workbook_status(inject_test('Zero Override','Scenario Inputs','I9'));assert zero['manual_behaviour_override'] and not zero['forward_current']
 policy=workbook_status(inject_test('Policy Edit','Recommendations','B4'));assert not policy['saved_policy_matches'] and not policy['forward_current']
 selector=workbook_status(inject_test('Selector Case','Scenario Inputs','B3'));assert selector['selected_case']==2 and selector['forward_current']
 stale=workbook_status(inject_test('Stale Capture','Scenario Comparison','D3'));assert not stale['forward_current']
 protocol=workbook_status(inject_test('Zero Override','Experiment Design','B13','I9'));assert not protocol['experiment_saved_protocol_match']
 capture=workbook_status(inject_test('Zero Override','Scenario Comparison','E31','I9'));assert capture['independent_capture_mismatch_count']>0 and not capture['forward_current']
 assert sources()==initial and workbook_status()['selected_case']==1 and workbook_status()['selected_price']==2
 result={'byte_identical_reporting_csvs':len(new)-1,'timestamp_metadata_exception':'EvidenceStatus.csv and validation manifest deliberately record each refresh time','valid_zero_override_suppresses_ranges_and_recommendations':True,'saved_policy_mismatch_suppresses_authority':True,'stale_capture_suppresses_authority':True,'experiment_protocol_mismatch_suppresses_authority':True,'display_selector_change_does_not_change_saved_named_evidence':True,'original_selector_and_evidence_unchanged':True,'native_dax_gating_execution':'pending; status derivation and static DAX guards checked'}
 result['inconsistent_capture_suppresses_authority_without_relying_on_cached_status']=True
 (ROOT/'analysis/powerbi_refresh_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':test()
