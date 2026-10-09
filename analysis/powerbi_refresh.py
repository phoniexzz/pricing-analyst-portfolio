"""Validate/rebuild the reporting snapshot before a native Import refresh.

Default refresh preserves authored report/model files and the Excel workbook.
--build explicitly regenerates project definitions. It never reruns forecasts.
"""
import argparse,json,urllib.request
from pathlib import Path
from powerbi_prepare import ROOT,prepare,digest
def theme_schema():
 path=ROOT/'powerbi/schemas/reportThemeSchema-2.157.json'
 if not path.exists():
  url='https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/Report%20Theme%20JSON%20Schema/reportThemeSchema-2.157.json'
  path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(urllib.request.urlopen(url,timeout=45).read())
 return path
def refresh(build=False):
 prepare()
 if build:
  from build_powerbi_project import model,report
  model();report()
 theme_schema()
 from verify_powerbi_project import verify
 verify()
 if build:
  from render_powerbi_previews import render
  render()
 print('Reporting snapshot validated. Next: refresh Import data in Power BI Desktop and rerun native acceptance for this snapshot. Previous acceptance is retained as a versioned record.')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--build',action='store_true',help='Regenerate project definitions and design previews explicitly')
 refresh(parser.parse_args().build)
