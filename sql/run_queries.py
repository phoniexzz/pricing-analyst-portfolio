"""Run fifteen saved read-only queries with the standard library."""
import csv,json,sqlite3
from load_data import ROOT,BUILD,load

def run():
    db=load();out=BUILD/'outputs';out.mkdir(exist_ok=True)
    results=[]
    con=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
    con.execute('PRAGMA query_only=ON')
    try:
        for entry in json.loads((ROOT/'sql/catalog.json').read_text()):
            file=ROOT/'sql/queries'/entry['file']
            cur=con.execute(file.read_text(encoding='utf-8'));rows=cur.fetchall()
            with (out/(file.stem+'.csv')).open('w',encoding='utf-8',newline='') as f:
                w=csv.writer(f);w.writerow([x[0] for x in cur.description]);w.writerows(rows)
            results.append({'query':entry['file'],'rows':len(rows)})
    finally:con.close()
    (BUILD/'query_results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
    return results

if __name__=='__main__':run()
