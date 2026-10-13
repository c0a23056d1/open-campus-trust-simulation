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