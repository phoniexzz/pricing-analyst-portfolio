"""Refresh live Phase 8 policy decisions while preserving all workbook sheets.

Guardrails are editable policy. Assignment, simulation and inference changes
require rerunning experiment_analysis.py with an explicitly revised configuration.
This refresh never changes observed source CSVs or creates new simulation evidence.
"""
import json
import subprocess
from zipfile import ZipFile
from pathlib import Path
import experiment_analysis as analysis
import package_recommendations as pack
import append_scenario_sheets as xml
from refresh_scenario_comparison import cells

ROOT=analysis.ROOT;PRE=analysis.PRE
NODE=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'

def refresh():
    payload=json.loads((PRE/'payload.json').read_text(encoding='utf-8'))
    evidence=json.loads((ROOT/'analysis/experiment_results.json').read_text(encoding='utf-8'))
    assert analysis.hashes()==evidence['input_hashes'], 'Prior evidence changed; rerun experiment analysis first'
    assert analysis.CFG==payload['config'], 'Experiment configuration changed; rerun experiment analysis first'
    with ZipFile(pack.OUTPUT) as z:
        paths=xml.sheet_paths(z);assert len(paths)>=31 and 'Experiment Results' in paths
        d=cells(z,paths['Experiment Design']);s=cells(z,paths['Scenario Inputs'])
        selected=(s['B3'],s['B4']);guard=[d.get('B'+str(r)) for r in range(4,11)]
        if any(not isinstance(v,(int,float)) or isinstance(v,bool) for v in guard):raise ValueError('Unavailable guardrail; provide valid numerical policy values')
        if not(0<=guard[0]<=1 and 0<=guard[1]<=1 and all(v>=0 for v in guard[2:5]) and guard[5]>0 and 0<guard[6]<1):raise ValueError('Invalid policy limits')
        expected=[1,analysis.CFG['seed'],10000,46023,46054]
        if [d.get('B'+str(r)) for r in range(12,17)]!=expected:raise ValueError('Protocol inputs changed; revise configuration and rerun matching/simulation/inference before refresh')
        # Imported simulation observations are immutable captures. Allow policy
        # edits only; edited observations require new inference rather than reuse.
        layout=json.loads((PRE/'layout.json').read_text(encoding='utf-8'))
        actual=cells(z,paths['Experiment Data']);original=json.loads((PRE/'final_values.json').read_text(encoding='utf-8'))['Experiment Data']['values']
        from refresh_scenario_comparison import col
        for row in range(21,777):
            for j in range(len(layout['monthly_columns'])):
                v=actual.get(col(j)+str(row));e=original[row-1][j]
                if isinstance(e,(int,float)) and not isinstance(e,bool):
                    if not isinstance(v,(int,float)) or abs(v-e)>max(1e-8,abs(e)*1e-10):raise ValueError('Experiment outcome changed; rerun inference before refresh')
                elif v!=e and not(v is None and e==''):raise ValueError('Experiment input changed; rerun analysis before refresh')
    base=PRE/'refresh_base.xlsx';base.write_bytes(pack.OUTPUT.read_bytes())
    payload['sources']=analysis.source_blocks();(PRE/'payload.json').write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8')
    (PRE/'refresh_inputs.json').write_text(json.dumps(dict(guardrails=guard,selected_case=selected[0],selected_price=selected[1])),encoding='utf-8')
    subprocess.run([str(NODE),'--max-old-space-size=16384',str(ROOT/'analysis/build_experiment_workbook.mjs'),'--refresh'],cwd=ROOT,check=True)
    subprocess.run([str(NODE),'--max-old-space-size=16384',str(ROOT/'analysis/style_experiment_segments.mjs')],cwd=ROOT,check=True)
    preservation=pack.graft(base,pack.OUTPUT,json.loads((PRE/'segments.json').read_text(encoding='utf-8')),PRE,PRE/'final_values.json',PRE/'final_formulas.json',PRE/'guide_updates.json',prefix='phase8_')
    with ZipFile(pack.OUTPUT) as z:
        paths=xml.sheet_paths(z);s=cells(z,paths['Scenario Inputs']);r=cells(z,paths['Experiment Results']);d=cells(z,paths['Experiment Design'])
        assert (s['B3'],s['B4'])==selected and len(paths)>=31
    result=dict(successful=True,selected_case_restored=True,selected_case=selected[0],selected_price=selected[1],sheet_count=len(paths),capture_status=r['F4'],guardrails=guard,preservation=preservation)
    (PRE/'refresh_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Experiment policy refresh saved; all earlier sheets and scenario selector preserved. Status: '+r['F4'])
    return result

if __name__=='__main__':refresh()
