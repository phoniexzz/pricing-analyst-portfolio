"""Re-validate delivered CSVs and prove failures are detected without editing them."""
import json
from pathlib import Path
import pandas as pd
from generate_synthetic_data import validate

ROOT=Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/'analysis'/'generation_config.json').read_text())
frames={p.stem:pd.read_csv(p) for p in sorted((ROOT/'data').glob('*.csv'))}
checks=validate(frames,cfg)
negative=[]
for table,index,field,increment,label in [
    ('monthly_performance',100,'closing_members',1,'Incorrect gym membership bridge'),
    ('membership_ledger',100,'opening_base_cancellations',100000,'Cancellations larger than eligible pool'),
    ('monthly_performance',100,'monthly_revenue',1,'Incorrect total revenue'),
]:
    original=frames[table].loc[index,field]
    frames[table].loc[index,field]=original+increment
    try:
        validate(frames,cfg)
    except AssertionError as error:
        negative.append({'case':label,'detected_by':str(error),'passed':True})
    else:
        raise AssertionError('Failed to detect: '+label)
    finally:
        frames[table].loc[index,field]=original

validation=json.loads((ROOT/'analysis'/'validation_results.json').read_text())
validation['checks']=[c for c in validation['checks'] if c['check'] not in {r['check'] for r in checks}]+checks
validation['csv_reload_validation']='All delivered CSVs independently reloaded and reconciled.'
validation['negative_tests']=negative
(ROOT/'analysis'/'validation_results.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
print(json.dumps({'csv_checks_passed':len(checks),'intentional_defects_detected':negative},indent=2))
