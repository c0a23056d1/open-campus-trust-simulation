import random
from src.models.agent import Agent

# Agentが持つ興味分野
INTEREST_FIELDS = [
    "AI",
    "Game",
    "WebApp",
    "Security",
    "Network",
    "Design",
    "Media",
]

def generate_agent(agent_number: int) -> Agent:
    """
    1人のAgentをランダム生成する
    """

    # A001, A002, ... の形でIDを生成
    agent_id = f"A{agent_number:03d}"

    # 各分野への興味を0.0 ~ 1.0 で生成
    interests = {
        field: random.random()
        for field in INTEREST_FIELDS
    }

    # Agentを生成
    agent = Agent(
        agent_id=agent_id,

        activity=random.random(),
        persistence=random.random(),
        cooperation=random.random(),
        governance=random.random(),
        reliability=random.random(),

        interests=interests,
    )

    return agent

def generate_agents(num_agents: int) -> list[Agent]:
    """
    指定された人数分のAgentを生成する
    """
    agents = []

    for i in range(1, num_agents + 1):
        agent = generate_agent(i)
        agents.append(agent)

    return agents