# Companion Product Roadmap v0.2

```text
Current Layers:
V9 Product UX / V10 Cost Boundary / V11 Reconnectable Memory / V13 Challenge Routing

Status:
PROVISIONAL / HOLD

Purpose:
Companionの短い入力、安全な実行、待機可視化、結果確認、再利用、異モデル反証を、
局所機能ではなく一つの製品導線として保存する。

Not:
実装承認
merge承認
release承認
外部採用主張
```

## 1. Historical As-of

この文書は、既存の
`field_notes/loopkit_orchestra_provisional_roadmap_v0_1.md`
を上書きしない。

旧版は、次のV13多モデル構造を保存した歴史的As-ofである。

```text
Repository observation
→ Pro design
→ Builder execution
→ independent Pro audit
→ Guard / test / rule fixation
```

v0.2は、その系譜をCompanionの実用UX、Field Notes Lite、待機可視化、
結果確認、コスト可視化、異モデル反証へForward-onlyに接続する。

## 2. Product Direction

Companionの基本価値は、ユーザーに長い運用説明や完成済みプロンプトを
書かせることではない。

```text
短い目的入力
→ bounded AI execution
→ wait-state visibility
→ human Approval
→ merge前に確認可能な成果物
→ reusable structure capture
→ automatic reconnection
→ 必要な場合だけ異モデル反証
```

毎回モデル呼び出しや説明文を増やすのではなく、短い入力と少ない出力のまま、
安全境界、再開可能性、再利用可能性を提供する。

## 3. Proven Baseline

creator環境では、次のbounded live flowが成立している。

```text
複数repository fileの読取り
→ Codexによる中規模作業
→ exact one-time Approval
→ 指定された1ファイルだけ作成
→ normal terminal completion
```

確立済み:

- creator self-use proof
- multiple repository reads
- one bounded file write
- one-time human Approval
- normal terminal completion

未確立:

- 第三者利用
- 大規模タスク性能
- 外部採用
- lower-model equivalence
- successful intelligence transplant

## 4. Track A — Field Notes Lite

### A1. Capture

成功Runの同じactive Codex Runが、side-effect-free typed tool
`propose_field_note_candidate`を最大1回だけ使って再利用候補を提案する。

```text
successful Run
→ ♻️ candidate 最大1件
→ save / skip
→ exact one-file Approval
→ .decision-os/field-notes/ に1ファイル保存
```

固定境界:

- candidate extraction用の追加model callなし
- free-form final response parsingなし
- failed / needs-attention / interruptedでは候補破棄
- candidateがなければ成功Runでも0件
- Level 3 → Level 2 → Level 1の順でproposal候補を縮約

### A2. Reconnect

後続Runでは、ユーザーにMarkdownの探索・分類・比較・選択を要求しない。

```text
bounded metadata scan
→ relevance最大の1件を選択
→ full Noteをcontrol contextへ注入
```

固定境界:

- relevanceをvalue levelより先に評価
- full-read / injectionは最大1件
- ordinary four-distinct-path read budgetを消費しない
- no matchまたはschema failureなら注入0件

### A3. Maturity

```text
CANDIDATE
→ REUSED
→ PROMOTABLE
```

保存、選択、注入だけでは再利用成功を主張しない。

## 5. Track B — Short Task Entry

通常は、ユーザーの短い入力をそのままRunへ渡す。

例:

```text
この2資料から実装設計を作って
```

Companionは追加model callなしで、既知の共通境界だけを決定論的に付加する。

- repository identity
- bounded Approval
- unauthorized commit / push禁止
- scope外変更のfail closed
- Run identity

AI Task Draftは標準にしない。

```text
[そのまま実行]
[AIでタスクを整える]
```

曖昧、高Impact、複雑な作業でだけ任意選択できる将来機能として扱う。

## 6. Track C — Run Awareness

第三者利用では、静かな待機画面だけでは、停止、遅延、進捗、終了時期を判別しにくい。

最低限表示する。

```text
Current stage
Elapsed time
Last activity
Repository reads used
What happens next
```

例:

```text
Reading repository files
Elapsed: 04:18
Last activity: 9 seconds ago
Reads: 3 / 4
Next: Approval may be requested
```

初期には出さない:

