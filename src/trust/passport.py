from config.settings import LABS

from src.trust.calculator import (
    calculate_participation,
    calculate_contribution,
    calculate_reliability,
    calculate_governance,
)

# 研究室IDと興味分野の対応表を自動生成
LAB_FIELDS = {
    lab["id"]: lab["field"]
    for lab in LABS
}


def calculate_interests(
    logs: list[dict],
    current_step: int,
) -> dict:

    # 現在のStepまでの訪問履歴を取得
    visited_labs = {
        log["target"]
        for log in logs
        if (
            log["step"] <= current_step
            and log["action"] == "visit_lab"
        )
    }

    # 分野ごとの訪問数
    field_counts = {
        field: 0
        for field in LAB_FIELDS.values()
    }

    for lab in visited_labs:
        if lab in LAB_FIELDS:
            field = LAB_FIELDS[lab]
            field_counts[field] += 1

    # 総訪問数
    total_visits = sum(field_counts.values())

    # 興味分野の割合を計算
    if total_visits > 0:
        interests = {
            field: count / total_visits
            for field, count in field_counts.items()
        }
    else:
        interests = {
            field: 0.0
            for field in field_counts
        }

    return interests

def generate_passport(
    agent_id: str,
    logs: list[dict],
    current_step: int,
    total_labs: int,
    community_start_step: int,
) -> dict:

    # 指定したAgentのログのみ取得
    agent_logs = [
        log for log in logs
        if (
            log["agent_id"] == agent_id
            and log["step"] <= current_step
        )
    ]

    # =======================================
    # SYSTEMのTask生成ログ
    # =======================================

    system_task_logs = [
        log for log in logs
        if (
            log["agent_id"] == "SYSTEM"
            and log["action"] == "task_created"
            and log["step"] <= current_step
        )
    ]

    # SYSTEMのIssue生成ログを取得
    system_issue_logs = [
        log for log in logs
        if (
            log["agent_id"] == "SYSTEM"
            and log["action"] == "issue_created"
            and log["step"] <= current_step
        )
    ]

    # RT用：対象Agentの行動ログ＋SYSTEMのTask生成ログ
    reliability_logs = agent_logs + system_task_logs
    governance_logs = agent_logs + system_issue_logs

    # 4種類のTrustを計算
    participation = calculate_participation(
        agent_logs,
        current_step,
        total_labs=total_labs,
        community_start_step=community_start_step,
    )

    contribution = calculate_contribution(
        agent_logs,
        current_step,
        community_start_step=community_start_step,
    )

    reliability = calculate_reliability(
        reliability_logs,
        current_step,
        community_start_step=community_start_step,
    )

    governance = calculate_governance(
        governance_logs,
        current_step,
        community_start_step=community_start_step,
    )

    # 興味分野を推定
    interests = calculate_interests(
        agent_logs,
        current_step,
    )

    # Trust Passportを生成
    passport = {
        "passport_id": f"TP{agent_id[1:]}",
        "agent_id": agent_id,
        "step": current_step,

        "participation": participation["participation"],
        "contribution": contribution["contribution"],
        "reliability": reliability["reliability"],
        "governance": governance["governance"],

        "interests": interests,

        "evidence": {
            "participation": participation,
            "contribution": contribution,
            "reliability": reliability,
            "governance": governance,
        },
    }

    return passport