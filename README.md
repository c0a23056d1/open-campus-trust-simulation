# open-campus-trust-simulation

## 1. プロジェクト概要

本プロジェクトでは、大学のオープンキャンパス参加者を想定したエージェントベースシミュレーションである。研究室訪問・スタンプ取得から、オープンキャンパス終了後のコミュニティ活動までをモデル化し、各エージェントの実際の行動をActivity Logとして記録する。

研究の最終的な目的は、行動ログから算出する多面的なTrust Passportを権限制御に活用し、権限付与方式の違いが権限取得とその後の参加行動に与える影響を比較・評価することである。

## 開発段階について

現在はAgent生成、Open Campus Phase、Community Phase、Issue・Task・投票処理、Activity Log出力に加え、**Activity LogからのTrust計算・Trust Passport生成・CSV出力まで実装済み**。現在の権限制御はスタンプ数を基準としており、Trust Passportを使った4方式比較・権限制御は今後の実装対象である。

## 2. シミュレーションの全体構造

Agent(潜在特性・興味分野)

  ↓

Behavior(行動選択)

  ↓

Environment (Open Campus / Community)

  ↓

Activity Log (観測された行動履歴)

  ↓

Trust Calculation（実装済み）

  ↓

Trust Passport（Stepごとに生成・CSV保存済み）

  ↓

Permission Control（4方式比較：今後）

  ↓

DAO Governance(投票・提案など)

  ↓

Community Outcome / Evaluation[今後]

### 2.1. 研究上の設計方針

Agentの潜在特性をそのまま、Trustの値としては利用しない。

潜在特性は行動を生成するための内部パラメータであり、Trustは観測された行動実績に基づいて計算する。

Latent Traits(内部の性質)

  ↓

Actual Behavior(実際に選択された行動)

  ↓

Activity Log(観測可能な記録)

  ↓

Trust Calculation(行動実績から算出)（実装済み）

  ↓

Trust Passport（実装済み）

この分離により、潜在的に協調性が高いAgentでも、実際に協調的な行動をとらなければ、その行動実績はTrustに反映されない設計である。

## 3. 基本設計

・Agent数：100人

・Open Campus Phase：10 Step

・Community Phase：30 Step

・研究室数：10研究室

・Issue(投票)発生期間：Community Phaseの5 Stepごと

・Task発生：設定した確率に基づき不定期に発生

・Random Seed：42

・行動の基本単位：1 Agent・1 Step につき主要行動を原則1つ選択

主な設定値は、`config/settings.py` で管理する。

Taskの発生確率、継続時間、種類、Issueのタイトル・選択肢もこのファイルで定義する。

## 4. Agent モデル

### 4.1. Agentの基本情報

各参加者を独立したAgentとして表現する。Agentは固有ID、潜在特性、興味分野、訪問履歴、スタンプ数、権限状態、Issue 閲覧、投票履歴などを保持する。

### 4.2. 潜在特性(Latent Traits)

・activity：行動の積極性・研究室訪問や活動開始のしやすさ

・persistence：継続性・コミュニティへの継続参加

・cooperation：協調性・チャット/Replyへの参加傾向

・governance：意思決定への関心・IssueやVote等への参加傾向

・reliability：責任性、安定性・将来の行動評価、Trust算出での利用を想定

各特性がどの行動確率式に反映されているかは `src/simulation/behavior.py` の実装を基準とする。

### 4.3. 興味分野

各 Agentは次の7分野に対して 0.0 ~ 1.0 の興味値を持つ

- `AI`

- `Game`

- `WebApp`

- `Security`

- `Network`

- `Design`

- `Media`

Interestは研究室の選択や、研究分野に関する投票の選択肢決定に使用する。

### 4.4. シミュレーション中に変化する状態

・stamp_count：取得済みスタンプ数

・visited_labs：訪問済み研究室

・chat_permission：Chatの利用権限

・vote_permission：Voteの利用権限

・proposal_permission：Proposalの利用権限

・left_community：コミュニティから離脱したか

・viewed_issues：閲覧済みIssue

・expressed_issue：意見投稿済みIssue

・voted_issue：投票済みIssue

## 5. Open Campus Phase

Open Campus Phaseは10 Stepで実行する。Agentは各Stepで研究室訪問などの行動を選択する。

### 5.1. 研究室訪問確率

