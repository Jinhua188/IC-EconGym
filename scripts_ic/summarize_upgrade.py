from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from scripts_ic.upgrade_common import ROOT,write_csv

def bootstrap_interval(matrix,rng):
    matrix=np.atleast_2d(matrix);b=1000
    draws=[]
    for _ in range(b):
        ix=rng.integers(matrix.shape[0],size=matrix.shape[0]);jx=rng.integers(matrix.shape[1],size=matrix.shape[1]);draws.append(matrix[np.ix_(ix,jx)].mean())
    return np.quantile(draws,[.025,.975]).tolist()

def main():
    out=ROOT/'benchmark_results/upgrade_summary';out.mkdir(parents=True,exist_ok=True)
    fig=ROOT/'paper/figures';fig.mkdir(exist_ok=True);rng=np.random.default_rng(7331)
    p1=pd.read_csv(ROOT/'benchmark_results/p1_v3/run_metrics.csv');summary=[];paired=[]
    for (task,split,policy),df in p1.groupby(['task','split','policy']):
        row={'task':task,'split':split,'policy':policy,'trajectories':len(df),'training_instances':10 if policy=='learned' else 0}
        for key in ['final_fill_rate','value_added','fiscal_spend','private_spend','max_price','welfare']:
            row[key]=float(df[key].mean())
        matrix=df.pivot(index='training_seed',columns='scenario_id',values='final_fill_rate').values if policy=='learned' else df.sort_values('scenario_id')['final_fill_rate'].values[None,:]
        row['fill_ci_low'],row['fill_ci_high']=bootstrap_interval(matrix,rng)
        summary.append(row)
        if policy=='learned':
            refname='rule' if task=='ic_r1' else 'uniform'
            ref=p1[(p1.task==task)&(p1.split==split)&(p1.policy==refname)].sort_values('scenario_id')['final_fill_rate'].values
            delta=matrix-ref[None,:];ci=bootstrap_interval(delta,rng)
            paired.append({'task':task,'split':split,'reference':refname,'mean_fill_difference_pp':float(delta.mean()*100),'ci_low_pp':ci[0]*100,'ci_high_pp':ci[1]*100})
    write_csv(out/'algorithm_summary.csv',summary);write_csv(out/'learned_paired_effects.csv',paired)
    fig1,axes=plt.subplots(2,2,figsize=(10,7),layout='constrained')
    for ax,(task,split) in zip(axes.flat,[('ic_r1','test_id'),('ic_r1','test_ood'),('ic_g5','test_id'),('ic_g5','test_ood')]):
        rows=[r for r in summary if r['task']==task and r['split']==split]
        names=[r['policy'] for r in rows];v=np.array([r['final_fill_rate'] for r in rows])*100
        low=np.array([r['fill_ci_low'] for r in rows])*100;hi=np.array([r['fill_ci_high'] for r in rows])*100
        ax.errorbar(v,np.arange(len(rows)),xerr=np.maximum(np.stack([v-low,hi-v]),0),fmt='o',capsize=3)
        ax.set_yticks(np.arange(len(rows)),names,fontsize=8);ax.set_title(task+' / '+split);ax.set_xlabel('Final-demand fill rate (%)');ax.grid(axis='x',alpha=.2)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.tick_params(axis='x',labelsize=9)
    fig1.savefig(fig/'v3_algorithm_generalization.png',dpi=180);plt.close(fig1)
    figure,axs=plt.subplots(1,2,figsize=(10,3.6),layout='constrained')
    cost=[]
    for ax,task in zip(axs,['ic_r1','ic_g5']):
        for seed in range(101,111):
            path=ROOT/'learning/results'/task/f'seed_{seed}';df=pd.read_csv(path/'learning_curve.csv');ax.plot(df.environment_steps,df.mean_reward,alpha=.45,linewidth=1)
            m=json.loads((path/'metadata.json').read_text(encoding='utf-8'));cost.append({'task':task,'seed':seed,'training_steps':m['environment_steps'],'validation_steps':1200,'wall_seconds':m['wall_seconds'],'parameters':m['parameters'],'checkpoint_sha256':m['checkpoint_sha256']})
        ax.set_title(task+' / ten independent training runs');ax.set_xlabel('Environment steps');ax.set_ylabel('Normalized training reward');ax.grid(alpha=.2)
    figure.savefig(fig/'v3_learning_curves.png',dpi=180);plt.close(figure);write_csv(out/'training_cost.csv',cost)
    robust=pd.read_csv(ROOT/'robustness/run_metrics.csv');rsummary=[]
    for (task,rule,policy),df in robust.groupby(['task','rationing_rule','policy']):
        refname='rule' if task=='ic_r1' else 'uniform'
        cols=['parameter_id','import_case','scenario_seed'];ref=robust[(robust.task==task)&(robust.rationing_rule==rule)&(robust.policy==refname)]
        pairs=df.merge(ref[cols+['final_fill_rate']],on=cols,suffixes=('','_ref'));delta=(pairs.final_fill_rate-pairs.final_fill_rate_ref)*100
        max_per_case=robust[(robust.task==task)&(robust.rationing_rule==rule)].groupby(cols).final_fill_rate.max().rename('best').reset_index()
        regret=df.merge(max_per_case,on=cols)
        rsummary.append({'task':task,'rationing_rule':rule,'policy':policy,'runs':len(df),'fill_mean':float(df.final_fill_rate.mean()),'fill_p05':float(df.final_fill_rate.quantile(.05)),'paired_difference_mean_pp':float(delta.mean()),'wins_fraction':float((delta>1e-7).mean()),'losses_fraction':float((delta<-1e-7).mean()),'within_candidate_mean_regret_pp':float(((regret.best-regret.final_fill_rate)*100).mean()),'within_candidate_max_regret_pp':float(((regret.best-regret.final_fill_rate)*100).max())})
    write_csv(out/'robustness_summary.csv',rsummary)
    figure,axs=plt.subplots(1,2,figsize=(10,3.5),layout='constrained')
    for ax,task in zip(axs,['ic_r1','ic_g5']):
        df=robust[(robust.task==task)&(robust.rationing_rule=='internal_first')]
        refname='rule' if task=='ic_r1' else 'uniform';keys=['parameter_id','import_case','scenario_seed']
        a=df[df.policy=='learned'];b=df[df.policy==refname];m=a.merge(b[keys+['final_fill_rate']],on=keys,suffixes=('','_ref'))
        effects=m.assign(delta=(m.final_fill_rate-m.final_fill_rate_ref)*100).groupby('parameter_id').delta.mean()
        ax.hist(effects,bins=25,color='#326b9e');ax.axvline(0,color='black',linewidth=1);ax.set_title(task+' / 200 joint parameter samples');ax.set_xlabel('Learned minus rule fill rate (pp)');ax.set_ylabel('Parameter samples')
    figure.savefig(fig/'v3_joint_robustness.png',dpi=180);plt.close(figure)
    external=pd.read_csv(ROOT/'external_validation/trajectories.csv');figure,ax=plt.subplots(figsize=(9,3.8),layout='constrained')
    observed=external[external.model=='capacity_queue'];x=np.arange(len(observed));ax.plot(x,observed.observed_monthly_capacity/1000,'ko-',label='Observed',markersize=3)
    for name,group in external.groupby('model'):ax.plot(x,group.modeled_monthly_capacity/1000,label=name)
    ax.axvspan(7.5,11.5,color='#d6dce7',alpha=.4);ax.axvspan(11.5,19.5,color='#e4f0e4',alpha=.4)
    ax.set_xticks(x[::2],observed.quarter.values[::2],rotation=45);ax.set_ylabel('Monthly capacity\n(thousand 8-inch-equivalent wafers)');ax.legend(fontsize=8);ax.grid(alpha=.2)
    figure.savefig(fig/'v3_external_capacity.png',dpi=180);plt.close(figure)
    meta={'p0':json.loads((ROOT/'benchmark_results/p0_v3/checks.json').read_text(encoding='utf-8')),'p1':json.loads((ROOT/'benchmark_results/p1_v3/metadata.json').read_text(encoding='utf-8')),'p2':json.loads((ROOT/'external_validation/metadata.json').read_text(encoding='utf-8')),'p3':json.loads((ROOT/'robustness/metadata.json').read_text(encoding='utf-8')),'paired_learning_effects':paired,'algorithm_summary':summary,'robustness_summary':rsummary,'training_cost':cost}
    if (ROOT/'benchmark_results/p4_v3/metadata.json').exists():meta['p4']=json.loads((ROOT/'benchmark_results/p4_v3/metadata.json').read_text(encoding='utf-8'))
    (out/'evidence_summary.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'paired_learning_effects':paired,'robustness_summary':rsummary},ensure_ascii=False))

if __name__=='__main__':main()
