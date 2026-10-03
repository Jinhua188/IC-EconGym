"""P0/P1/P3/P4 experiments with frozen data, matched scenarios and full logs."""
import argparse,json,time,gzip,csv,os,platform,hashlib
from pathlib import Path
from copy import deepcopy
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import psutil
from scripts_ic.upgrade_common import *
_POLICY_CACHE={}

def run_episode(cfg,policy,training_seed=None,full=False):
    task=cfg['task_id'];env=ICEnvironment(deepcopy(cfg));rng=np.random.default_rng(cfg['seed']+731)
    rule=RuleSectorPolicy(cfg);learned=None;periods=[]
    if policy=='learned':
        from learning.ppo import load_policy,features,apply_learned,torch
        key=(task,training_seed)
        if key not in _POLICY_CACHE:_POLICY_CACHE[key]=load_policy(task,training_seed)
        learned=_POLICY_CACHE[key]
    for _ in range(cfg.get('periods',30)):
        before_ai=env.ai.copy();before_tech=env.tech.copy();beforequal=env.qualification.copy()
        if learned is not None:
            with torch.no_grad():a,_,_,_=learned(torch.from_numpy(features(env,task)),deterministic=True)
            sa,ga=apply_learned(env,task,a.numpy())
        elif task=='ic_r1' and policy!='configured':
            sa=sector_actions(env,policy,rng,rule);ga=GovernmentAction.zeros()
        elif task=='ic_g5' and policy!='configured':
            sa=sector_actions(env,'rule',rng,rule);ga=government_action(env,policy,rng)
        else:
            rule.begin_period();sa=[rule.act(o) for o in env.observations()['sectors']];ga=RuleGovernmentPolicy(cfg).act(env.observations()['government'])
        _,reward,_,record=env.step(sa,ga)
        assert env.budget_remaining>=-1e-4 and env.fiscal_cost<=cfg.get('budget_share',0)*env.q0.sum()+1e-4
        assert np.all(env.output>=0) and np.all(np.isfinite(env.output))
        if full:
            record=deepcopy(record)
            record.update({'ai_delta':float((env.ai-before_ai).sum()),'technology_delta':float((env.tech-before_tech).sum()),'qualification_delta':float((env.qualification-beforequal).sum()),'sector_reward_sum':float(sum(reward['sectors'])),'government_reward':reward['government'],'sector_actions':json.dumps([vars(a) for a in sa]),'government_requests':json.dumps({k:getattr(ga,k).tolist() for k in CHANNELS}),'constraint_limits':json.dumps({k:v.tolist() for k,v in env.constraint_limits.items()}),'binding_masks':json.dumps({k:v.tolist() for k,v in env.binding.items()}),'queue_due_periods':json.dumps(sorted(env.pending))})
            periods.append(record)
    return metrics(env),periods