現在の基本形は次の通り

P(Visit) = 0.2 + 0.6 × Activity

Activity が高い Agent ほど研究室を訪問しやすい。

### 5.2 研究室選択

研究室ごとの重みを Agent の積極性と分野への興味から算出する。

Weight = 0.4 × Activity + 0.6 × Interest

重みが高い研究室ほど選ばれやすい。研究室の候補や対応分野は `config/settings.py` の定義を参照する。

### 5.3 スタンプ取得

- 初訪問：`visit_lab` を記録し、スタンプを1個取得して `get_stamp` を記録する。

- 再訪問：訪問は記録するが、同じ研究室のスタンプは重複取得しない。

- 権限更新：スタンプ数の変化に応じて、現在の暫定的なスタンプベース権限を更新する。

### 5.4 Open Campus 中のその他の行動

現在のシミュレーターには、訪問しない `no_action`、訪問後の感想 `post_visit_comment`、`chat`、`reply` の処理分岐がある。これらが実際にどの程度選ばれるかは `behavior.py` の行動選択と確率設定に依存する。

## 6. Community Phase

Open Campus Phase 終了後、30 Step の Community Phase に移る。Agent はコミュニティにログインし、利用可能な機能や発生中の Issue・Task に応じて行動する。

### 6.1 基本的な処理順序

各 Community Step

  ├─ Environment の Step・Phase を更新

  ├─ Issue の新規発生判定

  ├─ Task の発生・終了判定

  └─ 各 Agent

       ├─ 離脱・権限・ログイン判定

       ├─ 行動選択

       ├─ 選択行動の実行可否を確認

       ├─ Activity Log に記録

       └─ Task の達成条件を確認

### 6.2 Community で扱う主な行動

\| 行動 | 内容 | 主な前提・制約 | 主なログ Action |

\| --- | --- | --- | --- |

\| ログイン | コミュニティへの参加判定 | 離脱状態・Chat権限・ログイン確率など | `login_community` |

\| 何もしない | その Step は主要行動を行わない | 行動選択の結果 | `no_action` |

\| Chat | 新しいメッセージを投稿 | Chat権限 | `chat` |

\| Reply | 他者の投稿に返信 | Chat権限 | `reply` |

\| Issue 閲覧 | 発生中の議題を閲覧 | Issue が存在すること | `view_issue` |

\| 意見投稿 | 閲覧した議題に意見を投稿 | 対象 Issue の存在・閲覧状態等 | `express_opinion` |

\| Vote | Issue の選択肢から1つ選び投票 | Vote権限・Issue閲覧・未投票 | `vote` |

\| Task 達成 | Task 指定の行動を行い達成 | Task の有効期間・対象行動 | `complete_task` |

\| Proposal | 新しい企画や提案を投稿する想定 | Proposal権限 | ****実装・ログ出力を要確認**** |

### 6.3 Chat / Reply

Chat はコミュニティへの投稿、Reply は他の投稿への返信を表す。Chat権限が必要であり、行動発生時には Agent・Step・Action などをログに残す。Chat と Reply は参加状況や相互作用を評価するための基礎データとなる。

### 6.4 Issue（議題）の生成と閲覧

Community Phase では原則 ****5 Step ごと****に新しい Issue を生成する。Issue は `issue_id`、タイトル、複数の選択肢、開始 Step、投票結果を持つ。

例：

\| Issue のテーマ例 | 選択肢例 |

\| --- | --- |

\| 興味のある研究分野 | AI / Game / WebApp / Security / Network / Design / Media |

\| 学食で食べたいメニュー | カレー / ラーメン / 唐揚げ定食 / パスタ / 丼もの |

\| 興味のある学部 | コンピュータサイエンス学部 / メディア学部 / 工学部 / デザイン学部 / 応用生物学部 |

実際に使用するテーマ・選択肢は `config/settings.py` の `ISSUE_TEMPLATES` を参照する。Issue の発生時には `SYSTEM` による `issue_created` ログを記録する。Agent が議題を確認すると `view_issue` を記録する。

### 6.5 Express Opinion（意見投稿）

Agent が閲覧した Issue に対して意見を表明する行動である。投票とは異なり、議題に対する意見表明という参加実績を記録する。`express_opinion` は将来の Contribution Trust などを算出するための候補データとなる。

