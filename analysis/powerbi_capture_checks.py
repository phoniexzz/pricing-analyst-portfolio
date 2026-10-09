"""Compare saved workbook captures with approved CSV evidence; no calculations."""
import json,math
import numpy as np
import pandas as pd
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from refresh_scenario_comparison import col

def capture_differences(values):
    layout6=json.loads((ROOT/'analysis/.workbook_previews/phase6/layout.json').read_text())
    layout7=json.loads((ROOT/'analysis/.workbook_previews/phase7/layout.json').read_text())
    specifications=[('Scenario Comparison','gym_scenarios',layout6['captureColumns'],31),
      ('Recommendations','gym_recommendations',layout7['primary'],21),
      ('Recommendation Summary','recommendation_portfolio',layout7['portfolioCols'],131)]
    differences=[];compared=0
    def same(actual,expected):
        if pd.isna(expected):return actual in [None,'']
        if isinstance(expected,(bool,np.bool_)):return actual==expected
        if isinstance(expected,(int,float,np.number)):
            return isinstance(actual,(int,float)) and math.isclose(actual,float(expected),rel_tol=0,abs_tol=max(1e-6,min(.01,abs(float(expected))*1e-10)))
        return actual==expected
    for sheet,source,columns,first in specifications:
        csv=pd.read_csv(ROOT/'data'/f'{source}.csv')
        # Narrative strings may have workbook-specific formatting. Check every
        # numerical/boolean capture and the key/action/status classification.
        fields=[f for f in columns if f in csv and (pd.api.types.is_numeric_dtype(csv[f]) or pd.api.types.is_bool_dtype(csv[f]) or f in {'gym_id','variant','case','action','rule_id'})]
        cells=values[sheet]
        for i,row in enumerate(csv.to_dict('records')):
            for f in fields:
                address=col(columns.index(f))+str(first+i);compared+=1
                if not same(cells.get(address),row[f]):differences.append({'sheet':sheet,'cell':address,'field':f,'actual':cells.get(address),'expected':row[f]})
    return compared,differences

if __name__=='__main__':
    from zipfile import ZipFile
    from refresh_scenario_comparison import cells
    import append_scenario_sheets as xml
    with ZipFile(ROOT/'excel/gym_pricing_model.xlsx') as z:
        paths=xml.sheet_paths(z);values={s:cells(z,paths[s]) for s in ['Scenario Comparison','Recommendations','Recommendation Summary']}
    n,d=capture_differences(values)
    print(json.dumps({'checked_cells':n,'difference_count':len(d),'examples':d[:20]},indent=2,default=str))
