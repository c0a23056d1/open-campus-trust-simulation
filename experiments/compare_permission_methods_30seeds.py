"""30 seed * 4 permission methodsの比較実験"""

import csv
import json
import math
import os
import statistics
import random

from config.settings import NUM_AGENTS, RANDOM_SEED
from src.utils.random_utils import generate_agents, save_agent_profiles
from experiments.compare_permission_methods import PERMISSION_METHODS, run_single_method

SEED_COUNT = 30
OUTPUT_DIR = "results/comparison_30seeds"

def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def numeric_metrics(metrics):
    """Return only numeric, excluding booleans and missing values. """

    return {
        key: float(value)
        for key, value in metrics.items()
        if isinstance(value, (int, float)) 
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    }

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_rows = []
    metric_names = set()
    seeds = range(RANDOM_SEED, RANDOM_SEED + SEED_COUNT)

    print(f"30seed比較結果: {SEED_COUNT} seeds × {len(PERMISSION_METHODS)} methods")

    for index, seed in enumerate(seeds, start=1):
        seed_dir = os.path.join(OUTPUT_DIR, f"seed_{seed:04d}")
        os.makedirs(seed_dir, exist_ok=True)

        # Use identical initial profiles for the four methods of this seed
        random.seed(seed)
        initial_agents = generate_agents(NUM_AGENTS)
        save_agent_profiles(
            initial_agents,
            os.path.join(seed_dir, "initial_agents.csv")
        )

        for method in PERMISSION_METHODS:
            metrics = run_single_method(
                initial_agents=initial_agents,
                method=method,
                seed=seed,
                output_dir=seed_dir,
            )

            metric_names.update(metrics.keys())
            all_rows.append({"seed": seed, "method": method, **metrics})
            print(
                f"[{index:02d}/{SEED_COUNT}] seed={seed} {method:<5}"
                f"Vote={metrics['vote_permission_count']}"
                f"Proposal={metrics['proposal_permission_count']}"
            )

    ordered_metrics = sorted(metric_names)
    raw_path = os.path.join(OUTPUT_DIR, "all_seed_results.csv")
    write_csv(raw_path, all_rows, ["seed", "method", *ordered_metrics])

    summary_rows = []
    for method in PERMISSION_METHODS:
        method_rows = [row for row in all_rows if row["method"] == method]
        for metric in ordered_metrics:
            values = [
                numeric_metrics(row).get(metric)
                for row in method_rows
            ]
            values = [value for value in values if value is not None]
            if not values:
                continue

            summary_rows.append({
                "method": method,
                "metric": metric,
                "n": len(values),
                "mean": statistics.mean(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                "min": min(values),
                "max": max(values),
            })

    summary_path = os.path.join(OUTPUT_DIR, "summary_mean_std.csv")
    write_csv(
        summary_path,
        summary_rows,
        ["method", "metric", "n", "mean", "std_dev", "min", "max"],
    )

    with open(os.path.join(OUTPUT_DIR, "experiment_setting.json"), "w", encoding="utf-8") as file:
        json.dump({
            "seed_count": SEED_COUNT,
            "start_seed": RANDOM_SEED,
            "end_seed": RANDOM_SEED + SEED_COUNT - 1,
            "methods": PERMISSION_METHODS,
            "num_agents": NUM_AGENTS,
        }, file, ensure_ascii=False, indent=2)

    print("\n30seed比較完了")
    print(f"結果: {raw_path}")
    print(f"平均・標準偏差: {summary_path}")


if __name__ == "__main__":
    main()