### 6.6 Vote（投票）

Vote は、****1つの Issue に対して複数選択肢から1つを選ぶ方式****である。

```text
Issue 発生
  ↓
Agent が Issue を閲覧
  ↓
Vote 権限の有無を確認
  ↓
同じ Issue に未投票であることを確認
  ↓
選択肢を1つ決定
  ↓
Issue に投票結果を保存
  ↓
Agent の voted_issues を更新
  ↓
Activity Log（vote）を記録
```

研究分野など、Agent の Interest と対応する選択肢がある場合は、興味値を選択に反映する設計である。その他のテーマでは、行動モデルに定義された選択規則を用いる。

同じ Agent が同じ Issue に複数回投票しないよう、`Issue.add_vote(...)` と Agent の投票済み履歴を利用する。

### 6.7 Task（期間限定の行動課題）

Task は Community Phase で不定期に発生する。Task は ID、名称、対象 Action、開始・終了 Step、達成した Agent を管理する。

```text
Task 発生（task_created）
  ↓
有効期間中に Agent が対象行動を実行
  ↓
達成条件を判定
  ↓
達成時に complete_task を記録
  ↓
期間終了時に task_ended を記録
```

Task の種類は `TASK_TYPES`、発生確率は `TASK_SPAWN_PROBABILITY`、期間は `TASK_DURATION` で管理する。Task の達成判定は `check_task_completion(...)` が担当する。

### 6.8 Proposal（企画提案）

Proposal は Agent が新しい企画やテーマを提案する行動である。現在のシミュレーションでは `proposal` のActivity Log出力が確認されている。権限付与条件は現在スタンプベースであり、Trustベースへの変更は今後の課題である。

## 7. 権限制御

### 7.1 現在の暫定実装（スタンプ数による権限付与）

\| 条件 | 解放する権限 |

\| --- | --- |

\| Stamp ≥ 1 | Chat |

\| Stamp ≥ 3 | Vote |

\| Stamp ≥ 5 | Proposal |

この条件は現段階のシミュレーションを動作させるための****スタンプベースの暫定ルール****であり、4方式比較の最終仕様ではない。

### 7.2 比較予定の4方式

\| 方式 | 権限付与の判断基準 | 比較したい観点 |

\| --- | --- | --- |

\| Stamp-based | スタンプ取得数 | 単純な活動量に基づく付与 |

\| Participation Trust-based | 参加状況に関する Trust | 継続的・積極的な参加の反映 |

\| Contribution Trust-based | 貢献に関する Trust | 実質的なコミュニティ貢献の反映 |

\| Multi-dimensional Trust-based | 複数 Trust の組合せ | 多面的な行動実績を用いた付与 |

****Chat権限の解放条件（Stamp ≥ 1）は4方式で共通****とし、その後の Vote / Proposal 権限付与方法を比較する方針である。同じ Agent の特性・初期条件を使い、権限付与方法だけを変更することで、方式間の差を分析する。

## 8. Activity Log

Agent の実際の行動と、Issue・Task などのシステムイベントを記録する。

\| カラム | 内容 |

\| --- | --- |

\| `log_id` | ログ固有 ID |

\| `agent_id` | Agent ID。システムイベントでは `SYSTEM` |

\| `step` | 発生 Step |

\| `phase` | `open_campus` / `community` |

\| `action` | 行動・イベント種別 |

\| `target` | 対象研究室、Issue、Task など |

\| `value` | 選択肢や補足情報など |

### 8.1 主な Action 名

\| Phase | Action | 説明 |

\| --- | --- | --- |

\| Open Campus | `visit_lab` | 研究室を訪問 |

\| Open Campus | `get_stamp` | 初訪問によるスタンプ取得 |

\| Open Campus | `post_visit_comment` | 訪問後の感想 |

\| Open Campus | `chat` / `reply` | チャット・返信 |

\| Open Campus | `no_action` | 行動なし |

\| Open Campus | `unlocked_chat` など | 権限解放ログ（コードの命名に注意） |

\| Community | `login_community` | コミュニティにログイン |

\| Community | `chat` / `reply` | 投稿・返信 |

\| Community | `issue_created` | Issue 作成（SYSTEM） |

\| Community | `view_issue` | Issue 閲覧 |

\| Community | `express_opinion` | 意見投稿 |

