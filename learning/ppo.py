from pathlib import Path
import json,time,random,hashlib
import numpy as np
import torch
from torch import nn
from torch.distributions import Beta,Dirichlet
from scripts_ic.upgrade_common import *
torch.set_num_threads(1)

def features(env,task):
    obs=env.observations();rows=[]
    if task=='ic_r1':
        for o in obs['sectors']:
            b=max(o['base_output'],1);one=np.eye(13)[o['sector_id']-1]
            rows.append(np.r_[o['output']/b,o['capacity']/b,o['inventory']/b,o['backlog']/b,o['price'],o['observed_demand']/b,o['ai'],o['ai_effective'],o['technology'],o['absorption'],np.mean(o['upstream_prices']) if o['upstream_prices'] else 1,np.mean(o['upstream_health']) if o['upstream_health'] else 1,env.t/env.cfg['periods'],one])
    else:
        o=obs['government'];b=np.maximum(o['base_output'],1)
        rows=[np.r_[np.array(o['output'])/b,np.array(o['shortage'])/b,np.array(o['backlog'])/b,np.array(o['technology']),np.array(o['ai_effective']),np.array(o['backward_linkage']),np.array(o['price']),np.mean(np.array(o['edge_health']),axis=0),o['budget_remaining']/max(env.q0.sum(),1),env.t/env.cfg['periods']]]
    return np.asarray(rows,dtype=np.float32)

class ActorCritic(nn.Module):
    def __init__(self,task,dim):
        super().__init__();self.task=task
        self.body=nn.Sequential(nn.Linear(dim,64),nn.Tanh(),nn.Linear(64,64),nn.Tanh())
        self.actor=nn.Linear(64,6 if task=='ic_r1' else 13);self.critic=nn.Linear(64,1)
    def distribution(self,x):
        z=self.body(x);parameters=torch.nn.functional.softplus(self.actor(z))+1.0
        dist=Beta(parameters[:,:3],parameters[:,3:]) if self.task=='ic_r1' else Dirichlet(parameters)
        return dist,self.critic(z).squeeze(-1)
    def forward(self,x,action=None,deterministic=False):
        dist,value=self.distribution(x)
        action=dist.mean if deterministic else dist.sample() if action is None else action
        logprob=dist.log_prob(action);entropy=dist.entropy()
        if self.task=='ic_r1':logprob=logprob.sum(-1);entropy=entropy.sum(-1)
        return action,logprob,entropy,value

def apply_learned(env,task,actions):
    if task=='ic_r1':
        obs=env.observations()['sectors'];out=[]
        for o,v in zip(obs,actions):
            a=SectorAction(float(o['base_output']*(.3+1.7*v[0])),float(.5*v[1]),capex_share=float(.05*v[2]))
            out.append(project_sector(a,o,env.cfg))
        return out,GovernmentAction.zeros()
    rule=RuleSectorPolicy(env.cfg)
    return sector_actions(env,'rule',np.random.default_rng(env.seed+919),rule),government_action(env,'learned',None,actions[0])

def deterministic_episode(net,cfg,task):
    env=ICEnvironment(cfg);rewards=[]
    for _ in range(cfg['periods']):
        with torch.no_grad():a,_,_,_=net(torch.from_numpy(features(env,task)),deterministic=True)
        sa,ga=apply_learned(env,task,a.numpy());_,r,_,_=env.step(sa,ga)
        rewards.append(np.mean(np.array(r['sectors'])/env.q0) if task=='ic_r1' else r['government']/env.q0.sum())
    result=metrics(env);result['selection_score']=float(np.mean(rewards));return result

