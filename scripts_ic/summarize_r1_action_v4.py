"""Verify the R1 action diagnostic and summarize matched action swaps."""
import csv
import hashlib
import json

import numpy as np
import pandas as pd

from scripts_ic.upgrade_common_v4 import ROOT

ARMS = ('rule', 'learned', 'learned_plan', 'learned_inventory', 'learned_capex')


def interval(matrix, rng, iterations=2000):
    means = []
    for _ in range(iterations):
        seeds = rng.integers(matrix.shape[0], size=matrix.shape[0])
        scenarios = rng.integers(matrix.shape[1], size=matrix.shape[1])
        means.append(matrix[np.ix_(seeds, scenarios)].mean())
    return np.quantile(means, [.025, .975])


def main():
    out = ROOT / 'benchmark_results/r1_action_diagnostic_v4'
    df = pd.read_csv(out / 'episode_metrics.csv')
    meta = json.loads((out / 'metadata.json').read_text(encoding='utf-8'))
    scenarios = meta['scenario_count']
    seeds = meta['training_seeds']
    assert len(df) == scenarios * len(seeds) * len(ARMS)
    assert set(df.arm) == set(ARMS)
    for arm in ARMS:
        part = df[df.arm == arm]
        assert not part.duplicated(['training_seed', 'scenario_id']).any()
        assert set(part.training_seed) == set(seeds)
        assert set(part.scenario_id) == set(range(scenarios))
    p1 = pd.read_csv(ROOT / 'benchmark_results/p1_v4/run_metrics.csv')
    p1 = p1[(p1.task == 'ic_r1') & (p1.split == 'test_id')]
    learned = df[df.arm == 'learned'].merge(
        p1[p1.policy == 'learned'][['training_seed', 'scenario_id', 'final_fill_rate']],
        on=['training_seed', 'scenario_id'], suffixes=('_new', '_p1'), validate='one_to_one')
    rule = df[df.arm == 'rule'].merge(
        p1[p1.policy == 'rule'][['scenario_id', 'final_fill_rate']],
        on='scenario_id', suffixes=('_new', '_p1'), validate='many_to_one')
    error = max(float(np.abs(learned.final_fill_rate_new - learned.final_fill_rate_p1).max()),
                float(np.abs(rule.final_fill_rate_new - rule.final_fill_rate_p1).max()))
    assert error < 1e-12, error
    matrices = {
        arm: df[df.arm == arm].pivot(index='training_seed', columns='scenario_id',
                                     values='final_fill_rate').loc[seeds, range(scenarios)].to_numpy()
        for arm in ARMS
    }
    rng = np.random.default_rng(20261026)
    rows = []
    for arm in ARMS[1:]:
        delta = 100 * (matrices[arm] - matrices['rule'])
        low, high = interval(delta, rng)
        rows.append({'arm': arm, 'paired_episodes': delta.size,
                     'mean_difference_pp': float(delta.mean()),
                     'ci_low_pp': float(low), 'ci_high_pp': float(high),
                     'fraction_above_rule': float((delta > 0).mean())})
    with (out / 'paired_effects.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    meta['checkpoint_sha256'] = {
        str(seed): hashlib.sha256((ROOT / f'learning/results_v4/ic_r1/seed_{seed}/best.pt').read_bytes()).hexdigest()
        for seed in seeds}
    meta['diagnostic_code_sha256'] = hashlib.sha256(
        (ROOT / 'scripts_ic/diagnose_r1_policy_v4.py').read_bytes()).hexdigest()
    (out / 'metadata.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'verification.json').write_text(json.dumps({
        'status': 'PASS', 'episodes': len(df), 'locked_test_id_scenarios': scenarios,
        'training_seeds': len(seeds), 'arms': len(ARMS),
        'max_abs_final_fill_difference_vs_p1': error,
        'bootstrap': 'Independent resampling of training instances and locked scenarios; 2000 draws.'
    }, indent=2), encoding='utf-8')
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == '__main__':
    main()
