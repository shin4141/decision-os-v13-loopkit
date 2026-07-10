# V13 Build Capsule

## Pain Timing Map / Pain Signal Intelligence v0.1

## 1. Capsule Name

```text
Pain Timing Map — V13 Build Capsule v0.1
```

補助名：

```text
Pain Signal Intelligence
```

外向き名称：

```text
Pain Timing Map
```

内部概念：

```text
Pain Signal Intelligence
```

## 2. Target Layer

```text
V13 / Build Boundary / Loop Gate / Future-Line Discovery
```

隣接レイヤ：

```text
V9: As-of / Release integrity
V10: Survival-bounded planning
V12: Completion Integrity
V14: Resource Justice
Entry Window Radar: adjacent but separate
```

このカプセルは **V13 Build Capsule** であり、まだ新repo実装ではない。

## 3. Decision Owner

```text
Decision Owner: designated Decision Owner
```

AI / Codex の役割：

```text
整理役
圧縮役
反論役
証拠整理役
実装準備役
```

AI / Codex は、何を作るべきかを最終決定しない。

## 4. Current Gate

```text
MVP fixed draft: PASS
V13 capsule creation: GO
V13 capsule draft: PASS after this document
New repo build: HOLD
Codex implementation: HOLD
API route: HOLD
Generic search tool framing: BLOCK
Pain notebook framing: BLOCK
Build Command framing: BLOCK
“Sellable idea recommendation” framing: BLOCK
Evidence-backed Pain Signal Map framing: GO
```

### Repo Root Canon

```text
Before running git status, editing files, committing, or reporting repo state, confirm the actual project root.
Do not work from a parent directory, empty outer repo, or similarly named folder.
If the expected repo is nested, use the nested real repo path as the working root and report it explicitly in Context Health.
```

Context Health reporting, when relevant:

```text
Repo Root:
Root Drift Risk: YES/NO
If YES, state the correct working root and do not proceed from the wrong directory.
```

## 5. One-line Definition

```text
Pain Timing Map is an evidence-backed personal map that turns unnamed market pains into time-based Pain Market Signal curves across Now / 1M / 3M / 6M / 12M.
```

日本語：

```text
Pain Timing Map は、まだ名前のない市場の痛みを、Now / 1M / 3M / 6M / 12M の時間軸上の Pain Market Signal カーブとして整理する、証拠付きの個人用未来痛み地図である。
```

## 6. Purpose

Pain Timing Map の目的は、ユーザーに「これを作れ」と命令することではない。

目的はこれ。

```text
未命名の市場痛みを集める
痛みを時間軸上に置く
痛みを点ではなく成長カーブとして見る
Pain Market Signal を比較する
ユーザーの強み・避けたい領域・売りたい相手で補正する
未来線を選ぶための材料を出す
```

短く言うなら：

```text
自分専用の「次に来る痛み」地図を育てる。
```

## 7. Non-purpose

Pain Timing Map は以下ではない。

```text
売れるものを教えるツールではない
Build Commandではない
市場予測保証ツールではない
ただの検索ツールではない
Redditまとめツールではない
痛みノートではない
API収集エンジンではない
自動で作るものを決めるツールではない
ユーザーの代わりに事業責任を負うものではない
```

固定文：

```text
This is not a recommendation to build.
This is an evidence-backed pain signal map.
The build decision remains with the user.
```

日本語：

```text
これは「作れ」という推薦ではない。
証拠付きの痛みシグナル地図である。
作るかどうかの責任はユーザーに残る。
```

## 8. Build Boundary

### Allowed later, after separate GO

新repoビルドが別GateでGOになった場合、許可される最小範囲はこれ。

```text
README
AGENTS
STATUS
inputs/
outputs/
schema/
prompts/
examples/
manual sample report
manual validation prompt
```

MVP段階で許可される方向：

```text
manual-first
evidence-backed
local files
sample inputs
sample outputs
schema draft
prompt-based evaluation
no API dependency
no scraping dependency
no automated collection first
```

