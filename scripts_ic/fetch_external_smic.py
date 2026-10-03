"""Download official earnings releases and retain page-level extraction evidence."""
from pathlib import Path
import urllib.request,urllib.parse,re,json,concurrent.futures,hashlib
import fitz
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'external_validation/raw'

def download(item):
    year,q,url=item;target=OUT/f'smic_{year}Q{q}.pdf'
    encoded=urllib.parse.quote(url,safe=':/?=&%')
    if not target.exists():target.write_bytes(urllib.request.urlopen(encoded,timeout=60).read())
    doc=fitz.open(target)
    pages=[p.get_text(sort=True) for p in doc]
    (OUT/f'smic_{year}Q{q}.txt').write_text('\n\n'.join(f'PAGE {i+1}\n{s}' for i,s in enumerate(pages)),encoding='utf-8')
    return {'quarter':f'{year}Q{q}','url':url,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'pages':len(doc)}

def main():
    OUT.mkdir(parents=True,exist_ok=True);items=[]
    for year in range(2020,2026):
        url=f'https://www.smics.com/en/site/company_financialSummary?year={year}'
        s=urllib.request.urlopen(url,timeout=30).read().decode('utf-8')
        links=re.findall(r'''(?:href|src)=["']([^"']+)''',s)
        pdfs=[x.strip() for x in links if '.pdf' in x.lower() and not any(v in x.lower() for v in ['conference','announcement','annual','ar_en','e00981','interim','ar-'])]
        assert len(pdfs)==4,(year,pdfs)
        items.extend((year,4-i,url) for i,url in enumerate(pdfs))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:result=list(ex.map(download,items))
    (ROOT/'external_validation/source_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'downloaded':len(result),'quarters':[r['quarter'] for r in result]}))

if __name__=='__main__':main()
