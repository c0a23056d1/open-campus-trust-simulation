def calculate_proposal_metrics(proposals):
    """
    Proposalの意思決定品質を評価する。
    
    APQ: Accepted Proposal Quality
    APC: Accepted Proposal Count
    SPQ: Submitted Proposal Quality
    PAR: Proposal Acceptance Rate
    TAQ: Total Accepted Quality
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
    }