- 根拠のないETA
- 常時流れる長い思考実況
- unsupportedな残り時間予測

目的は、思考全文を見せることではなく、現在も動いており、どのbounded stageにいるかを示すこと。

## 7. Track D — Cost Visibility

静かな実行を「何もしていない」と誤認させず、実測可能なコストを表示する。

表示候補:

```text
Elapsed time
User input characters
Visible output characters
Repository paths read
Files changed
Actual token usage when available
```

actual token usageが取得不能なら`UNKNOWN`とする。

削減量を表示する場合は、比較基準を明示する。

```text
Estimated tokens avoided: 約620
Baseline: manual task template
```

比較対象がなければ、token savingsを断定しない。

## 8. Track E — Result Review Before Merge

merge前でもローカル成果物は確認可能である。

必要な導線:

```text
[Open result]
[Show exact diff]
[Prepare PR]
```

現在の弱さは、成果物が存在しないことではなく、Companionにローカル成果物へ
ワンクリックで到達する導線がないこと。

確認は毎回強制しない。

Low Impact:

```text
Recommended:
Prepare PR

[Open result]
[Prepare PR]
```

High Impact:

```text
Recommended:
Review before PR preparation

Reason:
This file controls future automated behavior.

[Review]
[Proceed without review]
```

AIは推奨を提示するが、最終Seatは人間が保持する。

## 9. Track F — Cross-Model Challenge

異モデル反証は全Runへ付けない。

```text
Level 1:
原則不要

Level 2:
高Impact時のみ候補

Level 3:
異モデルChallenge対象
```

役割:

- source model固有の思い込みを壊す
- 適用範囲の過剰拡張を検出する
- lower-cost modelが実行可能な形か確認する
- Evidenceを超えたclaimを防ぐ

未固定:

- 保存前に必須とするか
- lower-model再利用前に行うか
- maturity promotion前に行うか

v0.1実証結果を見て固定する。

## 10. Recommended Implementation Order

```text
1. Field Notes Lite Design fixation
2. A1 Capture
3. A2 Reconnect
4. Run Awareness: elapsed time / last activity
5. Result Review: Open result / exact diff
6. Cost Visibility: measured values only
7. Optional AI Task Draft
8. Level 3 Cross-Model Challenge
9. lower-model real reuse and independent verification
```

Field Notesの保存だけでReconnectがない状態を製品完成とは扱わない。

## 11. Third-Party Trial Minimum Line

```text
短いTask入力
＋経過時間
＋bounded Approval
＋merge前の結果確認
＋Field Note Capture / Reconnect
```

OS通知、AI Task Draft、異モデルChallengeは、この最小線の後段でよい。

## 12. Early Non-Goals

- 毎回のAI Task Draft
- 毎回の異モデル反証
- 信頼できないETA
- 常時model実況
- Field Notes management screen
- automatic AGENTS.md promotion
- complex Ledger
- external adoption claim
- successful transplant claim
- ユーザーによるMarkdown管理

## 13. Re-evaluation Conditions

次のいずれかでロードマップ順序を再評価する。

- Field Notes Captureが実Runで成功した
- Field Notes Reconnectが別Runで実際に使われた
- 第三者が待機時間または停止不明を摩擦として報告した
- merge前確認導線の不在が誤変更または不信につながった
- actual token usageが安定取得可能になった
- Level 3候補が生成された
- lower-cost model reuse taskが実行可能になった
- 異モデルChallengeが保存前、再利用前、promotion前のどこで最も高い価値を持つか観測できた

## 14. Current Gate

```text
Roadmap:
PRESERVED / HOLD

Field Notes Lite Design:
CONTENT PASS / PR #65 DRAFT

Implementation:
NOT AUTHORIZED BY THIS DOCUMENT

Merge / Install / Release / Publication:
NOT AUTHORIZED
```

## 15. Completion Line

第三者が短い目的だけを入力し、現在の経過時間とlast activityを確認しながら
bounded Runを待ち、Approval後の成果物をmerge前に開ける。

成功Runから再利用候補を最大1件保存でき、次の関連RunではCompanionが
自動で最大1件を再接続する。

追加のAI Task Draftや異モデル反証は必要な場面だけ選択され、費用、文字数、
待機負担、人間の確認負担を常時増やさない。
