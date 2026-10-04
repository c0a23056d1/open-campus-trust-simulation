# import random

# from config.settings import (
#     NUM_AGENTS,
#     RANDOM_SEED,
#     OC_STEPS,
#     LABS,
#     COMMUNITY_STEPS,
# )

# from src.utils.random_utils import (
#     generate_agents,
#     save_agent_profiles,
# )

# from src.models.activity_log import save_activity_logs

# from src.simulation.simulator import (
#     run_open_campus_simulation,
#     run_community_simulation,
# )


# def main():

#     # ==========================================
#     # Random Seed
#     # ==========================================

#     random.seed(RANDOM_SEED)

#     # ==========================================
#     # Agent生成
#     # ==========================================

#     agents = generate_agents(NUM_AGENTS)

#     # Agentの初期特性を保存
#     save_agent_profiles(
#         agents=agents,
#         file_path="results/agents/agent_profiles.csv",
#     )

#     print("=" * 60)
#     print("Open Campus Trust Simulation")
#     print("=" * 60)

#     print(f"生成Agent数: {len(agents)}")
#     print()

#     # ==========================================
#     # Open Campus Simulation
#     # ==========================================

#     environment, activity_logs = (
#         run_open_campus_simulation(
#             agents=agents,
#             labs=LABS,
#             oc_steps=OC_STEPS,
#         )
#     )

#     activity_logs = run_community_simulation(
#         agents=agents,
#         activity_logs=activity_logs,
#         community_steps=COMMUNITY_STEPS,
#         start_step=OC_STEPS + 1,
#     )

#     # ==========================================
#     # Activity Log保存
#     # ==========================================

#     save_activity_logs(
#         logs=activity_logs,
#         file_path="results/logs/activity_logs.csv",
#     )

#     # ==========================================
#     # 結果表示
#     # ==========================================

#     print("---- Open Campus Result ----")

#     for agent in agents[:5]:

#         print()
#         print(f"Agent ID: {agent.agent_id}")
#         print(f"Activity: {agent.activity:.3f}")
#         print(f"Stamp: {agent.stamp_count}")
#         print(
#             f"Visited Labs: "
#             f"{len(agent.visited_labs)}"
#         )
#         print(
#             f"Chat Permission: "
#             f"{agent.chat_permission}"
#         )

#     print()
#     print(f"Activity Log数: {len(activity_logs)}")

#     print(
#         "Activity Logを "
#         "results/logs/activity_logs.csv "
#         "に保存しました。"
#     )


# if __name__ == "__main__":
#     main()

import random

from config.settings import (
    NUM_AGENTS,
    OC_STEPS,
    COMMUNITY_STEPS,
    LABS,
    RANDOM_SEED,
)

from src.utils.random_utils import (
    generate_agents,
    save_agent_profiles,
)

from src.models.activity_log import (
    save_activity_logs,
)

from src.simulation.simulator import (
    run_open_campus_simulation,
    run_community_simulation,
)


def main():

    print("=" * 60)
    print("Open Campus Trust Simulation")
    print("=" * 60)

    # ==========================================
    # Random Seed
    # ==========================================

    random.seed(RANDOM_SEED)

    # ==========================================
    # Agent生成
    # ==========================================

    agents = generate_agents(NUM_AGENTS)

    print(f"生成Agent数: {len(agents)}")

    save_agent_profiles(
        agents,
        "results/agents/agent_profiles.csv",
    )

    # ==========================================
    # Open Campus Phase
    # ==========================================

    environment, activity_logs = (
        run_open_campus_simulation(
            agents=agents,
            labs=LABS,
            oc_steps=OC_STEPS,
        )
    )

    # ==========================================
    # Community Phase
    # ==========================================

    activity_logs = run_community_simulation(
        agents=agents,
        activity_logs=activity_logs,
        community_steps=COMMUNITY_STEPS,
        start_step=OC_STEPS + 1,
    )

    # ==========================================
    # 結果表示
    # ==========================================

    print()
    print("---- Open Campus Result ----")
    print()

    for agent in agents[:5]:

        print(f"Agent ID: {agent.agent_id}")
        print(
            f"Activity: "
            f"{agent.activity:.3f}"
        )
        print(
            f"Stamp: "
            f"{agent.stamp_count}"
        )
        print(
            f"Visited Labs: "
            f"{len(agent.visited_labs)}"
        )
        print(
            f"Chat Permission: "
            f"{agent.chat_permission}"
        )
        print()

    # Communityログだけ抽出
    community_logs = [
        log
        for log in activity_logs
        if log.phase == "community"
    ]

    print("---- Community Result ----")
    print()
    print(
        f"Community Log数: "
        f"{len(community_logs)}"
    )

    print(
        f"全Activity Log数: "
        f"{len(activity_logs)}"
    )

    # ==========================================
    # CSV保存
    # ==========================================

    save_activity_logs(
        activity_logs,
        "results/logs/activity_logs.csv",
    )

    print(
        "Activity Logを "
        "results/logs/activity_logs.csv "
        "に保存しました。"
    )


if __name__ == "__main__":
    main()