"""Verify Phase 6/7 replacement plumbing on a disposable 31-sheet copy.

Reuses previously validated owned-sheet segments. Their forecast and recommendation
engines are unchanged; this verifies preservation, guidance and selector handling.
"""
import json
from zipfile import ZipFile
import experiment_analysis as analysis
import package_recommendations as pack
import append_scenario_sheets as xml
from refresh_scenario_comparison import cells,read_inputs

def main():
    selected=read_inputs();base=pack.OUTPUT;out=analysis.PRE/'refresh_compatibility.xlsx'
    for phase,prefix in [(6,'phase6_refresh_'),(7,'phase7_')]:
        pre=analysis.AN/f'.workbook_previews/phase{phase}'
        source=base if phase==6 else analysis.PRE/'refresh_compatibility_phase6.xlsx'
        target=analysis.PRE/'refresh_compatibility_phase6.xlsx' if phase==6 else out
        pack.graft(source,target,json.loads((pre/'segments.json').read_text(encoding='utf-8')),pre,pre/'final_values.json',pre/'final_formulas.json',analysis.PRE/'guide_updates.json',prefix=prefix)
        with ZipFile(base) as original,ZipFile(target) as z:
            a=xml.sheet_paths(original);b=xml.sheet_paths(z);assert len(b)==31
            for name in ['Experiment Design','Experiment Data','Experiment Results','Monitoring']:assert original.read(a[name])==z.read(b[name]),name
            s=cells(z,b['Scenario Inputs']);assert s['B3']==selected['case'] and s['B4']==selected['price']
            for name,changes in json.loads((analysis.PRE/'guide_updates.json').read_text(encoding='utf-8')).items():
                v=cells(z,b[name]);assert all(v[k]==e for k,e in changes.items())
    report=dict(successful=True,sheet_count=31,phase6_refresh_accepts_current_inputs=True,phase6_and_phase7_preserve_all_four_experiment_sheets=True,phase8_guidance_current=True,selected_case_restored=True,method='Disposable package replacement using previously validated Phase 6/7 Artifact segments; unchanged full forecast engines not redundantly rerun. The actual Phase 8 refresh ran and saved separately.')
    (analysis.PRE/'refresh_compatibility.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
