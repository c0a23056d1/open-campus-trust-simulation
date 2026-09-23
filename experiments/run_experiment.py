import random

from config.settings import (
    NUM_AGENTS,
    RANDOM_SEED,
    OC_STEPS,
    LABS,
)

from src.models.environment import Environment
from src.models.activity_log import (
    create_activity_log,
    save_activity_logs,
)
from src.utils.random_utils import (
    generate_agents,
    save_agent_profiles,
)

from src.simulation.behavior import (
    occurs,
    calculate_visit_probability,
    choose_lab,
    visit_lab,
)

def main():

    # --------------------------------
    # 乱数を固定
    # --------------------------------
    random.seed(RANDOM_SEED)

    # --------------------------------
    # Agentを生成
    # --------------------------------
    agents = generate_agents(NUM_AGENTS)

    # -------------------------------
    # Agentの初期特性を保存
    # -------------------------------
    save_agent_profiles(
        agents=agents,
        file_path="results/agents/agent_profiles.csv",
    )

    # --------------------------------
    # Environment生成
    # --------------------------------
    environment = Environment()

    # --------------------------------
    # Activity Log
    # --------------------------------
    activity_logs = []

    print("=" * 60)
    print("Open Campus Trust Simulation")
    print("=" * 60)

    print(f"生成Agent数: {len(agents)}")
    print()

    # --------------------------------
    # 結果確認
    # --------------------------------
    print("=" * 60)
    print("Open Campus Trust Simulation")
    print("=" * 60)

    print(f"生成Agent数: {len(agents)}")
    print()

    # --------------------------------
    # Open Campus Simulation
    # --------------------------------
    print("---- Open Campus Simulation ----")
    print()

    for step in range(1, OC_STEPS + 1):
        environment.current_step = step
        environment.phase = "open_campus"

        print(f"==== Step {step} ====")

        for agent in agents:
            # --------------------------------
            # 研究室訪問の確率を計算
            # --------------------------------
            visit_probability = (
                calculate_visit_probability(agent)
            )

            # --------------------------------
            # 研究室訪問の判定
            # --------------------------------
            if not occurs(visit_probability):
                continue

            # --------------------------------
            # 訪問先を選択
            # --------------------------------
            selected_lab = choose_lab(
                agent,
                LABS,
            )

            # --------------------------------
            # 研究室訪問をログに記録
            # --------------------------------
            create_activity_log(
                logs=activity_logs,
                agent_id=agent.agent_id,
                step=environment.current_step,
                phase=environment.phase,
                action="visit_lab",
                target=selected_lab["id"],
            )

            # --------------------------------
            # 研究室訪問
            # --------------------------------
            new_stamp = visit_lab(
                agent,
                selected_lab,
            )

            # --------------------------------
            # 新しいスタンプを取得した場合
            # --------------------------------
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

            # --------------------------------
            # Stamp 1個以上でChat解放
            # --------------------------------
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
                    value=True,
                )
        print()
        print(f"Activity Log数: {len(activity_logs)}")

    save_activity_logs(
        logs=activity_logs,
        file_path="results/logs/activity_logs.csv",
    )
    print("Activity Logを保存しました: results/logs/activity_logs.csv")

    # 最初の5人だけ表示
    print("--- Open Campus Result ---")
    for agent in agents[:5]:
        print(f"Agent ID: {agent.agent_id}")
        print(f"Stamp : {agent.stamp_count}")
        print(f"Visited Labs : {len(agent.visited_labs)}")
        print(f"Chat : {agent.chat_permission}")
        print(f"Vote : {agent.vote_permission}")
        print(f"Proposal : {agent.proposal_permission}")
        print()

if __name__ == "__main__":
    main()