### Not allowed in initial build

```text
API-first architecture
Reddit scraper
generic search engine
full web crawler
automatic market prediction
paid recommendation engine
build command generator
agentic autonomous builder
ranking-only dashboard
genre calendar
single-operator personal pain tool
```

## 9. Input Boundary

ユーザーに最初から検索キーワードを聞かない。

初期入力は、検索語ではなく探索方針と制約。

```text
探索したい時間軸
自分の強み・技術・資産
作りたくない領域
売りたい相手
収益化まで待てる期間
出してほしい視点
```

Decision Owner向け初期入力例：

```text
AI / LLM / 個人開発 / バイブコーディング周辺で、今後3〜12ヶ月に顕在化しそうな未命名の痛みを探したい。
ただし動画ツール、API-first、大規模BtoB営業は避けたい。
自分の既存資産は Decision-OS、V12/V13、handoff、re-entry、AI作業の事故防止、GitHub/OSS導線。
目的は「すぐ作れ」ではなく、Pain Market Signal図を育てて、未来線と参入余地を見たい。
```

## 10. Core Object

MVPの主役は **Pain Record** と **Pain Timing Map**。

### Pain Record

```text
Pain ID
Pain Name
Raw Pain
Source
Evidence
Observed User
Audience
Skill Level
Primary Domain
Tags
Current Workaround
Timing Curve
Pain Market Signal
Market Size
Pain Intensity
Visible Population
Willingness to Pay
Unsolvedness
Growth Potential
LLM Absorption Risk
Existing Alternatives
Differentiation Need
User Fit
Avoidance Fit
Composable With
Immediate EV
Suggested Use
Confidence
Responsibility Boundary
Notes
```

### Pain Timing Map

```text
横軸: Now / 1M / 3M / 6M / 12M
縦軸: Pain Market Signal
表示: 痛みごとの成長カーブ
```

痛みは単一の点ではなく、

```text
兆候期
顕在化期
拡散期
飽和/吸収期
```

として扱う。

## 11. Pain Market Signal

Pain Market Signal は市場規模だけではない。

```text
Pain Market Signal =
痛みの強さ
× 顕在人数
× 支払い可能性
× 未解決度
× 拡大余地
× 利用者との適合
− LLM吸収リスク
− 競合/代替の強さ
− 利用者が避けたい領域との衝突
```

MVPでは厳密な数式ではなく、比較補助として使う。

評価項目：

```text
Pain Intensity
Visible Population
Market Size
Willingness to Pay
Unsolvedness
Growth Potential
Timing Advantage
User Fit
LLM Absorption Risk
Differentiation Need
Sales Friction
Build Burden
Avoidance Conflict
```

MVPでは各項目 1〜5 でよい。

ただし主役は精密スコアではなく、

```text
時間軸上の相対比較
```

である。

## 12. Labels

「GO / 作れ」は使いすぎない。

推奨ラベル：

```text
STRONG SIGNAL
EARLY SIGNAL
WATCH
NICHE SIGNAL
ABSORPTION RISK
DIFFERENTIATION REQUIRED
USER-FIT SIGNAL
LOW USER FIT
SELL-TEST CANDIDATE
NO BUILD SUGGESTION
COMBINE
```

固定ルール：

```text
ラベルは命令ではなく、素材分類である。
```

## 13. Do Not Do

```text
Do not make this a generic search tool.
Do not make this a Reddit scraping/API project first.
Do not make this a pain notebook.
Do not tell users what to build as a command.
Do not guarantee market outcomes.
Do not start from the Decision Owner's personal pain only.
Do not start from Decision-OS theory.
Do not treat future pain as current pain.
Do not use market size alone as a GO signal.
Do not ignore LLM absorption risk.
Do not ignore user fit.
Do not ignore what the user does not want to build.
Do not force pains into one genre calendar.
Do not display pains as single fixed points only.
Do not skip evidence.
Do not move to repo build before V13 capsule.
```

