"""Vote/Proposal権限取得率を近づけた4方式を比較する実験。
実行：python3 -m experiments.matched_acquisition_comparison_retry --seeds 1
"""

import argparse
import csv
import itertools
import json
import math
import os
import random
import statistics
from copy import deepcopy
from experiments.compare_permission_methods import NUM_AGENTS, generate_agents, run_single_method

BASE = {
    "Stamp": {"chat": 1, "vote": 3, "proposal": 5},
    "PT": {"vote": 0.4, "proposal": 0.6},
    "CT": {"vote": 0.4, "proposal": 0.6},
    "Multi": {"vote_pt": 0.3, "vote_ct": 0.3,
              "proposal_rt": 0.5, "proposal_gt": 0.5},
}

def candidates(method):
    base = BASE[method]
    if method == "Stamp":
        for vote, proposal in itertools.product((2, 3, 4), (3, 4, 5)):
            if proposal < vote:
                continue
            t = deepcopy(base)
            t.update(vote=vote, proposal=proposal)
            yield t
    elif method in ("PT", "CT"):
        for vote, proposal in itertools.product((0.3, 0.35, 0.4, 0.45, 0.5),
                                                (0.45, 0.5, 0.55, 0.6, 0.65, 0.7)):
            t = deepcopy(base)
            t.update(vote=vote, proposal=proposal)
            yield t
    else:
        # 最初はAND条件の2閾値を同時調整する候補を探索。
        for vote, proposal in itertools.product((0.2, 0.25, 0.3, 0.35, 0.4),
                                                (0.35, 0.4, 0.45, 0.5, 0.55, 0.6)):
            t = deepcopy(base)
            t.update(vote_pt=vote, vote_ct=vote,
                     proposal_rt=proposal, proposal_gt=proposal)
            yield t

def write_csv(path, rows):
    if not rows:
        return
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

def run(method, thresholds, seed, initial_agents):
    return run_single_method(initial_agents=initial_agents, method=method, seed=seed,
                             permission_thresholds=deepcopy(thresholds), save_outputs=False)

def permission_rates(metrics):
    # run_single_methodの既存指標名を使用
    vote = metrics.get("vote_permission_count")
    proposal = metrics.get("proposal_permission_count")
    if vote is None or proposal is None:
        raise KeyError("metrics に vote_permission_count / proposal_permission_count がありません")
    return vote / NUM_AGENTS, proposal / NUM_AGENTS

def summary(rows):
    groups = {}
    meta = {"seed", "method", "thresholds", "vote_permission_rate_calibrated",
            "proposal_permission_rate_calibrated"}
    for row in rows:
        groups.setdefault((row["method"], row["thresholds"]), []).append(row)
    output = []
    for (method, thresholds), group in groups.items():
        for metric in group[0]:
            if metric in meta:
                continue
            vals = [float(row[metric]) for row in group
                    if isinstance(row.get(metric), (int, float))
                    and not isinstance(row[metric], bool)
                    and math.isfinite(row[metric])]
            if vals:
                output.append({"method": method, "thresholds": thresholds,
                               "metric": metric, "n": len(vals),
                               "mean": statistics.mean(vals),
                               "std_dev": statistics.stdev(vals) if len(vals) > 1 else 0.0})
    return output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibration-seeds", type=int, default=3)
    parser.add_argument("--evaluation-seeds", type=int, default=30)
    parser.add_argument("--target-vote", type=float, default=0.65)
    parser.add_argument("--target-proposal", type=float, default=0.25)
    parser.add_argument("--calibration-seed-start", type=int, default=1000)
    parser.add_argument("--evaluation-seed-start", type=int, default=2000)
    args = parser.parse_args()
    if args.calibration_seeds < 1 or args.evaluation_seeds < 1:
        parser.error("seed数は1以上にしてください")
    if not (0 <= args.target_vote <= 1 and 0 <= args.target_proposal <= 1):
        parser.error("targetは0〜1で指定してください")
    cal_seeds = list(range(args.calibration_seed_start,
                           args.calibration_seed_start + args.calibration_seeds))
    eval_seeds = list(range(args.evaluation_seed_start,
                            args.evaluation_seed_start + args.evaluation_seeds))
    if set(cal_seeds) & set(eval_seeds):
        parser.error("探索seedと評価seedは重複させないでください")
    root = "results/matched_acquisition"
    os.makedirs(root, exist_ok=True)
    cal_agents = {}
    for seed in cal_seeds:
        random.seed(seed)
        cal_agents[seed] = generate_agents(NUM_AGENTS)
    calibration_rows, selected_rows, evaluation_rows = [], [], []
    selected = {}
    for method in BASE:
        best = None
        candidate_list = list(candidates(method))
        print(f"{method}: {len(candidate_list)}候補 × {len(cal_seeds)}探索seed", flush=True)
        for t in candidate_list:
            votes, proposals = [], []
            for seed in cal_seeds:
                metrics = run(method, t, seed, cal_agents[seed])
                v, p = permission_rates(metrics)
                votes.append(v)
                proposals.append(p)
            mv, mp = statistics.mean(votes), statistics.mean(proposals)
            # 両取得率を同じ重みで目標値に近づける
            error = (mv - args.target_vote) ** 2 + (mp - args.target_proposal) ** 2
            row = {"method": method, "thresholds": json.dumps(t, sort_keys=True),
                   "calibration_seeds": len(cal_seeds), "vote_rate": mv,
                   "proposal_rate": mp, "target_vote": args.target_vote,
                   "target_proposal": args.target_proposal, "squared_error": error}
            calibration_rows.append(row)
            if best is None or error < best[0]:
                best = (error, t, mv, mp)
        _, t, mv, mp = best
        selected[method] = deepcopy(t)
        selected_rows.append({"method": method,
                              "thresholds": json.dumps(t, sort_keys=True),
                              "calibration_vote_rate": mv,
                              "calibration_proposal_rate": mp,
                              "target_vote": args.target_vote,
                              "target_proposal": args.target_proposal,
                              "squared_error": best[0]})
        print(f"選択 {method}: Vote={mv:.3f} Proposal={mp:.3f} {t}", flush=True)
    # 探索後に独立seedで最終評価。全方式で同じAgent初期状態を使用する。
    for i, seed in enumerate(eval_seeds, 1):
        random.seed(seed)
        initial_agents = generate_agents(NUM_AGENTS)
        for method, t in selected.items():
            metrics = run(method, t, seed, initial_agents)
            v, p = permission_rates(metrics)
            evaluation_rows.append({"seed": seed, "method": method,
                                    "thresholds": json.dumps(t, sort_keys=True),
                                    "vote_permission_rate_calibrated": v,
                                    "proposal_permission_rate_calibrated": p,
                                    **metrics})
            print(f"[{i}/{len(eval_seeds)}] {method}: Vote={v:.3f} Proposal={p:.3f}",
                  flush=True)
    write_csv(os.path.join(root, "calibration.csv"), calibration_rows)
    write_csv(os.path.join(root, "matched_conditions.csv"), selected_rows)
    write_csv(os.path.join(root, "results.csv"), evaluation_rows)
    write_csv(os.path.join(root, "summary.csv"), summary(evaluation_rows))
    print(f"完了: {root} (CSV 4ファイル)")


if __name__ == "__main__":
    main()