\| Community | `vote` | Issue への投票 |

\| Community | `task_created` | Task 発生（SYSTEM） |

\| Community | `complete_task` | Task 達成 |

\| Community | `task_ended` | Task 終了（SYSTEM） |

\| Community | `no_action` | 行動なし |

****命名上の注意****：元のREADMEでは `unlock_chat` としていたが、確認できた `simulator.py` のコードは `action=f"unlocked\_{permission}"` となっている。CSV の実際の出力に合わせて統一すること。

### 8.2 ログの例

以下は形式を示す説明用の例であり、実際の実行結果を転載したものではない。

```csv
log_id,agent_id,step,phase,action,target,value
LOG_000001,A003,1,open_campus,visit_lab,LAB06,
LOG_000002,A003,1,open_campus,get_stamp,LAB06,1
LOG_000003,A003,1,open_campus,unlocked_chat,chat,True
LOG_000004,SYSTEM,15,community,issue_created,ISSUE_001,どの研究分野に興味を持ちましたか？
LOG_000005,A003,15,community,view_issue,ISSUE_001,
LOG_000006,A003,16,community,vote,ISSUE_001,AI
```

## 9. 出力データ

### 9.1 Agent Profile

****出力先****：`results/agents/agent_profiles.csv`

初期の潜在特性・Interest Profile を保存する。主なカラム：

```text
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
```

### 9.2 Activity Log

****出力先****：`results/logs/activity_logs.csv`

Open Campus / Community の行動履歴とシステムイベントを時系列で保存する。Trust 算出・権限制御方式比較・評価指標計算の基礎データとして利用する。

### 9.3 Trust Passport（今回追加・実装済み）

**出力先**：`results/passports/trust_passports.csv`

Open Campus 10 StepとCommunity 30 Stepの各Step終了時点で、100体のAgentについて、それまでのActivity Logを使ってTrust Passportを更新・保存する。1 Agent × 40 Stepで40件、全100体で**4,000件のスナップショット**を生成する。

| カラム | 内容 |
| --- | --- |
| `passport_id` | AgentのPassport ID（同じAgentでは各Stepで共通） |
| `agent_id` | Agent ID |
| `step` | 算出対象のStep |
| `participation` | 参加状況のTrust（0.0〜1.0） |
| `contribution` | 貢献度のTrust（0.0〜1.0） |
| `reliability` | 継続性・責任性のTrust（0.0〜1.0） |
| `governance` | 議題への関与度のTrust（0.0〜1.0） |
| `interests` | 訪問研究室の分野から算出した興味分野の割合（JSON文字列） |
| `evidence` | Trustの算出根拠・内訳（JSON文字列） |

**注意**：1 Agentにつき1つのPassportをStepごとに更新した履歴である。したがって`passport_id`単独では行が一意にならず、`agent_id`と`step`の組でスナップショットを識別する。`SYSTEM`のイベントはAgentのTrust計算対象に含めない。内部の潜在特性値をTrustとして直接使用しない。

### 9.4 今後の出力予定

- `results/metrics/`：方式別の評価結果
- `results/figures/`：方式間比較のグラフ
- 権限付与履歴など（Trust Passportの時系列履歴は実装済み）

## 9.5 Trust Passportの生成処理と計算式（今回追加）

各Stepの行動ログ記録後、AgentごとにそのStepまでのログを抽出し、`src/trust/calculator.py`の4関数でTrustを算出する。`src/trust/passport.py`の`generate_passport(...)`がTrust、興味分野、算出根拠をまとめ、`experiments/run_experiment.py`からCSVに出力する。ネストした`interests`と`evidence`はJSON文字列として保存する。

| Trust | 現在の計算式 | 使用するAction |
| --- | --- | --- |
| Participation | `0.5 × 訪問率 + 0.5 × コミュニティログイン率` | `visit_lab`、`login_community` |
| Contribution | `0.3 × コメント率 + 0.4 × 議論貢献率 + 0.3 × タスク完了実績` | `visit_lab`、`post_visit_comment`、`reply`、`express_opinion`、`complete_task` |
| Reliability | `0.4 × タスク達成実績 + 0.6 × ログイン継続率` | `complete_task`、`login_community` |
| Governance | `0.5 × 議題閲覧実績 + 0.5 × 意見表明率` | `view_issue`、`express_opinion` |

