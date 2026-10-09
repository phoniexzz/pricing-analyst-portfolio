"""Append Artifact Tool-authored sheets without rebuilding the large source workbook.

Only OOXML packaging, ID remapping and verified formula-cache transfer happen here.
Business formulas and all new styles/charts originate in Artifact Tool.
"""
import copy
import json
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / 'analysis' / '.workbook_previews' / 'phase3'
OUTPUT = ROOT / 'excel' / 'gym_pricing_model.xlsx'
BASE = PREVIEW / 'input_workbook.xlsx'
PARTS = PREVIEW / 'baseline_parts.xlsx'
MAIN = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
RID = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
T = '{'+MAIN+'}'
N = {'s': MAIN}
ADDED = ['Baseline', 'Estate Trends', 'Baseline Summary']
ET.register_namespace('', MAIN)
ET.register_namespace('r', RID)


def xml(e):
    namespace=e.tag.split('}')[0].lstrip('{') if e.tag.startswith('{') else MAIN
    ET.register_namespace('',namespace)
    raw=ET.tostring(e, encoding='utf-8', xml_declaration=True)
    ET.register_namespace('',MAIN)
    return raw


def sheet_paths(z):
    book = ET.fromstring(z.read('xl/workbook.xml'))
    rels = {r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    return {s.attrib['name']:resolve('xl/workbook.xml',rels[s.attrib['{'+RID+'}id']]) for s in book.find(T+'sheets')}


def resolve(part, target):
    return target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(part),target))


def relfile(part):
    folder,base=posixpath.split(part)
    return folder+'/_rels/'+base+'.rels'


def merge_styles(base, part):
    maps={}
    group=base.find(T+'numFmts')
    if group is None:
        group=ET.Element(T+'numFmts');base.insert(0,group)
    known={x.attrib['formatCode']:int(x.attrib['numFmtId']) for x in group}
    num={i:i for i in range(164)}
    for x in list(part.find(T+'numFmts')) if part.find(T+'numFmts') is not None else []:
        old=int(x.attrib['numFmtId']);code=x.attrib['formatCode']
        if code not in known:
            known[code]=max([163]+list(known.values()))+1
            new=copy.deepcopy(x);new.set('numFmtId',str(known[code]));group.append(new)
        num[old]=known[code]
    group.set('count',str(len(group)))
    for name in ['fonts','fills','borders','cellStyleXfs','cellXfs','dxfs']:
        src=part.find(T+name)
        dest=base.find(T+name)
        if dest is None:
            dest=ET.SubElement(base,T+name)
        mapping={};known_items={ET.tostring(x):i for i,x in enumerate(dest)}
        for i,x in enumerate(list(src) if src is not None else []):
            new=copy.deepcopy(x)
            if name in ['cellStyleXfs','cellXfs']:
                for attr,group_name in [('fontId','fonts'),('fillId','fills'),('borderId','borders')]:
                    if attr in new.attrib:new.set(attr,str(maps[group_name][int(new.attrib[attr])]))
                if 'numFmtId' in new.attrib:new.set('numFmtId',str(num[int(new.attrib['numFmtId'])]))
                if name=='cellXfs' and 'xfId' in new.attrib:new.set('xfId',str(maps['cellStyleXfs'][int(new.attrib['xfId'])]))
            raw=ET.tostring(new)
            if raw not in known_items:known_items[raw]=len(dest);dest.append(new)
            mapping[i]=known_items[raw]
        dest.set('count',str(len(dest)));maps[name]=mapping
    return maps


