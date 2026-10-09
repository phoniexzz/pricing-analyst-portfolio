"""A native acceptance applies only to the exact saved project and snapshot."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def fingerprint():
 paths=[]
 for base in ['Northstar.Report','Northstar.SemanticModel']:
  paths += [p for p in (ROOT/'powerbi'/base).rglob('*') if p.is_file() and '.pbi' not in p.parts and p.suffix in {'.json','.tmdl','.pbir','.pbism'}]
 paths += [ROOT/'powerbi/gym_pricing_dashboard.pbip']
 paths += list((ROOT/'powerbi/model_data').glob('*.csv'))
 return hashlib.sha256(json.dumps({str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},sort_keys=True).encode()).hexdigest()
def accepted():
 path=ROOT/'analysis/powerbi_native_acceptance.json'
 if not path.exists():return None
 proof=json.loads(path.read_text())
 if proof.get('status')!='Phase 9 native verification complete' or proof.get('project_fingerprint')!=fingerprint():return None
 return proof
def update_docs():
 proof=accepted()
 if not proof:return
 native=ROOT/'analysis/powerbi_native_validation.md'
 for p in [ROOT/'powerbi/README.md',ROOT/'powerbi/SETUP.md',ROOT/'analysis/powerbi_dashboard_specification.md']:
  text=p.read_text(encoding='utf-8')
  text=text.replace('Phase 9 build-ready; native verification pending.','Phase 9 native verification complete.')
  text=text.replace('Native verification is pending. Power BI Desktop was not found locally. No PBIX has been created.','Native verification completed in Power BI Desktop 2.158.1177.0. `gym_pricing_dashboard.pbix` was created through native Save As. See the native acceptance record.')
  text=text.replace('Native acceptance remains the checklist in `powerbi/NATIVE_VERIFICATION.md`.','Native acceptance is documented in `powerbi/NATIVE_VERIFICATION.md` and `analysis/powerbi_native_validation.md`.')
  if 'Native acceptance record' not in text:text+='\n\nNative acceptance record: [verification report](../analysis/powerbi_native_validation.md). Native screenshots are in `images/native_powerbi`, separate from design previews. Later project or snapshot refreshes require a new native check.\n'
  p.write_text(text,encoding='utf-8')
 (ROOT/'powerbi/NATIVE_VERIFICATION.md').write_text(native.read_text(encoding='utf-8'),encoding='utf-8')
 checks=ROOT/'powerbi/DAX_checks.dax';checks.write_text(checks.read_text(encoding='utf-8').replace('These queries have NOT been executed locally.','Executed against the native Desktop engine; results: analysis/powerbi_native_dax_results.json.'),encoding='utf-8')
 import pandas as pd
 d=ROOT/'analysis/powerbi_metric_dictionary.csv';frame=pd.read_csv(d);frame['native_execution']='Executed in Desktop 2.158.1177.0; 296 measures; see native validation';frame.to_csv(d,index=False)
 (ROOT/'analysis/powerbi_validation.md').write_text(native.read_text(encoding='utf-8'),encoding='utf-8')