def train_one(task,seed,steps=12000):
    torch.manual_seed(seed);np.random.seed(seed);random.seed(seed)
    out=ROOT/'learning/results'/task/f'seed_{seed}';out.mkdir(parents=True,exist_ok=True)
    env=ICEnvironment(scenario(task,'train',0));dim=features(env,task).shape[-1];net=ActorCritic(task,dim)
    opt=torch.optim.Adam(net.parameters(),lr=3e-4);rng=np.random.default_rng(seed+91821)
    log=[];scenario_log=[];best=-float('inf');start=time.perf_counter()
    gamma=.99;lam=.95;episodes=10;updates=steps//(episodes*30)
    for update in range(updates):
        states=[];actions=[];logps=[];values=[];rewards=[]
        for ep in range(episodes):
            index=int(rng.integers(0,100000));cfg=scenario(task,'train',index);scenario_log.append({'update':update,'episode':ep,'index':index,'cfg':cfg})
            env=ICEnvironment(cfg);ss=[];aa=[];ll=[];vv=[];rr=[]
            for t in range(30):
                s=features(env,task)
                with torch.no_grad():a,l,_,v=net(torch.from_numpy(s))
                sa,ga=apply_learned(env,task,a.numpy());_,reward,_,_=env.step(sa,ga)
                r=np.array(reward['sectors'])/env.q0 if task=='ic_r1' else np.array([reward['government']/env.q0.sum()])
                ss.append(s);aa.append(a.numpy());ll.append(l.numpy());vv.append(v.numpy());rr.append(r)
            states.append(ss);actions.append(aa);logps.append(ll);values.append(vv);rewards.append(rr)
        values=np.asarray(values);rewards=np.asarray(rewards);advantages=np.zeros_like(rewards);running=np.zeros_like(rewards[:,0])
        for t in reversed(range(30)):
            nxt=values[:,t+1] if t<29 else 0
            delta=rewards[:,t]+gamma*nxt-values[:,t]
            running=delta+gamma*lam*running;advantages[:,t]=running
        returns=advantages+values
        s=torch.as_tensor(np.asarray(states).reshape(-1,dim),dtype=torch.float32)
        a=torch.as_tensor(np.asarray(actions).reshape(-1,3 if task=='ic_r1' else 13),dtype=torch.float32)
        old=torch.as_tensor(np.asarray(logps).reshape(-1),dtype=torch.float32)
        adv=torch.as_tensor(advantages.reshape(-1),dtype=torch.float32);adv=(adv-adv.mean())/(adv.std()+1e-8)
        ret=torch.as_tensor(returns.reshape(-1),dtype=torch.float32)
        losses=[];kl_values=[]
        for epoch in range(4):
            indices=torch.randperm(len(s))
            for inds in indices.split(256):
                _,lp,entropy,value=net(s[inds],a[inds]);ratio=(lp-old[inds]).exp()
                policy=-torch.minimum(ratio*adv[inds],ratio.clamp(.8,1.2)*adv[inds]).mean()
                loss=policy+.5*(value-ret[inds]).square().mean()-.001*entropy.mean()
                opt.zero_grad();loss.backward();nn.utils.clip_grad_norm_(net.parameters(),.5);opt.step()
                losses.append(float(loss.detach()));kl_values.append(float((old[inds]-lp).mean().detach()))
        entry={'update':update+1,'environment_steps':(update+1)*300,'mean_reward':float(rewards.mean()),'loss':float(np.mean(losses)),'approx_kl':float(np.mean(kl_values)),'elapsed_seconds':time.perf_counter()-start,'validation_score':''}
        if (update+1)%10==0 or update==updates-1:
            result=[deterministic_episode(net,scenario(task,'validation',i),task) for i in range(10)]
            score=float(np.mean([r['selection_score'] for r in result]));entry['validation_score']=score
            if score>best:
                best=score;torch.save({'state_dict':net.state_dict(),'task':task,'dim':dim,'seed':seed,'selected_environment_steps':(update+1)*300,'validation_score':score},out/'best.pt')
        log.append(entry)
    write_csv(out/'learning_curve.csv',log)
    (out/'training_scenarios.json').write_text(json.dumps(scenario_log,ensure_ascii=False),encoding='utf-8')
    meta=provenance()|{'task':task,'algorithm':'parameter-sharing IPPO with local critic' if task=='ic_r1' else 'PPO government','training_seed':seed,'environment_steps':updates*300,'wall_seconds':time.perf_counter()-start,'best_validation_score':best,'observations':dim,'parameters':sum(p.numel() for p in net.parameters()),'gamma':gamma,'gae_lambda':lam,'clip':.2,'epochs':4,'minibatch':256,'learning_rate':3e-4,'finite_horizon':30,'terminal_value':0,'price_action':'frozen for all R1 strategies','private_spend_cap_fraction':.05,'checkpoint_sha256':hashlib.sha256((out/'best.pt').read_bytes()).hexdigest(),'ppo_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (out/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'task':task,'seed':seed,'seconds':meta['wall_seconds'],'score':best}

def load_policy(task,seed):
    checkpoint=torch.load(ROOT/'learning/results'/task/f'seed_{seed}'/'best.pt',map_location='cpu',weights_only=False)
    net=ActorCritic(task,checkpoint['dim']);net.load_state_dict(checkpoint['state_dict']);net.eval();return net
