"""Test changed refresh plumbing with previously validated Phase 6 segments.

The unchanged twelve-case forecast engine was verified in Phase 6; this checks
replacement/preservation on the current 27-sheet package without rerunning it.
"""
import json
from zipfile import ZipFile
import append_scenario_sheets as phase6
import package_recommendations as pack
from refresh_scenario_comparison import read_inputs,cells

def main():
    values=read_inputs();before=pack.OUTPUT;out=pack.PRE/'phase6_refresh_compatibility.xlsx'
    preservation=pack.graft(before,out,json.loads((phase6.PREVIEW/'segments.json').read_text(encoding='utf-8')),phase6.PREVIEW,
        phase6.PREVIEW/'final_values.json',phase6.PREVIEW/'final_formulas.json',None,prefix='phase6_refresh_')
    with ZipFile(before) as original,ZipFile(out) as saved:
        a=phase6.sheet_paths(original);b=phase6.sheet_paths(saved)
        assert len(a)==len(b)==27
        for name in ['Recommendations','Recommendation Summary']:assert original.read(a[name])==saved.read(b[name])
        selected=cells(saved,b['Scenario Inputs']);assert selected['B3']==values['case'] and selected['B4']==values['price']
    result=dict(successful=True,current_27_sheet_input_accepted=True,all_later_sheets_preserved=True,selected_case_restored=True,sheet_count=27,
        method='Changed preservation/replacement plumbing tested using already validated Phase 6 segments. Unchanged full twelve-case forecast calculation not redundantly rerun.',preservation=preservation)
    (pack.PRE/'phase6_refresh_compatibility.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Phase 6 refresh accepts 27 sheets and preserves later recommendation sheets and selection.')

if __name__=='__main__':main()
