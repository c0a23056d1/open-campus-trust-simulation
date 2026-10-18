import random 
from types import SimpleNamespace

from src.simulation.proposal_generator import (
    generate_proposal,
) 
from src.simulation.proposal_voting import (
    calculate_vote_score,
    cast_proposal_vote,
    finalize_proposal,
)
from src.evaluation.proposal_metrics import (
    calculate_proposal_metrics,
)

def main():
    rng = random.Random(42)

    #Proposalを提出するAgent
    proposer = SimpleNamespace(
        agent_id="A001",
        governance=0.8,
        reliability=0.7,
        cooperation=0.6,
        persistence=0.6,
        proposal_permission=True,
    )

    # Proposal 権限を確認
    if not proposer.proposal_permission:
        print("Proposal権限がありません。")
        return 

    # Proposalを生成
    proposal = generate_proposal(
        agent=proposer,
        proposal_id="P001",
        current_step=11,
        rng=rng,
    )

    print("Proposal Generation")
    print("Proposal ID:", proposal.proposal_id)
    print("Agent ID:", proposal.agent_id)
    print("Relevance:", round(proposal.relevance, 3))
    print("Feasibility:", round(proposal.feasibility, 3))
    print("Benefit:", round(proposal.benefit, 3))
    print("PQS:", round(proposal.quality, 3))

    # 動作確認用の投票者5人
    voters = [
        SimpleNamespace(
            agent_id=f"V{i:03d}",
            governance=0.7,
            persistence=0.6,
            vote_permission=True,
        )

        for i in range(1, 6)
    ]

    print("\n=== Proposal Voting ===")

    # このデモではVote行動が選択されたと仮定
    for voter in voters: 
        vote_score = calculate_vote_score(voter)

        result = cast_proposal_vote(
            agent=voter,
            proposal=proposal,
            current_step=12,
            rng=rng,
        )

        if result is None:
            continue

        print(
            voter.agent_id,
            "賛成" if result["support"] else "反対",
            "Vote Score:",
            round(vote_score, 3),
            "認識品質",
            round(result["perceived_quality"], 3),
        )

    # 投票期間終了後に採択判定
    finalize_proposal(
        proposal,
        current_step=17,
    )

    print("\n=== Proposal Result ===")
    print("有効投票数:", proposal.total_votes)
    print("賛成票:", proposal.yes_votes)
    print("反対票:", proposal.no_votes)
    print("賛成率:", proposal.approval_rate)
    print("採択結果:", proposal.status)
    print("不採択理由:", proposal.rejection_reason)

    # 評価指標
    metrics = calculate_proposal_metrics([proposal])

    print("\n=== Evaluation Metrics ===")
    for key, value in metrics.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()