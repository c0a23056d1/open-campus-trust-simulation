import random

from config.settings import (
    NUM_AGENTS,
    RANDOM_SEED,
    OC_STEPS,
    LABS,
)

from src.utils.random_utils import (
    generate_agents,
    save_agent_profiles,
)

from src.models.activity_log import save_activity_logs

from src.simulation.simulator import (
    run_open_campus_simulation,
)


def main():

    # ==========================================
    # Random Seed
    # ==========================================

    random.seed(RANDOM_SEED)

    # ==========================================
    # Agent生成
    # ==========================================

    agents = generate_agents(NUM_AGENTS)

    # Agentの初期特性を保存
    save_agent_profiles(
        agents=agents,
        file_path="results/agents/agent_profiles.csv",
    )

    print("=" * 60)
    print("Open Campus Trust Simulation")
    print("=" * 60)

    print(f"生成Agent数: {len(agents)}")
    print()

    # ==========================================
    # Open Campus Simulation
    # ==========================================

    environment, activity_logs = (
        run_open_campus_simulation(
            agents=agents,
            labs=LABS,
            oc_steps=OC_STEPS,
        )
    )

    # ==========================================
    # Activity Log保存
    # ==========================================

    save_activity_logs(
        logs=activity_logs,
        file_path="results/logs/activity_logs.csv",
    )

    # ==========================================
    # 結果表示
    # ==========================================

    print("---- Open Campus Result ----")

    for agent in agents[:5]:

        print()
        print(f"Agent ID: {agent.agent_id}")
        print(f"Activity: {agent.activity:.3f}")
        print(f"Stamp: {agent.stamp_count}")
        print(
            f"Visited Labs: "
            f"{len(agent.visited_labs)}"
        )
        print(
            f"Chat Permission: "
            f"{agent.chat_permission}"
        )

    print()
    print(f"Activity Log数: {len(activity_logs)}")

    print(
        "Activity Logを "
        "results/logs/activity_logs.csv "
        "に保存しました。"
    )


if __name__ == "__main__":
    main()