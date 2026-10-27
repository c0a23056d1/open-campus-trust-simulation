
import copy
import csv
import json
import os
import random

from collections import Counter

from config.settings import (
    NUM_AGENTS,
    OC_STEPS,
    COMMUNITY_STEPS,
    LABS,
    RANDOM_SEED,
    ISSUE_INTERVAL,
    PROPOSAL_VOTING_DURATION,
)

from src.utils.random_utils import (
    generate_agents,
    save_agent_profiles,
)

from src.models.activity_log import save_activity_logs

from src.simulation.simulator import (
    run_open_campus_simulation,
    run_community_simulation,
)


PERMISSION_METHODS = ["Stamp", "PT", "CT", "Multi"]

OUTPUT_DIR = "results/comparison"


def save_passports(passports, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

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

        for passport in passports:
            writer.writerow([
                passport["passport_id"],
                passport["agent_id"],
                passport["step"],
                passport["participation"],
                passport["contribution"],
                passport["reliability"],
                passport["governance"],
                json.dumps(passport["interests"], ensure_ascii=False),
                json.dumps(passport["evidence"], ensure_ascii=False),
            ])


def save_proposals(proposals, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

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

def calculate_permission_acquisition_metrics(
    agents,
    activity_logs,
):
    """
    権限取得人数、Stage移行率、
    権限取得Stepを計算する。
    """

    acquisition_steps = {
        agent.agent_id: {
            "chat": None,
            "vote": None,
            "proposal": None,
        }
        for agent in agents
    }

    action_to_permission = {
        "unlocked_chat": "chat",
        "unlocked_vote": "vote",
        "unlocked_proposal": "proposal",
    }

    # 権限を初めて取得したStepを記録
    for log in activity_logs:
        permission = action_to_permission.get(log.action)

        if permission is None:
            continue

        if log.agent_id not in acquisition_steps:
            continue

        current_step = acquisition_steps[
            log.agent_id
        ][permission]

        if current_step is None or log.step < current_step:
            acquisition_steps[
                log.agent_id
            ][permission] = log.step

    # 最終的な権限取得人数
    chat_count = sum(
        bool(agent.chat_permission)
        for agent in agents
    )

    vote_count = sum(
        bool(agent.vote_permission)
        for agent in agents
    )

    proposal_count = sum(
        bool(agent.proposal_permission)
        for agent in agents
    )

    # Stage移行率
    stage_1_to_2_rate = (
        vote_count / chat_count
        if chat_count > 0 else None
    )

    stage_2_to_3_rate = (
        proposal_count / vote_count
        if vote_count > 0 else None
    )

    # 権限取得Stepの平均
    def mean_acquisition_step(permission):
        steps = [
            values[permission]
            for values in acquisition_steps.values()
            if values[permission] is not None
        ]

        if not steps:
            return None

        return sum(steps) / len(steps)

    metrics = {
        "stage_1_to_2_rate": stage_1_to_2_rate,
        "stage_2_to_3_rate": stage_2_to_3_rate,

        "mean_chat_acquisition_step": (
            mean_acquisition_step("chat")
        ),
        "mean_vote_acquisition_step": (
            mean_acquisition_step("vote")
        ),
        "mean_proposal_acquisition_step": (
            mean_acquisition_step("proposal")
        ),

        "logged_chat_acquisition_count": sum(
            values["chat"] is not None
            for values in acquisition_steps.values()
        ),
        "logged_vote_acquisition_count": sum(
            values["vote"] is not None
            for values in acquisition_steps.values()
        ),
        "logged_proposal_acquisition_count": sum(
            values["proposal"] is not None
            for values in acquisition_steps.values()
        ),
    }

    return metrics, acquisition_steps

def save_permission_acquisition_steps(
    agents,
    acquisition_steps,
    output_path,
):
    """
    Agentごとの権限取得StepをCSVに保存する。
    """

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.writer(f)

        writer.writerow([
            "agent_id",
            "chat_acquisition_step",
            "vote_acquisition_step",
            "proposal_acquisition_step",
            "final_chat_permission",
            "final_vote_permission",
            "final_proposal_permission",
        ])

        for agent in agents:
            steps = acquisition_steps[agent.agent_id]

            writer.writerow([
                agent.agent_id,
                steps["chat"],
                steps["vote"],
                steps["proposal"],
                agent.chat_permission,
                agent.vote_permission,
                agent.proposal_permission,
            ])


def calculate_comparison_metrics(
    agents,
    activity_logs,
    proposal_metrics,
    acquisition_metrics,
):
    agent_count = len(agents)

    community_logs = [
        log for log in activity_logs
        if log.phase == "community"
        and log.agent_id != "SYSTEM"
    ]

    # Communityに1回以上ログインしたAgent
    login_agents = {
        log.agent_id
        for log in community_logs
        if log.action == "login_community"
    }

    # Vote権限を実際に利用したAgent
    vote_agents = {
        log.agent_id
        for log in community_logs
        if log.action in ("vote", "vote_proposal")
    }

    # Proposal権限を実際に利用したAgent
    proposal_agents = {
        log.agent_id
        for log in community_logs
        if log.action == "proposal"
    }

    chat_count = sum(a.chat_permission for a in agents)
    vote_count = sum(a.vote_permission for a in agents)
    proposal_count = sum(a.proposal_permission for a in agents)

    return {
        "agent_count": agent_count,

        "chat_permission_count": chat_count,
        "vote_permission_count": vote_count,
        "proposal_permission_count": proposal_count,

        "chat_permission_rate": chat_count / agent_count,
        "vote_permission_rate": vote_count / agent_count,
        "proposal_permission_rate": proposal_count / agent_count,

        "community_participation_rate": (
            len(login_agents) / agent_count
        ),

        "vote_utilization_rate": (
            len(vote_agents) / vote_count
            if vote_count > 0 else None
        ),

        "proposal_utilization_rate": (
            len(proposal_agents) / proposal_count
            if proposal_count > 0 else None
        ),

        "community_login_count": sum(
            log.action == "login_community"
            for log in community_logs
        ),

        "chat_action_count": sum(
            log.action == "chat"
            for log in community_logs
        ),

        "reply_action_count": sum(
            log.action == "reply"
            for log in community_logs
        ),

        "issue_vote_count": sum(
            log.action == "vote"
            for log in community_logs
        ),

        "proposal_vote_count": sum(
            log.action == "vote_proposal"
            for log in community_logs
        ),

        "submitted_count": proposal_metrics["submitted_count"],
        "APC": proposal_metrics["APC"],
        "APQ": proposal_metrics["APQ"],
        "SPQ": proposal_metrics["SPQ"],
        "PAR": proposal_metrics["PAR"],
        "TAQ": proposal_metrics["TAQ"],

        "rejected_insufficient_votes": (
            proposal_metrics["rejected_insufficient_votes"]
        ),
        "rejected_insufficient_approval": (
            proposal_metrics["rejected_insufficient_approval"]
        ),
        "open_count": proposal_metrics["open_count"],
    }


def run_single_method(
    initial_agents, 
    method, 
    seed,
    output_dir=None,
):
    # 同じ初期Agentを複製
    agents = copy.deepcopy(initial_agents)

    # 各方式の乱数Seedを統一
    random.seed(seed)

    environment, activity_logs, passport_history = (
        run_open_campus_simulation(
            agents=agents,
            labs=LABS,
            oc_steps=OC_STEPS,
            permission_method=method,
        )
    )

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
            permission_method=method,
            return_proposal_results=True,
        )
    )

    # method_dir = os.path.join(OUTPUT_DIR, method)
    # os.makedirs(method_dir, exist_ok=True)

    if output_dir is None:
        method_dir = os.path.join(OUTPUT_DIR, method)
    else:
        method_dir = os.path.join(output_dir, method)
    
    os.makedirs(method_dir, exist_ok=True)

    save_activity_logs(
        activity_logs,
        os.path.join(method_dir, "activity_logs.csv"),
    )

    save_passports(
        passport_history,
        os.path.join(method_dir, "trust_passports.csv"),
    )

    save_proposals(
        proposals,
        os.path.join(method_dir, "proposal_details.csv"),
    )

    # 権限取得・Stage移行の評価
    acquisition_metrics, acquisition_steps = (
        calculate_permission_acquisition_metrics(
            agents,
            activity_logs,
        )
    )

    # 権限取得Stepを保存
    save_permission_acquisition_steps(
        agents,
        acquisition_steps,
        os.path.join(
            method_dir,
            "permission_acquisition_steps.csv",
        ),
    )

    metrics = calculate_comparison_metrics(
        agents,
        activity_logs,
        proposal_metrics,
        acquisition_metrics,
    )

    with open(
        os.path.join(method_dir, "metrics.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    return metrics


def save_comparison(results):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_path = os.path.join(
        OUTPUT_DIR,
        "permission_comparison.csv",
    )

    rows = [
        {"method": method, **metrics}
        for method, metrics in results.items()
    ]

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def main():
    print("=" * 60)
    print("Permission Control Method Comparison")
    print("=" * 60)

    # Agentの初期状態を共通化
    random.seed(RANDOM_SEED)
    initial_agents = generate_agents(NUM_AGENTS)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    save_agent_profiles(
        initial_agents,
        os.path.join(OUTPUT_DIR, "initial_agents.csv"),
    )

    results = {}

    for method in PERMISSION_METHODS:
        print()
        print(f"---- {method}方式 ----")

        metrics = run_single_method(
            initial_agents=initial_agents,
            method=method,
            seed=RANDOM_SEED,
        )

        results[method] = metrics

        print(
            f"Chat={metrics['chat_permission_count']}, "
            f"Vote={metrics['vote_permission_count']}, "
            f"Proposal={metrics['proposal_permission_count']}"
        )

        print(
            f"Community参加率="
            f"{metrics['community_participation_rate']:.3f}"
        )

        print(
            f"Proposal提出={metrics['submitted_count']}, "
            f"採択={metrics['APC']}"
        )

    output_path = save_comparison(results)

    print()
    print("=" * 60)
    print("4方式比較完了")
    print(f"比較結果: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