追加V13制約：

```text
Do not start implementation from this capsule.
Do not turn this capsule into a Codex build instruction.
Do not create a new repo without a separate New Repo GO.
Do not add automation, hooks, MCP, pluginization, scraping, or API collection.
Do not frame output as “what will sell.”
Do not remove the user as Decision Owner.
```

## 14. Missing Closure

現時点の Missing Closure はこれ。

```text
New repo scaffold location: UNKNOWN
Initial file structure: not yet approved
First example pain records: not yet created
First sample report format: not yet created
Pain Timing Map visualization format: not yet selected
Evidence collection method: manual-first, but exact source workflow not yet fixed
Public positioning: not yet approved
External posting: HOLD
```

これは blocking failure ではない。

理由：

```text
このカプセルの目的は実装ではなく、ビルド前の境界固定である。
```

## 15. Next Actor

```text
Next Actor: Decision Owner / AI
```

次に許可される行動は1つ。

```text
このV13 Build Capsuleを保存用カプセルとして整えるか、CodexにV13 repo内のlaunch_capsules相当へ記録させる。
```

まだ許可されない行動：

```text
新repo作成
実装
API設計
スクレイピング設計
外向き投稿
Build Command化
```

## 16. Next Allowed Action

次の最小アクション：

```text
Create a V13 capsule file for Pain Timing Map / Pain Signal Intelligence.
```

候補ファイル名：

```text
launch_capsules/pain_timing_map_build_capsule_v0_1.md
```

ただし、これは **V13 repoに保存する場合のみ**。

保存せずにこのチャット上の固定稿として扱う場合は、ここで一旦 PASS。

## 17. Recheck Conditions

以下のどれかが起きたら再評価する。

```text
新repoを作りたくなった
Codexに実装させたくなった
API / scraping / automation を入れたくなった
Pain Timing Map が “売れるもの推薦” に寄りそうになった
痛みノート化しそうになった
Entry Window Radar と境界が混ざりそうになった
Decision Owner個人の痛みだけに寄りすぎた
Decision-OS理論説明から始めそうになった
外向き投稿したくなった
```

## 18. Completion Line

```text
Pain Timing Map / Pain Signal Intelligence MVP v0.1 is fixed as an evidence-backed personal Pain Market Signal map. It collects unnamed real-world pains, places them on a Now / 1M / 3M / 6M / 12M time axis, and displays each pain as a growth curve rather than a single point. The purpose is not to tell the user what to build, but to help the user grow a personal future-pain map, combine ideas, and choose future lines with better timing. Build responsibility remains with the user. The next step is to pass this fixed MVP to V13 for capsule recording before any new repo build.
```

日本語：

```text
Pain Timing Map / Pain Signal Intelligence のMVP v0.1は、証拠付きの個人用 Pain Market Signal 図として固定された。世の中にまだ名前がついていない痛みを収集し、Now / 1M / 3M / 6M / 12M の時間軸に置き、各痛みを単一の点ではなく成長カーブとして表示する。目的は「これを作れ」と命令することではなく、利用者が自分専用の未来痛み地図を育て、アイディアを結合し、よりよいタイミングで未来線を選ぶための素材を出すこと。作る責任はユーザーに残る。次のステップは、この固定MVPをV13へ渡してカプセルとして保存することであり、新repoビルドはその後である。
```

## 19. Capsule Status

```text
MVP fixed draft: PASS
V13 Build Capsule: PASS
Repo build: HOLD
Codex implementation: HOLD
API route: HOLD
Scraping route: HOLD
Generic search tool: BLOCK
Pain notebook: BLOCK
Build Command: BLOCK
Evidence-backed Pain Signal Map: GO
Human keeps the Seat: TRUE
```

このカプセルの次は、**V13 repoに保存するなら launch capsuleとして記録**。

新repoビルドはまだしない。
