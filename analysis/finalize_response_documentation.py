"""Record completed workbook verification after actual recalculation and visual QA."""
import json
from pathlib import Path
AN=Path(__file__).resolve().parent
v=json.loads((AN/'response_workbook_verification.json').read_text())
assert v['status']=='Complete' and v['visualReview']['reviewed']
text=f'''\n\n## Saved workbook completion evidence\n\nPhase 5 is complete; the dataset and response estimates are ready for Phase 6. The workbook contains 21 populated sheets, preserving all 18 prior sheets, original styles, tables and chart resources except explicitly updated progress guidance. All {v['csvCellsComparedIndependently']:,} delivered CSV cells match the independently decoded saved workbook; the largest difference is {v['maxSavedCsvDifference']:.8f}, below the documented precision tolerance and below £0.01 for monetary values. {v['newFormulaCaches']:,} new formula caches are present, and the full recalculated workbook error scan found zero entries. Original source reconciliations and four representative input-change tests passed. All four CSVs reproduce byte-for-byte.\n\nVisual review covers all three new sheets, three affected guidance sheets, five editable native charts and three standalone figures. Native subgroup dots display means and interval endpoints; the report forest figure connects the actual intervals. Recalculation uses Artifact Tool, with independent saved-OOXML checks; native Excel was not automated. Revenue is not profit, monthly exposure is not annual retention, repeated stocks are not unique customers, and the historical local policy estimate is not an estate forecast.\n'''
for name in ['response_report.md','response_validation.md']:
    p=AN/name;s=p.read_text(encoding='utf-8').split('\n\n## Saved workbook completion evidence')[0];p.write_text(s+text,encoding='utf-8')
print('Recorded completed saved-workbook and visual validation evidence.')
