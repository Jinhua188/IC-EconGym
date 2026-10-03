"""Frozen scenario generator, common action budgets and benchmark policies."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,csv,time
import numpy as np
from ic_extension.entrypoint import load_task
from ic_extension.model_v3 import ICEnvironment,SectorAction,GovernmentAction,RuleSectorPolicy,RuleGovernmentPolicy
ROOT=Path(__file__).resolve().parents[1]
IMPORTS=['proportional','intermediate_first','final_first']
CHANNELS=['ai','capacity','rd','qualification','inventory','edge_repair']
ENGINE_VERSION='v0.3-experimental'

def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:return
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def scenario(task,split,index):
    offsets={'train':100000,'validation':200000,'test_id':300000,'test_ood':400000,'robustness':500000}
    seed=offsets[split]+index
    rng=np.random.default_rng(seed);cfg=deepcopy(load_task(task));cfg.pop('variants',None)
    cfg['seed']=seed;cfg['periods']=30;cfg['benchmark_split']=split
    cfg['import_case']='final_first' if split=='test_ood' else IMPORTS[int(rng.integers(0,2))]
    cfg['capacity_lag']=int(rng.integers(7,11)) if split=='test_ood' else int(rng.integers(2,7))
    cfg['backlog_retention']=float(rng.uniform(.1,.6));cfg['capital_efficiency']=float(rng.uniform(.05,.2))
    cfg['external_supply_elasticity']=float(rng.uniform(1.05,1.5))
    cfg['policy']=deepcopy(cfg.get('policy',{}));cfg['policy']['spend_fraction']=.25
    if task=='ic_g5':
        proxy=json.loads((ROOT/'calibration/ai_proxy_initialization.json').read_text(encoding='utf-8'))
        cfg['ai_initial']=proxy['ai_initial'];cfg['absorption']=proxy['absorption']
        cfg['ai_initial_status']=proxy['status']
    # G5's channel mix and total budget stay common across targeting policies.
    if task=='ic_r1':
        cfg['demand_sector']=int(rng.choice([8,10])) if split=='test_ood' else int(rng.choice([9,11,12,13]))
        start=int(rng.integers(3,8));duration=int(rng.integers(10,16)) if split=='test_ood' else int(rng.integers(4,10))
        cfg['demand_shock']={'start':start,'end':start+duration,'increase':float(rng.uniform(.15,.5))}
    else:
        start=int(rng.integers(3,8));duration=int(rng.integers(8,14)) if split=='test_ood' else int(rng.integers(3,8))
        cfg['shock']={'sector':int(rng.choice([1,4,6])) if split=='test_ood' else int(rng.choice([7,8,12])), 'start':start,'end':start+duration,'capacity_loss':float(rng.uniform(.1,.4))}
        cfg['policy']['start_period']=start
    return cfg

def project_sector(action,obs,cfg):
    modules=set(cfg.get('modules',[]));allowed=set(obs['allowed_actions']);base=obs['base_output']
    action.production_plan=float(np.clip(action.production_plan,.3*base,2*base))
    action.inventory_target=float(np.clip(action.inventory_target,0,.5))
    for key,module,bound in [('price_change','price',.1),('capex_share','investment',.05),('rd_share','innovation',.01),('ai_share','ai',.01),('coordination','coordination',1),('diversification','diversification',1)]:
        value=float(getattr(action,key))
        setattr(action,key,float(np.clip(value,-bound if key=='price_change' else 0,bound)) if module in modules and key in allowed else 0.0)
    # Price action is frozen for every R1 algorithm, separating spending/control
    # performance from the unsupported demand-price response.
    if cfg.get('task_id')=='ic_r1':action.price_change=0.0
    total=action.capex_share+action.rd_share+action.ai_share
    if total>.05:
        for key in ['capex_share','rd_share','ai_share']:setattr(action,key,getattr(action,key)*.05/total)
    return action

def sector_actions(env,name,rng,rule):
    obs=env.observations()['sectors'];rule.begin_period();out=[]
    for o in obs:
        a=rule.act(o);base=o['base_output'];d=o['observed_demand']
        if name=='demand_tracking':a.production_plan=d
        elif name=='buffered_smoothing':a.production_plan=.5*base+.5*d;a.inventory_target=.25
        elif name=='random':a=SectorAction(float(base*rng.uniform(.3,2)),float(rng.uniform(0,.5)),capex_share=float(rng.uniform(0,.05)))
        elif name=='myopic_optimizer':
            # Convex proxy: .2*unserved + .1*excess + .02*plan,
            # using visible inventory, last demand and capacity only.
            a.production_plan=min(max(d-o['inventory'],.3*base),o['capacity']);a.inventory_target=0;a.capex_share=0
        elif name!='rule':raise ValueError(name)
        out.append(project_sector(a,o,env.cfg))
    return out

def government_action(env,name,rng,weights=None):
    cfg=env.cfg;p=cfg.get('policy',{});o=env.observations()['government']
    if not p.get('enabled',False) or env.t<int(p.get('start_period',0)):return GovernmentAction.zeros()
    if weights is None:
        if name=='uniform':weights=np.ones(13)
        elif name=='linkage':weights=np.array(o['backward_linkage'])
        elif name=='stress':weights=np.array(o['backward_linkage'])*(.1+np.array(o['shortage'])/np.maximum(o['base_output'],1))
        elif name=='random':weights=rng.dirichlet(np.ones(13))
        elif name=='myopic_optimizer':
            # Exact solution of a linear one-period stress-allocation proxy
            # on the same nonnegative unit simplex as every other policy.
            scores=np.array(o['shortage'])/np.maximum(o['base_output'],1)*np.array(o['backward_linkage'])
            weights=np.zeros(13);weights[int(np.argmax(scores))]=1.0
        elif name=='configured':return RuleGovernmentPolicy(cfg).act(o)
        else:raise ValueError(name)
    weights=np.maximum(weights,0);weights=weights/max(weights.sum(),1e-12)
    spend=float(p.get('spend_fraction',.25))*env.budget_remaining
    channels=p.get('channels',{'capacity':1});total=sum(channels.values())
    a=GovernmentAction.zeros()
    for key,value in channels.items():setattr(a,key,weights*spend*value/total)
    return a

def metrics(env):
    rows=env.history
    sums=lambda k:float(sum(r[k] for r in rows))
    return {'final_fill_rate':sums('final_delivered')/max(sums('final_demand'),1e-12),'final_shortage':sums('final_shortage'),'value_added':sums('value_added'),'welfare':sums('welfare'),'fiscal_spend':float(env.fiscal_cost),'private_spend':sums('private_investment')+sums('private_rd')+sums('private_ai'),'max_price':max(r['max_price'] for r in rows),'terminal_pending_capacity':rows[-1]['pending_capacity'],'binding_capacity_fraction':sums('binding_capacity_count')/(13*len(rows)),'binding_domestic_fraction':sums('binding_domestic_count')/(13*len(rows)),'binding_import_fraction':sums('binding_import_count')/(13*len(rows))}

def provenance():
    files=[ROOT/'ic_extension/model_v3.py',Path(__file__)]+list((ROOT/'ic_extension/data').glob('*.npz'))
    return {'engine_version':ENGINE_VERSION,'hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'parameter_status':'behavioral coefficients are scenarios; AI proxies are separately documented','historical_policy_causality':False}
