import random
from dataclasses import asdict
from src.trust.passport import generate_passport

from src.models.task import Task
from config.settings import (
    TASK_SPAWN_PROBABILITY,
    TASK_DURATION,
    TASK_TYPES,
)
from src.models.environment import Environment
from src.models.activity_log import create_activity_log
from src.simulation.behavior import (
    occurs,
    choose_lab,
    visit_lab,
    choose_open_campus_action,
    choose_community_action,
    calculate_post_visit_comment_probability,
    calculate_visit_probability,
    calculate_login_probability,
)

from src.simulation.permission import update_permissions

from src.simulation.behavior import calculate_vote_probability
from src.models.issue import Issue
from config.settings import ISSUE_TEMPLATES
from src.simulation.behavior import choose_vote_option

from src.simulation.proposal_generator import (
    generate_proposal,
)

from src.simulation.proposal_voting import (
    cast_proposal_vote,
    finalize_proposal,
)

from src.evaluation.proposal_metrics import (
    calculate_proposal_metrics,
)

from config.settings import (
    PROPOSAL_VOTING_DURATION,
)

def update_trust_passports(
    agents,
    activity_logs,
    current_step,
    passport_history,
    total_labs,
    community_start_step,
    permission_method="Stamp",
    permission_thresholds=None,
):
    """
    各Step終了時にTrust Passportを生成し、
    権限制御方式に応じて権限を更新する。
    """

    trust_logs = [
        asdict(log)
        for log in activity_logs
        if log.agent_id != "SYSTEM"
    ]

    for agent in agents:

        passport = generate_passport(
            agent_id=agent.agent_id,
            logs=trust_logs,
            current_step=current_step,
            total_labs=total_labs,
            community_start_step=community_start_step,
        )

        passport_history.append(passport)

        # Trust方式のみPassportから権限制御
        if permission_method in ("PT", "CT", "Multi"):
            unlocked_permissions = update_permissions(
                agent=agent,
                method=permission_method,
                passport=passport,
                thresholds=permission_thresholds,
            )

            for permission in unlocked_permissions:

                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=current_step,
                    phase=(
                        "open_campus"
                        if current_step < community_start_step
                        else "community"
                    ),
                    action=f"unlocked_{permission}",
                    target=permission,
                    value=True,
                )

def run_open_campus_simulation(
    agents,
    labs,
    oc_steps,
    permission_method="Stamp",
    permission_thresholds=None,
):
    """
    Open Campus Phaseを実行する。

    1 Stepにつきメイン行動は1つ。

    visit_labの場合のみ、
    Stamp取得や訪問感想投稿などの
    付随イベントが発生する。
    """

    environment = Environment()

    activity_logs = []
    passport_history = []

    # ==========================================
    # Open Campus Phase
    # ==========================================

    for step in range(1, oc_steps + 1):

        environment.current_step = step
        environment.phase = "open_campus"

        for agent in agents:

            # ==================================
            # メイン行動を1つ選択
            # ==================================

            action = choose_open_campus_action(
                agent
            )

            # ==================================
            # no_action
            # ==================================

            if action == "no_action":

                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=environment.current_step,
                    phase=environment.phase,
                    action="no_action",
                )

                continue

            # ==================================
            # visit_lab
            # ==================================

            if action == "visit_lab":

                selected_lab = choose_lab(
                    agent,
                    labs,
                )

                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=environment.current_step,
                    phase=environment.phase,
                    action="visit_lab",
                    target=selected_lab["id"],
                )

                # ----------------------------------
                # Stamp取得
                # ----------------------------------

                new_stamp = visit_lab(
                    agent,
                    selected_lab,
                )

                if new_stamp:

                    create_activity_log(
                        logs=activity_logs,
                        agent_id=agent.agent_id,
                        step=environment.current_step,
                        phase=environment.phase,
                        action="get_stamp",
                        target=selected_lab["id"],
                        value=agent.stamp_count,
                    )

                    # ------------------------------
                    # スタンプ数に基づく権限制御
                    # ------------------------------

                    # unlocked_permissions = (
                    #     update_permissions(
                    #         agent=agent,
                    #         method="Stamp",
                    #     )
                    #     if permission_method == "Stamp"
                    #     else []
                    # )
                    if permission_method == "Stamp":

                        unlocked_permissions = update_permissions(
                            agent=agent,
                            method="Stamp",
                        )

                    else:

                        unlocked_permissions = []

                        # 全方式共通：Stamp 1個でChat解放
                        if agent.stamp_count >= 1 and not agent.chat_permission:
                            agent.chat_permission = True
                            unlocked_permissions.append("chat")

                    for permission in unlocked_permissions:

                        create_activity_log(
                            logs=activity_logs,
                            agent_id=agent.agent_id,
                            step=environment.current_step,
                            phase=environment.phase,
                            action=f"unlocked_{permission}",
                            target=permission,
                            value=True
                        )

                    # ------------------------------
                    # 訪問後の感想投稿
                    # ------------------------------

                    comment_probability = (
                        calculate_post_visit_comment_probability(
                            agent
                        )
                    )

                    if occurs(comment_probability):

                        create_activity_log(
                            logs=activity_logs,
                            agent_id=agent.agent_id,
                            step=environment.current_step,
                            phase=environment.phase,
                            action="post_visit_comment",
                            target=selected_lab["id"],
                        )

                continue

            # ==================================
            # chat
            # ==================================

            if action == "chat":

                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=environment.current_step,
                    phase=environment.phase,
                    action="chat",
                    target="community",
                )

                continue

            # ==================================
            # reply
            # ==================================

            if action == "reply":

                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=environment.current_step,
                    phase=environment.phase,
                    action="reply",
                    target="community",
                )

                continue

        # このStep終了時点のTrust Passportを生成
        update_trust_passports(
            agents=agents,
            activity_logs=activity_logs,
            current_step=step,
            passport_history=passport_history,
            total_labs=len(labs),
            community_start_step=oc_steps + 1,
            permission_method=permission_method,
            permission_thresholds=permission_thresholds,
        )

    return environment, activity_logs, passport_history