def p0():
    out=ROOT/'benchmark_results/p0_v3';out.mkdir(parents=True,exist_ok=True);summary=[]
    logs=gzip.open(out/'period_logs.csv.gz','wt',encoding='utf-8-sig',newline='');writer=None
    for task in [f'ic_{g}{n}' for g in ['e','r','g'] for n in range(1,6)]:
        base=load_task(task);variants=base.pop('variants',{})
        # Preserve all named arms, including historical synonymous arm names.
        for arm,override in [('base',{})]+list(variants.items()):
            for seed in range(1,11):
                cfg=deepcopy(base)
                for k,v in override.items():
                    if isinstance(v,dict) and isinstance(cfg.get(k),dict):cfg[k].update(v)
                    else:cfg[k]=v
                cfg['seed']=seed;result,records=run_episode(cfg,'configured',full=True)
                row={'task':task,'arm':arm,'seed':seed,**result,'max_mismatch':max(r['max_mismatch'] for r in records),'qualification_min':min(r['qualification_min'] for r in records),'ai_delta':sum(r['ai_delta'] for r in records),'qualification_delta':sum(r['qualification_delta'] for r in records),'max_pending_material':max(r['pending_material'] for r in records)};summary.append(row)
                for record in records:
                    record={'task':task,'arm':arm,'seed':seed,**record}
                    if writer is None:writer=csv.DictWriter(logs,fieldnames=list(record));writer.writeheader()
                    writer.writerow(record)
        print(f'P0 {task} done',flush=True)
    logs.close();write_csv(out/'arm_metrics.csv',summary)
    table=[]
    for task in sorted({r['task'] for r in summary}):
        rows=[r for r in summary if r['task']==task]
        table.append({'task':task,'runs':len(rows),'fill_min':min(r['final_fill_rate'] for r in rows),'fill_max':max(r['final_fill_rate'] for r in rows),'max_mismatch':max(r['max_mismatch'] for r in rows),'qualification_min':min(r['qualification_min'] for r in rows),'ai_delta_max':max(r['ai_delta'] for r in rows),'qualification_delta_max':max(r['qualification_delta'] for r in rows),'binding_capacity_mean':float(np.mean([r['binding_capacity_fraction'] for r in rows])),'binding_domestic_mean':float(np.mean([r['binding_domestic_fraction'] for r in rows]))})
    write_csv(out/'task_activation.csv',table)
    from ic_extension.model_v3 import SectorAction,GovernmentAction
    failures=[]
    for case in ['negative_plan','nan_plan','negative_government','nan_government','wrong_government_shape']:
        cfg=load_task('ic_r1');env=ICEnvironment(cfg);rule=RuleSectorPolicy(cfg);sa=sector_actions(env,'rule',np.random.default_rng(1),rule);ga=GovernmentAction.zeros()
        if case=='negative_plan':sa[0].production_plan=-1
        if case=='nan_plan':sa[0].production_plan=float('nan')
        if case=='negative_government':ga.ai[0]=-1
        if case=='nan_government':ga.ai[0]=float('nan')
        if case=='wrong_government_shape':ga.ai=np.zeros(12)
        try:env.step(sa,ga);raise AssertionError(case+' not rejected')
        except ValueError as e:failures.append({'case':case,'rejected':True,'message':str(e)})
    (out/'checks.json').write_text(json.dumps(provenance()|{'runs':len(summary),'invalid_actions':failures,'nonnegative_output':True,'government_budget':True,'logs':len(summary)*30},indent=2),encoding='utf-8')

def evaluation_group(task,split,policy,seed):
    cases=json.loads((ROOT/'benchmark_splits/locked_scenarios_v3.json').read_text(encoding='utf-8'))[task][split]
    rows=[]
    for i,cfg in enumerate(cases):
        result,_=run_episode(cfg,policy,seed)
        rows.append({'task':task,'split':split,'policy':policy,'training_seed':seed if seed is not None else '', 'scenario_id':i,'scenario_seed':cfg['seed'],**result})
    return rows

def p1(workers):
    out=ROOT/'benchmark_results/p1_v3';out.mkdir(parents=True,exist_ok=True);rows=[]
    jobs=[]
    for task in ['ic_r1','ic_g5']:
        baselines=['rule','demand_tracking','buffered_smoothing','random','myopic_optimizer'] if task=='ic_r1' else ['uniform','linkage','stress','random','myopic_optimizer']
        for split in ['test_id','test_ood']:
            jobs.extend((task,split,p,None) for p in baselines)
            jobs.extend((task,split,'learned',s) for s in range(101,111))
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for f in as_completed([ex.submit(evaluation_group,*j) for j in jobs]):rows.extend(f.result());print(f'P1 {len(rows)}/{len(jobs)*100}',flush=True)
    write_csv(out/'run_metrics.csv',sorted(rows,key=lambda r:(r['task'],r['split'],r['policy'],str(r['training_seed']),r['scenario_id'])))
    (out/'metadata.json').write_text(json.dumps(provenance()|{'test_scenarios_per_split':100,'training_seeds':list(range(101,111)),'runs':len(rows),'test_split_sha256':hashlib.sha256((ROOT/'benchmark_splits/locked_scenarios_v3.json').read_bytes()).hexdigest(),'economic_resources':'same actions, spending bounds, government budgets and channels','random_policy_seed':'scenario seed + 731','learning_steps_each':12000},indent=2),encoding='utf-8')

