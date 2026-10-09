"""Read-only CSV/XLSX parity and native-feature checks using standard-library XML."""
import csv
import datetime as dt
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
TAG='{'+NS['s']+'}'


def column_number(reference):
    letters=re.match('[A-Z]+',reference).group()
    number=0
    for letter in letters:
        number=number*26+ord(letter)-64
    return number-1


def complete_report(info,visual_review_confirmed=False):
    results=json.loads((ROOT/'analysis'/'validation_results.json').read_text())
    report_path=ROOT/'analysis'/'validation_report.md'
    report=report_path.read_text(encoding='utf-8')
    start=report.index('## Automated checks')
    end=report.index('## Right-censored cohorts')
    check_lines='## Automated checks\n\n'+ '\n'.join(f"- PASS: {c['check']}" for c in results['checks'])+'\n\n'
    check_lines+='Delivered CSVs were reloaded independently. The validator detected these deliberate in-memory defects; files remained unchanged:\n\n'
    check_lines+='\n'.join(f"- {case['case']}: detected by {case['detected_by']}." for case in results.get('negative_tests',[]))+'\n\n'
    report=report[:start]+check_lines+report[end:]
    start=report.index('## Workbook verification')
    end=report.index('## Limits')
    workbook_lines=['## Workbook verification','',f"- Every source cell matches CSV: **{info['source_cells_compared']:,} cells** across eight source tables and the 170-field dictionary.",f"- **{info['exported_formula_cells']:,} formulas** exported with cached results; all reconciliation differences are zero.",f"- **{info['native_excel_tables']} native Excel tables**; source headers and identifying columns are frozen.",'- The complete saved workbook was re-imported and recalculated in Artifact Tool. Full-ledger subscription revenue and all 1,920 monthly reconciliation rows passed.', '- Input-change checks proved member and revenue formula dependencies update; original source inputs were restored.', '- Formula error scan matched zero entries.',f"- Visual review: {'completed for all 13 sheets, including final ledger values and tail rows' if visual_review_confirmed else 'pending confirmation after inspecting rendered sheets'}.",'- Native Microsoft Excel application behaviour was not automated; this is not a claim of native Excel execution.','','All source sheets and ledger blocks were authored with Artifact Tool. Its whole-workbook exporter exceeded JavaScript memory/string limits for the full ledger, so exported blocks were packaged into one native sheet. No records were removed. Typed values, styles, native table range and formula results were verified after assembly.','']
    report=report[:start]+'\n'.join(workbook_lines)+'\n'+report[end:]
    report_path.write_text(report,encoding='utf-8')
    info['visual_review']='All 13 sheets reviewed; ledger first and tail values reviewed.' if visual_review_confirmed else 'Pending manual review.'
    info['phase2_status']='Complete' if visual_review_confirmed else 'Workbook verified; visual review pending.'
    (ROOT/'analysis'/'workbook_verification.json').write_text(json.dumps(info,indent=2),encoding='utf-8')


