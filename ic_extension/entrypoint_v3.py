"""Run a v0.3 world from a task configuration or a locked benchmark scenario."""
import argparse,json
from pathlib import Path
from .entrypoint import load_task
from .iewm13_v3 import make

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--problem_scene',default='ic_g5')
    p.add_argument('--sector-policy',default='rule')
    p.add_argument('--government-policy',default='configured')
    p.add_argument('--learning-seed',type=int,default=101)
    p.add_argument('--split',choices=['test_id','test_ood'])
    p.add_argument('--scenario',type=int,default=0)
    p.add_argument('--out',type=Path,default=Path('results_ic/v3_run.json'))
    args=p.parse_args()
    if args.split:
        path=Path(__file__).resolve().parents[1]/'benchmark_splits/locked_scenarios_v3.json'
        cfg=json.loads(path.read_text(encoding='utf-8'))[args.problem_scene][args.split][args.scenario]
    else:cfg=load_task(args.problem_scene)
    world=make(cfg,sector_policy=args.sector_policy,government_policy=args.government_policy,learning_seed=args.learning_seed)
    for _ in range(cfg.get('periods',30)):world.step(world.run_agents())
    result={'engine':'v0.3-experimental','config':cfg,'sector_policy':args.sector_policy,'government_policy':args.government_policy,'checkpoint_seed':args.learning_seed,'metrics':world.evaluate(),'trajectory':world.environment.history}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(args.out),'metrics':result['metrics']},ensure_ascii=False))

if __name__=='__main__':main()
