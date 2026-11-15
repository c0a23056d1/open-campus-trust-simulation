"""権限取得率を揃えた4方式比較(調整seedと評価seedを分離)。

配置: experiments/matched_permission_rates.py
実行: python3 -m experiments.matched_permission_rate --calibration-seeds 3 --evaluation-seeds 30
事前確認: python3 -m experiments.matched_permission_rates --calibration-seeds 1 --evaluation-seeds 1
前提: compare_permission_methods.run_single_method(..., permission_thresholds=..., save_outputs=False)
"""

import argparse
import csv
import json
import math
import os
import random
import statistics
from copy import deepcopy
from experiments.compare_permission_methods import NUM_AGENTS, generate_agents, run_single_method

STAMP = {"chat": 1, "vote": 3, "proposal": 5}
BASE = {
    "PT": {"vote": 0.4, "proposal": 0.6},
    "CT": {"vote": 0.4, "proposal": 0.6},
    "Multi": {"vote_pt": 0.3, "vote_ct": 0.3, "proposal_rt": 0.5, "proposal_gt": 0.5}
}

GRIDS = {
    "PT": {"vote": [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60],
           "proposal": [0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85]},
    "CT": {"vote": [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65],
           "proposal": [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]},
    "Multi": {"vote_pt": [0.25, 0.30, 0.35, 0.40, 0.45, 0.50],
              "vote_ct": [0.25, 0.30, 0.35, 0.40, 0.45, 0.50],
              "proposal_rt": [0.45, 0.50, 0.55, 0.60, 0.65, 0.70],
              "proposal_gt": [0.45, 0.50, 0.55, 0.60, 0.65, 0.70]},
}

def write_csv(path, rows, fields=None):
    if not rows:
        return
    fields = fields or list(dict.fromkeys(k for row in rows for k in row))
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def make_agents(seed):
    random.seed(seed)
    return generate_agents(NUM_AGENTS)

def simulate(method, thresholds, seed, agents):
    # run_single_method が入力Agentを変更しても他条件に波及させない
    return run_single_method(
        initial_agents=deepcopy(agents), method=method, seed=seed,
        permission_thresholds=deepcopy(thresholds), save_outputs=False,
    )

def rates(metrics):
    def get(rate_key, count_key):
        value = metrics.get(rate_key)
        if value is None:
            value = float(metrics[count_key]) / NUM_AGENTS
        value = float(value)
        if not math.isfinite(value):
            raise ValueError(f"Invalid {rate_key}: {value}")
        return value
    return get("vote_permission_rate", "vote_permission_count"), get("proposal_permission_rate", "proposal_permission_count")

