"""Refresh policy classifications and shared-draw portfolio captures, preserving all sheets."""
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile
import recommendation_analysis as analysis
import package_recommendations as pack
from refresh_scenario_comparison import cells
import append_scenario_sheets as xml

ROOT=Path(__file__).resolve().parents[1];PRE=ROOT/'analysis/.workbook_previews/phase7'
NODE=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'

def finish(preservation,selected,available):
    with ZipFile(pack.OUTPUT) as z:
        paths=xml.sheet_paths(z);saved=cells(z,paths['Scenario Inputs']);assert (saved.get('B3'),saved.get('B4'))==selected
        summary=cells(z,paths['Recommendation Summary']);assert summary['E5']==('CURRENT' if available else 'UNAVAILABLE')
    result=dict(successful=True,selected_case_restored=True,selected_case=selected[0],selected_price=selected[1],evidence_available=available,portfolio_status=summary['E5'],sheet_count=len(paths),preservation=preservation)
    (PRE/'refresh_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Recommendation policy refresh complete; shared portfolio captures current and selected scenario restored.' if available else 'Recommendations recalculated; evidence unavailable and authoritative outputs suppressed.')
    return result

def refresh(allow_unavailable=False):
    output=pack.OUTPUT;payload=json.loads((PRE/'payload.json').read_text(encoding='utf-8'))
    with ZipFile(output) as z:
        paths=xml.sheet_paths(z);assert 'Recommendations' in paths and len(paths)>=27
        r=cells(z,paths['Recommendations']);s=cells(z,paths['Scenario Inputs']);c=cells(z,paths['Scenario Comparison'])
        policy=dict(member_loss_limit=r.get('B4'),minimum_gap=r.get('B5'),test_repeats=r.get('B6')==1)
        assert all(analysis.finite(policy[k]) for k in ['member_loss_limit','minimum_gap']) and 0<=policy['member_loss_limit']<=1 and policy['minimum_gap']>=0 and r.get('B6') in [0,1], 'Invalid policy inputs'
        selected=(s.get('B3'),s.get('B4'));available=c.get('D3')=='CURRENT' and s.get('E23')==0 and all(s.get('I'+str(i)) is None for i in range(9,18))
        if not available and not allow_unavailable:raise ValueError('Scenario evidence unavailable. Refresh/rerun Phase 6 evidence before portfolio uncertainty.')
        # Retained joint draws apply only to evidence-derived comparisons.
        if available:
            original=payload['sources']['Scenario Comparison']
            for address,value in original.items():
                if address.startswith(('A','B','C')) or not isinstance(value,(int,float)) or isinstance(value,bool):continue
                current=c.get(address)
                if not analysis.finite(current) or abs(value-current)>max(1e-7,abs(value)*1e-10):
                    raise ValueError('Saved comparison differs from retained Phase 6 evidence: '+address)
    evidence=analysis.Evidence();captures={};portfolio=[]
    for variant in analysis.CFG['variants']:
        q=evidence.recommend(variant,policy);captures[variant]=q.set_index('gym_id').proposed_increment.to_dict()
        for case in analysis.CFG['cases']:
            p=evidence.portfolio(q,case)
            if not available:
                for f in list(p):
                    if f.endswith(('_lower','_upper')) or f=='positive_revenue_draw_fraction':p[f]=None
            portfolio.append(p)
    base=PRE/'refresh_base.xlsx';base.write_bytes(output.read_bytes())
    # Use actual current saved source caches, preserving the 25 earlier sheets as a fresh base.
    payload['sources']=analysis.source_blocks();(PRE/'payload.json').write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8')
    (PRE/'refresh_inputs.json').write_text(json.dumps(dict(**policy,captures=captures,portfolio=portfolio,selected_case=selected[0],selected_price=selected[1],evidence_available=available),separators=(',',':')),encoding='utf-8')
    subprocess.run([str(NODE),'--max-old-space-size=16384',str(ROOT/'analysis/build_recommendation_workbook.mjs'),'--refresh'],cwd=ROOT,check=True)
    phase8_guides=ROOT/'analysis/.workbook_previews/phase8/guide_updates.json'
    with ZipFile(base) as z:has_experiment='Experiment Results' in xml.sheet_paths(z)
    preservation=pack.graft(base,output,json.loads((PRE/'segments.json').read_text(encoding='utf-8')),PRE,PRE/'final_values.json',PRE/'final_formulas.json',phase8_guides if has_experiment else PRE/'guide_updates.json')
    result=finish(preservation,selected,available)
    if has_experiment:
        from refresh_experiment_workbook import refresh as refresh_experiment
        result['experiment_refresh']=refresh_experiment()
    return result

if __name__=='__main__':
    if '--finish' in sys.argv:
        inputs=json.loads((PRE/'refresh_inputs.json').read_text(encoding='utf-8'))
        with ZipFile(PRE/'refresh_base.xlsx') as z:has_experiment='Experiment Results' in xml.sheet_paths(z)
        guides=ROOT/'analysis/.workbook_previews/phase8/guide_updates.json' if has_experiment else PRE/'guide_updates.json'
        preserved=pack.graft(PRE/'refresh_base.xlsx',pack.OUTPUT,json.loads((PRE/'segments.json').read_text(encoding='utf-8')),PRE,PRE/'final_values.json',PRE/'final_formulas.json',guides)
        finish(preserved,(inputs['selected_case'],inputs['selected_price']),inputs['evidence_available'])
        if has_experiment:
            from refresh_experiment_workbook import refresh as refresh_experiment
            refresh_experiment()
    else:refresh()
