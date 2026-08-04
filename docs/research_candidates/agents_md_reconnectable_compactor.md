# V11 / V13 保存候補 — AGENTS.md Reconnectable Compactor

## 位置づけ

**Primary Layer：V11 — Reconnectable Forgetting**  
**Execution Layer：V13 — Loop Gate / Agent Routing**

長大化した`AGENTS.md`を単純に要約・削除するのではなく、

> 常時必要な指示だけを残し、条件付き・専門領域・過去経緯を別Markdownへ退避し、必要な時だけAIが再接続できる構造へ変換する

ためのツール候補。

仮称：

**AGENTS.md Reconnectable Compactor**

## Problem

`AGENTS.md`は、運用を続けるほど次の内容が蓄積する。

- 常時守るべき固定ルール
- 特定タスクだけに必要な指示
- テスト、Release、Security、Handoffなどの専門ルール
- 過去事故から追加された再発防止
- 背景説明や判断理由
- 重複した指示
- 現在は古い可能性がある指示

これらを一つのファイルへ残し続けると、

- 毎回不要なContextまで読み込む
- 重要指示が埋もれる
- 指示同士が競合する
- 探索範囲が無駄に広がる
- Agentの判断が硬直する
- 古い運用ルールが常時命令として残る

という問題が起きる。

一方、単純に短縮・削除すると、

- なぜそのルールがあったか
- どの条件で必要になるか
- 何を防ぐためのものか
- 元の完全な指示は何だったか

が失われる。

したがって必要なのは、単なる圧縮ではなく、

**必要時に元の知識へ戻れる軽量化**

である。

## Core Function

ユーザーが既存の`AGENTS.md`を入力すると、AIが内容を自動分類する。

```text
KEEP_ALWAYS
ROUTE_ON_CONDITION
MOVE_TO_REFERENCE
DUPLICATE
STALE_CANDIDATE
HUMAN_REVIEW_REQUIRED
```

### KEEP_ALWAYS

すべての実行で常に必要な、短く重要な固定ルール。

例：

- protected branchへ直接pushしない
- secretsをcommitしない
- testsを通さず完了宣言しない

### ROUTE_ON_CONDITION

特定の問題や作業条件が発生した場合だけ読むルール。

例：

- Completion / handoff / restart
- Release / publication
- Security / permissions
- Migration
- Incident recovery

### MOVE_TO_REFERENCE

背景、詳細手順、長い説明、過去経緯など、常時Contextには不要だが保持すべき内容。

### DUPLICATE

意味が重複している指示候補。

自動削除はせず、統合候補として提示する。

### STALE_CANDIDATE

現在のRepository状態と合わない可能性がある指示。

自動削除せず、再確認対象として分離する。

### HUMAN_REVIEW_REQUIRED

意味、責任、権限、公開境界など、人間の判断なしに移動・短縮できないもの。

## Expected Output Structure

例：

```text
AGENTS.md

docs/agent-guides/
├── testing.md
├── release.md
├── security.md
├── handoff.md
├── incident-recovery.md
├── architecture.md
└── decision-os-router.md
```

軽量化後の`AGENTS.md`には、常時ルールと検索ルーターだけを残す。

例：

```markdown
## Always Required

- Do not modify protected branches directly.
- Do not claim completion without attached test evidence.
- Preserve the human Decision Owner's final approval boundary.

## Conditional Guidance

When the task involves test failure or completion uncertainty:
- Read `docs/agent-guides/testing.md`

When the task involves release or public claims:
- Read `docs/agent-guides/release.md`

When the task involves handoff, restart, or ownership transfer:
- Read `docs/agent-guides/handoff.md`

When the task involves permissions or external access:
- Read `docs/agent-guides/security.md`
```

## Reconnection Metadata

別ファイルへ移動した各ルールには、最低限次を保持する。

```text
Original Text
Original Location
Classification
Move Reason
Recall Condition
Source Hash
Last Reviewed As-of
Related Failure / Evidence
```

これにより、

- 何が移動されたか
- なぜ常時Contextから外したか
- いつ再読すべきか
- 元の指示が改変されていないか

を追跡できる。

## V11 Meaning

これは「不要な指示を忘れる」ツールではない。

V11的には、

> 常時記憶から外しても、必要な時に理由・条件・原文へ再接続できる忘却

を実装する。

```text
Long AGENTS.md
→ Classification
→ Conditional externalization
→ Lightweight active memory
→ Recall trigger
→ Reconnection to full context
```

削除によって軽くするのではなく、**記憶階層を分けて軽くする**。

## V13 Meaning

V13側では、現在のタスクに必要なレンズだけをAgentへ通す。

```text
Current Task
→ Detect task condition
→ Route to relevant guide
→ Reinterpret current design
→ Continue / HOLD / CAP / BLOCK
```

これにより、すべてのルールを毎回読み込ませず、

> 必要な問題が発生した時だけ、必要な統治レイヤーを起動する

ことができる。

Decision-OSとの接続例：

```text
As-of / Release / Seat → V9 guide
Carrier survival / rescale → V10 guide
Compression / causal reconnection → V11 guide
Completion / handoff / restart → V12 guide
Repeated loop / authority consumption → V13 guide
```

## Difference from Ordinary Summarization

通常の要約ツール：

```text
Long text → Short text
```

本候補：

```text
Long operational instruction
→ Persistent core rules
+ Conditional routes
+ Searchable reference files
+ Reconnection metadata
+ Review candidates
```

目的は文字数削減そのものではない。

**Agentが毎回読む必要のない知識を外へ逃がしながら、必要時に正しく呼び戻せること**

が目的。

## User Value

外向きの簡易説明：

> **増え続けるAGENTS.mdを、常時必要な指示だけに軽量化。残りは消さず、必要な時だけAIが再接続できるMarkdownへ自動整理する。**

英語候補：

> **Your AGENTS.md keeps growing. This tool keeps only what every run needs, moves the rest into searchable guides, and preserves exactly when each rule should be recalled.**

想定価値：

- Context使用量の削減
- 重要指示の可視性向上
- 指示競合の減少
- 古いルールの発見
- Agent探索コストの低減
- Framework Lensの必要時起動
- 過去事故由来ルールの再利用
- 複数Agent間の共通運用基盤

## Safety Boundary

自動処理で行ってよいこと：

- 分類案の生成
- 移動先Markdown案の生成
- 重複候補の提示
- Recall Conditionの提案
- 軽量化後のdiff生成

自動処理で行ってはいけないこと：

- 意味が曖昧な指示の削除
- 権限・責任・公開境界の勝手な変更
- `STALE_CANDIDATE`の自動廃棄
- 元の指示より強い命令への書き換え
- Decision Ownerの承認なしの適用

## Current Gate

```text
Status: PRESERVED PRODUCT / RESEARCH CANDIDATE
Primary Layer: V11
Execution Layer: V13
Current Gate: HOLD — SAVED ONLY / NO IMPLEMENTATION AUTHORITY
Completion Line: 本線に候補として保存され、
現在進行中のStage 2を横切らないこと
Missing Closure: なし
Next Action Owner: AI — 本線記録のみ
Shinへ返してはいけない後始末: 現時点ではなし
```
