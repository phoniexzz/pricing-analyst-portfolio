"""Re-run the complete Phase 5 analysis and compare all four delivered CSVs."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES=['historical_response_panel','historical_event_response','pilot_pair_response','price_response_estimates']
def hashes():return {name:hashlib.sha256((ROOT/'data'/(name+'.csv')).read_bytes()).hexdigest() for name in NAMES}
before=hashes()
subprocess.run([sys.executable,str(ROOT/'analysis'/'response_analysis.py')],check=True,stdout=subprocess.DEVNULL)
after=hashes()
assert before==after,'Phase 5 output changed under identical inputs/configuration'
info={'all_four_csvs_byte_identical':True,'hashes':after,'bootstrap_seed':20261005,'whole_pair_samples':10000}
(ROOT/'analysis'/'.workbook_previews'/'phase5'/'reproducibility.json').write_text(json.dumps(info,indent=2))
print(json.dumps(info,indent=2))
