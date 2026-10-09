"""Package Artifact Tool exports into one workbook; no business formulas authored here.

Ledger cells, styles and types originate in Artifact Tool block exports. Standard-
library OOXML packaging avoids its single-string export limit for large workbooks.
"""
import copy
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
PARTS=ROOT/'analysis'/'.workbook_previews'/'parts'
OUTPUT=ROOT/'excel'/'gym_pricing_model.xlsx'
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
N={'s':NS,'r':REL}
T='{'+NS+'}'
ET.register_namespace('',NS)
ET.register_namespace('r',REL)


def sheet_path(z,name):
    book=ET.fromstring(z.read('xl/workbook.xml'))
    relations={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    sheet=next(s for s in book.find('s:sheets',N) if s.attrib['name']==name)
    target=relations[sheet.attrib['{'+REL+'}id']]
    return target.lstrip('/') if target.startswith('/') else 'xl/'+target


def bytes_xml(element):
    return ET.tostring(element,encoding='utf-8',xml_declaration=True)


def update_caches():
    cache=json.loads((ROOT/'analysis'/'final_formula_cache.json').read_text())
    replacements={}
    with ZipFile(OUTPUT) as z:
        for name,values in cache.items():
            p=sheet_path(z,name)
            tree=ET.fromstring(z.read(p))
            for cell in tree.iter(T+'c'):
                if cell.attrib['r'] in values:
                    assert cell.find(T+'f') is not None
                    value=cell.find(T+'v')
                    if value is None:
                        value=ET.SubElement(cell,T+'v')
                    value.text=str(values[cell.attrib['r']])
            replacements[p]=bytes_xml(tree)
        tmp=OUTPUT.with_suffix('.xlsx.tmp')
        with ZipFile(tmp,'w',ZIP_DEFLATED,compresslevel=6) as out:
            for item in z.infolist():
                out.writestr(item,replacements.get(item.filename,z.read(item.filename)))
    tmp.replace(OUTPUT)
    print('Saved recalculated formula caches from Artifact Tool verification.')


def main():
    if '--update-caches' in sys.argv:
        update_caches()
        return
    payload=json.loads((ROOT/'analysis'/'workbook_data.json').read_text(encoding='utf-8'))
    expected=len(payload['membership_ledger']['data'])
    columns=len(payload['membership_ledger']['columns'])
    block_size=6000
    suffix=''
    for num in [columns]:
        while num:
            num,rem=divmod(num-1,26)
            suffix=chr(65+rem)+suffix
    final_ref=f'A1:{suffix}{expected+1}'
    with ZipFile(PARTS/'core.xlsx') as core:
        styles=ET.fromstring(core.read('xl/styles.xml'))
        shared=ET.fromstring(core.read('xl/sharedStrings.xml'))
        shared_index={ET.tostring(si):i for i,si in enumerate(shared)}
        ledger_path=sheet_path(core,'Membership Ledger')
        tree=ET.fromstring(core.read(ledger_path))
        dimension=tree.find(T+'dimension')
        if dimension is not None:
            dimension.set('ref',final_ref)
        sheetdata=tree.find(T+'sheetData')
        first_rows=list(sheetdata)
        for row in first_rows:
            for cell in row.findall(T+'c'):
                # Value metadata is optional; keep portable, typed boolean values.
                cell.attrib.pop('cm',None)
                cell.attrib.pop('vm',None)
        sheetdata.clear()
        template=ET.tostring(tree,encoding='utf-8')
        marker=b'<sheetData />'
        assert marker in template,'Missing sheetData export marker'
        before,after=template.split(marker,1)
        ledger_xml=PARTS/'assembled_ledger.xml'
        count=0

        def merge_styles(partstyles):
            number_formats=styles.find(T+'numFmts')
            if number_formats is None:
                number_formats=ET.Element(T+'numFmts',{'count':'0'})
                styles.insert(0,number_formats)
            known={f.attrib['formatCode']:int(f.attrib['numFmtId']) for f in number_formats}
            num_map={i:i for i in range(164)}
            part_num_formats=partstyles.find(T+'numFmts')
            for f in (list(part_num_formats) if part_num_formats is not None else []):
                code=f.attrib['formatCode']
                old=int(f.attrib['numFmtId'])
                if code not in known:
                    known[code]=max([163]+list(known.values()))+1
                    item=copy.deepcopy(f);item.set('numFmtId',str(known[code]));number_formats.append(item)
                num_map[old]=known[code]
            number_formats.set('count',str(len(number_formats)))
            maps={}
            for group in ['fonts','fills','borders']:
                target=styles.find(T+group)
                existing={ET.tostring(item):i for i,item in enumerate(target)}
                mapping={}
                for i,item in enumerate(partstyles.find(T+group)):
                    raw=ET.tostring(item)
                    if raw not in existing:
                        existing[raw]=len(target);target.append(copy.deepcopy(item))
                    mapping[i]=existing[raw]
                target.set('count',str(len(target)));maps[group]=mapping
            xf_map={}
            for group in ['cellStyleXfs','cellXfs']:
                target=styles.find(T+group)
                existing={ET.tostring(item):i for i,item in enumerate(target)}
                mapping={}
                for i,old in enumerate(partstyles.find(T+group)):
                    item=copy.deepcopy(old)
                    for attribute,category in [('fontId','fonts'),('fillId','fills'),('borderId','borders')]:
                        if attribute in item.attrib:
                            item.set(attribute,str(maps[category][int(item.attrib[attribute])]))
                    if 'numFmtId' in item.attrib:
                        item.set('numFmtId',str(num_map[int(item.attrib['numFmtId'])]))
                    if group=='cellXfs' and 'xfId' in item.attrib:
                        item.set('xfId',str(xf_map[int(item.attrib['xfId'])]))
                    raw=ET.tostring(item)
                    if raw not in existing:
                        existing[raw]=len(target);target.append(item)
                    mapping[i]=existing[raw]
                target.set('count',str(len(target)))
                if group=='cellStyleXfs':
                    xf_map=mapping
                else:
                    return mapping

        with ledger_xml.open('wb') as stream:
            stream.write(b'<?xml version="1.0" encoding="UTF-8"?>\n'+before+b'<sheetData>')
            for row in first_rows:
                stream.write(ET.tostring(row,encoding='utf-8'))
            count=len(first_rows)-1
            for start in range(block_size,expected,block_size):
                with ZipFile(PARTS/f'ledger_{start}.xlsx') as part:
                    style_map=merge_styles(ET.fromstring(part.read('xl/styles.xml')))
                    string_map={}
                    for i,si in enumerate(ET.fromstring(part.read('xl/sharedStrings.xml'))):
                        raw=ET.tostring(si)
                        if raw not in shared_index:
                            shared_index[raw]=len(shared);shared.append(copy.deepcopy(si))
                        string_map[i]=shared_index[raw]
                    p=sheet_path(part,'Membership Ledger')
                    for _,row in ET.iterparse(part.open(p),events=('end',)):
                        if row.tag!=T+'row':
                            continue
                        original_row=int(row.attrib['r'])
                        if original_row==1:
                            row.clear();continue
                        final_row=original_row+start
                        row.set('r',str(final_row))
                        for cell in row.findall(T+'c'):
                            cell.set('r',re.sub('[0-9]+$',str(final_row),cell.attrib['r']))
                            if 's' in cell.attrib:
                                cell.set('s',str(style_map[int(cell.attrib['s'])]))
                            if cell.attrib.get('t')=='s':
                                value=cell.find(T+'v');value.text=str(string_map[int(value.text)])
                            cell.attrib.pop('cm',None);cell.attrib.pop('vm',None)
                        stream.write(ET.tostring(row,encoding='utf-8'))
                        count+=1;row.clear()
                print(f'Assembled {count:,} ledger rows',flush=True)
            stream.write(b'</sheetData>'+after)
        assert count==expected,(count,expected)
        shared.set('uniqueCount',str(len(shared)))
        shared.attrib.pop('count',None)
        replacements={'xl/styles.xml':bytes_xml(styles),'xl/sharedStrings.xml':bytes_xml(shared)}
        # Preserve the core's native Excel table and extend its range to all blocks.
        for filename in core.namelist():
            if filename.startswith('xl/tables/') and filename.endswith('.xml'):
                table=ET.fromstring(core.read(filename))
                if table.attrib.get('name')=='Source_membership_ledger':
                    table.set('ref',final_ref)
                    af=table.find(T+'autoFilter')
                    if af is not None:af.set('ref',final_ref)
                    replacements[filename]=bytes_xml(table)
        book=ET.fromstring(core.read('xl/workbook.xml'))
        calc=book.find(T+'calcPr')
        if calc is None:calc=ET.SubElement(book,T+'calcPr')
        calc.set('calcMode','auto');calc.set('fullCalcOnLoad','1')
        replacements['xl/workbook.xml']=bytes_xml(book)
        tmp=OUTPUT.with_suffix('.xlsx.tmp')
        with ZipFile(tmp,'w',ZIP_DEFLATED,compresslevel=6) as out:
            for item in core.infolist():
                if item.filename==ledger_path:
                    out.write(ledger_xml,ledger_path)
                else:
                    out.writestr(item,replacements.get(item.filename,core.read(item.filename)))
    tmp.replace(OUTPUT)
    print(f'Saved full workbook with {count:,} ledger rows; next verify and refresh caches.')


if __name__=='__main__':
    main()