def main():
    if '--update-caches' in sys.argv:
        update_caches();return
    # Keep one ignored recovery copy. Repeated Phase 3 assembly starts from that copy.
    if not BASE.exists():BASE.write_bytes(OUTPUT.read_bytes())
    changed={};preserved=[]
    with ZipFile(BASE) as base, ZipFile(PARTS) as parts:
        old_paths=sheet_paths(base);new_paths=sheet_paths(parts)
        assert not any(name in old_paths for name in ADDED),'Recovery copy must be pre-Phase-3 workbook'
        styles=ET.fromstring(base.read('xl/styles.xml'))
        maps=merge_styles(styles,ET.fromstring(parts.read('xl/styles.xml')))
        changed['xl/styles.xml']=xml(styles)
        strings=[]
        if 'xl/sharedStrings.xml' in parts.namelist():
            strings=list(ET.fromstring(parts.read('xl/sharedStrings.xml')))
        mapped={}
        next_table=max([0]+[int(ET.fromstring(base.read(n)).attrib['id']) for n in base.namelist() if n.startswith('xl/tables/') and n.endswith('.xml')])+1
        def copy_part(part):
            nonlocal next_table
            if part in mapped:return mapped[part]
            folder,name=posixpath.split(part);target=folder+'/phase3_'+name;mapped[part]=target
            raw=parts.read(part)
            if part.endswith('.xml') and part.startswith(('xl/worksheets/','xl/tables/')):
                tree=ET.fromstring(raw)
                if part.startswith('xl/worksheets/'):
                    for node in tree.iter():
                        if node.tag in [T+'c',T+'row',T+'col'] and 's' in node.attrib:node.set('s',str(maps['cellXfs'][int(node.attrib['s'])]))
                        if node.tag==T+'col' and 'style' in node.attrib:node.set('style',str(maps['cellXfs'][int(node.attrib['style'])]))
                        if 'dxfId' in node.attrib:node.set('dxfId',str(maps['dxfs'][int(node.attrib['dxfId'])]))
                        if node.tag==T+'c':
                            node.attrib.pop('cm',None);node.attrib.pop('vm',None)
                            if node.attrib.get('t')=='s':
                                value=node.find(T+'v');si=strings[int(value.text)]
                                node.remove(value);node.set('t','inlineStr');inline=ET.SubElement(node,T+'is')
                                for child in si:inline.append(copy.deepcopy(child))
                if part.startswith('xl/tables/'):
                    tree.set('id',str(next_table));next_table+=1
                raw=xml(tree)
            changed[target]=raw
            source_rels=relfile(part)
            if source_rels in parts.namelist():
                relations=ET.fromstring(parts.read(source_rels))
                for relation in relations:
                    if relation.attrib.get('TargetMode')=='External':continue
                    resolved=resolve(part,relation.attrib['Target']);new_target=copy_part(resolved)
                    relation.set('Target',posixpath.relpath(new_target,posixpath.dirname(target)))
                changed[relfile(target)]=xml(relations)
            return target
        book=ET.fromstring(base.read('xl/workbook.xml'));rels=ET.fromstring(base.read('xl/_rels/workbook.xml.rels'))
        sheets=book.find(T+'sheets');next_sheet=max(int(x.attrib['sheetId']) for x in sheets)+1
        existing_ids={r.attrib['Id'] for r in rels};next_rel=1
        for name in ADDED:
            target=copy_part(new_paths[name])
            while 'rId'+str(next_rel) in existing_ids:next_rel+=1
            rid='rId'+str(next_rel);existing_ids.add(rid)
            ET.SubElement(rels,'{'+REL+'}Relationship',{'Id':rid,'Type':RID+'/worksheet','Target':posixpath.relpath(target,'xl')})
            ET.SubElement(sheets,T+'sheet',{'name':name,'sheetId':str(next_sheet),'{'+RID+'}id':rid});next_sheet+=1
        calc=book.find(T+'calcPr')
        if calc is None:calc=ET.SubElement(book,T+'calcPr')
        calc.set('calcMode','auto');calc.set('fullCalcOnLoad','1')
        changed['xl/workbook.xml']=xml(book);changed['xl/_rels/workbook.xml.rels']=xml(rels)
        ct=ET.fromstring(base.read('[Content_Types].xml'));pct=ET.fromstring(parts.read('[Content_Types].xml'))
        defaults={x.attrib.get('Extension') for x in ct if x.tag.endswith('Default')}
        for x in pct:
            if x.tag.endswith('Override') and x.attrib['PartName'].lstrip('/') in mapped:
                new=copy.deepcopy(x);new.set('PartName','/'+mapped[x.attrib['PartName'].lstrip('/')]);ct.append(new)
            elif x.tag.endswith('Default') and x.attrib['Extension'] not in defaults:ct.append(copy.deepcopy(x));defaults.add(x.attrib['Extension'])
        changed['[Content_Types].xml']=xml(ct)
        # Keep workbook package metadata consistent with its actual sheet list.
        if 'docProps/app.xml' in base.namelist():
            app=ET.fromstring(base.read('docProps/app.xml'))
            an={'a':'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties','v':'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'}
            vector=app.find('a:TitlesOfParts/v:vector',an)
            if vector is not None:
                for name in ADDED:ET.SubElement(vector,'{'+an['v']+'}lpstr').text=name
                vector.set('size',str(len(vector)))
            hp=app.find('a:HeadingPairs/v:vector',an)
            if hp is not None:
                for node in hp.iter('{'+an['v']+'}i4'):node.text=str(len(sheets))
            changed['docProps/app.xml']=xml(app)
        tmp=OUTPUT.with_suffix('.xlsx.tmp')
        with ZipFile(tmp,'w',ZIP_DEFLATED,compresslevel=6) as out:
            for item in base.infolist():
                out.writestr(copy.copy(item),changed.pop(item.filename,base.read(item.filename)))
            for name,raw in changed.items():out.writestr(name,raw)
        tmp.replace(OUTPUT)
        with ZipFile(OUTPUT) as final:
            for name,part in old_paths.items():
                assert final.read(part)==base.read(part),'Unintended change to original '+name
                preserved.append(name)
            for item in base.infolist():
                if item.filename not in ['xl/styles.xml','xl/workbook.xml','xl/_rels/workbook.xml.rels','[Content_Types].xml','docProps/app.xml']:
                    assert final.read(item.filename)==base.read(item.filename),'Unintended change to original feature '+item.filename
    (PREVIEW/'preservation.json').write_text(json.dumps({'existing_sheets_preserved':preserved,'all_original_source_parts_byte_identical':True,'appended_sheets':ADDED},indent=2),encoding='utf-8')
    print('Appended three Artifact Tool sheets; all 13 original sheet parts and native features preserved.')


