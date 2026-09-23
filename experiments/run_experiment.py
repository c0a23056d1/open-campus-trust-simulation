import random

from config.settings import (
    NUM_AGENTS,
    RANDOM_SEED,
    OC_STEPS,
    LABS,
)

from src.models.environment import Environment
from src.utils.random_utils import generate_agents

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

    # --------------------------------
    # Environment生成
    # --------------------------------
    environment = Environment()

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
            # 研究室訪問
            # --------------------------------
            new_stamp = visit_lab(
                agent,
                selected_lab,
            )

            # --------------------------------
            # 今は確認用に最初の5人だけ表示
            # --------------------------------
            if agent.agent_id in [
                "A001",
                "A002",
                "A003",
                "A004",
                "A005",
            ]:
                if new_stamp:
                    print(
                        f"{agent.agent_id}"
                        f"→ {selected_lab['name']}"
                        f" (新しいStampを取得)"
                        f"Stamp={agent.stamp_count}"
                    )
                else:
                    print(
                        f"{agent.agent_id}"
                        f"→ {selected_lab['name']}"
                        f" (訪問済み)"
                        f"Stamp={agent.stamp_count}"
                    )
        print()

    # 最初の5人だけ表示
    print("--- Open Campus Result ---")
    for agent in agents[:5]:
        print(f"Agent ID: {agent.agent_id}")
        print(f"Stamp : {agent.stamp_count}")
        print(f"Visited Labs : {len(agent.visited_labs)}")
        print(f"Chat : {agent.chat_permission}")
        print(f"Vote : {agent.vote_permission}")
        print(f"Proposal : {agent.proposal_permission}")

if __name__ == "__main__":
    main()