"""Fit a physical-unit capacity queue and test on independent SMIC disclosures."""
from pathlib import Path
import json,re,hashlib
import numpy as np
from scripts_ic.upgrade_common import ROOT,write_csv
from ic_extension.capacity_transition import schedule_capacity

def parse():
    manifest=json.loads((ROOT/'external_validation/source_manifest.json').read_text(encoding='utf-8'));rows=[]
    for source in sorted(manifest,key=lambda r:r['quarter']):
        text=(ROOT/'external_validation/raw'/f"smic_{source['quarter']}.txt").read_text(encoding='utf-8')
        patterns={'monthly_capacity':r'Monthly capacity (?:increased to|was|decreased to)\s*([\d,]+)', 'capex_usd_million':r'Capital expenditures? (?:was|were)\s*\$\s*([\d,.]+)\s*million', 'utilization_percent':r'Utilization rate(?:\(\d\))?\s*([\d.]+)%','shipments':r'Wafer shipments(?:\(\d\))?\s*([\d,]+)'}
        row={'quarter':source['quarter']};evidence={}
        for field,pattern in patterns.items():
            matches=list(re.finditer(pattern,text,re.I));match=matches[-1] if field=='monthly_capacity' else matches[0] if matches else None
            if match is None:raise ValueError((source['quarter'],field,pattern))
            row[field]=float(match.group(1).replace(',',''))
            page=re.findall(r'PAGE (\d+)',text[:match.start()])[-1]
            evidence[field]={'page':int(page),'excerpt':text[match.start():match.end()]}
        row.update(source_url=source['url'],source_sha256=source['sha256'],evidence=json.dumps(evidence,ensure_ascii=False))
        rows.append(row)
    write_csv(ROOT/'external_validation/smic_quarterly.csv',rows)
    return rows

def main():
    rows=parse();k=np.array([r['monthly_capacity'] for r in rows]);invest=np.array([r['capex_usd_million'] for r in rows]);initial=k[3]
    train=np.arange(4,12);validation=np.arange(12,16);test=np.arange(16,24)
    predictions={};fits=[]
    for lag in range(1,5):
        exposure=np.cumsum([invest[t-lag] for t in range(4,24)])
        eta=max(0,float(np.dot(exposure[:8],k[train]-initial)/np.dot(exposure[:8],exposure[:8])))
        queue={};current=initial;pred=[]
        for t in range(0,24):
            schedule_capacity(queue,t,invest[t],lag,eta)
            if t>=4:current+=queue.pop(t,0.0);pred.append(current)
        pred=np.array(pred);assert np.allclose(pred,initial+eta*exposure)
        fits.append({'lag_quarters':lag,'efficiency_wafers_per_month_per_usd_million':eta,'calibration_mae':float(np.mean(abs(pred[:8]-k[train]))),'validation_mae':float(np.mean(abs(pred[8:12]-k[validation])))})
        predictions[lag]=pred
    best=min(fits,key=lambda r:r['validation_mae']);chosen=predictions[best['lag_quarters']]
    # Same-information baselines, frozen at the end of 2023 for an 8-quarter test.
    x=np.arange(4,12);slope,intercept=np.polyfit(x,k[x],1)
    linear=intercept+slope*np.arange(4,24)
    persistence=np.r_[k[3:15],np.repeat(k[15],8)]
    result=[];series=[]
    for name,pred in [('capacity_queue',chosen),('linear_trend',linear),('persistence',persistence)]:
        for split,ind in [('calibration',train),('validation',validation),('test',test)]:
            diff=pred[ind-4]-k[ind]
            result.append({'model':name,'split':split,'n':len(ind),'mae_wafers_per_month':float(np.mean(abs(diff))),'mape':float(np.mean(abs(diff)/k[ind])),'rmse_wafers_per_month':float(np.sqrt(np.mean(diff**2)))})
        for t in range(4,24):series.append({'model':name,'quarter':rows[t]['quarter'],'split':'calibration' if t<12 else 'validation' if t<16 else 'test','observed_monthly_capacity':float(k[t]),'modeled_monthly_capacity':float(pred[t-4])})
    write_csv(ROOT/'external_validation/fit_candidates.csv',fits);write_csv(ROOT/'external_validation/metrics.csv',result);write_csv(ROOT/'external_validation/trajectories.csv',series)
    meta={'observation':'end-of-quarter monthly standard-logic 8-inch-equivalent wafer capacity','input':'observed historical capex in USD million','case_scope':'shared capacity queue only; not full 13-sector validation','calibration':'2021Q1-2022Q4','validation':'2023Q1-2023Q4','test':'2024Q1-2025Q4','presample':'2020Q1-2020Q4 capex and 2020Q4 capacity','best':best,'classification':'conditional historical replay, not ex-ante forecast','national_coefficient_transfer':False,'baseline_linear':'OLS on calibration 2021-2022 capacity only, fixed before test','baseline_persistence':'2023Q4 capacity held constant throughout test; earlier rows are one-step diagnostics','shared_transition_sha256':hashlib.sha256((ROOT/'ic_extension/capacity_transition.py').read_bytes()).hexdigest()}
    (ROOT/'external_validation/metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8');print(json.dumps(meta|{'metrics':result}))

if __name__=='__main__':main()
