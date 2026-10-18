# ======================================
# シミュレーション基本設定
# ======================================

# 仮想参加者 (Agent) の人数
NUM_AGENTS = 100

# オープンキャンパス期間
OC_STEPS = 10

# コミュニティ活動期間
COMMUNITY_STEPS = 30

# 研究室数
NUM_LABS = 10

# 乱数シード
RANDOM_SEED = 42

# ======================================
# Community / Issue Settings
# ======================================
ISSUE_INTERVAL = 5


# ======================================
# 研究室情報
# ======================================

LABS = [
    {
        "id": "LAB01",
        "name": "AI Lab",
        "field": "AI",
    },
    {
        "id": "LAB02",
        "name": "Data Science Lab",
        "field": "AI",
    },
    {
        "id": "LAB03",
        "name": "Game Lab",
        "field": "Game",
    },
    {
        "id": "LAB04",
        "name": "Game CG Lab",
        "field": "Game",
    },
    {
        "id": "LAB05",
        "name": "Web App Lab",
        "field": "WebApp",
    },
    {
        "id": "LAB06",
        "name": "Web Service Lab",
        "field": "WebApp",
    },
    {
        "id": "LAB07",
        "name": "Security Lab",
        "field": "Security",
    },
    {
        "id": "LAB08",
        "name": "Network Lab",
        "field": "Network",
    },
    {

        "id": "LAB09",
        "name": "Design Lab",
        "field": "Design",
    },
    {
        "id": "LAB10",
        "name": "Media Lab",
        "field": "Media",
    },
]

# ======================================
# Task Setting
# ======================================

# Taskが発生する確率(各Community Step)
TASK_SPAWN_PROBABILITY = 0.25

# Taskの有効期限(Step数)
TASK_DURATION = 5

# 現段階で発生するTask
TASK_TYPES = [
    {
        "name": "チャットしてみよう",
        "required_action": "chat",
    },
    {
        "name": "返信してみよう",
        "required_action": "reply",
    },
    {
        "name": "issueに意見を投稿しよう",
        "required_action": "express_opinion",
    },
]

# 将来の拡張候補
FUTURE_TASK_TYPES = [
    {
        "name": "投票してみよう",
        "required_action": "vote",
    },
    {
        "name": "企画を提案してみよう",
        "required_action": "proposal",
    },
]

ISSUE_TEMPLATES = [
    {
        "title": "どの研究分野に興味を持ちましたか？",
        "options": [
            "AI",
            "Game",
            "WebApp",
            "Security",
            "Network",
            "Design",
            "Media",
        ],
        "interest_based": True,
    },
    {
        "title": "学食で食べたいメニューは？",
        "options": [
            "カレー",
            "ラーメン",
            "唐揚げ定食",
            "パスタ",
            "丼もの",
        ],
        "interest_based": False,
    },
    {
        "title": "興味のある学部は？",
        "options": [
            "コンピュータサイエンス学部",
            "メディア学部",
            "工学部",
            "デザイン学部",
            "応用生物学部",
        ],
        "interest_based": False,
    },
]

PROPOSAL_TEMPLATES = [
    "新しい研究室展示を追加する",
    "高校生と大学生の交流企画を開催する",
    "体験授業を開催する",
    "スタンプラリーの対象研究室を増やす",
    "学食の特別メニューを企画する",
    "研究室紹介イベントを開催する",
]

# ==========================================
# Proposal生成・品質評価
# ==========================================

# Proposal 品質生成
PROPOSAL_QUALITY_BASE = 0.2
PROPOSAL_QUALITY_WEIGHT = 0.6
PROPOSAL_QUALITY_NOISE = 0.1

# Agentの認識品質
PROPOSAL_PERCEPTION_NOISE = 0.2
PROPOSAL_SUPPORT_THRESHOLD = 0.6

# Proposalの採択条件
PROPOSAL_APPROVAL_THRESHOLD = 0.6
PROPOSAL_MIN_VOTES = 3

# 投票期間 (初期仮定)
PROPOSAL_VOTING_DURATION = 5