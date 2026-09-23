import random

from src.models.agent import Agent

def occurs(probability: float) -> bool:
    """
    指定された確率でTrueを返す
    """

    return random.random() < probability

def calculate_visit_probability(agent: Agent) -> float:
    """
    Agentが研究室を訪問す確率を計算する

    P(Visit) = 0.2 + 0.6 * Activity
    """
    probability = 0.2 + 0.6 * agent.activity

    # 念のため,0.0~1.0の範囲に収める
    probability = max(0.0, min(1.0, probability))

    return max(0.0, min(1.0, probability))

def choose_lab(agent: Agent, labs: list[dict]) -> dict:
    """
    AgentのActivityとInterestをもとに
    訪問する研究室を選択する
    
    Weight = 0.4 * Activity + 0.6 * Interest
    """

    weights = []
    for lab in labs:
        field = lab["field"]
        interest = agent.interests.get(field, 0.0)

        weight = (
            0.4 * agent.activity + 0.6 * interest
        )

        weights.append(weight)

    selected_lab = random.choices(
        labs,
        weights=weights,
        k=1,
    )[0]

    return selected_lab

def visit_lab(agent: Agent, lab: dict) -> bool:
    """
    研究室を訪問する
    
    初めて訪問した研究室の場合はStampを1個取得する

    Returns:
        True: 新しいStampを取得した
        False: 訪問済みだった
    """

    lab_id = lab["id"]

    # すでに訪問済み
    if lab_id in agent.visited_labs:
        return False

    # 初訪問
    agent.visited_labs.add(lab_id)
    agent.stamp_count += 1

    return True