def update_caches():
    values=json.loads((PREVIEW/'final_values.json').read_text())
    with ZipFile(OUTPUT) as z:
        paths=sheet_paths(z);replacements={}
        repairs=PREVIEW/'style_repairs.xlsx'
        styles=ET.fromstring(z.read('xl/styles.xml'))
        repair_styles={}
        if repairs.exists():
            with ZipFile(repairs) as repaired:
                style_map=merge_styles(styles,ET.fromstring(repaired.read('xl/styles.xml')))['cellXfs']
                repair_sheet=ET.fromstring(repaired.read(sheet_paths(repaired)['Baseline Summary']))
                chosen={'B20','C20','B21','C21','B27','C27','B28','C28','B42'}
                repair_styles={cell.attrib['r']:style_map[int(cell.attrib.get('s','0'))] for cell in repair_sheet.iter(T+'c') if cell.attrib['r'] in chosen}
            replacements['xl/styles.xml']=xml(styles)
        for name,payload in values.items():
            tree=ET.fromstring(z.read(paths[name]));matrix=payload['values']
            for cell in tree.iter(T+'c'):
                if name=='Baseline Summary' and cell.attrib['r'] in repair_styles:cell.set('s',str(repair_styles[cell.attrib['r']]))
                if cell.find(T+'f') is None:continue
                letters=re.match('[A-Z]+',cell.attrib['r']).group();ci=0
                for c in letters:ci=ci*26+ord(c)-64
                ri=int(re.search('[0-9]+$',cell.attrib['r']).group())-1
                actual=matrix[ri][ci-1]
                old=cell.find(T+'v')
                if old is not None:cell.remove(old)
                value=ET.SubElement(cell,T+'v')
                if isinstance(actual,bool):cell.set('t','b');value.text='1' if actual else '0'
                elif isinstance(actual,(int,float)):cell.attrib.pop('t',None);value.text=str(actual)
                else:cell.set('t','str');value.text='' if actual is None else str(actual)
            replacements[paths[name]]=xml(tree)
        # These values were authored through Artifact Tool during final verification.
        for name,changes in json.loads((PREVIEW/'guide_updates.json').read_text()).items():
            tree=ET.fromstring(z.read(paths[name]))
            for cell in tree.iter(T+'c'):
                if cell.attrib['r'] in changes:
                    for child in list(cell):cell.remove(child)
                    cell.set('t','inlineStr');ET.SubElement(ET.SubElement(cell,T+'is'),T+'t').text=changes[cell.attrib['r']]
            replacements[paths[name]]=xml(tree)
        tmp=OUTPUT.with_suffix('.xlsx.tmp')
        with ZipFile(tmp,'w',ZIP_DEFLATED,compresslevel=6) as out:
            for item in z.infolist():out.writestr(copy.copy(item),replacements.get(item.filename,z.read(item.filename)))
    tmp.replace(OUTPUT)
    print('Saved verified recalculated caches and Phase 3 guide updates.')


if __name__=='__main__':main()