def robust_design():
    rng=np.random.default_rng(20261003);n=200;dimensions=9
    samples=np.stack([(rng.permutation(n)+rng.random(n))/n for _ in range(dimensions)],axis=1)
    records=[]
    for i,u in enumerate(samples):
        records.append({'parameter_id':i,'backlog_retention':float(.75*u[0]),'external_supply_elasticity':float(.9+.9*u[1]),'capital_efficiency':float(.03+.27*u[2]),'capacity_lag':int(1+min(9,int(10*u[3]))),'shock_size':float(.1+.5*u[4]),'budget_share':float(.002+.028*u[5]),'ai_conversion':float(.01+.19*u[6]),'inventory_adjustment':float(.1+.4*u[7]),'edge_health_floor':float(.6+.35*u[8])})
    return records

def robust_group(task,case,rationing):
    rows=[]
    for mode in IMPORTS:
        for policy in (['rule','buffered_smoothing','learned'] if task=='ic_r1' else ['uniform','stress','learned']):
            for seed in range(5):
                cfg=scenario(task,'robustness',seed)
                cfg['import_case']=mode;cfg['rationing_rule']=rationing
                for key,val in case.items():
                    if key not in ['parameter_id','shock_size']:cfg[key]=val
                mult=float(np.clip(1+.04*np.random.default_rng(74000+seed).normal(),.8,1.2))
                if task=='ic_r1':cfg['demand_shock']['increase']=case['shock_size']*mult;cfg['demand_sector']=12
                else:cfg['shock']['capacity_loss']=min(.95,case['shock_size']*mult);cfg['shock']['sector']=8
                result,_=run_episode(cfg,policy,101+seed if policy=='learned' else None)
                rows.append({'task':task,'parameter_id':case['parameter_id'],'import_case':mode,'rationing_rule':rationing,'policy':policy,'scenario_seed':seed,'training_seed':101+seed if policy=='learned' else '',**result})
    return rows

def mechanism_grid():
    out=[]
    proxy=json.loads((ROOT/'calibration/ai_proxy_initialization.json').read_text(encoding='utf-8'))
    for task in ['ic_e1','ic_r4','ic_r2','ic_g4']:
        for mode in IMPORTS:
            for level in range(5):
                cfg=load_task(task);cfg.pop('variants',None);cfg['import_case']=mode
                if task=='ic_e1':
                    cfg['ai_initial']=proxy['ai_initial'];cfg['absorption']=[min(.95,max(.05,a*(.5+.25*level))) for a in proxy['absorption']]
                    cfg['demand_sector']=8;cfg['demand_shock']={'start':5,'end':20,'increase':.3}
                elif task=='ic_r4':cfg['search_precision']=[0,2,5,12,20][level]
                elif task=='ic_r2':cfg['ai_initial']=[.25*level]*13;cfg['absorption']=[.2]*13
                else:cfg['qualification_initial']=[.2,.4,.6,.8,1][level]
                for seed in range(1,11):
                    cfg['seed']=seed;result,period=run_episode(cfg,'configured',full=True)
                    out.append({'task':task,'import_case':mode,'level':level,'seed':seed,**result,'max_mismatch':max(r['max_mismatch'] for r in period),'qualification_min':min(r['qualification_min'] for r in period),'ai_effective_terminal':period[-1]['ai_effective_mean']})
    write_csv(ROOT/'robustness/mechanism_grid.csv',out)

