
import random

from src.models.agent import Agent


def occurs(probability: float) -> bool:
    """
    指定された確率でTrueを返す。
    """
    return random.random() < probability


def calculate_visit_probability(agent: Agent) -> float:
    """
    Agentが研究室を訪問する確率。

    P(Visit) = 0.2 + 0.6 * Activity
    """
    probability = 0.2 + 0.6 * agent.activity

    return max(0.0, min(1.0, probability))


def calculate_login_probability(agent: Agent) -> float:
    """
    Communityにログインする確率。

    Persistence：継続参加傾向
    Activity：積極的に行動する傾向
    """
    probability = (
        0.7 * agent.persistence
        + 0.3 * agent.activity
    )

    return max(0.0, min(1.0, probability))


def choose_lab(agent: Agent, labs: list[dict]) -> dict:
    """
    ActivityとInterestをもとに訪問する研究室を選択する。

    Weight = 0.4 * Activity + 0.6 * Interest
    """
    weights = []

    for lab in labs:
        field = lab["field"]
        interest = agent.interests.get(field, 0.0)

        weight = (
            0.4 * agent.activity
            + 0.6 * interest
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
    研究室を訪問する。

    初めて訪問した研究室の場合はStampを1個取得する。

    Returns:
        True：新しいStampを取得した
        False：訪問済みだった
    """
    lab_id = lab["id"]

    if lab_id in agent.visited_labs:
        return False

    agent.visited_labs.add(lab_id)
    agent.stamp_count += 1

    return True


def calculate_chat_probability(agent: Agent) -> float:
    """
    旧chat行動の選択重み。

    chat行動自体は廃止するが、
    従来の行動機会をreplyに統合するために残す。
    """
    probability = (
        0.5 * agent.cooperation
        + 0.5 * agent.activity
    )

    return max(0.0, min(1.0, probability))


def calculate_reply_probability(agent: Agent) -> float:
    """
    旧reply行動の選択重み。
    """
    probability = (
        0.7 * agent.cooperation
        + 0.3 * agent.activity
    )

    return max(0.0, min(1.0, probability))


def calculate_combined_reply_weight(agent: Agent) -> float:
    """
    旧chatとreplyの選択重みを合算する。

    これまで2種類だったチャット行動を
    replyという1種類の行動に統一する。

    ※これはrandom.choicesの選択重みであり、
      単独の発生確率ではない。
    """
    return (
        calculate_chat_probability(agent)
        + calculate_reply_probability(agent)
    )


def calculate_post_visit_comment_probability(
    agent: Agent,
) -> float:
    """
    研究室訪問後に感想を投稿する確率。

    post_visit_commentは独立したメイン行動ではなく、
    visit_labに付随するイベントとして扱う。
    """
    probability = (
        0.5 * agent.cooperation
        + 0.5 * agent.activity
    )

    return max(0.0, min(1.0, probability))


def choose_community_action(
    agent: Agent,
    environment,
    proposals=None,
    proposal_submission_open=True,
) -> str:
    """
    Community Phaseで実行するメイン行動を1つ選択する。

    基本行動：
        reply
        no_action

    条件に応じて追加：
        view_issue
        express_opinion
        vote
        vote_proposal
        proposal

    join_chat、chat、reply_chat、
    join_governance_discussion、accept_taskは生成しない。
    """

    if proposals is None:
        proposals = []

    # ============================================
    # 基本行動
    # ============================================

    actions = [
        "reply",
        "no_action",
    ]

    weights = [
        calculate_combined_reply_weight(agent),
        0.2,
    ]

    # ============================================
    # Issue関連行動
    # ============================================

    if environment.issue_available:

        issue_id = environment.current_issue_id

        if issue_id is not None:

            # 未閲覧のIssueを閲覧する
            if issue_id not in agent.viewed_issues:

                actions.append("view_issue")

                weights.append(
                    calculate_view_issue_probability(agent)
                )

            # 閲覧済み、かつ意見表明していない場合
            if (
                issue_id in agent.viewed_issues
                and issue_id not in agent.expressed_issues
            ):

                actions.append("express_opinion")

                weights.append(
                    calculate_express_opinion_probability(agent)
                )

            # Vote権限があり、Issue閲覧済みで、
            # まだ投票していない場合
            if (
                agent.vote_permission
                and issue_id in agent.viewed_issues
                and issue_id not in agent.voted_issues
            ):

                actions.append("vote")

                weights.append(
                    calculate_vote_probability(agent)
                )

    # ============================================
    # Proposalへの賛否投票
    # ============================================

    if agent.vote_permission:

        from config.settings import PROPOSAL_VOTING_DURATION

        available_proposals = [
            proposal
            for proposal in proposals
            if proposal.is_voting_open(
                environment.current_step,
                PROPOSAL_VOTING_DURATION,
            )
            and agent.agent_id not in proposal.votes
        ]

        if available_proposals:

            actions.append("vote_proposal")

            weights.append(
                calculate_vote_probability(agent)
            )

    # ============================================
    # Proposal提出
    # ============================================

    if (
        agent.proposal_permission
        and proposal_submission_open
    ):

        actions.append("proposal")

        weights.append(
            calculate_proposal_probability(agent)
        )

    # ============================================
    # メイン行動を1つ選択
    # ============================================

    selected_action = random.choices(
        actions,
        weights=weights,
        k=1,
    )[0]

    return selected_action


def choose_open_campus_action(agent: Agent) -> str:
    """
    Open Campus期間中のメイン行動を1つ選択する。

    候補：
        visit_lab
        reply
        no_action

    Chat権限がないAgentはreplyを選択できない。
    """

    actions = [
        "visit_lab",
        "no_action",
    ]

    weights = [
        calculate_visit_probability(agent),
        0.2,
    ]

    # ============================================
    # Chat権限取得後のみreplyを追加
    # ============================================

    if agent.chat_permission:

        actions.append("reply")

        weights.append(
            calculate_combined_reply_weight(agent)
        )

    return random.choices(
        actions,
        weights=weights,
        k=1,
    )[0]


def calculate_view_issue_probability(
    agent: Agent,
) -> float:
    """
    Issueを閲覧する行動の選択重み。

    Governance：意思決定への関心
    Activity：積極性
    """
    probability = (
        0.7 * agent.governance
        + 0.3 * agent.activity
    )

    return max(0.0, min(1.0, probability))


def calculate_express_opinion_probability(
    agent: Agent,
) -> float:
    """
    Issueに意見表明する行動の選択重み。

    Governance：意思決定への関心
    Cooperation：協調性
    """
    probability = (
        0.6 * agent.governance
        + 0.4 * agent.cooperation
    )

    return max(0.0, min(1.0, probability))


def calculate_vote_probability(agent: Agent) -> float:
    """
    Vote行動の選択重み。

    Governance：意思決定への関心
    Persistence：継続参加傾向
    """
    return (
        0.7 * agent.governance
        + 0.3 * agent.persistence
    )


def choose_vote_option(agent, issue):
    """
    Issueの選択肢から1つを選択する。

    Agentの興味分野と対応する場合は、
    その興味の強さを選択重みに反映する。
    """
    options = issue.options

    weights = []

    for option in options:

        if option in agent.interests:
            weight = 0.1 + agent.interests[option]
        else:
            weight = 1.0

        weights.append(weight)

    return random.choices(
        options,
        weights=weights,
        k=1,
    )[0]


def calculate_proposal_probability(agent: Agent) -> float:
    """
    Proposal行動の選択重み。

    Activity：活動への積極性
    Persistence：継続性
    Governance：意思決定への関心
    """
    score = (
        0.3 * agent.activity
        + 0.3 * agent.persistence
        + 0.4 * agent.governance
    )

    return max(0.0, min(1.0, score))
