def calculate_participation(
    logs: list[dict],
    current_step: int,
    total_labs: int = 10,
    community_start_step: int = 11,
) -> dict:

    target_logs = [
        log for log in logs
        if log["step"] <= current_step
    ]

    visited_labs = {
        log["target"]
        for log in target_logs
        if log["action"] == "visit_lab"
    }

    visit_rate = min(1.0, len(visited_labs) / total_labs)

    active_steps = {
        log["step"]
        for log in target_logs
        if log["action"] == "login_community"
    }

    community_steps = max(
        0, current_step - community_start_step + 1
    )

    if community_steps > 0:
        community_rate = min(
            1.0,
            len(active_steps) / max(5, community_steps)
        )
    else:
        community_rate = 0.0

    participation = (
        0.5 * visit_rate
        + 0.5 * community_rate
    )

    return {
        "participation": participation,
        "visit_rate": visit_rate,
        "community_rate": community_rate,
        "visited_labs": len(visited_labs),
        "active_step_count": len(active_steps),
    }


def calculate_contribution(
    logs: list[dict],
    current_step: int,
    community_start_step: int = 11,
) -> dict:

    target_logs = [
        log for log in logs
        if log["step"] <= current_step
    ]

    visited_labs = {
        log["target"]
        for log in target_logs
        if log["action"] == "visit_lab"
    }

    rated_labs = {
        log["target"]
        for log in target_logs
        if log["action"] == "post_visit_comment"
    }

    evaluation_rate = (
        len(rated_labs & visited_labs) / len(visited_labs)
        if visited_labs else 0.0
    )

    reply_count = sum(
        log["action"] == "reply"
        for log in target_logs
    )

    opinion_count = sum(
        log["action"] == "express_opinion"
        for log in target_logs
    )

    completed_task_count = len({
        log["target"]
        for log in target_logs
        if log["action"] == "complete_task"
    })

    opportunity_steps = max(
        0, current_step - community_start_step + 1
    )

    if opportunity_steps > 0:
        denominator = max(5, opportunity_steps)

        discussion_rate = min(
            1.0,
            (reply_count + opinion_count) / denominator
        )

        task_rate = min(
            1.0,
            completed_task_count / denominator
        )
    else:
        discussion_rate = 0.0
        task_rate = 0.0

    contribution = (
        0.3 * evaluation_rate
        + 0.4 * discussion_rate
        + 0.3 * task_rate
    )

    return {
        "contribution": contribution,
        "evaluation_rate": evaluation_rate,
        "discussion_rate": discussion_rate,
        "task_rate": task_rate,
        "visited_lab_count": len(visited_labs),
        "rated_lab_count": len(rated_labs & visited_labs),
        "reply_count": reply_count,
        "opinion_count": opinion_count,
        "completed_task_count": completed_task_count,
        "opportunity_steps": opportunity_steps,
    }


def calculate_reliability(
    logs: list[dict],
    current_step: int,
    community_start_step: int = 11,
    task_duration: int = 5,
) -> dict:

    target_logs = [
        log for log in logs
        if log["step"] <= current_step
    ]

    # SYSTEMログから期限終了Taskを取得
    expired_tasks = {
        log["target"]
        for log in target_logs
        if (
            log["action"] == "task_created"
            and log["agent_id"] == "SYSTEM"
            and log["step"] + task_duration - 1
                < current_step
        )
    }

    completed_tasks = {
        log["target"]
        for log in target_logs
        if log["action"] == "complete_task"
    }

    expired_count = len(expired_tasks)
    completed_count = len(completed_tasks & expired_tasks)

    # F：期限終了Taskの履行率
    if expired_count > 0:
        completion_ratio = completed_count / expired_count
        experience_factor = min(1.0, expired_count / 3)
        fulfillment_rate = (
            completion_ratio * experience_factor
        )
    else:
        fulfillment_rate = 0.0

    login_steps = {
        log["step"]
        for log in target_logs
        if log["action"] == "login_community"
    }

    community_steps = max(
        0, current_step - community_start_step + 1
    )

    if community_steps > 0:
        continuity_rate = min(
            1.0,
            len(login_steps) / max(5, community_steps)
        )
    else:
        continuity_rate = 0.0

    has_left = any(
        log["action"] == "leave_community"
        for log in target_logs
    )

    stay = float(bool(login_steps) and not has_left)

    reliability = (
        0.4 * fulfillment_rate
        + 0.4 * continuity_rate
        + 0.2 * stay
    )

    return {
        "reliability": reliability,
        "fulfillment_rate": fulfillment_rate,
        "continuity_rate": continuity_rate,
        "stay": stay,
        "expired_task_count": expired_count,
        "completed_task_count": completed_count,
        "login_step_count": len(login_steps),
        "community_steps": community_steps,
        "has_left": has_left,
    }



def calculate_governance(
    logs: list[dict],
    current_step: int,
    community_start_step: int = 11,
) -> dict:

    # 評価時点までのログ
    target_logs = [
        log for log in logs
        if log["step"] <= current_step
    ]

    # 発生済みIssue（SYSTEMログ）
    created_issues = {
        log["target"]
        for log in target_logs
        if (
            log["agent_id"] == "SYSTEM"
            and log["action"] == "issue_created"
        )
    }

    # 発生Issue数
    issue_count = len(created_issues)

    # Agentが閲覧したIssue
    viewed_issues = {
        log["target"]
        for log in target_logs
        if (
            log["action"] == "view_issue"
            and log["target"] in created_issues
        )
    }

    # Agentが意見表明したIssue
    opinion_issues = {
        log["target"]
        for log in target_logs
        if (
            log["action"] == "express_opinion"
            and log["target"] in viewed_issues
        )
    }

    # 議題が未発生の場合
    if issue_count == 0:
        issue_view_rate = 0.0
        opinion_rate = 0.0
    else:
        issue_view_rate = min(
            1.0,
            len(viewed_issues) / issue_count,
        )

        opinion_rate = min(
            1.0,
            len(opinion_issues) / issue_count,
        )

    # Governance Trust
    governance = (
        0.5 * issue_view_rate
        + 0.5 * opinion_rate
    )

    return {
        "governance": governance,
        "issue_view_rate": issue_view_rate,
        "opinion_rate": opinion_rate,
        "created_issue_count": issue_count,
        "viewed_issue_count": len(viewed_issues),
        "opinion_issue_count": len(opinion_issues),
    }