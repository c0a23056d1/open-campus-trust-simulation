
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
        
def save_permission_aquisition_steps(
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

def calculate_permission_acquisition_metrics(
    agents,
    activity_logs,
):
    """
    権限取得・Stage移行に関する補助評価を計算する。
    """

    # Agentごとの権限取得Step
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

    # 初回権限取得Stepを記録
    for log in activity_logs:
        permission = action_to_permission.get(log.action)

        if permission is None:
            continue

        if log.agent_id not in acquisition_steps:
            continue

        current_step = acquisition_steps[log.agent_id][permission]

        if current_step is None or log.step < current_step:
            acquisition_steps[log.agent_id][permission] = log.step

    # 権限取得Agent数(最終状態)
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

    # ログから取得できた権限取得人数
    logged_counts = {
        permission: sum(
            values[permission] is not None
            for values in acquisition_steps.values()
        )
        for permission in ("chat", "vote", "proposal")
    }

    metrics = {
        "stage_1_to_2_rate": stage_1_to_2_rate,
        "stage_2_to_3_rate": stage_2_to_3_rate,

        "mean_chat_acquisition_step": mean_acquisition_step("chat"),
        "mean_vote_acquisition_step": mean_acquisition_step("vote"),
        "mean_proposal_acquisition_step": mean_acquisition_step("proposal"),

        "logged_chat_acquisition_count": logged_counts["chat"],
        "logged_vote_acquisition_count": logged_counts["vote"],
        "logged_proposal_acquisition_count": logged_counts["proposal"],
    }

    return metrics, acquisition_steps



def calculate_permission_opportunities(
    agents,
    activity_logs,
):
    community_start = OC_STEPS + 1
    community_end = OC_STEPS + COMMUNITY_STEPS

    proposal_deadline = (
        community_end - PROPOSAL_VOTING_DURATION - 1
    )

    # Agentごとの権限取得Step
    unlock_steps = {
        agent.agent_id: {}
        for agent in agents
    }

    # Agentごとの離脱Step
    leave_steps = {}

    # Issue・Proposalの生成Step
    issue_steps = []
    proposal_steps = []

    # ======================================
    # ① Activity Logを最後まで読み込む
    # ======================================
    for log in activity_logs:

        if log.action in (
            "unlocked_chat",
            "unlocked_vote",
            "unlocked_proposal",
        ):
            permission = log.action.replace("unlocked_", "")

            unlock_steps[log.agent_id].setdefault(
                permission,
                log.step,
            )

        elif log.action == "leave_community":
            leave_steps[log.agent_id] = log.step

        elif log.action == "issue_created":
            issue_steps.append(log.step)

        elif log.action == "proposal":
            proposal_steps.append(log.step)

    # ======================================
    # ② Issue・Proposalの利用可能期間
    # ======================================

    issue_available_steps = set()

    if issue_steps:
        first_issue_step = min(issue_steps)

        issue_available_steps = set(
            range(first_issue_step, community_end + 1)
        )

    proposal_vote_steps = set()

    for created_step in proposal_steps:
        for step in range(
            created_step + 1,
            min(
                community_end,
                created_step + PROPOSAL_VOTING_DURATION - 1,
            ) + 1,
        ):
            proposal_vote_steps.add(step)

    # ======================================
    # ③ 権限利用機会の判定
    # ======================================

    opportunity_agents = {
        "chat": set(),
        "vote": set(),
        "proposal": set(),
    }

    for agent in agents:
        agent_id = agent.agent_id
        acquired = unlock_steps[agent_id]
        leave_step = leave_steps.get(agent_id)

        for permission in ("chat", "vote", "proposal"):

            unlock_step = acquired.get(permission)

            if unlock_step is None:
                continue

            first_usable_step = max(
                community_start,
                unlock_step + 1,
            )

            last_usable_step = community_end

            if leave_step is not None:
                last_usable_step = min(
                    last_usable_step,
                    leave_step - 1,
                )

            if first_usable_step > last_usable_step:
                continue

            usable_steps = range(
                first_usable_step,
                last_usable_step + 1,
            )

            if permission == "chat":
                opportunity_agents["chat"].add(agent_id)

            elif permission == "vote":
                if any(
                    step in issue_available_steps
                    or step in proposal_vote_steps
                    for step in usable_steps
                ):
                    opportunity_agents["vote"].add(agent_id)

            elif permission == "proposal":
                if any(
                    step <= proposal_deadline
                    for step in usable_steps
                ):
                    opportunity_agents["proposal"].add(agent_id)

    return opportunity_agents


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

    # ======================================
    # 継続参加：POPR / CR
    # ======================================

    login_steps_by_agent = {
        agent.agent_id: set()
        for agent in agents
    }

    for log in community_logs:
        if log.action == "login_community":
            login_steps_by_agent[log.agent_id].add(log.step)

    login_agents = {
        agent_id
        for agent_id, steps in login_steps_by_agent.items()
        if steps
    }

    community_participant_count = len(login_agents)

    popr = (
        community_participant_count / agent_count
        if agent_count > 0 else None
    )

    cr = (
        sum(
            len(steps) / COMMUNITY_STEPS
            for steps in login_steps_by_agent.values()
        ) / agent_count
        if agent_count > 0 and COMMUNITY_STEPS > 0
        else None
    )

    # ======================================
    # Governance参加：GPR / VPR / PPR
    # ======================================

    vote_agents = {
        log.agent_id
        for log in community_logs
        if log.action in ("vote", "vote_proposal")
    }

    proposal_agents = {
        log.agent_id
        for log in community_logs
        if log.action == "proposal"
    }

    governance_agents = vote_agents | proposal_agents

    def participation_rate(target_agents):
        if community_participant_count == 0:
            return None
        return len(target_agents) / community_participant_count

    gpr = participation_rate(governance_agents)
    vpr = participation_rate(vote_agents)
    ppr = participation_rate(proposal_agents)

    # ======================================
    # 権限利用：CUR / VUR / PUR
    # ======================================

    chat_agents = {
        log.agent_id
        for log in community_logs
        if log.action in ("chat", "reply")
    }

    opportunity_agents = calculate_permission_opportunities(
        agents,
        activity_logs,
    )

    def utilization_rate(users, permission):
        eligible = opportunity_agents[permission]

        if not eligible:
            return None

        return len(users & eligible) / len(eligible)

    cur = utilization_rate(chat_agents, "chat")
    vur = utilization_rate(vote_agents, "vote")
    pur = utilization_rate(proposal_agents, "proposal")

    # ======================================
    # Community貢献：Task
    # ======================================

    completed_task_logs = [
        log for log in community_logs
        if log.action == "complete_task"
    ]

    task_completion_count = len(completed_task_logs)

    task_completion_agents = {
        log.agent_id
        for log in completed_task_logs
    }

    task_completion_agent_rate = (
        len(task_completion_agents) / community_participant_count
        if community_participant_count > 0 else None
    )

    # ======================================
    # 権限取得
    # ======================================

    chat_count = sum(a.chat_permission for a in agents)
    vote_count = sum(a.vote_permission for a in agents)
    proposal_count = sum(a.proposal_permission for a in agents)

    def acquisition_rate(count):
        return count / agent_count if agent_count > 0 else None

    # ======================================
    # 結果
    # ======================================

    return {
        "agent_count": agent_count,

        # 権限取得
        "chat_permission_count": chat_count,
        "vote_permission_count": vote_count,
        "proposal_permission_count": proposal_count,

        "chat_permission_rate": acquisition_rate(chat_count),
        "vote_permission_rate": acquisition_rate(vote_count),
        "proposal_permission_rate": acquisition_rate(proposal_count),

        # 継続参加
        "community_participant_count": community_participant_count,
        "POPR": popr,
        "CR": cr,

        # 既存コードとの互換性
        "community_participation_rate": popr,

        # Governance参加
        "GPR": gpr,
        "VPR": vpr,
        "PPR": ppr,

        # 権限利用
        "CUR": cur,
        "VUR": vur,
        "PUR": pur,

        # 既存コードとの互換性
        "vote_utilization_rate": vur,
        "proposal_utilization_rate": pur,

        # Community貢献
        "task_completion_count": task_completion_count,
        "task_completion_agent_count": len(task_completion_agents),
        "task_completion_agent_rate": task_completion_agent_rate,

        # Community行動件数
        "community_login_count": sum(
            len(steps)
            for steps in login_steps_by_agent.values()
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

        # Proposal評価
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

        # 権限取得・Stage移行の補助評価
        **acquisition_metrics,
    }


def run_single_method(initial_agents, method, seed):
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

    method_dir = os.path.join(OUTPUT_DIR, method)
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

    # ============================================
    # 権限取得・Stage移行の補助評価
    # ============================================

    acquisition_metrics, acquisition_steps = (
        calculate_permission_acquisition_metrics(
            agents,
            activity_logs,
        )
    )

    # Agentごとの権限取得Stepを保存
    save_permission_aquisition_steps(
        agents,
        acquisition_steps,
        os.path.join(
            method_dir,
            "permission_acquisition_steps.csv",
        ),
    )

    # ============================================
    # Community Outcome + 補助評価
    # ============================================
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
