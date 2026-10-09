"""Package four Artifact-authored experiment sheets from the fresh Phase 7 copy."""
import json
import experiment_analysis as analysis
import package_recommendations as pack

if __name__=='__main__':
    p=analysis.PRE
    result=pack.graft(p/'input_workbook.xlsx',pack.OUTPUT,json.loads((p/'segments.json').read_text(encoding='utf-8')),p,p/'final_values.json',p/'final_formulas.json',p/'guide_updates.json',prefix='phase8_')
    (p/'preservation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Saved 31 sheets; prior 27 sheets and native resources preserved apart from authorised guidance updates.')