def update_task(
    environment,
    current_task,
    current_step,
    task_count,
    activity_logs,
):
    """
    Taskの終了確認と新規発生を行う。
    """

    # ==================================
    # 既存Taskの終了判定
    # ==================================

    if current_task is not None:

        if not current_task.is_active(current_step):

            create_activity_log(
                logs=activity_logs,
                agent_id="SYSTEM",
                step=current_step,
                phase="community",
                action="task_ended",
                target=current_task.task_id,
            )

            current_task = None

    # ==================================
    # 新しいTaskの発生判定
    # ==================================

    if current_task is None:

        if random.random() < TASK_SPAWN_PROBABILITY:

            task_count += 1

            selected_type = random.choice(
                TASK_TYPES
            )

            task_id = f"TASK_{task_count:03d}"

            current_task = Task(
                task_id=task_id,
                name=selected_type["name"],
                required_action=selected_type["required_action"],
                start_step=current_step,
                end_step=current_step + TASK_DURATION - 1,
            )

            create_activity_log(
                logs=activity_logs,
                agent_id="SYSTEM",
                step=current_step,
                phase="community",
                action="task_created",
                target=task_id,
                value=current_task.name,
            )

    # ==================================
    # Environment更新
    # ==================================

    environment.task_available = (
        current_task is not None
    )

    environment.current_task_id = (
        current_task.task_id
        if current_task is not None
        else None
    )

    return current_task, task_count

def check_task_completion(
    agent,
    action,
    current_task,
    current_step,
    activity_logs,
):
    """
    Agentの主要ActionがTask達成条件を満たしているか確認する。
    """

    if current_task is None:
        return False
    
    if not current_task.can_complete(
        agent_id=agent.agent_id,
        action=action,
        current_step=current_step,
    ):
        return False

    # Task達成者として登録
    current_task.completed_agents.add(
        agent.agent_id
    )

    # Activity Logへ達成イベントを記録
    create_activity_log(
        logs=activity_logs,
        agent_id=agent.agent_id,
        step=current_step,
        phase="community",
        action="complete_task",
        target=current_task.task_id,
        value=action,
    )

    return True


