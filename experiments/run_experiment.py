import random
from dataclasses import asdict
import csv
import json
import os

from config.settings import (
    NUM_AGENTS,
    OC_STEPS,
    COMMUNITY_STEPS,
    LABS,
    RANDOM_SEED,
    ISSUE_INTERVAL,
)

from src.utils.random_utils import (
    generate_agents,
    save_agent_profiles,
)

from src.models.activity_log import (
    save_activity_logs,
)

from src.simulation.simulator import (
    run_open_campus_simulation,
    run_community_simulation,
)

from collections import Counter


def main():

    print("=" * 60)
    print("Open Campus Trust Simulation")
    print("=" * 60)

    # ==========================================
    # Random Seed
    # ==========================================

    random.seed(RANDOM_SEED)

    # ==========================================
    # Agent生成
    # ==========================================

    agents = generate_agents(NUM_AGENTS)

    print(f"生成Agent数: {len(agents)}")

    save_agent_profiles(
        agents,
        "results/agents/agent_profiles.csv",
    )

    # ==========================================
    # Open Campus Phase
    # ==========================================

    environment, activity_logs, passport_history = (
        run_open_campus_simulation(
            agents=agents,
            labs=LABS,
            oc_steps=OC_STEPS,
        )
    )

    # ==========================================
    # Community Phase
    # ==========================================

    activity_logs = run_community_simulation(
        agents=agents,
        activity_logs=activity_logs,
        community_steps=COMMUNITY_STEPS,
        start_step=OC_STEPS + 1,
        environment=environment,
        issue_interval=ISSUE_INTERVAL,
        passport_history=passport_history,
        total_labs=len(LABS),
        community_start_step=OC_STEPS + 1,
    )

    # ==========================================
    # 結果表示
    # ==========================================

    print()
    print("---- Open Campus Result ----")
    print()

    for agent in agents[:5]:

        print(f"Agent ID: {agent.agent_id}")
        print(
            f"Activity: "
            f"{agent.activity:.3f}"
        )
        print(
            f"Stamp: "
            f"{agent.stamp_count}"
        )
        print(
            f"Visited Labs: "
            f"{len(agent.visited_labs)}"
        )
        print(
            f"Chat Permission: "
            f"{agent.chat_permission}"
        )
        print()

    # Communityログだけ抽出
    community_logs = [
        log
        for log in activity_logs
        if log.phase == "community"
    ]

    print("---- Community Result ----")
    print()
    print(
        f"Community Log数: "
        f"{len(community_logs)}"
    )

    print(
        f"全Activity Log数: "
        f"{len(activity_logs)}"
    )

    # ==========================================
    # Trust計算用のログ形式に変換
    # ==========================================

    trust_logs = [
        asdict(log)
        for log in activity_logs
        if log.agent_id != "SYSTEM"
    ]

    print(
        f"Trust計算対象ログ数: {len(trust_logs)}"
    )

    # ==========================================
    # CSV保存
    # ==========================================

    save_activity_logs(
        activity_logs,
        "results/logs/activity_logs.csv",
    )

    print(
        "Activity Logを "
        "results/logs/activity_logs.csv "
        "に保存しました。"
    )

    print()
    print("---- Permission Summary ----")

    print(
        "Chat権限取得者：",
        sum(agent.chat_permission for agent in agents)
    )

    print(
        "Vote権限取得者：",
        sum(agent.vote_permission for agent in agents)
    )

    print(
        "Proposal権限取得者：",
        sum(agent.proposal_permission for agent in agents)
    )

    community_actions = Counter(
    log.action
    for log in activity_logs
    if log.phase == "community"
    )

    print()
    print("---- Community Action Counts ----")

    for action, count in community_actions.items():
        print(f"{action}: {count}")

        # Trust PassportをCSVに保存
    output_path = "results/passports/trust_passports.csv"

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "passport_id",
            "agent_id",
            "step",
            "participation",
            "contribution",
            "reliability",
            "governance",
            "interests",
            "evidence",
        ])

        for passport in passport_history:
            writer.writerow([
                passport["passport_id"],
                passport["agent_id"],
                passport["step"],
                passport["participation"],
                passport["contribution"],
                passport["reliability"],
                passport["governance"],
                json.dumps(
                    passport["interests"],
                    ensure_ascii=False,
                ),
                json.dumps(
                    passport["evidence"],
                    ensure_ascii=False,
                ),
            ])

    print(
        f"Trust Passportを{output_path}に保存しました。"
    )
    print(
        f"生成Passport数: {len(passport_history)}"
    )


if __name__ == "__main__":
    main()