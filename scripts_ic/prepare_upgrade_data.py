"""Read supplied sources; preserve measured proxies versus scenario coefficients."""
from pathlib import Path
import csv, json, hashlib, re, zipfile, xml.etree.ElementTree as ET
import numpy as np
import openpyxl

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent

def write_csv(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    out=ROOT/'calibration';out.mkdir(exist_ok=True)
    source=BASE/'AI渗透综合指标.xlsx'
    wb=openpyxl.load_workbook(source,data_only=True)
    specifications=[('任务暴露度',0,4,31,'task_exposure',2024),('招聘_2024',0,5,16,'hiring_proxy',2024),('文本披露型采纳强度',0,7,5,'text_adoption_proxy',2023),('专利吸收与知识扩散强度',1,8,None,'patent_intensity_proxy','unspecified')]
    raw=[];audit=[]
    for sheet,key_col,group_col,value_col,metric,year in specifications:
        seen={};duplicates=0;ws=wb[sheet]
        for rownum,r in enumerate(ws.values,1):
            if rownum==1 or r[key_col] is None:continue
            code=re.sub(r'\D','',str(r[key_col]).split('.')[0]).zfill(6)
            match=re.search(r'环节(\d)',str(r[group_col]));group=int(match.group(1)) if match else None
            if group is None:continue
            if metric=='patent_intensity_proxy':
                if not isinstance(r[10],(int,float)) or r[10]<=0:continue
                value=float(np.log1p(float(r[9])/(float(r[10])/1e8)))
            else:
                if not isinstance(r[value_col],(int,float)):continue
                value=float(r[value_col])
            identity=(code,year)
            if identity in seen:
                duplicates+=1
                if abs(seen[identity]['value']-value)>1e-10 or seen[identity]['H']!=group:
                    raise ValueError(f'Conflicting duplicate {sheet} {code}')
                continue
            seen[identity]={'firm_code':code,'year':year,'H':group,'metric':metric,'value':value,'sheet':sheet,'excel_row':rownum}
        raw.extend(seen.values())
        audit.append({'sheet':sheet,'source_rows':ws.max_row-1,'unique_valid_firms':len(seen),'duplicate_rows_removed':duplicates,'year':year})
    write_csv(out/'ai_firm_proxies.csv',raw)
    metrics=[s[4] for s in specifications]
    grouped=[]
    for h in range(1,7):
        for metric in metrics:
            values=[r['value'] for r in raw if r['H']==h and r['metric']==metric]
            grouped.append({'H':h,'metric':metric,'n':len(values),'mean':float(np.mean(values)) if values else '', 'std':float(np.std(values,ddof=1)) if len(values)>1 else '', 'year':next(s[5] for s in specifications if s[4]==metric)})
    write_csv(out/'ai_H_means.csv',grouped)
    # Functional mapping is explicitly coarse; it is not firm-industry identification.
    mapping={1:[2],2:[2],3:[2],4:[1],5:[1],6:[2],7:[1],8:[3,4,5],9:[6],10:[6],11:[6],12:[6],13:[6]}
    with (ROOT/'ic_extension/data/sector_labels.csv').open(encoding='utf-8-sig') as f:labels=list(csv.DictReader(f))[:13]
    rows=[]
    for sector,hs in mapping.items():
        row={'sector_id':sector,'label':labels[sector-1]['io_label'],'H_groups':'|'.join(map(str,hs)),'mapping_status':'functional_proxy_not_industry_identified'}
        for metric in metrics:
            values=[r['value'] for r in raw if r['H'] in hs and r['metric']==metric]
            row[metric+'_mean']=float(np.mean(values)) if values else ''
            row[metric+'_n']=len(values)
        rows.append(row)
    for metric in metrics:
        values=np.array([float(r[metric+'_mean']) for r in rows])
        span=values.max()-values.min()
        for r,v in zip(rows,values):r[metric+'_relative_score']=float((v-values.min())/span) if span>0 else 0.5
    write_csv(out/'ai_sector_proxies.csv',rows)
    proxy={'ai_initial':[0.2*r['text_adoption_proxy_relative_score'] for r in rows], 'absorption':[0.3+0.4*r['patent_intensity_proxy_relative_score'] for r in rows], 'proxy_mapping_scale':{'ai_initial_max':0.2,'absorption_min':0.3,'absorption_max':0.7},'status':'proxy-informed scenario initialization; not estimated conversion or causal absorption', 'ai_conversion_changed':False,'year_alignment':'mixed 2023/2024/unspecified; not 2020 observations'}
    (out/'ai_proxy_initialization.json').write_text(json.dumps(proxy,ensure_ascii=False,indent=2),encoding='utf-8')
    # Audit the supplied manuscript against the executable data version.
    path=BASE/'打印-返修2.1-基于投入产出表的中国集成电路全产业链结构与关联效应研究(1).docx'
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with zipfile.ZipFile(path) as z:tree=ET.fromstring(z.read('word/document.xml'))
    paragraphs=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in tree.findall('.//w:p',ns)]
    source_evidence=[{'paragraph':i+1,'text':p} for i,p in enumerate(paragraphs) if any(k in p for k in ['拆分所需','分离系数为','线性插值','比例拆分假设','国家统计局编制'])]
    (out/'io_source_evidence.json').write_text(json.dumps(source_evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    audit_report={'sources':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [source,path,BASE/'remake-2020年投入产出表与指标.xlsx']], 'ai_sheets':audit,'pooling':'firm-weighted arithmetic mean; H3/H4/H5 pooled before mean, not unweighted mean of group means','patent_H5_observations':0,'patent_year':'unspecified','warnings':['AI workbook is not a ready combined longitudinal AI score','Within-H functional mapping repeats proxies across several IO sectors','Missing recruitment/patent firms are not filled with zero','AI conversion remains a scenario coefficient','Yearbook editions and source-year statements are transcribed from supplied manuscript, not independently authenticated','2020 interpolated revenue can use 2023 information; not vintage-2020 forecasting'],'io_statistics':'2020 executable matrix retained; supplied manuscript uses a different sector scope including information services'}
    (out/'data_audit.json').write_text(json.dumps(audit_report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'firms_by_sheet':audit,'sector_proxy_rows':len(rows)},ensure_ascii=False))

if __name__=='__main__':main()
