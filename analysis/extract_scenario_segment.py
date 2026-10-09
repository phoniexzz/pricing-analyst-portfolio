"""Prune a read-only audit copy to the changed, saved dependency graph.

The delivered 25-sheet workbook remains untouched. Keep selected worksheets and
all transitively required tables/charts/themes/styles; remove unselected worksheet
relationships and content-type entries so the importer cannot load unrelated data.
"""
import copy
import posixpath
import xml.etree.ElementTree as ET
from zipfile import ZipFile,ZIP_DEFLATED
import append_scenario_sheets as pack

def main():
    with ZipFile(pack.OUTPUT) as z:
        book=ET.fromstring(z.read('xl/workbook.xml'));selected=set(pack.ADDED+['Monthly Performance'])
        sheets=book.find(pack.T+'sheets');ids=set()
        for s in list(sheets):
            if s.attrib['name'] not in selected:sheets.remove(s)
            else:ids.add(s.attrib['{'+pack.RID+'}id'])
        names=book.find(pack.T+'definedNames')
        if names is not None:book.remove(names)
        view=book.find(pack.T+'bookViews')
        if view is not None:
            for v in view:v.set('activeTab','0')
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        for r in list(rels):
            if r.attrib['Type'].endswith('/worksheet') and r.attrib['Id'] not in ids:rels.remove(r)
            elif r.attrib['Type'].endswith(('/calcChain','/externalLink')):rels.remove(r)
        replacements={'xl/workbook.xml':pack.xml(book),'xl/_rels/workbook.xml.rels':pack.xml(rels)}
        keep=set()
        def walk(part):
            if part in keep or part not in z.namelist():return
            keep.add(part);rf=pack.relfile(part)
            if rf in z.namelist():
                keep.add(rf)
                links=rels if part=='xl/workbook.xml' else ET.fromstring(z.read(rf))
                for r in links:
                    if r.attrib.get('TargetMode')!='External':walk(pack.resolve(part,r.attrib['Target']))
        keep.add('_rels/.rels')
        for r in ET.fromstring(z.read('_rels/.rels')):
            if r.attrib.get('TargetMode')!='External':walk(pack.resolve('',r.attrib['Target']))
        ct=ET.fromstring(z.read('[Content_Types].xml'))
        for c in list(ct):
            if c.tag.endswith('Override') and c.attrib['PartName'].lstrip('/') not in keep:ct.remove(c)
        replacements['[Content_Types].xml']=pack.xml(ct);keep.add('[Content_Types].xml')
        with ZipFile(pack.PREVIEW/'saved_segment.xlsx','w',ZIP_DEFLATED,compresslevel=6) as out:
            for item in z.infolist():
                if item.filename in keep:out.writestr(copy.copy(item),replacements.get(item.filename,z.read(item.filename)))
    print('Extracted only saved Phase 6 sheets, Monthly Performance and their required native resources. Delivered workbook untouched.')

if __name__=='__main__':main()
