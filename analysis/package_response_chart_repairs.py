"""Copy only Artifact-authored chart resources and explicit month-label cells."""
import copy
import posixpath
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile,ZIP_DEFLATED
from append_response_sheets import PREVIEW,PARTS,OUTPUT,T,xml,sheet_paths,merge_styles,resolve,relfile

def main():
    target_file=OUTPUT if '--final' in sys.argv else PARTS
    with ZipFile(target_file) as base,ZipFile(PREVIEW/'chart_repairs.xlsx') as repair:
        changed={}
        old_graphs={n for n in base.namelist() if n.startswith('xl/drawings/')}
        new_graphs={n for n in repair.namelist() if n.startswith('xl/drawings/')}
        def mapped(name):
            if '--final' not in sys.argv:return name
            if '/_rels/' in name:return relfile(mapped(name.replace('/_rels/','/').removesuffix('.rels')))
            folder,leaf=posixpath.split(name);return folder+'/phase5_'+leaf
        assert {mapped(n) for n in new_graphs}.issubset(old_graphs),'Expected existing native chart/drawing package paths'
        for name in new_graphs:
            raw=repair.read(name)
            if name.endswith('.rels') and '--final' in sys.argv:
                owner=name.replace('/_rels/','/').removesuffix('.rels');tree=ET.fromstring(raw)
                for rel in tree:
                    if rel.attrib.get('TargetMode')!='External':rel.set('Target',posixpath.relpath(mapped(resolve(owner,rel.attrib['Target'])),posixpath.dirname(mapped(owner))))
                raw=xml(tree)
            changed[mapped(name)]=raw
        styles=ET.fromstring(base.read('xl/styles.xml'));maps=merge_styles(styles,ET.fromstring(repair.read('xl/styles.xml')));changed['xl/styles.xml']=xml(styles)
        source=sheet_paths(repair)['Elasticity Summary'];dest=sheet_paths(base)['Elasticity Summary']
        tree=ET.fromstring(base.read(dest));rows={int(r.attrib['r']):r for r in tree.find(T+'sheetData')}
        strings=[]
        if 'xl/sharedStrings.xml' in repair.namelist():strings=list(ET.fromstring(repair.read('xl/sharedStrings.xml')))
        donor=ET.fromstring(repair.read(source))
        for cell in donor.iter(T+'c'):
            address=cell.attrib['r']
            if address not in ['H'+str(r) for r in range(80,96)]+['E'+str(r) for r in range(120,127)]:continue
            new=copy.deepcopy(cell);new.set('s',str(maps['cellXfs'][int(new.attrib.get('s','0'))]))
            if new.attrib.get('t')=='s':
                value=new.find(T+'v');si=strings[int(value.text)];new.remove(value);new.set('t','inlineStr');inline=ET.SubElement(new,T+'is')
                for child in si:inline.append(copy.deepcopy(child))
            letters=address.rstrip('0123456789');row=rows[int(address[len(letters):])]
            for existing in list(row):
                if existing.attrib.get('r')==address:row.remove(existing)
            # H belongs after all A:G cells and before any I:R cells.
            at=next((i for i,c in enumerate(row) if c.attrib.get('r','').rstrip('0123456789')>letters),len(row))
            row.insert(at,new)
        changed[dest]=xml(tree)
        tmp=target_file.with_suffix('.tmp.xlsx')
        with ZipFile(tmp,'w',ZIP_DEFLATED) as out:
            for item in base.infolist():out.writestr(copy.copy(item),changed.get(item.filename,base.read(item.filename)))
    tmp.replace(target_file);print('Copied only Artifact-authored native charts, month/group labels and their styles.')

if __name__=='__main__':main()
