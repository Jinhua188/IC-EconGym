"""Prespecified synthetic R2 threshold checks; retain the failed 0..1 scan."""
from copy import deepcopy
import json
import numpy as np
from scripts_ic.upgrade_common import *

def main():
    runs=[];logs=[]
    for mode in IMPORTS:
        for label in ['homogeneous_ai1','homogeneous_ai2','heterogeneous_ai1']:
            for edge in [False,True]:
                cfg=deepcopy(load_task('ic_r2'));cfg.pop('variants',None)
                cfg.update(import_case=mode,seed=1,periods=30,absorption=[.2]*13,ai_initial=[1.0 if label!='homogeneous_ai2' else 2.0]*13)
                if label=='heterogeneous_ai1':
                    cfg['ai_initial']=[0.0]*13;cfg['ai_initial'][7]=1.0;cfg['absorption'][7]=.8
                if not edge:cfg['modules'].remove('edge')
                env=ICEnvironment(cfg);rule=RuleSectorPolicy(cfg);gov=RuleGovernmentPolicy(cfg)
                mask=env.a_domestic[:13]>0;periods=[]
                for t in range(30):
                    obs=env.observations();rule.begin_period()
                    _,_,_,record=env.step([rule.act(o) for o in obs['sectors']],gov.act(obs['government']))
                    mismatch=np.maximum(env.ai_effective[:,None]-env.absorb[None,:],0)
                    row={'import_case':mode,'case':label,'edge_enabled':edge,'period':t,'actual_IO_edge_mismatch_max':float(mismatch[mask].max()),'actual_IO_edge_health_min':float(env.health[mask].min()),'final_delivered':record['final_delivered'],'final_demand':record['final_demand'],'binding_domestic_count':record['binding_domestic_count']}
                    periods.append(row);logs.append(row)
                runs.append({'import_case':mode,'case':label,'edge_enabled':edge,**metrics(env),'actual_IO_edge_mismatch_max':max(r['actual_IO_edge_mismatch_max'] for r in periods),'actual_IO_edge_health_min':min(r['actual_IO_edge_health_min'] for r in periods)})
    out=ROOT/'robustness'
    write_csv(out/'threshold_diagnostics.csv',runs);write_csv(out/'threshold_periods.csv',logs)
    (out/'threshold_metadata.json').write_text(json.dumps(provenance()|{'runs':18,'selection':'three synthetic recipes x three imports x edge on/off; no favorable-run filtering','parameter_identity':'synthetic threshold cases, not AI proxy initial conditions','no_behavioral_parameter_change':True},indent=2),encoding='utf-8')
    print(json.dumps(runs))

if __name__=='__main__':main()
