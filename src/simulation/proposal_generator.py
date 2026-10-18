
import random

from config.settings import (
    PROPOSAL_QUALITY_BASE,
    PROPOSAL_QUALITY_WEIGHT,
    PROPOSAL_QUALITY_NOISE,
)

from src.models.proposal import Proposal


def clip(value: float) -> float:
    """値を0.0～1.0に収める。"""
    return max(0.0, min(1.0, value))


def generate_proposal(
    agent,
    proposal_id: str,
    current_step: int,
    rng=None,
) -> Proposal:
    """
    AgentのGovernance、Reliability、Cooperationから
    Proposalの品質を生成する。

    ※ Proposal権限の確認は呼び出し側で行う。
    """

    if rng is None:
        rng = random

    # 各品質要素に独立した確率的変動を与える
    epsilon_r = rng.uniform(
        -PROPOSAL_QUALITY_NOISE,
        PROPOSAL_QUALITY_NOISE,
    )

    epsilon_f = rng.uniform(
        -PROPOSAL_QUALITY_NOISE,
        PROPOSAL_QUALITY_NOISE,
    )

    epsilon_b = rng.uniform(
        -PROPOSAL_QUALITY_NOISE,
        PROPOSAL_QUALITY_NOISE,
    )

    # ① Relevance：Governanceから生成
    relevance = clip(
        PROPOSAL_QUALITY_BASE
        + PROPOSAL_QUALITY_WEIGHT * agent.governance
        + epsilon_r
    )

    # ② Feasibility：Reliabilityから生成
    feasibility = clip(
        PROPOSAL_QUALITY_BASE
        + PROPOSAL_QUALITY_WEIGHT * agent.reliability
        + epsilon_f
    )

    # ③ Community Benefit：Cooperationから生成
    benefit = clip(
        PROPOSAL_QUALITY_BASE
        + PROPOSAL_QUALITY_WEIGHT * agent.cooperation
        + epsilon_b
    )

    # ④ Proposal Quality Score
    quality = (
        relevance + feasibility + benefit
    ) / 3.0

    return Proposal(
        proposal_id=proposal_id,
        agent_id=agent.agent_id,
        created_step=current_step,
        relevance=relevance,
        feasibility=feasibility,
        benefit=benefit,
        quality=quality,
    )
