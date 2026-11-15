
import csv
import math
import os
import random
import statistics

from config.settings import NUM_AGENTS
from src.utils.random_utils import generate_agents, save_agent_profiles
from experiments.compare_permission_methods import (
    PERMISSION_METHODS,
    run_single_method,
)

OUTPUT_DIR = "results/multi_seed"

# 最初は3 Seedで動作確認し、問題なければ30に変更
NUM_SEEDS = 3
START_SEED = 0


def save_csv(rows, output_path):
    if not rows:
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = list(
        dict.fromkeys(
            key
            for row in rows
            for key in row.keys()
        )
    )

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


def summarize_metrics(rows):
    summary_rows = []

    for method in PERMISSION_METHODS:
        method_rows = [
            row for row in rows
            if row["method"] == method
        ]

        summary = {
            "method": method,
            "seed_count": len(method_rows),
        }

        # 評価指標の列を取得
        metric_names = [
            key
            for key in method_rows[0].keys()
            if key not in ("seed", "method")
        ]

        for metric_name in metric_names:
            values = [
                row[metric_name]
                for row in method_rows
                if (
                    isinstance(
                        row.get(metric_name),
                        (int, float),
                    )
                    and not isinstance(
                        row[metric_name], bool
                    )
                    and math.isfinite(row[metric_name])
                )
            ]

            summary[f"{metric_name}_n"] = len(values)

            if values:
                summary[f"{metric_name}_mean"] = (
                    statistics.mean(values)
                )

                summary[f"{metric_name}_std"] = (
                    statistics.stdev(values)
                    if len(values) >= 2
                    else None
                )
            else:
                summary[f"{metric_name}_mean"] = None
                summary[f"{metric_name}_std"] = None

        summary_rows.append(summary)

    return summary_rows


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_results = []

    for seed in range(
        START_SEED,
        START_SEED + NUM_SEEDS,
    ):
        print()
        print("=" * 60)
        print(f"Seed {seed} 実験開始")
        print("=" * 60)

        seed_dir = os.path.join(
            OUTPUT_DIR,
            f"seed_{seed:03d}",
        )

        os.makedirs(seed_dir, exist_ok=True)

        # Seedごとに初期Agentを生成
        random.seed(seed)
        initial_agents = generate_agents(NUM_AGENTS)

        save_agent_profiles(
            initial_agents,
            os.path.join(
                seed_dir,
                "initial_agents.csv",
            ),
        )

        # 同じ初期Agentを4方式で比較
        for method in PERMISSION_METHODS:
            print(f"  実行中: {method}")

            metrics = run_single_method(
                initial_agents=initial_agents,
                method=method,
                seed=seed,
                output_dir=seed_dir,
            )

            all_results.append({
                "seed": seed,
                "method": method,
                **metrics,
            })

            popr = metrics.get(
                "POPR",
                metrics.get("community_participation_rate")
            )

            print(
                f"    Vote={metrics['vote_permission_count']}, "
                f"Proposal={metrics['proposal_permission_count']}, "
                f"POPR={popr:.3f}"
            )

        # Seed単位でも途中結果を保存
        save_csv(
            all_results,
            os.path.join(
                OUTPUT_DIR,
                "all_seed_metrics.csv",
            ),
        )

        print(f"Seed {seed} 完了")

    # 全Seedの集計
    summary_rows = summarize_metrics(all_results)

    save_csv(
        summary_rows,
        os.path.join(
            OUTPUT_DIR,
            "summary_metrics.csv",
        ),
    )

    print()
    print("=" * 60)
    print("複数Seed実験 完了")
    print(f"Seed数: {NUM_SEEDS}")
    print(f"方式数: {len(PERMISSION_METHODS)}")
    print(
        "総実行回数: "
        f"{NUM_SEEDS * len(PERMISSION_METHODS)}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
