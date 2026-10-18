# ============================================================
# Trust-based Permission Control
# ============================================================

TRUST_THRESHOLDS = {
    "PT": {
        "vote": 0.6,
        "proposal": 0.8,
    },
    "CT": {
        "vote": 0.4,
        "proposal": 0.7,
    },
    "Multi": {
        "vote_pt": 0.6,
        "vote_gt": 0.5,
        "proposal_ct": 0.7,
        "proposal_rt": 0.6,
    },
}

# def calculate_multi_trust(passport: dict) -> float:
#     """
#     4種類のTrustを組み合わせて
#     Multi Trust Scoreを計算する。
#     """

#     score = (
#         MULTI_WEIGHTS["participation"]
#         * passport["participation"]

#         + MULTI_WEIGHTS["contribution"]
#         * passport["contribution"]

#         + MULTI_WEIGHTS["reliability"]
#         * passport["reliability"]

#         + MULTI_WEIGHTS["governance"]
#         * passport["governance"]
#     )

#     return max(0.0, min(1.0, score))

# def get_permission_score(
#     passport: dict,
#     method: str,
# ) -> float:
#     """
#     権限制御方式に応じたスコアを取得する。

#     PT：Participation Trust
#     CT: Contribution Trust
#     Multi: 複数Trustの組み合わせ
#     """

#     if method == "PT":
#         return passport["participation"]
#     if method == "CT":
#         return passport["contribution"]
#     if method == "Multi":
#         return calculate_multi_trust(passport)
#     raise ValueError(
#         f"未対応の権限制御方式です：{method}"
#     )

def update_trust_permissions(
    agent,
    passport: dict,
    method: str,
    thresholds: dict | None = None,
) -> list[str]:

    if method not in ("PT", "CT", "Multi"):
        raise ValueError(
            f"未対応のTrust方式です: {method}"
        )

    if thresholds is None:
        thresholds = TRUST_THRESHOLDS[method]

    unlocked_permissions = []

    # ======================================
    # Stage 1：Chat権限（全方式共通）
    # ======================================
    if agent.stamp_count >= 1 and not agent.chat_permission:
        agent.chat_permission = True
        unlocked_permissions.append("chat")

    # ======================================
    # 方式別の権限取得条件
    # ======================================
    if method == "PT":
        vote_condition = (
            passport["participation"] >= thresholds["vote"]
        )
        proposal_condition = (
            passport["participation"] >= thresholds["proposal"]
        )

    elif method == "CT":
        vote_condition = (
            passport["contribution"] >= thresholds["vote"]
        )
        proposal_condition = (
            passport["contribution"] >= thresholds["proposal"]
        )

    else:  # Multi
        vote_condition = (
            passport["participation"] >= thresholds["vote_pt"]
            and passport["governance"] >= thresholds["vote_gt"]
        )
        proposal_condition = (
            passport["contribution"] >= thresholds["proposal_ct"]
            and passport["reliability"] >= thresholds["proposal_rt"]
        )

    # ======================================
    # Stage 2：Vote権限
    # Chat権限を取得していることが必須
    # ======================================
    if (
        agent.chat_permission
        and vote_condition
        and not agent.vote_permission
    ):
        agent.vote_permission = True
        unlocked_permissions.append("vote")

    # ======================================
    # Stage 3：Proposal権限
    # Vote権限を取得していることが必須
    # ======================================
    if (
        agent.vote_permission
        and proposal_condition
        and not agent.proposal_permission
    ):
        agent.proposal_permission = True
        unlocked_permissions.append("proposal")

    return unlocked_permissions


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

def update_permissions(
    agent,
    method: str,
    passport: dict | None = None,
    thresholds: dict | None = None,
) -> list[str]:
    """
    権限制御方式に応じて権限を更新する

    Stamp : スタンプ数
    PT    : Participation Trust
    CT    : Contribution Trust
    Multi : 複数Trustの加重平均
    """

    if method == "Stamp":
        return update_stamp_permissions(agent)

    if method in ("PT", "CT", "Multi"):

        if passport is None:
            raise ValueError(
                f"{method}方式ではTrust Passportが必要です"
            )
        
        return update_trust_permissions(
            agent=agent,
            passport=passport,
            method=method,
            thresholds=thresholds,
        )

    raise ValueError(
        f"未対応の権限制御方式です:{method}"
    )


