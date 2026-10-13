def update_stamp_permissions(agent):
    """
    スタンプ数に応じて権限を更新する。

    Chat     : 1個以上
    Vote     : 3個以上
    Proposal : 5個以上
    """

    unlocked_permissions = []

    # Chat権限
    if agent.stamp_count >= 1 and not agent.chat_permission:
        agent.chat_permission = True
        unlocked_permissions.append("chat")

    # Vote権限
    if agent.stamp_count >= 3 and not agent.vote_permission:
        agent.vote_permission = True
        unlocked_permissions.append("vote")

    # Proposal権限
    if agent.stamp_count >= 5 and not agent.proposal_permission:
        agent.proposal_permission = True
        unlocked_permissions.append("proposal")

    return unlocked_permissions