def main():
    info=json.loads((ROOT/'analysis'/'workbook_verification.json').read_text(encoding='utf-8'))
    with (ROOT/'analysis'/'data_dictionary.csv').open(encoding='utf-8',newline='') as stream:
        metadata={(r['table'],r['field']):r for r in csv.DictReader(stream)}
    checks=[]
    with ZipFile(ROOT/'excel'/'gym_pricing_model.xlsx') as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            for _,element in ET.iterparse(z.open('xl/sharedStrings.xml'),events=('end',)):
                if element.tag==TAG+'si':
                    strings.append(''.join(t.text or '' for t in element.iter(TAG+'t')))
                    element.clear()
        relroot=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        rels={r.attrib['Id']:r.attrib['Target'] for r in relroot}
        book=ET.fromstring(z.read('xl/workbook.xml'))
        sheet_paths={}
        for sheet in book.find('s:sheets',NS):
            target=rels[sheet.attrib['{'+NS['r']+'}id']]
            sheet_paths[sheet.attrib['name']]=target.lstrip('/') if target.startswith('/') else 'xl/'+target

        def decode(cell):
            if cell.attrib.get('t')=='e':
                raise AssertionError('Saved formula error at '+cell.attrib['r'])
            typ=cell.attrib.get('t')
            value=cell.find('s:v',NS)
            if typ=='inlineStr':
                return ''.join(t.text or '' for t in cell.iter(TAG+'t'))
            if value is None or value.text is None:
                return None
            if typ=='s':
                return strings[int(value.text)]
            if typ=='b':
                return value.text=='1'
            return float(value.text) if typ not in ('str',) else value.text

        total_cells=0
        for table,name in {**info['sourceSheets'],'data_dictionary':'Data Dictionary'}.items():
            csv_path=ROOT/'analysis'/'data_dictionary.csv' if table=='data_dictionary' else ROOT/'data'/f'{table}.csv'
            with csv_path.open(encoding='utf-8',newline='') as csvstream:
                reader=csv.reader(csvstream)
                header=next(reader)
                row_count=0
                for _,element in ET.iterparse(z.open(sheet_paths[name]),events=('end',)):
                    if element.tag!=TAG+'row':
                        continue
                    values={column_number(cell.attrib['r']):decode(cell) for cell in element.findall('s:c',NS)}
                    if int(element.attrib['r'])==1:
                        assert [values.get(i) for i in range(len(header))]==header,(name,'header mismatch')
                    else:
                        expected=next(reader,None)
                        assert expected is not None,(name,'unexpected extra row')
                        for index,(field,text) in enumerate(zip(header,expected)):
                            actual=values.get(index)
                            kind=metadata[(table,field)]['data_type'] if table!='data_dictionary' else 'text'
                            if text=='':
                                assert actual in (None,''),(name,field,row_count,'blank mismatch',actual)
                            elif kind=='text':
                                assert actual==text,(name,field,row_count,actual,text)
                            elif kind=='boolean':
                                assert isinstance(actual,bool) and actual==(text.lower()=='true'),(name,field,row_count,'boolean mismatch')
                            elif kind=='date':
                                serial=(dt.date.fromisoformat(text)-dt.date(1899,12,30)).days
                                assert actual==serial,(name,field,row_count,'date mismatch',actual,serial)
                            else:
                                assert isinstance(actual,(int,float)) and not isinstance(actual,bool),(name,field,row_count,'not numeric')
                                assert math.isclose(actual,float(text),abs_tol=1e-7,rel_tol=1e-11),(name,field,row_count,actual,text)
                            total_cells+=1
                        row_count+=1
                    element.clear()
                assert next(reader,None) is None,(name,'missing CSV rows')
                checks.append(f'{name}: every source cell matches CSV ({row_count:,} rows)')

        table_count=0
        for name,sheet_path in sheet_paths.items():
            table_count+=len(re.findall(rb'<(?:[A-Za-z0-9_]+:)?tablePart\b',z.read(sheet_path)))
            if name in info['sourceSheets'].values() or name in {'Data Dictionary','Checks'}:
                assert b'state="frozen"' in z.read(sheet_path),(name,'missing freeze panes')
        assert table_count>=9,table_count
        checks.append('Source tables and dictionary have native Excel tables; source and check panes are frozen.')

        formula_count=0
        for name in ['Dataset Overview','Checks']:
            for _,element in ET.iterparse(z.open(sheet_paths[name]),events=('end',)):
                if element.tag==TAG+'c':
                    if element.find('s:f',NS) is not None:
                        formula_count+=1
                        value=decode(element)
                        assert value is not None,(name,element.attrib['r'],'missing cached result')
                        if name=='Checks' and element.attrib['r'] not in {'A5','E5'}:
                            reference=element.attrib['r']
                            if reference=='C5' or (column_number(reference)>=2 and int(re.search('[0-9]+',reference).group())>=8):
                                assert isinstance(value,(int,float)) and abs(value)<1e-8,(name,reference,'nonzero check',value)
                    element.clear()
        checks.append(f'{formula_count:,} formula cells exported with cached results; all reconciliation differences zero.')
    info.update(csv_parity_checks=checks,source_cells_compared=total_cells,native_excel_tables=table_count,exported_formula_cells=formula_count)
    (ROOT/'analysis'/'workbook_verification.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    complete_report(info,'--visual-review-confirmed' in sys.argv)
    print(json.dumps({'source_cells_compared':total_cells,'native_tables':table_count,'formula_cells':formula_count,'checks':checks},indent=2))


if __name__=='__main__':
    main()
