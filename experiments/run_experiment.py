import random

from config.settings import NUM_AGENTS, RANDOM_SEED
from src.utils.random_utils import generate_agents

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
    # 結果確認
    # --------------------------------
    print("=" * 60)
    print("Open Campus Trust Simulation")
    print("=" * 60)

    print(f"生成Agent数: {len(agents)}")
    print()

    # 最初の5人だけ表示
    for agent in agents[:5]:
        print(f"Agent ID: {agent.agent_id}")

        print("---- 潜在特性 (Latent Traits) ----")
        print(f"Activity: {agent.activity:.3f}")
        print(f"Persistence: {agent.persistence:.3f}")
        print(f"Cooperation: {agent.cooperation:.3f}")
        print(f"Governance: {agent.governance:.3f}")
        print(f"Reliability: {agent.reliability:.3f}")

        print("---- 興味分野 ----")

        for field, value in agent.interests.items():
            print(f"{field:10}: {value:.3f}")

        print("--- Initial State ---")
        print(f"Stamp :{agent.stamp_count}")
        print(f"Chat :{agent.chat_permission}")
        print(f"Vote :{agent.vote_permission}")
        print(f"Proposal :{agent.proposal_permission}")

        print("-" * 60)

if __name__ == "__main__":
    main()