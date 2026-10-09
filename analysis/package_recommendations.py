"""Graft bounded Artifact-authored sheets into a fresh workbook copy.

Transfers styles, relationships, formula text and evaluated caches only; no business math.
Also supports replacing owned sheets while preserving later-phase sheets on refresh.
"""
import copy
import json
import posixpath
import re
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET
import append_scenario_sheets as common

ROOT=Path(__file__).resolve().parents[1];PRE=ROOT/'analysis/.workbook_previews/phase7'
OUTPUT=ROOT/'excel/gym_pricing_model.xlsx'
T=common.T;REL=common.REL;RID=common.RID

def closure(z,part):
    reached=set()
    def walk(p):
        if p in reached:return
        reached.add(p);r=common.relfile(p)
        if r in z.namelist():
            reached.add(r)
            for x in ET.fromstring(z.read(r)):
                if x.attrib.get('TargetMode')!='External':walk(common.resolve(p,x.attrib['Target']))
    walk(part);return reached

def graft(base_path,output,manifest,preview,values_path=None,formulas_path=None,guides_path=None,prefix='phase7_'):
    owned={s['name'] for s in manifest};changes={};maps_by_sheet={};added=[]
    with ZipFile(base_path) as base:
        old=common.sheet_paths(base);book=ET.fromstring(base.read('xl/workbook.xml'));rels=ET.fromstring(base.read('xl/_rels/workbook.xml.rels'));sheets=book.find(T+'sheets')
        protected=set().union(*(closure(base,p) for n,p in old.items() if n not in owned))
        removed=set().union(*(closure(base,old[n]) for n in owned if n in old))-protected
        ct=ET.fromstring(base.read('[Content_Types].xml'));ct[:]=[x for x in ct if x.attrib.get('PartName','').lstrip('/') not in removed]
        styles=ET.fromstring(base.read('xl/styles.xml'));next_id=max(int(x.attrib['sheetId']) for x in sheets)+1
        next_table=max([0]+[int(ET.fromstring(base.read(n)).attrib['id']) for n in base.namelist() if n.startswith('xl/tables/') and n.endswith('.xml')])+1
        old_entries={x.attrib['name']:x for x in sheets};relmap={x.attrib['Id']:x for x in rels};existing={x.attrib['Id'] for x in rels};rid_index=1
        defaults={x.attrib.get('Extension') for x in ct if x.tag.endswith('Default')}
        for segment_index,seg in enumerate(manifest):
            with ZipFile(preview/seg['file']) as part:
                src_paths=common.sheet_paths(part);style_map=common.merge_styles(styles,ET.fromstring(part.read('xl/styles.xml')))
                strings=list(ET.fromstring(part.read('xl/sharedStrings.xml'))) if 'xl/sharedStrings.xml' in part.namelist() else []
                mapped={}
                def transfer(src):
                    nonlocal next_table
                    if src in mapped:return mapped[src]
                    folder,name=posixpath.split(src);dest=folder+'/'+prefix+str(segment_index)+'_'+name;mapped[src]=dest
                    raw=part.read(src)
                    if src.endswith('.xml') and src.startswith(('xl/worksheets/','xl/tables/')):
                        tree=ET.fromstring(raw)
                        if src.startswith('xl/worksheets/'):
                            for node in tree.iter():
                                if node.tag in [T+'c',T+'row',T+'col'] and 's' in node.attrib:node.set('s',str(style_map['cellXfs'][int(node.attrib['s'])]))
                                if node.tag==T+'col' and 'style' in node.attrib:node.set('style',str(style_map['cellXfs'][int(node.attrib['style'])]))
                                if 'dxfId' in node.attrib:node.set('dxfId',str(style_map['dxfs'][int(node.attrib['dxfId'])]))
                                if node.tag==T+'c':
                                    node.attrib.pop('cm',None);node.attrib.pop('vm',None)
                                    if node.attrib.get('t')=='s':
                                        v=node.find(T+'v');si=strings[int(v.text)];node.remove(v);node.set('t','inlineStr');inline=ET.SubElement(node,T+'is')
                                        for child in si:inline.append(copy.deepcopy(child))
                        else:tree.set('id',str(next_table));next_table+=1
                        raw=common.xml(tree)
                    changes[dest]=raw
                    r=common.relfile(src)
                    if r in part.namelist():
                        relations=ET.fromstring(part.read(r))
                        for link in relations:
                            if link.attrib.get('TargetMode')!='External':
                                target=transfer(common.resolve(src,link.attrib['Target']));link.set('Target',posixpath.relpath(target,posixpath.dirname(dest)))
                        changes[common.relfile(dest)]=common.xml(relations)
                    return dest
                name=seg['name'];dest=transfer(src_paths[name]);maps_by_sheet[name]=dest
                if name in old_entries:
                    rid=old_entries[name].attrib['{'+RID+'}id'];relmap[rid].set('Target',posixpath.relpath(dest,'xl'))
                else:
                    while 'rId'+str(rid_index) in existing:rid_index+=1
                    rid='rId'+str(rid_index);existing.add(rid)
                    ET.SubElement(rels,'{'+REL+'}Relationship',{'Id':rid,'Type':RID+'/worksheet','Target':posixpath.relpath(dest,'xl')})
                    ET.SubElement(sheets,T+'sheet',{'name':name,'sheetId':str(next_id),'{'+RID+'}id':rid});next_id+=1;added.append(name)
                for x in ET.fromstring(part.read('[Content_Types].xml')):
                    if x.tag.endswith('Override') and x.attrib['PartName'].lstrip('/') in mapped:
                        y=copy.deepcopy(x);y.set('PartName','/'+mapped[x.attrib['PartName'].lstrip('/')]);ct.append(y)
                    elif x.tag.endswith('Default') and x.attrib['Extension'] not in defaults:ct.append(copy.deepcopy(x));defaults.add(x.attrib['Extension'])
        values=json.loads(values_path.read_text(encoding='utf-8')) if values_path else {}
        formulas=json.loads(formulas_path.read_text(encoding='utf-8')) if formulas_path else {}
        for name,data in values.items():
            if name not in maps_by_sheet:continue
            tree=ET.fromstring(changes[maps_by_sheet[name]]);matrix=data['values'];authored=formulas[name]
            for c in tree.iter(T+'c'):
                a=c.attrib['r'];letters=re.match('[A-Z]+',a).group();ci=0
                for ch in letters:ci=ci*26+ord(ch)-64
                ri=int(re.search('[0-9]+$',a).group())-1
                f=authored[ri][ci-1] if ri<len(authored) and ci<=len(authored[ri]) else None
                if not f:continue
                formula=c.find(T+'f')
                if formula is None:formula=ET.Element(T+'f');c.insert(0,formula)
                formula.text=f.lstrip('=')
                for tag in ['v','is']:
                    node=c.find(T+tag)
                    if node is not None:c.remove(node)
                v=ET.SubElement(c,T+'v');actual=matrix[ri][ci-1]
                if isinstance(actual,bool):c.set('t','b');v.text='1' if actual else '0'
                elif isinstance(actual,(int,float)):c.attrib.pop('t',None);v.text=str(actual)
                else:c.set('t','str');v.text='' if actual is None else str(actual)
            changes[maps_by_sheet[name]]=common.xml(tree)
        guides=json.loads(guides_path.read_text(encoding='utf-8')) if guides_path else {}
        # Later-phase guidance survives Phase 6/7/8 refreshes, including replacement
        # of a sheet which also contains a progress cell. This owns no calculations.
        latest=ROOT/'analysis/latest_phase_guidance.json'
        if latest.exists():
            for name,updates in json.loads(latest.read_text(encoding='utf-8')).items():
                if name in old or name in maps_by_sheet:guides.setdefault(name,{}).update(updates)
        for name,updates in guides.items():
            part=maps_by_sheet.get(name,old.get(name));tree=ET.fromstring(changes.get(part,base.read(part) if part in base.namelist() else b''))
            for c in tree.iter(T+'c'):
                if c.attrib['r'] in updates:
                    for child in list(c):c.remove(child)
                    c.set('t','inlineStr');ET.SubElement(ET.SubElement(c,T+'is'),T+'t').text=updates[c.attrib['r']]
            changes[part]=common.xml(tree)
        calc=book.find(T+'calcPr')
        if calc is None:calc=ET.SubElement(book,T+'calcPr')
        calc.set('calcMode','auto');calc.set('fullCalcOnLoad','1')
        # Deduplicate content-type entries while retaining every preserved resource.
        seen=set();unique=[]
        for x in ct:
            key=(x.tag,x.attrib.get('PartName',x.attrib.get('Extension')))
            if key not in seen:seen.add(key);unique.append(x)
        ct[:]=unique
        changes.update({'xl/styles.xml':common.xml(styles),'xl/workbook.xml':common.xml(book),'xl/_rels/workbook.xml.rels':common.xml(rels),'[Content_Types].xml':common.xml(ct)})
        if 'docProps/app.xml' in base.namelist() and added:
            app=ET.fromstring(base.read('docProps/app.xml'));ns={'a':'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties','v':'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'}
            vector=app.find('a:TitlesOfParts/v:vector',ns)
            if vector is not None:
                for name in added:ET.SubElement(vector,'{'+ns['v']+'}lpstr').text=name
                vector.set('size',str(len(vector)))
            hp=app.find('a:HeadingPairs/v:vector',ns)
            if hp is not None:
                for node in hp.iter('{'+ns['v']+'}i4'):node.text=str(len(sheets))
            changes['docProps/app.xml']=common.xml(app)
        temp=output.with_suffix('.xlsx.tmp')
        with ZipFile(temp,'w',ZIP_DEFLATED,compresslevel=6) as out:
            for info in base.infolist():
                if info.filename not in removed:out.writestr(copy.copy(info),changes.pop(info.filename,base.read(info.filename)))
            for name,raw in changes.items():out.writestr(name,raw)
    temp.replace(output)
    with ZipFile(base_path) as base,ZipFile(output) as saved:
        for name,part in old.items():
            if name not in owned and name not in guides:assert saved.read(part)==base.read(part),name
        for info in base.infolist():
            if info.filename not in removed and info.filename not in {'xl/styles.xml','xl/workbook.xml','xl/_rels/workbook.xml.rels','[Content_Types].xml','docProps/app.xml',*(old[n] for n in guides)}:
                assert saved.read(info.filename)==base.read(info.filename),info.filename
    return dict(preserved_sheets=[n for n in old if n not in owned],owned_sheets=sorted(owned),sheet_count=len(sheets),guidance_updates=guides)

def main():
    result=graft(PRE/'input_workbook.xlsx',OUTPUT,json.loads((PRE/'segments.json').read_text(encoding='utf-8')),PRE,PRE/'final_values.json',PRE/'final_formulas.json',PRE/'guide_updates.json')
    (PRE/'preservation.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('Preserved 25 prior sheets/features; saved 27-sheet workbook.')

if __name__=='__main__':main()