**計算の補足**

- **Participation**：訪問率は訪問済みの異なる研究室数÷全10研究室。ログイン率はログインしたStep数÷コミュニティ開始後の経過Step数。
- **Contribution**：コメント率はコメント済み訪問研究室数÷訪問研究室数。議論貢献率は`min(1, (reply回数 + express_opinion回数) / コミュニティ経過Step数)`。タスク完了実績は`min(1, complete_task回数 / コミュニティ経過Step数)`。`reply`は現行コードではOC期間のものも集計する。
- **Reliability**：タスク達成実績は`min(1, 完了した異なるTask数 / 3)`。ログイン継続率はログインStep数÷コミュニティ経過Step数。**3件で満点**は現行の設計上の基準であり、全Taskに対する達成率とは異なる。
- **Governance**：議題閲覧実績は`min(1, 閲覧した異なるIssue数 / 3)`。意見表明率は、閲覧したIssueのうち意見投稿したIssueの割合。`vote`や`proposal`は現行のGovernance算出には含めない。
- **Interests**：訪問した異なる研究室の分野別件数を集計し、その合計で割った割合。Agentの潜在的な興味値をそのままコピーしない。
- 分母が0の場合は対応する比率を0とする。`min(1, ...)`で一部の指標の上限を1とする。

**注意**：これらは現在の実装式であり、各Trustの妥当性や重みの適切さを検証した結果ではない。現在のPassport生成は既存のスタンプベース権限制御と独立しており、Trust値で権限を変更する処理はまだ導入していない。

## 10. ファイル構成と役割

以下は現在の構成と、これまでの開発で扱った主要ファイルを整理したもの。****存在・実装内容を確認できていないファイルは「予定／要確認」と明記する。****

```text
open-campus-trust-simulation/
├── config/
│   └── settings.py                # 実験条件、研究室、Issue・Task設定
├── experiments/
│   └── run_experiment.py          # 実験実行の入口
├── results/
│   ├── agents/
│   │   └── agent_profiles.csv     # Agentの初期特性
│   ├── figures/                   # 図の出力先（今後）
│   ├── logs/
│   │   └── activity_logs.csv      # 行動履歴
│   └── metrics/                   # 評価指標の出力先（今後）
├── src/
│   ├── evaluation/
│   │   └── metrics.py             # 評価指標（実装状況要確認）
│   ├── models/
│   │   ├── activity_log.py        # Activity Logの構造・作成処理
│   │   ├── agent.py               # Agentの属性・状態
│   │   ├── environment.py         # Step・Phase・Issue/Taskの環境状態
│   │   ├── issue.py               # Issueと選択肢・投票結果
│   │   ├── task.py                # Taskと達成状況
│   │   └── trust_passport.py      # Trust Passport（今後／要確認）
│   ├── simulation/
│   │   ├── behavior.py            # 行動確率・行動選択
│   │   ├── permission.py          # 現在のスタンプベース権限制御
│   │   ├── simulator.py           # Open Campus / Communityの進行
│   │   └── trust.py               # Trust算出（今後／要確認）
│   └── utils/
│       └── random_utils.py        # 乱数関連（存在要確認）
├── tests/
│   └── test_open_campus.py        # 単体テスト
├── README.md
└── requirements.txt
```

### 10.1 ファイル別の詳しい役割

\| ファイル | 主な責務 | 関連する処理・データ |

\| --- | --- | --- |

\| `config/settings.py` | シミュレーション全体の設定 | Agent数、Step数、研究室、乱数Seed、Issueテンプレート、Task設定 |

\| `experiments/run_experiment.py` | 実行入口 | Agent生成、フェーズ実行、CSV出力、結果集計 |

\| `src/models/agent.py` | Agentデータ構造 | 潜在特性、Interest、Stamp、権限、Issue履歴 |

\| `src/models/environment.py` | 環境の現在状態 | `current_step`、`phase`、Issue/Task の発生状態 |

\| `src/models/activity_log.py` | ログ作成・管理 | `ActivityLog`、`create_activity_log(...)` |

\| `src/models/issue.py` | 投票対象の管理 | Issue ID、タイトル、選択肢、`add_vote(...)`、重複防止 |

\| `src/models/task.py` | 期間限定課題の管理 | 開始・終了 Step、対象 Action、達成 Agent |

