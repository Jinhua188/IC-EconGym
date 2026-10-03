"""Check learned adapters, fixed splits, checkpoint identity and queue timing."""
from pathlib import Path
import json,hashlib,csv
import numpy as np
from scripts_ic.upgrade_common import ROOT,scenario,write_csv
from scripts_ic.run_upgrade_experiments import run_episode
from ic_extension.iewm13_v3 import make
from ic_extension.capacity_transition import schedule_capacity

def main():
    report={'adapter_runs':[],'training_instances':20}
    test=json.loads((ROOT/'benchmark_splits/locked_scenarios_v3.json').read_text(encoding='utf-8'))
    index_path=ROOT/'benchmark_splits/training_scenario_indices.csv'
    stored_indices=list(csv.DictReader(index_path.open(encoding='utf-8-sig'))) if index_path.exists() else None
    indices=[]
    for task in ['ic_r1','ic_g5']:
        tests={cfg['seed'] for split in test[task].values() for cfg in split}
        validation={scenario(task,'validation',i)['seed'] for i in range(10)}
        assert len(tests)==200 and not tests.intersection(validation)
        for seed in range(101,111):
            folder=ROOT/'learning/results'/task/f'seed_{seed}'
            metadata=json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
            assert metadata['checkpoint_sha256']==hashlib.sha256((folder/'best.pt').read_bytes()).hexdigest()
            assert metadata['ppo_source_sha256']==hashlib.sha256((ROOT/'learning/ppo.py').read_bytes()).hexdigest()
            if stored_indices is not None:
                selected=[r for r in stored_indices if r['task']==task and int(r['training_seed'])==seed]
                episodes=[{'update':int(r['update']),'episode':int(r['episode']),'index':int(r['index']),'cfg':scenario(task,'train',int(r['index']))} for r in selected]
                assert all(e['cfg']['seed']==int(r['scenario_seed']) for e,r in zip(episodes,selected))
            else:
                episodes=json.loads((folder/'training_scenarios.json').read_text(encoding='utf-8'))
            assert len(episodes)==400
            assert not {e['cfg']['seed'] for e in episodes}.intersection(tests|validation)
            indices.extend({'task':task,'training_seed':seed,'update':e['update'],'episode':e['episode'],'index':e['index'],'scenario_seed':e['cfg']['seed']} for e in episodes)
        cfg=test[task]['test_id'][0]
        world=make(cfg,sector_policy='learned' if task=='ic_r1' else 'rule',government_policy='learned' if task=='ic_g5' else 'configured')
        for period in range(30):
            actions=world.run_agents()
            for action,ob in zip(actions['sectors'],world.environment.observations()['sectors']):
                assert .3*ob['base_output']-1e-4<=action.production_plan<=2*ob['base_output']+1e-4
                assert 0<=action.inventory_target<=.5 and action.capex_share+action.ai_share+action.rd_share<=.05+1e-10
                if task=='ic_r1':assert action.price_change==0
            _,_,done,_=world.step(actions)
            assert done==(period==29)
        expected,_=run_episode(cfg,'learned',101)
        actual=world.evaluate()
        assert np.isclose(actual['final_fill_rate'],expected['final_fill_rate'],atol=1e-12)
        report['adapter_runs'].append({'task':task,'fill':actual['final_fill_rate'],'matched':True})
    queue={}
    schedule_capacity(queue,3,100,4,.1)
    schedule_capacity(queue,3,50,4,.1)
    assert queue=={7:15.0} and 6 not in queue
    write_csv(ROOT/'benchmark_splits/training_scenario_indices.csv',indices)
    report.update({'train_validation_test_disjoint':True,'checkpoint_and_source_hashes_match':True,'queue_timing_and_accumulation':True,'training_episodes':len(indices),'periods_per_adapter':30})
    out=ROOT/'benchmark_results/upgrade_summary/verification.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
