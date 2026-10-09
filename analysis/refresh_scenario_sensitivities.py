"""Regenerate the labelled alternatives without rerunning unchanged joint bootstrap draws."""
import json
import numpy as np
import pandas as pd
import scenario_analysis as sa

def main():
    before=sa.input_hashes();model=sa.Model();sa.MODEL=model
    cf=model.simulate(model.primary,0);model.baseline_months=cf
    df=sa.build_sensitivities(model,cf)
    trace=model.simulate(model.primary,2,future_churn=.5,trace=True)[1]
    expected=.5*model.primary[1]*np.log1p(2/model.prices[:,0])/model.primary[3]/model.calibration[0]
    observed=trace[1]['h'][:,model.K+3]-model.dr['standard_churn'][:,1]
    assert np.allclose(expected,observed,atol=1e-12),'Future-joiner response must be half the billed incumbent increment, not half again for notice'
    path=sa.DATA/'scenario_sensitivity.csv';path.write_bytes(df.to_csv(index=False,float_format='%.12g',na_rep='',lineterminator='\n').encode('utf-8'))
    p=json.loads((sa.PRE/'payload.json').read_text());p['sensitivity']=sa.frame_payload(df);(sa.PRE/'payload.json').write_text(json.dumps(p,separators=(',',':')))
    monthly=pd.read_csv(sa.DATA/'scenario_monthly.csv');sites=pd.read_csv(sa.DATA/'gym_scenarios.csv');estate=pd.read_csv(sa.DATA/'estate_scenarios.csv');results=json.loads((sa.AN/'scenario_results.json').read_text())
    # Regenerate prose/dictionary from calculated evidence. Core source files remain untouched.
    core=(sa.PRE/'core_validation.md').read_text()
    sa.CHECKS[:]=[s.removeprefix('- PASS: ') for s in core.splitlines() if s.startswith('- PASS: ')]+['Future-joiner sensitivity exactly half incumbent billing response']
    results['checks_passed']=len(sa.CHECKS);(sa.AN/'scenario_results.json').write_text(json.dumps(results,indent=2))
    sa.documentation(model,monthly,sites,estate,df,results['bridges'],results)
    # Preserve the full earlier validation evidence; the main script remains the complete reproducer.
    assert sa.input_hashes()==before
    print(df[(df.gym_id=='ESTATE')&(df.price_increment==2)][['variant','incremental_revenue','member_impact']].to_string(index=False))

if __name__=='__main__':main()
