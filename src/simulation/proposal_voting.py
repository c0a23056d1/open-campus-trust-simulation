import random

from config.settings import (
    PROPOSAL_PERCEPTION_NOISE,
    PROPOSAL_SUPPORT_THRESHOLD,
    PROPOSAL_APPROVAL_THRESHOLD,
    PROPOSAL_MIN_VOTES,
    PROPOSAL_VOTING_DURATION,
)

from src.simulation.proposal_generator import clip


def calculate_vote_score(agent) -> float:
    """
    Vote行動の選択スコア。
    実行確率そのものではない
    """

    return (
        0.7 * agent.governance
        + 0.3 * agent.persistence
    )

def decide_support(proposal, rng=None):
    """
    PQSと認識誤差から賛否を決定する。
    InterestやGovernanceは使用しない。
    """

    if rng is None:
        rng = random

    perception_error = rng.uniform(
        -PROPOSAL_PERCEPTION_NOISE,
        PROPOSAL_PERCEPTION_NOISE,
    )

    perceived_quality = clip(
        proposal.quality + perception_error
    )

    support = (
        perceived_quality >= PROPOSAL_SUPPORT_THRESHOLD
    )

    return support, perceived_quality

def cast_proposal_vote(
        agent,
        proposal,
        current_step: int,
        rng=None,
):
    """
    Vote行動が選択された後に呼び出す。
    権限・投票期間・重複投票を確認する。
    """

    if not agent.vote_permission:
        return None

    if not proposal.is_voting_open(
        current_step,
        PROPOSAL_VOTING_DURATION,
    ):
        return None

    if agent.agent_id in proposal.votes:
        return None

    support, perceived_quality = decide_support(
        proposal,
        rng=rng,
    )

    success = proposal.add_vote(
        agent_id=agent.agent_id,
        support=support,
        perceived_quality=perceived_quality,
        current_step=current_step,
        duration=PROPOSAL_VOTING_DURATION,
    )

    if not success:
        return None

    return {
        "proposal_id": proposal.proposal_id,
        "agent_id": agent.agent_id,
        "support": support,
        "perceived_quality": perceived_quality,
    }

def finalize_proposal(proposal, current_step: int):
    """
    投票期間終了後に採択判定する
    """

    if proposal.status != "open":
        return proposal.status

    end_step = (
        proposal.created_step + PROPOSAL_VOTING_DURATION
    )

    if current_step <= end_step:
        return proposal.status

    if proposal.total_votes < PROPOSAL_MIN_VOTES:
        proposal.status = "rejected"
        proposal.rejection_reason = "insufficient_votes"

    elif (
        proposal.approval_rate
        < PROPOSAL_APPROVAL_THRESHOLD
    ):
        proposal.status = "rejected"
        proposal.rejection_reason = "insufficient_approval"

    else:
        proposal.status = "accepted"
        proposal.rejection_reason = None

    return proposal.status