\| `src/simulation/behavior.py` | Agentの行動決定 | 訪問確率、研究室選択、ログイン確率、Community行動、投票選択肢 |

\| `src/simulation/permission.py` | 権限更新 | `update_stamp_permissions(...)` |

\| `src/simulation/simulator.py` | Step進行とイベント処理 | `run_open_campus_simulation(...)`、`run_community_simulation(...)`、`update_issue(...)`、`update_task(...)`、`check_task_completion(...)` |

\| `tests/test_open_campus.py` | 実装の動作確認 | 訪問、Stamp、権限、行動・ログのテスト等 |

\| `src/simulation/trust.py` | Trust算出 | 今後の実装対象・要確認 |

\| `src/models/trust_passport.py` | Trust値の保持 | 今後の実装対象・要確認 |

\| `src/evaluation/metrics.py` | 方式比較と評価 | 今後の実装対象・要確認 |

## 11. 実行方法

プロジェクトルートで実行する。

### 11.1 仮想環境の有効化

```bash
source .venv/bin/activate
```

### 11.2 必要ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 11.3 シミュレーションの実行

```bash
python3 -m experiments.run_experiment
```

### 11.4 結果の確認

```text
results/agents/agent_profiles.csv
results/logs/activity_logs.csv
results/passports/trust_passports.csv
```

## 12. 動作確認の観点

「プログラムがエラーなく終了した」ことと「研究上の意図どおり動いた」ことは区別する。以下を確認する。

- [x] 100 Agent が生成され、初期特性が保存される

- [x] Open Campus 10 Step、Community 30 Step が実行される

- [ ] 同じ研究室のスタンプを重複取得しない

- [ ] Chat権限のない Agent が Chat / Reply を実行しない

- [ ] Vote権限のない Agent が Vote を実行しない

- [ ] Vote は有効な選択肢から1つを選び、同一 Issue に重複投票しない

- [ ] Issue が指定間隔で生成される

- [ ] Task の開始・終了・達成が適切に記録される

- [ ] Proposal の行動分岐と権限制御が実装され、ログが記録される

- [ ] 主要行動が原則1 Agent・1 Step に1つとなる

- [ ] `SYSTEM` イベントと Agent 行動を区別できる

- [ ] テストが成功する

- [ ] 同じ Seed・設定で同じ結果を再現できる

## 13. 今後の実装予定

### 13.1 Trust Calculation / Trust Passport（生成機能は実装済み）

Activity Logをもとに4種類のTrustを計算し、各Agent・各StepのTrust Passportを`results/passports/trust_passports.csv`に保存する処理は実装済み。今後は、スタンプ数だけでは表現できない活動の違いをTrust Passportが表現できるか検証する。**潜在特性の値をそのままTrustとして転用しない。**

### 13.2 4方式への分岐

Stamp を1個取得して Chat 権限を得た時点を共通の起点とし、同一条件の Agent を4方式に分けてシミュレーションする。方式間で Agent の初期特性や比較条件が変わらないように管理する。

### 13.3 権限付与と行動のフィードバック

```text
Activity Log
  ↓
Trust Passport 更新
  ↓
方式ごとに Vote / Proposal 権限を判定
  ↓
権限に応じて実行可能な行動が変化
  ↓
新しい Activity Log が蓄積
  ↓
Trust Passport を再更新
```

### 13.4 評価項目

\| 評価観点 | 主な指標 | 明らかにしたいこと |

\| --- | --- | --- |

\| 継続参加 | Post-OC Participation Rate / Continuation Rate | どの権限制御方式がOC後の継続参加につながるか |

\| Stage移行 | Stage 1→2 / Stage 2→3 Transition Rate | 参加者が意思決定者・共創者へ移行するか |

\| 権限利用 | Vote / Proposal Utilization Rate | 付与された権限が実際に使われるか |

\| 権限適切性 | Precision / Recall / FAR | 適切なAgentへ権限を付与できるか |

必要に応じて、閾値を変化させる感度分析も行う。権限適切性の評価には「適切なAgent」の基準を別途定義する必要がある。

## 14. 再現性と比較実験

現段階では `RANDOM_SEED = 42` を用いる。これにより同じ実行環境・設定・乱数消費順序で結果を再現しやすくする。最終評価では複数 Seed で繰り返し実験し、方式間の差が特定の乱数系列だけに依存していないかを検討する。

