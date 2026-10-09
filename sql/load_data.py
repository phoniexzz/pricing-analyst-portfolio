"""Strict import of declared synthetic interfaces; no type inference at runtime."""
from pathlib import Path
import csv, datetime, hashlib, json, sqlite3

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'sql/.build'
def quoted(s):return '"'+s.replace('"','""')+'"'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def load(database=None):
    BUILD.mkdir(parents=True,exist_ok=True)
    db=Path(database) if database else BUILD/'northstar.sqlite'
    schema=json.loads((ROOT/'sql/schema.json').read_text())
    # Build atomically, so failed import cannot leave a partially populated database.
    staging=db.with_suffix('.loading.sqlite');staging.unlink(missing_ok=True)
    con=sqlite3.connect(staging);manifest={}
    try:
        for table,meta in schema.items():
            columns=meta['columns'];defs=[quoted(k)+' '+v['sqlite_type']+(' NOT NULL' if k in meta['key'] else '') for k,v in columns.items()]
            defs+=['UNIQUE ('+','.join(map(quoted,meta['key']))+')']
            con.execute('CREATE TABLE '+quoted(table)+' ('+','.join(defs)+')')
            file=ROOT/meta['csv'];count=0
            with file.open(encoding='utf-8-sig',newline='') as f:
                reader=csv.DictReader(f)
                assert reader.fieldnames==list(columns),f'Unexpected columns: {table}'
                batch=[]
                for row in reader:
                    values=[]
                    for col,spec in columns.items():
                        x=row[col]
                        if x=='':
                            assert spec['nullable'],(table,col,'unexpected unavailable value')
                            values.append(None);continue
                        kind=spec['kind']
                        if kind=='boolean':
                            assert x in ('True','False');x=int(x=='True')
                        elif kind=='integer':x=int(x)
                        elif kind=='number':
                            x=float(x)
                            assert __import__('math').isfinite(x)
                        elif kind=='date':datetime.date.fromisoformat(x)
                        values.append(x)
                    batch.append(values);count+=1
                    if len(batch)==2000:
                        con.executemany('INSERT INTO '+quoted(table)+' VALUES ('+','.join('?' for _ in columns)+')',batch);batch=[]
                if batch:con.executemany('INSERT INTO '+quoted(table)+' VALUES ('+','.join('?' for _ in columns)+')',batch)
            manifest[table]={'rows':count,'key':meta['key'],'sha256':digest(file)}
        # History is repeated under three simulation labels. This view removes labels
        # and requires identical historical values before exposing one gym-month.
        fields=[x for x in schema['experiment_monthly']['columns'] if x not in ('simulation',)]
        body=','.join(map(quoted,fields))
        con.execute('CREATE VIEW experiment_history AS SELECT DISTINCT '+body+' FROM experiment_monthly WHERE is_simulated=0')
        repeated=con.execute('SELECT gym_id,month,COUNT(*) FROM experiment_history GROUP BY gym_id,month HAVING COUNT(*)<>1').fetchall()
        assert not repeated,'Historical cases disagree; cannot deduplicate safely'
        con.commit()
    finally:con.close()
    staging.replace(db)
    (BUILD/'load_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return db

if __name__=='__main__':print(load())
