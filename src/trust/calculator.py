def calculate_participation(
    logs: list[dict],
    current_step: int,
    total_labs: int = 10,
    community_start_step: int = 11,
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

    #コミュニティ活動率
    if community_steps > 0:
        community_rate = len(active_steps) / community_steps
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
    community_start_step: int = 11,
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
        if log["action"] == "post_visit_comment"
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
        if log["action"] == "reply"
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

    # D：議論貢献率
    if opportunity_steps > 0:
        discussion_rate = min(
            1.0,
            (reply_count + opinion_count) / opportunity_steps
        )
    else:
        discussion_rate = 0.0

    # T：タスク完了率
    if opportunity_steps > 0:
        task_rate = min(
            1.0,
            completed_task_count / opportunity_steps
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
    community_start_step: int = 11,
) -> dict:

    # 現在のStepまでのログを取得
    target_logs = [
        log for log in logs
        if log["step"] <= current_step
    ]

    # 完了したタスクを取得（重複なし）
    completed_tasks = {
        log["target"]
        for log in target_logs
        if log["action"] == "complete_task"
    }

    # T：タスク達成実績
    task_score = min(
        1.0,
        len(completed_tasks) / 3
    )

    # ログインしたStepを取得
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
    if community_steps > 0:
        continuity_rate = (
            len(login_steps) / community_steps
        )
    else:
        continuity_rate = 0.0

    # Reliability Trust
    reliability = (
        0.4 * task_score
        + 0.6 * continuity_rate
    )

    return {
        "reliability": reliability,
        "task_score": task_score,
        "continuity_rate": continuity_rate,
        "completed_task_count": len(completed_tasks),
        "login_step_count": len(login_steps),
        "community_steps": community_steps,
    }

def calculate_governance(
    logs: list[dict],
    current_step: int,
    community_start_step: int = 11,
) -> dict:

    # 現在のStepまでのログを取得
    target_logs = [
        log for log in logs
        if log["step"] <= current_step
    ]

    # 閲覧した議題
    viewed_issues = {
        log["target"]
        for log in target_logs
        if log["action"] == "view_issue"
    }

    # 意見表明した議題
    opinion_issues = {
        log["target"]
        for log in target_logs
        if log["action"] == "express_opinion"
    }

    # V：議題閲覧実績
    view_score = min(
        1.0,
        len(viewed_issues) / 3
    )

    # O：意見表明率
    if len(viewed_issues) > 0:
        opinion_rate = (
            len(opinion_issues & viewed_issues)
            / len(viewed_issues)
        )
    else:
        opinion_rate = 0.0

    # Governance Trust
    governance = (
        0.5 * view_score
        + 0.5 * opinion_rate
    )

    return {
        "governance": governance,
        "view_score": view_score,
        "opinion_rate": opinion_rate,
        "viewed_issue_count": len(viewed_issues),
        "opinion_issue_count": len(
            opinion_issues & viewed_issues
        ),
    }