def p3(workers):
    out=ROOT/'robustness';out.mkdir(exist_ok=True);design=robust_design();write_csv(out/'parameter_design.csv',design)
    jobs=[(task,c,'internal_first') for task in ['ic_r1','ic_g5'] for c in design]
    # Additional balanced structural tests use the first 30 preassigned samples.
    jobs.extend((task,c,rule) for task in ['ic_r1','ic_g5'] for c in design[:30] for rule in ['proportional','final_first'])
    rows=[]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for f in as_completed([ex.submit(robust_group,*j) for j in jobs]):
            rows.extend(f.result())
            if len(rows)%900==0:print(f'P3 {len(rows)}/{len(jobs)*45}',flush=True)
    write_csv(out/'run_metrics.csv',rows)
    (out/'metadata.json').write_text(json.dumps(provenance()|{'parameter_samples':200,'sampling':'Latin hypercube over explicitly exploratory ranges','seeds_per_case':5,'main_runs':18000,'additional_rationing_runs':5400,'total_runs':len(rows),'learning_checkpoint_seeds':[101,102,103,104,105],'scope':'sampling-design coverage, not empirical probability','inactive_parameters':'AI/budget parameters do not identify R1 effects; report task-specific active dimensions'},indent=2),encoding='utf-8')
    mechanism_grid()

def runtime_batch(count):
    cfg=scenario('ic_g5','test_id',0);cfg['periods']=10
    start=time.perf_counter();rows=[]
    for i in range(count):
        cfg['seed']=600000+i;run_episode(cfg,'uniform');rows.append(1)
    return time.perf_counter()-start,psutil.Process().memory_info().rss/1024**2,os.getpid()

def p4(workers):
    out=ROOT/'benchmark_results/p4_v3';out.mkdir(parents=True,exist_ok=True);rows=[]
    from learning.ppo import load_policy,features,apply_learned,torch
    for task in ['ic_r1','ic_g5']:
        net=load_policy(task,101)
        for repeat in range(5):
            cfg=scenario(task,'test_id',repeat);env=ICEnvironment(cfg);policy_ms=[];env_ms=[];all_ms=[]
            for t in range(30):
                start=time.perf_counter()
                with torch.no_grad():a,_,_,_=net(torch.from_numpy(features(env,task)),deterministic=True)
                sa,ga=apply_learned(env,task,a.numpy());mid=time.perf_counter();env.step(sa,ga);end=time.perf_counter()
                policy_ms.append((mid-start)*1000);env_ms.append((end-mid)*1000);all_ms.append((end-start)*1000)
            rows.append({'task':task,'repeat':repeat,'policy_ms':float(np.median(policy_ms)),'environment_ms':float(np.median(env_ms)),'end_to_end_ms':float(np.median(all_ms)),'process_rss_mb':psutil.Process().memory_info().rss/1024**2})
    write_csv(out/'step_timings.csv',rows)
    batches=[]
    # Report both execution and initialization; persistent pool avoids counting
    # Python worker startup as steady-state simulation scaling.
    with ProcessPoolExecutor(max_workers=workers) as ex:
        list(ex.map(runtime_batch,[1]*workers))
        for count in [1,8,32,128]:
            chunks=[count//min(count,workers)+(1 if i<count%min(count,workers) else 0) for i in range(min(count,workers))]
            for repeat in range(3):
                start=time.perf_counter();results=list(ex.map(runtime_batch,chunks));seconds=time.perf_counter()-start
                rss_by_pid={r[2]:r[1] for r in results}
                batches.append({'environment_count':count,'repeat':repeat,'workers_used':len(rss_by_pid),'worker_limit':workers,'periods_each':10,'wall_seconds':seconds,'steps_per_second':count*10/seconds,'sum_worker_rss_mb':sum(rss_by_pid.values())})
    write_csv(out/'batch_throughput.csv',batches)
    (out/'metadata.json').write_text(json.dumps(provenance()|{'platform':platform.platform(),'processor':platform.processor(),'logical_cpus':os.cpu_count(),'python':platform.python_version(),'numpy':np.__version__,'torch':torch.__version__,'actors_per_environment':14,'scaling_claim':'batched independent environments, not number-of-agents scaling'},indent=2),encoding='utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--package',choices=['p0','p1','p3','p4'],required=True);p.add_argument('--workers',type=int,default=6);a=p.parse_args()
    if a.package=='p0':p0()
    else:globals()[a.package](a.workers)

if __name__=='__main__':main()
