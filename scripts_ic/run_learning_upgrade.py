import argparse,json,os,time
from concurrent.futures import ProcessPoolExecutor,as_completed
from learning.ppo import train_one
from scripts_ic.upgrade_common import ROOT,scenario

def main():
    p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=6);p.add_argument('--steps',type=int,default=12000);p.add_argument('--seeds',default='101,102,103,104,105,106,107,108,109,110');a=p.parse_args()
    seeds=[int(x) for x in a.seeds.split(',')]
    out=ROOT/'benchmark_splits';out.mkdir(exist_ok=True)
    manifest={task:{split:[scenario(task,split,i) for i in range(100)] for split in ['test_id','test_ood']} for task in ['ic_r1','ic_g5']}
    path=out/'locked_scenarios_v3.json'
    data=json.dumps(manifest,ensure_ascii=False,indent=2)
    if path.exists():assert path.read_text(encoding='utf-8')==data,'Frozen test split changed'
    else:path.write_text(data,encoding='utf-8')
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        futures=[ex.submit(train_one,task,s,a.steps) for task in ['ic_r1','ic_g5'] for s in seeds]
        for f in as_completed(futures):print(json.dumps(f.result()),flush=True)

if __name__=='__main__':main()
