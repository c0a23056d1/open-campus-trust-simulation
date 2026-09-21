from dataclasses import dataclass, field

@dataclass
class Agent:
    """
    仮想的なオープンキャンパス参加者を表すクラス
    """

    # ======================================
    # 基本情報
    # ======================================

    agent_id: str

    # ======================================
    # 潜在特性 (Latent Traits)
    # ======================================

    # 行動の積極性
    activity: float

    # 継続して参加する傾向
    persistence: float

    # 他者と協力・交流する傾向
    cooperation: float

    # 投票・意思決定への関心
    governance: float

    # 責任をもって行動する傾向
    reliability: float

    # ======================================
    # 興味分野
    # ======================================
    interests: dict[str, float]

    # ======================================
    # Open Campus で変化する状態
    # ======================================

    # 現在のスタンプ数
    stamp_count: int = 0

    # 訪問済み研究室
    visited_labs: set[str] = field(default_factory=set)


    # ======================================
    # Communityで利用する権限
    # ======================================

    chat_permission: bool = False

    vote_permission: bool = False

    proposal_permission: bool = False


    # ======================================
    # Community状態
    # ======================================

    # コミュニティから離脱したか
    left_community: bool = False
    