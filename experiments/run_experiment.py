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

    activity_logs, proposals, proposal_metrics = (
        run_community_simulation(
            agents=agents,
            activity_logs=activity_logs,
            community_steps=COMMUNITY_STEPS,
            start_step=OC_STEPS + 1,
            environment=environment,
            issue_interval=ISSUE_INTERVAL,
            passport_history=passport_history,
            total_labs=len(LABS),
            community_start_step=OC_STEPS + 1,
            return_proposal_results=True,
        )
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

    # ==========================================
    # Proposal結果の集計
    # ==========================================

    print()
    print("---- Proposal Metrics ----")
    print()

    print(
        f"提出Proposal数："
        f"{proposal_metrics['submitted_count']}"
    )

    print(
        f"採択Proposal数(APC):"
        f"{proposal_metrics['APC']}"
    )

    if proposal_metrics["APQ"] is not None:
        print(
            f"採択Proposal平均品質(APQ): "
            f"{proposal_metrics['APQ']:.3f}"
        )
    else:
        print("採択Proposal平均品質(APQ): None")

    if proposal_metrics["SPQ"] is not None:
        print(
            f"提出Proposal平均品質(SPQ): "
            f"{proposal_metrics['SPQ']:.3f}"
        )
    else:
        print("提出Proposal平均品質(SPQ): None")

    if proposal_metrics["PAR"] is not None:
        print(
            f"Proposal採択率 (PAR): "
            f"{proposal_metrics['PAR']:.3f}"
        )
    else:
        print("Proposal採択率 (PAR): None")

    print(
        f"採択Proposal品質合計(TAQ): "
        f"{proposal_metrics['TAQ']:.3f}"
    )

    print(
        f"最低投票数不足による不採択: "
        f"{proposal_metrics['rejected_insufficient_votes']}"
    )

    print(
        f"賛成率不足による不採択: "
        f"{proposal_metrics['rejected_insufficient_approval']}"
    )

    print(
        f"投票期間中のProposal数: "
        f"{proposal_metrics['open_count']}"
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

    # ==========================================
    # Proposal結果をCSVに保存
    # ==========================================

    proposal_output_path = (
        "results/proposals/proposal_details.csv"
    )

    os.makedirs(
        os.path.dirname(proposal_output_path),
        exist_ok=True,
    )

    with open(
        proposal_output_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)
        writer.writerow([
            "proposal_id",
            "agent_id",
            "created_step",
            "relevance",
            "feasibility",
            "benefit",
            "PQS",
            "total_votes",
            "yes_votes",
            "no_votes",
            "approval_rate",
            "status",
            "rejection_reason",
        ])

        for proposal in proposals:

            writer.writerow([
                proposal.proposal_id,
                proposal.agent_id,
                proposal.created_step,
                proposal.relevance,
                proposal.feasibility,
                proposal.benefit,
                proposal.quality,
                proposal.total_votes,
                proposal.yes_votes,
                proposal.no_votes,
                proposal.approval_rate,
                proposal.status,
                proposal.rejection_reason,
            ])

    print(
        f"Proposal詳細を{proposal_output_path}に保存しました。"
    )

    # ==========================================
    # Proposal結果をJSONに保存
    # ==========================================

    metrics_output_path = (
        "results/proposals/proposal_metrics.csv"
    )

    with open(
        metrics_output_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            list(proposal_metrics.keys())
        )

        writer.writerow(
            list(proposal_metrics.values())
        )

    print(
        f"Proposal評価指標を{metrics_output_path}に保存しました。"
    )


if __name__ == "__main__":
    main()