## 15. 開発状況まとめ

\| 項目 | 状況 |

\| --- | --- |

\| Agent生成・潜在特性・Interest | 実装済み |

\| Open Campus Phase・訪問・Stamp | 実装済み |

\| Activity Log・Agent Profile CSV | 実装済み |

\| 暫定Stampベース権限制御 | 実装済み |

\| Community Phase・ログイン・Chat・Reply | 実装済みの処理あり |

\| Issue生成・閲覧・意見投稿 | 実装済みの処理あり |

\| 複数選択肢からのVote・重複防止 | 実装済みの処理あり |

\| Task生成・達成・終了 | 実装済みの処理あり |

\| Proposal行動・ログ出力 | 実行結果で確認済み |

\| Trust Calculation（4種類）/ Trust Passport生成 | 実装済み |
| Trust PassportのStep別CSV出力（4,000件） | 実装済み |
| Trust Passportを使った権限制御 | 今後の主要実装 |

\| 4方式比較・分岐 | 今後の主要実装 |

\| 評価指標・感度分析 | 今後の主要実装 |

\> 本READMEは現時点で共有された設計と確認可能な `simulator.py` を基に整理したもの。各行動の確率式、Proposal の実装状況、ディレクトリ内の未確認ファイルについては、リポジトリの最新コードに合わせて更新する。

---

## 16. コードの読み方・既存ファイルの簡単な説明（学習用付録）

この節は、READMEに記載された主要ファイルと、今回追加したTrust Passport関連ファイルの**役割・よく使うPython構文**を整理する。未共有のファイルについて、実際の全行や`import`文を確認した説明ではない。実際の処理の詳細はソースコードを参照すること。

### 16.1 `import`の意味

| 記述例 | 意味 |
| --- | --- |
| `import random` | Python標準の乱数モジュールを読み込む。`random.random()`などを使う。 |
| `import csv` | CSVの読み書き用モジュールを読み込む。 |
| `import os` | ディレクトリやパスなど、OS関連の操作に使う。 |
| `import json` | 辞書・リストとJSON文字列の相互変換に使う。 |
| `from pathlib import Path` | パスをオブジェクトとして扱う`Path`を読み込む。 |
| `from dataclasses import dataclass, asdict` | `dataclass`はデータを保持するクラスの定義を簡単にし、`asdict`はそのインスタンスを辞書に変換する。 |
| `from typing import Any` | 型が一種類に限定されない値を型注釈で示す。 |
| `import pandas as pd` | 表形式のデータを扱うライブラリを`pd`という短い名前で使う。 |
| `from config.settings import LABS` | 自分のプロジェクト内の設定ファイルから`LABS`を読み込む。 |
| `from src.trust.calculator import calculate_participation` | 自作モジュールから指定した関数を読み込む。 |

`import`は**別のファイル・ライブラリにある機能を使えるようにする宣言**であり、それ自体がシミュレーションを実行する命令とは限らない。`from A import B`はAの中のBを指定して読み込む書き方である。

### 16.2 Pythonの基本構文

| 構文 | 意味・例 |
| --- | --- |
| `def calculate_participation(...):` | 関数を定義する。処理を名前でまとめ、必要なときに呼び出せる。 |
| `return {...}` | 関数の計算結果を呼び出し元へ返す。 |
| `class Agent:` | Agentの属性・処理をまとめるクラスを定義する。 |
| `@dataclass` | 主にデータ保持用のクラスの初期化などを簡潔に記述する。 |
| `for agent in agents:` | `agents`から1件ずつ取り出して繰り返す。 |
| `if action == "visit_lab":` | 条件が成立したときだけ処理する。 |
| `list[dict]` | 辞書を要素として持つリストを表す型注釈。 |
| `set` / `{... for ...}` | 重複しない値の集合。訪問研究室や閲覧Issueの重複排除に使う。 |
| `[log for log in logs if ...]` | 条件に合うログだけを取り出すリスト内包表記。 |
| `sum(1 for log in logs if ...)` | 条件に合うログの件数を数える。 |
| `min(1.0, value)` | 値が1.0を超えないよう上限を設ける。 |
| `max(0, value)` | 値が0未満にならないよう下限を設ける。 |
| `None` | 値がないことを表す。ログの`target`や`value`が空の場合などに使う。 |
| `True` / `False` | 真偽値。権限の有無や条件判定に使う。 |
| `f"TP{agent_id[1:]}"` | f文字列。Agent IDの一部を埋め込んでPassport IDを作る。 |

