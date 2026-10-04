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

def run_community_simulation(
        agents,
        activity_logs,
        community_steps,
        start_step,
):
    """
    Open Campus終了後のCommunity Phaseを実行する
    """

    for offset in range(community_steps):
        current_step = start_step + offset

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

            action = choose_community_action(agent)

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

                continue

    return activity_logs

        



