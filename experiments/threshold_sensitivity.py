"""4方式の閾値感度分析。MultiではOFATと同時変更を区別して評価する。
実行: python3 -m experiments.threshold_sensitivity --seeds 30
前提: run_single_method(..., permission_thresholds=..., save_outputs=False)
"""
import argparse
import csv
import json
import math
import os
import random
import statistics
from copy import deepcopy
from experiments.compare_permission_methods import (
    NUM_AGENTS, RANDOM_SEED, generate_agents, run_single_method,
)

BASE = {
    "Stamp": {"chat": 1, "vote": 3, "proposal": 5},
    "PT": {"vote": 0.4, "proposal": 0.6},
    "CT": {"vote": 0.4, "proposal": 0.6},
    "Multi": {"vote_pt": 0.3, "vote_ct": 0.3,
              "proposal_rt": 0.5, "proposal_gt": 0.5},
}

def conditions():
    for method, base in BASE.items():
        yield method, "baseline", "baseline", deepcopy(base)
        if method == "Stamp":
            # スタンプ上限が5個の場合、閾値6は到達不能なため使用しない。
            variations = [("vote", 2), ("vote", 4),
                          ("proposal", 3), ("proposal", 4)]
            for key, level in variations:
                t = deepcopy(base)
                t[key] = level
                yield method, "ofat", f"{key}_{level}", t
        elif method in ("PT", "CT"):
            for key, levels in (("vote", (0.3, 0.5)),
                                ("proposal", (0.5, 0.7))):
                for level in levels:
                    t = deepcopy(base)
                    t[key] = level
                    yield method, "ofat", f"{key}_{level}", t
        else:
            for key, levels in (("vote_pt", (0.2, 0.4)),
                                ("vote_ct", (0.2, 0.4)),
                                ("proposal_rt", (0.4, 0.6)),
                                ("proposal_gt", (0.4, 0.6))):
                for level in levels:
                    t = deepcopy(base)
                    t[key] = level
                    yield method, "ofat", f"{key}_{level}", t
            # 2×2の組み合わせ分析：各権限で4条件ずつ
            for pt in (0.2, 0.4):
                for ct in (0.2, 0.4):
                    t = deepcopy(base)
                    t.update(vote_pt=pt, vote_ct=ct)
                    yield method, "joint", f"vote_pt_{pt}_ct_{ct}", t
            for rt in (0.4, 0.6):
                for gt in (0.4, 0.6):
                    t = deepcopy(base)
                    t.update(proposal_rt=rt, proposal_gt=gt)
                    yield method, "joint", f"proposal_rt_{rt}_gt_{gt}", t

def write_csv(path, rows):
    if not rows:
        return
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

def summarize(rows):
    grouped = {}
    metadata = {"seed", "method", "analysis", "condition", "thresholds"}
    for row in rows:
        key = (row["method"], row["analysis"], row["condition"], row["thresholds"])
        grouped.setdefault(key, []).append(row)
    result = []
    for (method, analysis, condition, thresholds), group in grouped.items():
        for metric in group[0]:
            if metric in metadata:
                continue
            values = [float(row[metric]) for row in group
                      if isinstance(row.get(metric), (int, float))
                      and not isinstance(row[metric], bool)
                      and math.isfinite(row[metric])]
            if values:
                result.append({
                    "method": method, "analysis": analysis,
                    "condition": condition, "thresholds": thresholds,
                    "metric": metric, "n": len(values),
                    "mean": statistics.mean(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "min": min(values), "max": max(values),
                })
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=1)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be >= 1")
    root = "results/threshold_sensitivity"
    os.makedirs(root, exist_ok=True)
    baseline_rows, sensitivity_rows = [], []
    scenarios = list(conditions())
    print(f"条件数: {len(scenarios)} / 実行回数: {len(scenarios) * args.seeds}", flush=True)
    for index in range(args.seeds):
        seed = RANDOM_SEED + index
        random.seed(seed)
        initial_agents = generate_agents(NUM_AGENTS)
        for method, analysis, condition, thresholds in scenarios:
            metrics = run_single_method(
                initial_agents=initial_agents, method=method, seed=seed,
                permission_thresholds=deepcopy(thresholds), save_outputs=False,
            )
            row = {
                "seed": seed, "method": method, "analysis": analysis,
                "condition": condition,
                "thresholds": json.dumps(thresholds, ensure_ascii=False, sort_keys=True),
                **metrics,
            }
            (baseline_rows if analysis == "baseline" else sensitivity_rows).append(row)
            print(f"[{index + 1}/{args.seeds}] {method} {analysis} {condition}: "
                  f"Vote={metrics.get('vote_permission_count')} "
                  f"Proposal={metrics.get('proposal_permission_count')}", flush=True)
    write_csv(os.path.join(root, "baseline_results.csv"), baseline_rows)
    write_csv(os.path.join(root, "baseline_summary.csv"), summarize(baseline_rows))
    write_csv(os.path.join(root, "sensitivity_results.csv"), sensitivity_rows)
    write_csv(os.path.join(root, "sensitivity_summary.csv"), summarize(sensitivity_rows))
    print(f"完了: {root} (CSV 4ファイル)")


if __name__ == "__main__":
    main()