### 16.3 ファイルごとの役割

| ファイル | 簡単な説明 |
| --- | --- |
| `config/settings.py` | Agent数、Step数、研究室一覧、Issue・Task設定、乱数Seedなどの**設定値**をまとめる。 |
| `experiments/run_experiment.py` | **実行の入口**。Agent生成→OC→Community→各CSV保存をまとめて呼び出す。今回Trust Passport CSV出力を追加。 |
| `src/models/agent.py` | Agentの潜在特性、興味分野、スタンプ、権限、行動履歴に関する状態を持つ。 |
| `src/models/environment.py` | 現在のStep、Phase、IssueやTaskなど、シミュレーション環境の状態を扱う。 |
| `src/models/activity_log.py` | `ActivityLog`データ構造、`create_activity_log`によるログ追加、CSV保存を担当。`@dataclass`、`csv`などを使用。 |
| `src/models/issue.py` | 議題のID・選択肢・投票結果を保持し、投票や重複投票防止を扱う。 |
| `src/models/task.py` | Taskの開始・終了Step、必要なAction、達成者を扱う。 |
| `src/simulation/behavior.py` | Agentの特性や興味から行動確率を求め、研究室・行動・投票先などを選ぶ。乱数処理と関係が深い。 |
| `src/simulation/permission.py` | 現在のスタンプ数に応じたChat/Vote/Proposal権限更新を扱う。 |
| `src/simulation/permissions.py` | リポジトリに存在する場合の役割は要確認。`permission.py`とは別ファイルなので混同しない。 |
| `src/simulation/simulator.py` | Stepを進め、行動を実行してログを作る中心処理。今回、各Step終了時のPassport生成処理を追加。 |
| `src/simulation/trust.py` | 既存ファイル。実際の役割は要確認。今回の4種類のTrust計算本体は`src/trust/calculator.py`。 |
| `src/trust/__init__.py` | `src/trust`をPythonパッケージとして扱うためのファイル。空でもよい。 |
| `src/trust/calculator.py` | `calculate_participation`、`calculate_contribution`、`calculate_reliability`、`calculate_governance`で4種類のTrustを計算する。 |
| `src/trust/passport.py` | `calculate_interests`で興味分野を推定し、`generate_passport`でTrust、Interests、Evidenceを1つの辞書にまとめる。 |
| `src/models/trust_passport.py` | 旧READMEに記載されたファイル。存在と内容は要確認。今回のPassport生成本体とは別。 |
| `src/evaluation/metrics.py` | 権限方式の比較・評価指標を計算するためのファイルとして記載。現行の実装内容は要確認。 |
| `src/utils/random_utils.py` | 乱数関連の補助処理用として記載。ファイルの存在・内容は要確認。 |
| `tests/test_open_campus.py` | OC訪問・スタンプ・権限などが想定どおり動くかテストするためのファイル。 |
| `requirements.txt` | `pip install -r requirements.txt`で必要な外部ライブラリをインストールするための一覧。 |
| `README.md` | 研究・シミュレーションの設計、実行方法、開発状況を記録する説明書。 |

### 16.4 今回追加したTrust Passport処理のつながり

```text
experiments/run_experiment.py
  ├─ src/simulation/simulator.py
  │    ├─ Open Campus / Community の各Stepを実行
  │    ├─ ActivityLogを作成・蓄積
  │    └─ Step終了後に各AgentのPassportを生成
  │          └─ src/trust/passport.py
  │                ├─ calculate_interests(...)  # 訪問分野から興味を算出
  │                └─ generate_passport(...)
  │                      └─ src/trust/calculator.py
  │                            ├─ calculate_participation(...)
  │                            ├─ calculate_contribution(...)
  │                            ├─ calculate_reliability(...)
  │                            └─ calculate_governance(...)
  └─ results/passports/trust_passports.csv に保存
```

**CSVの保存とTrustによる権限制御は別機能**。現在は生成・保存まで実装済みであり、Trust値を用いたVote/Proposal権限判定や4方式比較は今後の実装対象である。
