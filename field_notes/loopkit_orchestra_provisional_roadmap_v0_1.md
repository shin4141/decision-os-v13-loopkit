# LoopKit Orchestra — Provisional Roadmap v0.1

```text
Current Layer:
V13

Status:
PROVISIONAL / HOLD

Purpose:
今日見えた方向性を失わず、
本線を進めながら順番に再評価できるようにする

Not:
実装承認
公開主張
製品完成計画
```

## 1. Core Hypothesis

最上位モデルへ作業全体を丸投げするのではなく、

- 実行AgentがRepositoryを観測する
- 上位モデルが設計する
- 実行Agentが実装する
- 独立した上位モデルが完了を監査する
- 発見をGuard・test・ruleへ固定する

ことで、上位知能の一回限りの発見を、下位システムの反復可能な
能力へ変換する。

## 2. Two Surfaces

### Acceleration Surface

```text
Guided Intake
→ Repository Scout
→ Pro Design
→ Builder Execution
```

目的：

- 丸投げより良い設計
- 不要な実装の削減
- 修正ループの削減
- 上位知能による設計品質向上

### Control Surface

```text
Builder Completion
→ Pro Audit
→ Repair / PASS
→ Guard・test化
```

目的：

- 偽完了
- 自己監査の盲点
- silent drift
- false complexity
- 根拠のない完了自己申告

を発見し、次回から自動で防ぐ。

## 3. Intended Compound Loop

```text
上位知能が新構造を発見
→ 下位Agentが実装
→ 独立監査
→ Guard・test・ruleへ固定
→ 次回は安く既知問題として処理
→ さらに上の未知構造を探索
```

目標は、毎回上位モデルを使うことではない。

> 上位モデルから出る構造差分が枯れるまで抽出し、
> その後は下位システムだけでも得をする状態を作る。

## 4. Provisional Stages

### Stage 1 — Pro Manual Protocol

- SOL / coding agentがEvidence Packetを作る
- Proが設計する
- coding agentが実装する
- Proが独立監査する
- Reusable Deltaを固定する

目的：

二件目以降でも新構造または設計品質向上が出るか確認する。

### Stage 2 — Companion Manual Bridge

- Copy for Pro
- Paste Pro Design
- Paste Pro Audit
- hash・model・role・timeの固定
- execution handoff生成
- finding / cost / reusable deltaのReceipt

目的：

Shinの手動転送と再説明を減らす。

### Stage 3 — Guided Intake

曖昧な依頼を、

- Objective
- Completion Line
- Do Not Touch
- UNKNOWN
- Evidence Needed

へ変換する。

目的：

高度な企画能力を持たない利用者でも、丸投げより良い開始状態を
作る。

### Stage 4 — Multi-Agent Roles

モデル名ではなく役割として扱う。

- Scout
- Architect
- Builder
- Auditor
- Repair Executor

候補：

- Codex
- Claude Code
- Grok系Agent
- GPT上位モデル
- 将来の上位モデル

### Stage 5 — LoopKit Orchestra

知能、権限、情報境界、証拠、反証、責任移転をCompanionが管理する。

完全自動化は着火条件ではなく、反復と拡張のための後段。

## 5. Evidence Already Obtained

V13-SDFP-001で一度成立したこと：

- 上位側だけがMI-09を事前発見
- 完了文書と実Git状態の不一致を特定
- 独立評価でfalse complexityも発見
- 修復設計へ変換
- coding agentが実装
- Guardとtestsへ固定
- mainへmerge
- 次回以降は下位系でも再利用可能

Repository evidence:
[V13-SDFP-001 Final Closure Record](../validation/v13_sdfp_001_final_closure.md)

## 6. Unknowns

- 毎回新構造が出るか
- Pro設計がSOL設計より継続的に良いか
- Reliable Completion Costが下がるか
- token総量が本当に減るか
- 丸投げ利用者にも効果があるか
- 第三者が継続利用するか
- 外部で発見事例が話題になるか

## 7. Re-evaluation Conditions

次のいずれかで再評価する。

- 別の実タスクでRun 002を行った
- 上位モデルだけの新構造が再び出た
- 新構造は出ないが実装修正・token・人間負荷が減った
- Manual Bridgeの摩擦が繰り返し発生した
- 丸投げ利用者向けGuided Intakeを試せる対象が得られた
- モデル更新により新しいCapability Deltaが期待できる

## 8. Current Gate

```text
HOLD — ROADMAP PRESERVED / NO IMPLEMENTATION AUTHORITY
```

## 9. Next Authorized Action

現在の本線を進める。

次の高レバレッジな実タスクが自然に現れた時だけ、Pro Manual Run
002候補として評価する。

## 10. Completion Line

方向性、順序、既知証拠、UNKNOWN、再評価条件が保存され、現在の
本線へ戻れること。
