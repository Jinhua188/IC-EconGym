"""Public reset/run_agents/step/evaluate adapter for the experimental benchmark."""
from copy import deepcopy
import numpy as np
from .model_v3 import ICEnvironment,RuleSectorPolicy

class World13V3:
    def __init__(self,cfg,sector_policy='rule',government_policy='configured',learning_seed=101):
        self.cfg=deepcopy(cfg);self.sector_policy=sector_policy;self.government_policy=government_policy;self.learning_seed=learning_seed;self.reset()
    def reset(self,seed=None):
        if seed is not None:self.cfg['seed']=int(seed)
        self.environment=ICEnvironment(self.cfg);self.rule=RuleSectorPolicy(self.cfg);self.rng=np.random.default_rng(self.cfg.get('seed',0)+731);self.network=None
        if 'learned' in [self.sector_policy,self.government_policy]:
            from learning.ppo import load_policy
            if self.cfg['task_id']=='ic_r1' and self.sector_policy!='learned':raise ValueError('R1 checkpoint controls sectors')
            if self.cfg['task_id']=='ic_g5' and self.government_policy!='learned':raise ValueError('G5 checkpoint controls government')
            self.network=load_policy(self.cfg['task_id'],self.learning_seed)
        return self.environment.observations()
    def run_agents(self):
        from scripts_ic.upgrade_common import sector_actions,government_action
        if self.network is not None:
            from learning.ppo import features,apply_learned,torch
            with torch.no_grad():a,_,_,_=self.network(torch.from_numpy(features(self.environment,self.cfg['task_id'])),deterministic=True)
            sa,ga=apply_learned(self.environment,self.cfg['task_id'],a.numpy())
        else:
            sa=sector_actions(self.environment,self.sector_policy,self.rng,self.rule);ga=government_action(self.environment,self.government_policy,self.rng)
        return {'sectors':sa,'government':ga}
    def step(self,actions):
        o,r,_,info=self.environment.step(actions['sectors'],actions['government'])
        return o,r,self.environment.t>=self.cfg.get('periods',30),info
    def evaluate(self):
        from scripts_ic.upgrade_common import metrics
        if not self.environment.history:raise ValueError('no completed periods')
        return metrics(self.environment)

def make(cfg,*,sector_policy='rule',government_policy='configured',learning_seed=101):
    return World13V3(cfg,sector_policy,government_policy,learning_seed)
