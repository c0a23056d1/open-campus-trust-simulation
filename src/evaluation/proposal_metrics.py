def calculate_proposal_metrics(proposals):
    """
    Proposalの意思決定品質を評価する。
    
    APQ: Accepted Proposal Quality
    APC: Accepted Proposal Count
    SPQ: Submitted Proposal Quality
    PAR: Proposal Acceptance Rate
    TAQ: Total Accepted Quality

    best_pqs:
        当該seedで提出されたProposalの最高PQS
    best_pqs_accepted:
        最高PQS提案が採択された場合1、そうでなければ0
    best_pqs_eligible:
        Proposalが1件以上あれば1、なければ0

    """

    proposals = list(proposals)

    submitted_count = len(proposals)

    accepted = [
        p for p in proposals 
        if p.status == "accepted"
    ]

    accepted_count = len(accepted)

    #採択されたProposalの品質合計
    taq = sum(
        p.quality for p in accepted
    )

    # APQ: 採択Proposalの平均品質
    apq = (
        taq / accepted_count
        if accepted_count > 0
        else None
    )

    # SPQ: 提出Proposalの平均品質
    spq = (
        sum(p.quality for p in proposals) 
        / submitted_count
        if submitted_count > 0
        else None
    )

    # PAR: 提出Proposalに対する採択割合
    par = (
        accepted_count / submitted_count
        if submitted_count > 0
        else None
    )

    # ==========================================
    # 最高PQS提案の採択判定
    # ==========================================
    if submitted_count > 0:
        best_pqs = max(p.quality for p in proposals)

        best_proposals = [
            p for p in proposals
            if abs(p.quality - best_pqs) <= 1e-12
        ]

        best_pqs_accepted = int(
            any(
                p.status == "accepted"
                for p in best_proposals
            )
        )

        best_pqs_eligible = 1

    else:
        best_pqs = None
        best_pqs_accepted = 0
        best_pqs_eligible = 0

    return {
        "APQ": apq,
        "APC": accepted_count,
        "SPQ": spq,
        "PAR": par,
        "TAQ": taq,
        "submitted_count": submitted_count,
        "rejected_insufficient_votes": sum(
            p.rejection_reason == "insufficient_votes"
            for p in proposals
        ),
        "rejected_insufficient_approval": sum(
            p.rejection_reason == "insufficient_approval"
            for p in proposals
        ),
        "open_count": sum(
            p.status == "open"
            for p in proposals
        ),

        # BPAR集計用の追加項目
        "best_pqs": best_pqs,
        "best_pqs_accepted": best_pqs_accepted,
        "best_pqs_eligible": best_pqs_eligible,
    }

def calculate_bpar(seed_metrics):
    """
    複数seedのProposal評価結果からBPARを計算する。
    """

    accepted = sum(
        m["best_pqs_accepted"]
        for m in seed_metrics
    )

    eligible = sum(
        m["best_pqs_eligible"]
        for m in seed_metrics
    )

    return accepted / eligible if eligible > 0 else None