def summary(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["method"], []).append(row)
    output = []
    metadata = {"seed", "method", "thresholds"}
    for method, group in grouped.items():
        for metric in group[0]:
            if metric in metadata:
                continue
            values = [float(r[metric]) for r in group if isinstance(r.get(metric), (int, float))
                      and not isinstance(r[metric], bool) and math.isfinite(r[metric])]
            if values:
                output.append({"method": method, "metric": metric, "n": len(values),
                               "mean": statistics.mean(values),
                               "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                               "min": min(values), "max": max(values)})
    return output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibration-seeds", type=int, default=3)
    parser.add_argument("--evaluation-seeds", type=int, default=30)
    parser.add_argument("--calibration-start", type=int, default=10000)
    parser.add_argument("--evaluation-start", type=int, default=20000)
    parser.add_argument("--passes", type=int, default=2)
    args = parser.parse_args()
    if min(args.calibration_seeds, args.evaluation_seeds, args.passes) < 1:
        parser.error("seed counts and passes must be >= 1")
    calibration_ids = list(range(args.calibration_start, args.calibration_start + args.calibration_seeds))
    evaluation_ids = list(range(args.evaluation_start, args.evaluation_start + args.evaluation_seeds))
    if set(calibration_ids) & set(evaluation_ids):
        parser.error("Calibration and evaluation seed ranges must not overlap")

    root = "results/matched_permission_rates"
    os.makedirs(root, exist_ok=True)
    initial = {seed: make_agents(seed) for seed in calibration_ids}
    calibration_rows = []
    cache = {}

    def evaluate_calibration(method, thresholds):
        key = (method, json.dumps(thresholds, sort_keys=True))
        if key in cache:
            return cache[key]
        vote_values, proposal_values = [], []
        for seed in calibration_ids:
            m = simulate(method, thresholds, seed, initial[seed])
            v, p = rates(m)
            vote_values.append(v)
            proposal_values.append(p)
        result = (statistics.mean(vote_values), statistics.mean(proposal_values))
        cache[key] = result
        calibration_rows.append({"method": method, "thresholds": key[1],
                                 "vote_permission_rate": result[0],
                                 "proposal_permission_rate": result[1],
                                 "calibration_seeds": args.calibration_seeds})
        return result

    target_vote, target_proposal = evaluate_calibration("Stamp", STAMP)
    print(f"調整目標（Stamp）: Vote={target_vote:.3%}, Proposal={target_proposal:.3%}", flush=True)

    # VoteとProposalは別々に最適化。相互依存の可能性を考慮して交互に複数パス。
    selected = {"Stamp": deepcopy(STAMP)}
    for method in ("PT", "CT", "Multi"):
        t = deepcopy(BASE[method])
        for pass_index in range(args.passes):
            for keys, target, rate_index in (
                (("vote",) if method != "Multi" else ("vote_pt", "vote_ct"), target_vote, 0),
                (("proposal",) if method != "Multi" else ("proposal_rt", "proposal_gt"), target_proposal, 1),
            ):
                for k in keys:
                    best_value, best_error = t[k], float("inf")
                    for value in GRIDS[method][k]:
                        candidate = deepcopy(t)
                        candidate[k] = value
                        observed = evaluate_calibration(method, candidate)[rate_index]
                        error = abs(observed - target)
                        if error < best_error - 1e-12:
                            best_error, best_value = error, value
                    t[k] = best_value
            v, p = evaluate_calibration(method, t)
            print(f"{method} pass {pass_index + 1}: {t} / Vote={v:.3%} Proposal={p:.3%}", flush=True)
        selected[method] = t

    matched = []
    for method in ("Stamp", "PT", "CT", "Multi"):
        t = selected[method]
        v, p = evaluate_calibration(method, t)
        matched.append({"method": method, "thresholds": json.dumps(t, sort_keys=True),
                        "target_vote_rate": target_vote, "target_proposal_rate": target_proposal,
                        "calibration_vote_rate": v, "calibration_proposal_rate": p,
                        "vote_gap_pp": (v - target_vote) * 100,
                        "proposal_gap_pp": (p - target_proposal) * 100})

    write_csv(os.path.join(root, "calibration.csv"), calibration_rows)
    write_csv(os.path.join(root, "matched_conditions.csv"), matched)
    results = []
    for i, seed in enumerate(evaluation_ids, start=1):
        agents = make_agents(seed)
        for method in ("Stamp", "PT", "CT", "Multi"):
            t = selected[method]
            m = simulate(method, t, seed, agents)
            results.append({"seed": seed, "method": method,
                            "thresholds": json.dumps(t, sort_keys=True), **m})
            v, p = rates(m)
            print(f"評価 [{i}/{len(evaluation_ids)}] {method}: Vote={v:.1%} Proposal={p:.1%}", flush=True)
    write_csv(os.path.join(root, "results.csv"), results)
    write_csv(os.path.join(root, "summary.csv"), summary(results))
    print(f"完了: {root}（CSV 4ファイル）", flush=True)
    print("注意: summary.csvで取得率の差が十分小さいか必ず確認してください。", flush=True)


if __name__ == "__main__":
    main()