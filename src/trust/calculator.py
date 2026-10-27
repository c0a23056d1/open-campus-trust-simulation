def calculate_participation(
    logs: list[dict],
    current_step: int,
    total_labs: int = 6,
    community_start_step: int = 6,
) -> dict:

    #現在のstepまでのログを取得
    target_logs = [
        log for log in logs
        if log["step"] <= current_step
    ]

    #訪問した研究室を重複無しで取得
    visited_labs = {
        log["target"]
        for log in target_logs
        if log["action"] == "visit_lab"
    }

    #研究室訪問率
    visit_rate = len(visited_labs) / total_labs

    #コミュニティ活動を行ったstepを取得
    active_steps = {
        log["step"]
        for log in target_logs
        if log["action"] == "login_community"
    }

    #コミュニティ活動が可能だったstep数
    community_steps = max(
        0,
        current_step - community_start_step + 1
    )

    # コミュニティ活動率
    # 最低評価期間を5Stepとし、初回ログインによる過大評価を防ぐ
    minimum_community_steps = 5

    if community_steps > 0:
        community_rate = min(
            1.0,
            len(active_steps)
            / max(minimum_community_steps, community_steps)
        )
    else:
        community_rate = 0.0

    #Participation Trust
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
    community_start_step: int = 6,
) -> dict:

    # 現在のStepまでのログを取得
    target_logs = [
        log for log in logs
        if log["step"] <= current_step
    ]

    # 訪問した研究室を取得（重複なし）
    visited_labs = {
        log["target"]
        for log in target_logs
        if log["action"] == "visit_lab"
    }

    # 評価した研究室を取得（重複なし）
    rated_labs = {
        log["target"]
        for log in target_logs
        if log["action"] == "rate_lab"
    }

    # E：研究室評価率
    if len(visited_labs) > 0:
        evaluation_rate = (
            len(rated_labs & visited_labs) / len(visited_labs)
        )
    else:
        evaluation_rate = 0.0

    # 返信回数
    reply_count = sum(
        1 for log in target_logs
        if log["action"] == "reply_chat"
    )

    # 意見表明回数
    opinion_count = sum(
        1 for log in target_logs
        if log["action"] == "express_opinion"
    )

    # タスク完了回数
    completed_task_count = sum(
        1 for log in target_logs
        if log["action"] == "complete_task"
    )

    # Step 6以降の活動機会数
    opportunity_steps = max(
        0,
        current_step - community_start_step + 1
    )

    # 最低評価期間
    minimum_community_steps = 5

    # D：議論貢献率
    if opportunity_steps > 0:
        discussion_rate = min(
            1.0,
            (reply_count + opinion_count)
            / max(minimum_community_steps, opportunity_steps)
        )
    else:
        discussion_rate = 0.0

    # T：タスク完了率
    if opportunity_steps > 0:
        task_rate = min(
            1.0,
            completed_task_count
            / max(minimum_community_steps, opportunity_steps)
        )
    else:
        task_rate = 0.0
    # Contribution Trust
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
    community_start_step: int = 6,
) -> dict:

    # 現在のStepまでのログを取得
    target_logs = [
        log for log in logs
        if log["step"] <= current_step
    ]

    # 引き受けたタスクを取得（重複なし）
    accepted_tasks = {
        log["target"]
        for log in target_logs
        if log["action"] == "accept_task"
    }

    # 完了したタスクを取得（重複なし）
    completed_tasks = {
        log["target"]
        for log in target_logs
        if log["action"] == "complete_task"
    }

    # F：タスク履行率（実績件数も考慮）
    accepted_count = len(accepted_tasks)
    completed_count = len(completed_tasks & accepted_tasks)

    minimum_task_count = 3

    if accepted_count > 0:
        completion_ratio = completed_count / accepted_count
        experience_factor = min(
            1.0,
            accepted_count / minimum_task_count
        )
        fulfillment_rate = completion_ratio * experience_factor
    else:
        fulfillment_rate = 0.0

    # ログインしたStepを取得（重複なし）
    login_steps = {
        log["step"]
        for log in target_logs
        if log["action"] == "login_community"
    }

    # コミュニティ活動可能Step数
    community_steps = max(
        0,
        current_step - community_start_step + 1
    )

    # C：ログイン継続率
    minimum_community_steps = 5

    if community_steps > 0:
        continuity_rate = min(
            1.0,
            len(login_steps)
            / max(minimum_community_steps, community_steps)
        )
    else:
        continuity_rate = 0.0

    # S：コミュニティ継続状態
    has_left = any(
        log["action"] == "leave_community"
        for log in target_logs
    )

    if len(login_steps) > 0 and not has_left:
        stay = 1.0
    else:
        stay = 0.0

    # Reliability Trust
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
        "accepted_task_count": accepted_count,
        "completed_task_count": completed_count,
        "login_step_count": len(login_steps),
        "community_steps": community_steps,
        "has_left": has_left,
    }
def calculate_governance(
    logs: list[dict],
    current_step: int,
    community_start_step: int = 6,
) -> dict:

    # 現在のStepまでのログを取得
    target_logs = [
        log for log in logs
        if log["step"] <= current_step
    ]

    # 閲覧した議題を取得（重複なし）
    viewed_issues = {
        log["target"]
        for log in target_logs
        if log["action"] == "view_issue"
    }

    # ガバナンス議論に参加した議題を取得
    discussed_issues = {
        log["target"]
        for log in target_logs
        if log["action"] == "join_governance_discussion"
    }

    # 意見を表明した議題を取得
    opinion_issues = {
        log["target"]
        for log in target_logs
        if log["action"] == "express_opinion"
    }

    # 閲覧済み議題への議論参加・意見表明
    valid_discussions = discussed_issues & viewed_issues
    valid_opinions = opinion_issues & viewed_issues

    # Step 6以降の活動機会数
    opportunity_steps = max(
        0,
        current_step - community_start_step + 1
    )

    # 最低評価期間
    minimum_community_steps = 5

    # I：議題閲覧率
    if opportunity_steps > 0:
        denominator = max(
            minimum_community_steps,
            opportunity_steps
        )

        issue_view_rate = min(
            1.0,
            len(viewed_issues) / denominator
        )

        # Dg：ガバナンス議論参加率
        governance_discussion_rate = min(
            1.0,
            len(valid_discussions) / denominator
        )

        # O：意見表明率
        opinion_rate = min(
            1.0,
            len(valid_opinions) / denominator
        )

    else:
        issue_view_rate = 0.0
        governance_discussion_rate = 0.0
        opinion_rate = 0.0

    # Governance Trust
    governance = (
        0.4 * issue_view_rate
        + 0.3 * governance_discussion_rate
        + 0.3 * opinion_rate
    )

    return {
        "governance": governance,
        "issue_view_rate": issue_view_rate,
        "governance_discussion_rate": governance_discussion_rate,
        "opinion_rate": opinion_rate,
        "viewed_issue_count": len(viewed_issues),
        "discussed_issue_count": len(valid_discussions),
        "opinion_issue_count": len(valid_opinions),
        "opportunity_steps": opportunity_steps,
    }