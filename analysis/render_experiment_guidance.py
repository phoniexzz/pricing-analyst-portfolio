"""Extract a read-only cached guidance preview; never edits the delivered workbook."""
import copy
import xml.etree.ElementTree as ET
from zipfile import ZipFile,ZIP_DEFLATED
import append_scenario_sheets as xml
import experiment_analysis as analysis
import package_recommendations as pack

if __name__=='__main__':
    with ZipFile(pack.OUTPUT) as z:
        book=ET.fromstring(z.read('xl/workbook.xml'));sheets=book.find(xml.T+'sheets');selected={'Dataset Overview':10,'README':24,'Recommendation Summary':18};ids=set();parts=xml.sheet_paths(z)
        for s in list(sheets):
            if s.attrib['name'] not in selected:sheets.remove(s)
            else:ids.add(s.attrib['{'+xml.RID+'}id'])
        dn=book.find(xml.T+'definedNames')
        if dn is not None:book.remove(dn)
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        for r in list(rels):
            if r.attrib['Type'].endswith('/worksheet') and r.attrib['Id'] not in ids:rels.remove(r)
            elif r.attrib['Type'].endswith(('/calcChain','/externalLink')):rels.remove(r)
        replacements={'xl/workbook.xml':xml.xml(book),'xl/_rels/workbook.xml.rels':xml.xml(rels)}
        for name,last in selected.items():
            t=ET.fromstring(z.read(parts[name]));rows=t.find(xml.T+'sheetData')
            for row in list(rows):
                if int(row.attrib['r'])>last:rows.remove(row);continue
                for c in row:
                    f=c.find(xml.T+'f')
                    if f is not None:c.remove(f)
            replacements[parts[name]]=xml.xml(t)
        keep=set()
        def walk(part):
            if part in keep or part not in z.namelist():return
            keep.add(part);rf=xml.relfile(part)
            if rf in z.namelist():
                keep.add(rf);links=rels if part=='xl/workbook.xml' else ET.fromstring(z.read(rf))
                for r in links:
                    if r.attrib.get('TargetMode')!='External':walk(xml.resolve(part,r.attrib['Target']))
        keep.add('_rels/.rels')
        for r in ET.fromstring(z.read('_rels/.rels')):
            if r.attrib.get('TargetMode')!='External':walk(xml.resolve('',r.attrib['Target']))
        ct=ET.fromstring(z.read('[Content_Types].xml'))
        for c in list(ct):
            if c.tag.endswith('Override') and c.attrib['PartName'].lstrip('/') not in keep:ct.remove(c)
        replacements['[Content_Types].xml']=xml.xml(ct);keep.add('[Content_Types].xml')
        with ZipFile(analysis.PRE/'guidance_segment.xlsx','w',ZIP_DEFLATED) as out:
            for item in z.infolist():
                if item.filename in keep:out.writestr(copy.copy(item),replacements.get(item.filename,z.read(item.filename)))
    print('Prepared current saved guidance preview with intact original styles and cached values.')
