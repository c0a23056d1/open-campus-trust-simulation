import random
from src.models.agent import Agent
import csv
import os

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

def save_agent_profiles(
    agents: list[Agent],
    file_path: str,
) -> None:
    """
    生成したAgentの初期特性をCSVファイルとして保存する
    """
    directory = os.path.dirname(file_path)

    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(
        file_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        # CSVヘッダー
        writer.writerow([
            "agent_id",
            "activity",
            "persistence",
            "cooperation",
            "governance",
            "reliability",
            "interest_AI",
            "interest_Game",
            "interest_WebApp",
            "interest_Security",
            "interest_Network",
            "interest_Design",
            "interest_Media",
        ])

        # Agentごとに保存
        for agent in agents:
            writer.writerow([
                agent.agent_id,
                agent.activity,
                agent.persistence,
                agent.cooperation,
                agent.governance,
                agent.reliability,
                agent.interests.get("AI", 0.0),
                agent.interests.get("Game", 0.0),
                agent.interests.get("WebApp", 0.0),
                agent.interests.get("Security", 0.0),
                agent.interests.get("Network", 0.0),
                agent.interests.get("Design", 0.0),
                agent.interests.get("Media", 0.0),
            ])

def generate_agents(num_agents: int) -> list[Agent]:
    """
    指定された人数分のAgentを生成する
    """
    agents = []

    for i in range(1, num_agents + 1):
        agent = generate_agent(i)
        agents.append(agent)

    return agents