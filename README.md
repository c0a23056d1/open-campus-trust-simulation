# open-campus-trust-simulation

## 概要

本プロジェクトでは、オープンキャンパス参加者を想定したエージェントベースシミュレーションである。

オープンキャンパスにおける研究室訪問やスタンプ取得、
その後のコミュニティ活動をシミュレーションし、
Activity LogからTrust Passportを生成する。

さらに、Trust Passportを用いた権限付与方法の違いが、
DAO型コミュニティにおける参加行動や意思決定に
どのような影響を与えるかを比較することを目的とする。

## シミュレーション全体構成

Agent
  ↓
Behavior
  ↓
Activity Log
  ↓
Trust Calculation
  ↓
Trust Passport
  ↓
Permission Control
  ↓
DAO Governance
  ↓
Community Outcome
  ↓
Evaluation

## 研究上の役割

本シミュレーションでは、Agentが持つ潜在特性そのものをTrustとして使用しない。

Latent Traits
    ↓
行動確率に影響
    ↓
Actual Behavior
    ↓
Activity Log
    ↓
Trust Calculation
    ↓
Trust Passport

この構造により、
「Agent内部の性質」と「実際に観測された行動から算出するTrust」
を分離する。


## Agent

シミュレーションでは、オープンキャンパス参加者を
Agentとして表現する。

現在は100人のAgentを生成する。


## 潜在特性

各Agentは以下の5つの潜在特性を持つ

| Trait | 内容 |
|---|---|
| Activity | 行動の積極性 |
| Persistence | 継続性 |
| Cooperation | 協調性 |
| Governance | 意思決定への関心 |
| Reliability | 責任を持って行動する傾向 |

各値は0.0～1.0で生成する。


## 興味分野

各Agentは以下の分野に対するInterestを0.0~1.0で持つ

- AI
- Game
- WebApp
- Security
- Network
- Design
- Media


## Open Campus Simulation

Open Campus Phaseでは10 Stepのシミュレーションを行う。

各ステップでAgentは研究室を訪問するかどうかを決定する。

## 研究室訪問確率

研究室を訪問する確率は以下とする

P(Visit) = 0.2 + 0.6 * Activity

Activityが高いAgentほど研究室を訪問しやすい

## 研究室選択

研究室を訪問する場合、
Activityと研究分野へのInterestから研究室選択の重みを計算する

Weight = 0.4 * Activity + 0.6 * Interest

重みが高い研究室ほど選択されやすくなる。

## Stamp取得

未訪問の研究室を訪問した場合、Stampを1個獲得する。
同じ研究室を再訪問した場合、新しいStampは取得しない。

初訪問
↓
Stamp + 1

再訪問
↓
Stamp変化なし

## Chat Permission

4つの権限付与方式全てにおいて、
Chatの利用条件は共通とする。

Stamp >= 1
↓
Chat Permission = True

最初のStampを取得した時点でChatが解放される。

## Activity Log

Agentの実際の行動をActivity Logとして記録する。

現在記録している主なActionは以下である。

visit_lab
get_stamp
unlock_chat

Activity Logの形式は以下である。

| Column | 内容 |
|---|---|
| log_id | ログ固有ID |
| agent_id | Agent ID |
| step | 行動したStep |
| phase | シミュレーションフェーズ |
| action | 行動内容 |
| target | 行動対象 |
| value | 追加情報 |


## 出力データ

### Agent Profile

result/agents/agent_profiles.csv

各Agentの初期特性を保存する。

主なデータ
agent_id
activity
persistence
cooperation
governance
reliability
interest_AI
interest_Game
interest_WebApp
interest_Security
interest_Network
interest_Design
interest_Media

### Activity Log

results/logs/activity_logs.csv

シミュレーション中に発生した行動履歴を保存する

例：
LOG_000001,A003,1,open_campus,visit_lab,LAB06
LOG_000002,A003,1,open_campus,get_stamp,LAB06,1
LOG_000003,A003,1,open_campus,unlock_chat,chat,True


## ディレクトリ構成

```text
open-campus-trust-simulation/
│
├── config/
│   └── settings.py
│
├── experiments/
│   └── run_experiment.py
│
├── results/
│   ├── agents/
│   │   └── agent_profiles.csv
│   ├── figures/
│   ├── logs/
│   │   └── activity_logs.csv
│   └── metrics/
│
├── src/
│   ├── evaluation/
│   │   └── metrics.py
│   │
│   ├── models/
│   │   ├── activity_log.py
│   │   ├── agent.py
│   │   ├── environment.py
│   │   └── trust_passport.py
│   │
│   ├── simulation/
│   │   ├── behavior.py
│   │   ├── permissions.py
│   │   ├── simulator.py
│   │   └── trust.py
│   │
│   └── utils/
│       └── random_utils.py
│
├── tests/
├── README.md
└── requirements.txt
```


## 実行方法

### 1.仮想環境を有効化

source .venv/bin/activate

### 2.必要ライブラリをインストール

pip install -r requirements.txt

### 3.シミュレーション実行

プロジェクトルートで以下を実行する

python3 -m experiments.run_experiment

### 4.結果確認

Agent初期特性：results/agents/agent_profiles.csv

Activity Log：results/logs/activity_logs.csv


## 現在の実装状況

実装済み：
- シミュレーション基本設定
- Agentモデル
- 潜在特性
- Interest Profile
- 100 Agent生成
- Random Seedによる再現性確保
- Environment
- Open Campus 10 Step
- 研究室訪問確率
- Interestを考慮した研究室選択
- Stamp取得
- Chat Permission解放
- Activity Log
- Agent Profile CSV出力
- Activity Log CSV出力


## 今後の実装予定

今後は以下を実装する。

Community Phase
    ↓
Chat / Reply / Issue / Opinion / Task
    ↓
Trust Calculation
    ↓
Trust Passport
    ↓
4種類のPermission Method
    ↓
Vote / Proposal
    ↓
Community Outcome
    ↓
Evaluation


比較する権限付与方式は以下の4方式を予定している。

1. Stamp-based
2. Participation Trust-based
3. Contribution Trust-based
4. Multi-dimensional Trust-based


## 再現性

現在はRandom Seedを固定している。

RANDOM_SEED = 42

同じ条件で実行した場合に、
同じAgent特性および同じ乱数系列を再現できるようにする。

最終評価では複数のRandom Seedを使用し、
特定の乱数系列だけに依存しない結果を評価する予定である