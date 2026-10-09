"""Pin Microsoft's public PBIP/PBIR JSON schemas and validate offline."""
import json, urllib.request, sys
from pathlib import Path
from urllib.parse import urljoin, urldefrag
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis/.powerbi_tools'))
CACHE=ROOT/'powerbi/schemas'
BASE='https://developer.microsoft.com/json-schemas/fabric/item/'
URLS={
 'project':'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json',
 'reportReference':BASE+'report/definitionProperties/2.0.0/schema.json',
 'modelReference':BASE+'semanticModel/definitionProperties/1.0.0/schema.json',
 'report':BASE+'report/definition/report/3.0.0/schema.json',
 'pages':BASE+'report/definition/pagesMetadata/1.0.0/schema.json',
 'page':BASE+'report/definition/page/2.1.0/schema.json',
 'visual':BASE+'report/definition/visualContainer/2.4.0/schema.json',
 'version':BASE+'report/definition/versionMetadata/1.0.0/schema.json',
 'bookmarks':BASE+'report/definition/bookmarksMetadata/1.0.0/schema.json',
 'bookmark':BASE+'report/definition/bookmark/1.3.0/schema.json',
}
def local(url):
 return CACHE/(url.replace('https://developer.microsoft.com/json-schemas/fabric/','').replace('/','_'))
def fetch(url):
 url=urldefrag(url)[0]
 path=local(url)
 if path.exists():return json.loads(path.read_text(encoding='utf-8'))
 try:raw=urllib.request.urlopen(url,timeout=45).read()
 except Exception as e:raise RuntimeError(f'{url}: {e}') from e
 doc=json.loads(raw);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 return doc
def pin(url, seen=None):
 seen=seen if seen is not None else set();url=urldefrag(url)[0]
 if url in seen:return
 seen.add(url);doc=fetch(url)
 def walk(x):
  if isinstance(x,dict):
   for k,v in x.items():
    if k=='$ref' and isinstance(v,str) and not v.startswith('#'):pin(urljoin(url,v),seen)
    else:walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(doc)
 return doc
def validate(path):
 import jsonschema
 doc=json.loads(Path(path).read_text(encoding='utf-8'));url=doc.get('$schema')
 if not url:return
 schema=pin(url)
 from referencing import Registry,Resource
 from referencing.jsonschema import DRAFT7
 registry=Registry(retrieve=lambda uri:Resource.from_contents(fetch(uri),default_specification=DRAFT7))
 registry=registry.with_resource(url,Resource.from_contents(schema,default_specification=DRAFT7))
 jsonschema.Draft7Validator(schema,registry=registry).validate(doc)
if __name__=='__main__':
 for name,url in URLS.items():
  try:
   s=pin(url);print(name, list(s.get('properties',{})), 'required',s.get('required',[]))
  except Exception as e:print(name,str(e))