def run_community_simulation(
    agents,
    activity_logs,
    community_steps,
    start_step,
    environment,
    issue_interval,
    passport_history,
    total_labs,
    community_start_step,
    permission_method="Stamp",
    permission_thresholds=None,
    return_proposal_results=False,
):
    current_issue = None
    current_task = None
    task_count = 0
    proposals = []

    """
    Open Campus終了後のCommunity Phaseを実行する
    """

    for offset in range(community_steps):
        current_step = start_step + offset

        environment.current_step = current_step
        environment.phase = "community"

        # Issue更新

        new_issue = update_issue(
            environment=environment,
            current_step=current_step,
            start_step=start_step,
            issue_interval=issue_interval,
        )

        if new_issue:

            issue_number = (
                (current_step - start_step + 1)
                // issue_interval
            )

            template = ISSUE_TEMPLATES[
                (issue_number - 1) % len(ISSUE_TEMPLATES)
            ]

            current_issue = Issue(
                issue_id=environment.current_issue_id,
                title=template["title"],
                options=template["options"],
                start_step=current_step,
            )
            create_activity_log(
                logs=activity_logs,
                agent_id="SYSTEM",
                step=current_step,
                phase="community",
                action="issue_created",
                target=current_issue.issue_id,
                value=current_issue.title,
            )

        current_task, task_count = update_task(
            environment=environment,
            current_task=current_task,
            current_step=current_step,
            task_count=task_count,
            activity_logs=activity_logs,
        )

        for agent in agents:

            # すでにCommunityから離脱している場合
            if agent.left_community:
                continue

            # Chat権を持っていない場合は、Communityに参加できない
            if not agent.chat_permission:
                continue

            # ==========================================
            # Community離脱判定
            # ==========================================
            leave_probability = 0.10 * (1.0 - agent.persistence)

            if random.random() < leave_probability:

                agent.left_community = True

                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=current_step,
                    phase="community",
                    action="leave_community",
                )

                continue

            # Communityへのログイン確立を計算
            login_probability = calculate_login_probability(agent)

            # このStepでログインしなかった場合
            if not occurs(login_probability):
                continue

            # ログインしたことをActivity Logへ記録
            create_activity_log(
                logs=activity_logs,
                agent_id=agent.agent_id,
                step=current_step,
                phase="community",
                action="login_community",
            )

            # ==========================================
            # Proposal提出締め切りの判定
            # ==========================================

            community_end_step = (
                start_step + community_steps - 1
            )

            # 投票期間終了後の採択判定まで完了できるようにする
            proposal_submission_deadline = (
                community_end_step
                - PROPOSAL_VOTING_DURATION
                - 1
            )

            proposal_submission_open = (
                current_step <= proposal_submission_deadline
            )

            # ============================================
            # Community行動選択
            # ============================================

            action = choose_community_action(
                agent=agent,
                environment=environment,
                proposals=proposals,
                proposal_submission_open=proposal_submission_open
            )

            if action == "no_action":
                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=current_step,
                    phase="community",
                    action="no_action",
                )

                continue

            if action == "chat":

                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=current_step,
                    phase="community",
                    action="chat",
                    target="community",
                )

                # Task完了判定
                check_task_completion(
                    agent=agent,
                    action=action,
                    current_task=current_task,
                    current_step=current_step,
                    activity_logs=activity_logs,
                )

                continue

            if action == "reply":
                
                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=current_step,
                    phase="community",
                    action="reply",
                    target="community",
                )

                check_task_completion(
                    agent=agent,
                    action=action,
                    current_task=current_task,
                    current_step=current_step,
                    activity_logs=activity_logs,
                )

                continue

            if action == "view_issue":

                issue_id = environment.current_issue_id

                if issue_id is None:
                    raise RuntimeError(
                        "Issueが存在しない状態でview_issueが選択されました"
                    )

                # Agentの閲覧履歴に追加
                agent.viewed_issues.add(issue_id)
                
                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=current_step,
                    phase="community",
                    action="view_issue",
                    target=environment.current_issue_id,
                )

                continue

            if action == "express_opinion":

                issue_id = environment.current_issue_id

                if issue_id is None:
                    raise RuntimeError(
                        "Issueが存在しない状態でexpress_opinionが選択されました"
                    )

                # 閲覧していないIssueには意見表明できない
                if issue_id not in agent.viewed_issues:
                    raise RuntimeError(
                        f"{agent.agent_id}は{issue_id}を閲覧していません"
                    )

                # 同じIssueへの重複意見表明を防ぐ
                if issue_id in agent.expressed_issues:
                    raise RuntimeError(
                        f"{agent.agent_id}は{issue_id}に意見表明済みです"
                    )
                
                # 意見表明履歴に追加
                agent.expressed_issues.add(issue_id)
                

                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=current_step,
                    phase="community",
                    action="express_opinion",
                    target=issue_id,
                )

                check_task_completion(
                agent=agent,
                action="express_opinion",
                current_task=current_task,
                current_step=current_step,
                activity_logs=activity_logs,
            )

                continue

            # ==================================
            # vote
            # ==================================

            if action == "vote":

                issue_id = environment.current_issue_id

                # Issueの存在確認
                if issue_id is None:
                    raise RuntimeError(
                        "Issueが存在しない状態でvoteが選択されました"
                    )

                # Vote権限の確認
                if not agent.vote_permission:
                    raise RuntimeError(
                        f"{agent.agent_id}にはVote権限がありません"
                    )

                # Issue閲覧済みか確認
                if issue_id not in agent.viewed_issues:
                    raise RuntimeError(
                        f"{agent.agent_id}は{issue_id}を閲覧していません"
                    )

                # 重複投票防止
                if issue_id in agent.voted_issues:
                    raise RuntimeError(
                        f"{agent.agent_id}は{issue_id}に投票済みです"
                    )

                if current_issue is None:
                    raise RuntimeError("投票対象のIssueがありません")

                vote_choice = choose_vote_option(
                    agent,
                    current_issue,
                )

                if not current_issue.add_vote(
                    agent.agent_id,
                    vote_choice,
                ):
                    raise RuntimeError("投票の登録に失敗しました")

                agent.voted_issues.add(
                    current_issue.issue_id
                )

                # Activity Logに記録
                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=current_step,
                    phase="community",
                    action="vote",
                    target=issue_id,
                    value=vote_choice,
                )

                # Vote Taskの達成判定
                check_task_completion(
                    agent=agent,
                    action="vote",
                    current_task=current_task,
                    current_step=current_step,
                    activity_logs=activity_logs,
                )

                continue

            elif action == "proposal":

                if not agent.proposal_permission:
                    raise RuntimeError(
                        f"{agent.agent_id}にはProposal権限がありません"
                    )

                proposal_id = (
                    f"PROPOSAL_{len(proposals) + 1:04d}"
                )

                # Agentの潜在特性からPQSを生成
                proposal = generate_proposal(
                    agent=agent,
                    proposal_id=proposal_id,
                    current_step=current_step,
                )

                proposals.append(proposal)

                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=current_step,
                    phase="community",
                    action="proposal",
                    target=proposal_id,
                    value=proposal.quality,
                )

                check_task_completion(
                    agent=agent,
                    action="proposal",
                    current_task=current_task,
                    current_step=current_step,
                    activity_logs=activity_logs,
                )

                continue

            if action == "vote_proposal":

                if not agent.vote_permission:
                    raise RuntimeError(
                        f"{agent.agent_id}にはVote権限がありません"
                    )

                # 投票可能なProposalを取得
                available_proposals = [
                    proposal
                    for proposal in proposals
                    if proposal.is_voting_open(
                        current_step,
                        PROPOSAL_VOTING_DURATION,
                    )
                    and agent.agent_id not in proposal.votes
                ]

                if not available_proposals:
                    raise RuntimeError(
                        "投票可能なProposalがありません"
                    )

                # 初期モデルでは候補から一様にランダム選択
                target_proposal = random.choice(
                    available_proposals
                )

                result = cast_proposal_vote(
                    agent=agent,
                    proposal=target_proposal,
                    current_step=current_step,
                )

                if result is None:
                    raise RuntimeError(
                        "Proposalへの投票に失敗しました"
                    )

                create_activity_log(
                    logs=activity_logs,
                    agent_id=agent.agent_id,
                    step=current_step,
                    phase="community",
                    action="vote_proposal",
                    target=target_proposal.proposal_id,
                    value="yes" if result["support"] else "no",
                )

                check_task_completion(
                    agent=agent,
                    action="vote_proposal",
                    current_task=current_task,
                    current_step=current_step,
                    activity_logs=activity_logs,
                )

                continue

        # ===========================================
        # Proposalの採択判定
        # ===========================================
        for proposal in proposals:
            if proposal.status != "open":
                continue

            old_status = proposal.status

            new_status = finalize_proposal(
                proposal=proposal,
                current_step=current_step,
            )

            if old_status == "open" and new_status != "open":

                create_activity_log(
                    logs=activity_logs,
                    agent_id="SYSTEM",
                    step=current_step,
                    phase="community",
                    action="proposal_finalized",
                    target=proposal.proposal_id,
                    value=new_status,
                )

        # このStep終了時点のTrust Passportを生成
        update_trust_passports(
            agents=agents,
            activity_logs=activity_logs,
            current_step=current_step,
            passport_history=passport_history,
            total_labs=total_labs,
            community_start_step=community_start_step,
            permission_method=permission_method,
            permission_thresholds=permission_thresholds,
        )

    # ===========================================
    # Community終了時のProposalの集計
    # ===========================================
    proposal_metrics = calculate_proposal_metrics(proposals)

    # Proposal結果を取得したい場合
    if return_proposal_results:
        return activity_logs, proposals, proposal_metrics

    return activity_logs


def update_issue(
    environment,
    current_step,
    start_step,
    issue_interval,
):
    """
    Community Phaseで一定期間ごとに新しい
    Issue(Vote内容)を発生させる
    """

    community_step = (
        current_step - start_step + 1
    )

    # 5 Step目、10 Step目、15 Step目...に新しいIssueを発生させる
    if community_step % issue_interval == 0:

        issue_number = (
            community_step // issue_interval
        )

        environment.issue_available = True
        environment.current_issue_id = (
            f"ISSUE_{issue_number:03d}"
        )

        return True

    return False


        



