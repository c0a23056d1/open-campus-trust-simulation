import random

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

def run_open_campus_simulation(
    agents,
    labs,
    oc_steps,
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
                    # Chat解放
                    # ------------------------------

                    if (
                        agent.stamp_count >= 1
                        and not agent.chat_permission
                    ):

                        agent.chat_permission = True

                        create_activity_log(
                            logs=activity_logs,
                            agent_id=agent.agent_id,
                            step=environment.current_step,
                            phase=environment.phase,
                            action="unlock_chat",
                            target="chat",
                            value=True,
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

    return environment, activity_logs

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
):
    current_task = None
    task_count = 0

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
            create_activity_log(
                logs=activity_logs,
                agent_id="SYSTEM",
                step=current_step,
                phase="community",
                action="issue_created",
                target=environment.current_issue_id,
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

            action = choose_community_action(agent, environment)

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


        



