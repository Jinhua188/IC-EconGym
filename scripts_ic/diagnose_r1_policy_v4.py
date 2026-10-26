"""Matched, held-out R1 action-component interventions for the 15-sector model."""
import argparse
import csv
import hashlib
import json
from copy import deepcopy

import numpy as np

from scripts_ic.upgrade_common_v4 import (
    GovernmentAction, ICEnvironment, ROOT, RuleSectorPolicy, metrics,
    project_sector, sector_actions,
)
from learning.ppo_v4 import apply_learned, features, load_policy, torch

ARMS = ('rule', 'learned', 'learned_plan', 'learned_inventory', 'learned_capex')


def episode(cfg, net, arm):
    env = ICEnvironment(deepcopy(cfg))
    rule = RuleSectorPolicy(cfg)
    rng = np.random.default_rng(cfg['seed'] + 731)
    rows = []
    for _ in range(cfg['periods']):
        obs = env.observations()['sectors']
        if arm == 'rule':
            actions = sector_actions(env, 'rule', rng, rule)
        else:
            with torch.no_grad():
                a, _, _, _ = net(torch.from_numpy(features(env, 'ic_r1')), deterministic=True)
            learned, _ = apply_learned(env, 'ic_r1', a.numpy())
            if arm == 'learned':
                actions = learned
            else:
                actions = sector_actions(env, 'rule', rng, rule)
                component = {'learned_plan': 'production_plan',
                             'learned_inventory': 'inventory_target',
                             'learned_capex': 'capex_share'}[arm]
                for base, new, o in zip(actions, learned, obs):
                    setattr(base, component, getattr(new, component))
                    project_sector(base, o, cfg)
        _, _, _, rec = env.step(actions, GovernmentAction.zeros())
        rows.append({
            'plan_ratio': float(np.mean([x.production_plan / max(o['base_output'], 1)
                                         for x, o in zip(actions, obs)])),
            'inventory_target': float(np.mean([x.inventory_target for x in actions])),
            'capex_share': float(np.mean([x.capex_share for x in actions])),
            'binding_plan_fraction': rec['binding_plan_count'] / 15,
            'internal_orders': rec['internal_orders'],
        })
    result = metrics(env)
    result.update({k: float(np.mean([r[k] for r in rows])) for k in rows[0]})
    return result


def write_rows(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--scenarios', type=int, default=100)
    p.add_argument('--seeds', type=int, default=10)
    args = p.parse_args()
    locked = ROOT / 'benchmark_splits_v4/locked_scenarios_v4.json'
    cases = json.loads(locked.read_text(encoding='utf-8'))['ic_r1']['test_id']
    if not (1 <= args.scenarios <= len(cases) and 1 <= args.seeds <= 10):
        raise ValueError('scenarios must be 1..100 and seeds 1..10')
    out = ROOT / 'benchmark_results/r1_action_diagnostic_v4'
    out.mkdir(parents=True, exist_ok=True)
    all_rows = []
    for seed in range(101, 101 + args.seeds):
        net = load_policy('ic_r1', seed)
        for i, cfg in enumerate(cases[:args.scenarios]):
            for arm in ARMS:
                all_rows.append({'scenario_id': i, 'scenario_seed': cfg['seed'],
                                 'training_seed': seed, 'arm': arm, **episode(cfg, net, arm)})
        print(f'seed {seed}: {len(all_rows)} episodes', flush=True)
    write_rows(out / 'episode_metrics.csv', all_rows)
    summary = []
    for arm in ARMS:
        selected = [r for r in all_rows if r['arm'] == arm]
        summary.append({'arm': arm, 'episodes': len(selected),
                        **{key: float(np.mean([r[key] for r in selected])) for key in
                           ('final_fill_rate', 'welfare', 'private_spend', 'plan_ratio',
                            'inventory_target', 'capex_share', 'binding_plan_fraction',
                            'internal_orders')}})
    write_rows(out / 'summary.csv', summary)
    (out / 'metadata.json').write_text(json.dumps({
        'task': 'ic_r1', 'split': 'test_id', 'scenario_count': args.scenarios,
        'training_seeds': list(range(101, 101 + args.seeds)),
        'arms': ARMS, 'locked_scenarios_sha256': hashlib.sha256(locked.read_bytes()).hexdigest(),
        'design': 'One learned action component replaces the rule action on each evolving hybrid trajectory; no retraining.',
        'scope': 'Model-internal intervention; not observed economic or policy effects.'
    }, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
