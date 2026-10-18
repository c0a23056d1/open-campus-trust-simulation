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

def calculate_login_probability(agent: Agent) -> float:
    """
    Communityにログインする確率を計算する。
    
    Persistence:
        継続して参加する傾向
    
    Activity:
        積極的に行動する傾向
    """

    probability = (
        0.7 * agent.persistence
        + 0.3 * agent.activity
    )

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

def calculate_chat_probability(agent: Agent) -> float:
    """
    通常のChat投稿を行う傾向を計算する。

    Cooperation:
        他者と関わろうとする傾向

    Activity:
        積極的に行動する傾向
    """

    probability = (
        0.5 * agent.cooperation
        + 0.5 * agent.activity
    )

    return max(0.0, min(1.0, probability))


def calculate_reply_probability(agent: Agent) -> float:
    """
    他者のChatに返信する傾向を計算する。
    """

    probability = (
        0.7 * agent.cooperation
        + 0.3 * agent.activity
    )

    return max(0.0, min(1.0, probability))


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
    proposal_submission_open=True
) -> str:
    """
    Community Phaseで実行する
    メイン行動を一つ選択する。
    """

    if proposals is None:
        proposals = []

    actions = [
        "chat",
        "reply",
        "no_action",
    ]

    weights = [
        calculate_chat_probability(agent),
        calculate_reply_probability(agent),
        0.2,
    ]

    if environment.issue_available:
        issue_id = environment.current_issue_id

        if issue_id is not None:
            if issue_id not in agent.viewed_issues:
                actions.append("view_issue")

                weights.append(
                    calculate_view_issue_probability(agent)
                )

                # -------------------------------
                # 閲覧済み、かつ意見表明をしていない場合
                # -------------------------------

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

    # ===========================================
    # 行動を一つ選択
    # ===========================================

    selected_action = random.choices(
        actions,
        weights=weights,
        k=1,
    )[0]

    return selected_action

def choose_open_campus_action(agent: Agent) -> str:
    """
    Open Campus期間中のメイン行動を1つ選択する。

    現段階での候補：
    - visit_lab
    - chat
    - reply
    - no_action

    Chat権限がないAgentは
    chat / replyを選択できない。
    """

    actions = [
        "visit_lab",
        "no_action",
    ]

    weights = [
        calculate_visit_probability(agent),
        0.2,
    ]

    # Chat権限がある場合だけ
    # Chat系行動を候補に追加する
    if agent.chat_permission:

        actions.append("chat")
        weights.append(
            calculate_chat_probability(agent)
        )

        actions.append("reply")
        weights.append(
            calculate_reply_probability(agent)
        )

    return random.choices(
        actions,
        weights=weights,
        k=1,
    )[0]

def calculate_view_issue_probability(
        agent: Agent
) -> float:

    probability = (
        0.7 * agent.governance
        + 0.3 * agent.activity
    )

    return max(
        0.0,
        min(1.0, probability),
    )

def calculate_express_opinion_probability(
    agent: Agent
) -> float:

    probability = (
        0.6 * agent.governance
        + 0.4 * agent.cooperation
    )

    return max(
        0.0, 
        min(1.0, probability),
    )

def calculate_vote_probability(agent: Agent) -> float:
    """
    Vote行動の選択重みを計算する。

    Governance：意思決定への関心
    Persistence：継続的な参加傾向
    """

    return (
        0.7 * agent.governance
        + 0.3 * agent.persistence
    )

def choose_vote_option(agent, issue):
    """
    Issueの選択肢から1つを選択する。
    Agentの興味分野と対応する場合は
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