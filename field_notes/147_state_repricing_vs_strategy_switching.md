# Field Note 147 — State Repricing vs. Strategy Switching

As-of: 2026-10-13 JST

Status: Verification pending — Forward-only research candidate; prior未採用

Primary layer: V13（V9との接続を含む）

Decision Owner: Shin

Execution Owner: Codex

Evidence class: Owner-provided conceptual example / research hypothesis;
実際の故障・修理・比較実験の証拠ではない

Current Gate: 研究仮説の保存 GO / Canon採用 HOLD

## Purpose and preservation boundary

初期判断の正当性を守りながら、実行途中の状態変化によって戦略を変更すべきかを
判断する際の失敗条件を、次のAIが検証できる状態にする。新理論の成立を宣言しない。

正準保存先は `shin4141/decision-os-v13-loopkit` の `field_notes/`。
保存前に取得した `origin/main` は
`1189d2c070d94ee8f8645a56c27151f063061e3f`。
同As-ofの既存記録へ、Forward-onlyの研究候補として本Noteを追加する。
同名の記録は対象のField Notes・docs内で確認されなかったが、概念上の独立性は未確認。
既存の重複候補は下記に残す。

今回の承認は、この研究候補と既存索引への最小リンクの保存、commit、同一remoteへの
push、remote全文read-back、cleanup・writer解放まで。検証実験の開始、次のループ、
Canon採用、公開論文・README・固定Canon・Value-Locked Pattern Memoryの変更は含まない。
本Noteは既存のoperational Current Gate、実行権限、runtimeを変更しない。

## Central hypothesis

> 初期判断が正しかったこと、途中で優劣が逆転したこと、最終結果が再び逆転したことは、
> 矛盾せず同時に成立する。
>
> 現在の状態評価を更新することと、既存戦略を放棄して別戦略へ切り替えることは、
> 異なる判断である。

ここでいう「初期判断が正しかった」は、当時利用可能だった証拠・条件・目的・権限に
照らした評価である。最終結果による正当化ではない。初期判断自体の不備が後で判明する
可能性も排除しない。その場合は旧As-ofを残したForward-onlyの訂正として記録する。

## Origin: AA vs. 66

| 時点 | 説明用の状態 |
| --- | --- |
| Preflop | AAが有利 |
| Flop | 66がセットを完成させ優位になる |
| Turn | AAに逆転可能性があるが、なお66が有利 |
| River | AAが逆転勝利 |

これは区別を説明する概念例であり、具体的なboard、ベット履歴、観測ログ、勝率数値は
提供されていない。実際のポーカーで相手の手札が常に観測できることを前提にしない。
AA/66の優劣を記述しただけで、個別のベット・コール・フォールドのEVや判断の正当性が
決まるわけではない。ポット、相手のrange、費用、情報、可能な行動などが別に必要になる。
Riverの結果を、Preflop・Flop・Turnで既に観測できた情報として扱わない。

## A. State Repricing

新しい証拠によって、現在の確率、不確実性、損失、選択肢、実行条件を更新する。

- 当時の証拠と、今回新しく得た証拠をAs-ofごとに区別する。
- 現在の状態評価が変わっても、過去の判断根拠を後知恵で書き換えない。
- 部分的な回復と、重大なリスクの解消を区別する。
- 観測できない状態を既知として埋めない。

State Repricingの出力は現在の評価であり、戦略変更や追加実行の承認ではない。

## B. Strategy Switching

既存戦略を維持するか、変更するかを判断する。現在の優劣だけから切替を決めず、
同じ現在As-ofから、継続・変更それぞれの将来を比較する。

| 比較軸 | 区別するもの |
| --- | --- |
| 初期計画 | 当初想定した状態変化か、方策の前提を壊す新しい状態か |
| 残存価値 | 継続で得られる将来価値と、失われた価値 |
| 切替 | 切替費用、移行中の損失、移行リスク |
| 既存成果物 | 今後再利用できる資産と、既に支払って回収不能な費用 |
| 追加損失 | 継続・変更それぞれで、今から追加で負う損失 |
| 権限 | 継続・変更それぞれの現在の実行権限 |

埋没費用を回収したいという理由だけで継続を正当化しない。一方、既存成果物が将来
再利用できるという証拠まで、埋没費用と同一視して捨てない。
一時的な優劣逆転だけで既存計画を放棄することも正当化されない。
評価不足なら切替の合理性は未確認として残し、適用可能な既存V13 Gateで扱う。

## C. Conditional Policy vs. Fresh Decision

将来の不利な状態を想定していたことと、その状態での追加実行まで承認していたことは別。

確認するのは、初期方策が今回の条件、行動種別、範囲、量、停止条件をカバーしているか、
その承認が現在も有効かである。

- 一致している場合：既に承認された条件付き方策の実行として扱えるかを確認する。
- 一致しない、または未確認の場合：新しい意思決定と、必要な承認の有無を独立に判断する。

Fresh Decisionであることから、毎回Shinへの質問が必要とは推定しない。現在の承認内の
技術判断・証拠整理はCodexが担う。価値、リスク受容、外部化、新しい権限などの実質的な
Human Seat判断が残る場合に、Decision OwnerであるShinへ戻す。

## D. Repricing vs. Reauthorization

現在の期待価値が改善しても、失効・撤回された実行承認は復活しない。
評価更新と実行権限の確認を独立させる。

過去のGO、過去の承認、現在の好結果、記録の存在は、それだけでは現在の実行権限を
生成しない。条件付き方策の適用可能性が確認されても、権限の有効性は別途確認する。

## Relation to existing layers and known overlap

今回読んだのはV13内の既存記録・bindingである。以下の「既知」はその記録で確認できた
範囲を指す。公開論文の原文を今回再取得・照合したという意味ではない。

| 既存の正準記録・候補 | 確認できた重複・関係 | 今回未確認の部分 |
| --- | --- | --- |
| [AGENTS.md §§1–3, 7](../AGENTS.md) / [FN125 current card](../docs/rule_practice/fn125.md) | 現在の証拠・scope・権限が必要。過去の承認、完了、通過したtest、Field Noteは新しい実行権限を生まない。PASSとGOも別 | A–Dの全体が既存運用で十分に表現されるか |
| [V9.1 binding — Entry 004](../docs/decision_lineage_reconnection_register_v0_1.md#entry-004--v91-condition-bound-judgment-reuse) | As-of、責任、証拠を保持し、条件失効は現在の再利用可能性を変える。過去判断を遡及的に誤りにせず、新権限も生まない。A/C/Dとの強い重複 | V9・V9.1原文と後続deltaの再照合、既存bindingでは防げない反例 |
| [FN087 — Rechallenge Gate](087_rechallenge_gate.md) | 条件変化、現在の総EV、費用、下振れ、学習価値、埋没費用による継続の否定 | 失敗後の再挑戦と、実行途中の維持・切替が同じ規則で扱えるか。Field NoteをCanonとは扱わない |
| [FN141 — Retry Escalation Without Recompute](141_retry_escalation_without_recompute.md) | 失敗をmethodの証拠として再計算し、因果・method差分なしの圧力増加を区別。最終成功までの経路も保持 | 想定済みの一時的不利で適切な継続まで止めないか。候補Gateの増分効果 |
| [FN144 — Memory-Authority Separation](144_memory_authority_separation.md) | Record / Validity / Authorityを分離。新証拠はreviewを促すが、Human Gateの失効・撤回をAIが解除できない | Dが説明例だけで足りるか。FN144もVerification pending |
| [Progress Preservation Check / Opportunity-Loss Boundary](../docs/progress_preservation_principle_v0_1.md#progress-preservation-check) | 停止の機会損失、最小制約、再評価条件を扱い、能力向上から自動的に拡張しない | Bの残存価値、再利用、切替費用、双方の追加損失を十分に比較できるか |
| [Bounded Operational Authority Window — Authority Exhaustion](../docs/bounded_operational_authority_window_v0_1.md#authority-exhaustion) | 枯渇した権限は再承認なしに延長できない。Dに関する既存の具体例 | stale approvalの全条件を覆うか。歴史的windowを今回の権限として継承しない |
| [Time-Tube関連FN134](134_hidden_variable_timetube_trajectory.md) / [PIC・V8 source register](../docs/decision_lineage_reconnection_register_v0_1.md#verified-source-authority-for-pic) | 点だけでなく軌道・driftを保存し、V9 As-of replayで後知恵を区別。PICの非破壊的保存と現在の条件妥当性は別 | Time-Tube / PIC原文に同等の方策・切替規則があるか。FN134の実験結果は今回の実証ではない |
| EBG | stale approval・外部操作の実行境界を後続照合する対象 | 今回EBGのsource・runtime・testsは未読。同等規則の有無・実装効果ともUNKNOWN |
| Value-Locked | 実際の故障、修理、再検証による再利用知識とは証拠classを分ける | Pattern Memoryへの追加資格は未成立。今回読込・変更・追加しない |

A/C/Dには既知の重複がある。Bを含む一体の整理に独立した増分価値があるかはUNKNOWN。
タイトル一致がないことを、新規性や既存Canonの不足の証拠にしない。

## Candidate failure patterns

以下は説明用の仮称であり、独立した故障類型としては未検証。

| 仮称 | 失敗条件 | 後続検証で区別する正常ケース |
| --- | --- | --- |
| AA記憶バグ | 初期の高評価を理由に、新しい重大な証拠を無視して継続する | 現在の証拠を更新したうえで、残存価値と有効な方策から継続する |
| ターン希望バグ | 部分的な改善だけでリスク解消や戦略変更の合理性を認定する | 回復の範囲と未解決リスクを残し、継続・変更の将来を比較する |
| リバー正当化バグ | 最終成功を理由に、途中の不適切な判断を正当化する | 各As-ofの証拠と権限に照らして経路を評価する |
| 過剰ピボットバグ | 一時的な優劣逆転だけで計画を放棄し、切替費用と残存価値を無視する | 初期方策の範囲と今からの費用・損失を比較して維持・変更する |

## Next research Gate and actors

Canon採用はHOLD。以下は次回の検証課題であり、今回その研究ループを開始しない。
再開には対象source、scope、証拠、終了条件、実行権限を結び付けた別のbounded taskが必要。

| Gate | Codexが後続検証で残す証拠 | 現在の未完部分 / 判断先 |
| --- | --- | --- |
| R1 — 同等規則 | V9、V13、Time-Tube、PIC、EBGの固定source / As-of / 具体的section / 後続deltaとA–Dの対照表 | 一部V13記録の重複確認のみ。原文・EBG照合は未完 |
| R2 — 反例 | 既存の状態更新・条件付き方策・承認再検証を適用しても防げない具体的case。どのjointが不足するか | 反例未提示。既存概念で防げる場合は独立Canon候補を取り下げる |
| R3 — 再現 | 同一初期状態・同一証拠・同一権限の未修正／修正後比較で、行動結果が変わるtest設計 | 設計・実行とも未完。実際の故障・修理証拠と合成testを分ける |
| R4 — 副作用 | 状態更新頻度、実行コスト、不要な切替、判断遅延、誤検知、適切な継続を止める率 | 未測定。検証前に観測項目と停止条件を固定する |
| R5 — 主体分離 | 検知主体、Gate判断主体、最終Decision Owner、実行主体と各権限の対応 | 検知担当はcaseごとに指定。Codexが証拠整理・bounded Gate提案、Shinが最終Decision Owner |

R3の設計候補は、一時的不利でも継続が適切なcase、重大な証拠で変更が必要なcase、
部分改善でもリスクが残るcase、最終成功でも途中判断に不備があるcase、有利に戻っても
承認失効で実行できないcaseを対にする。正答の行動・費用・権限を先に固定し、後から
成功した結果に合わせて判定を変えない。これは設計候補であり、再現test実施済みではない。

同等規則への重複が確認された場合、新Canonを追加せず、既存概念の説明例・回帰testへ
回収する。本Noteのorigin・As-of・仮説・反証結果は残し、対応先と判定をForward-onlyで
追記する。Canon採用が提案される場合も、既存の[Concept Promotion Gateとlifecycle](../docs/field_note_lifecycle.md)
に従い、根拠、反証条件、downgrade条件と必要なShinの判断を別に記録する。

## Reconnection, Completion Line, and Missing Closure

既存のREADME / AGENTSのAI Reading Order入口から、
[条件付き研究索引の追記](../docs/ai_reading_order.md#forward-only-research-reconnection--2026-10-13)
を経由して本Noteへ戻る。全Field Noteの読込やoperational restart pointの変更は不要。

今回の保存作業のCompletion Lineは、研究候補・既知の重複・未確認部分・次のGateと主体を
保存し、既存入口からのforward linkを確認し、commit・push後の固定remote commitから
変更2ファイルの全文を読み戻してlocal bytesと照合し、cleanup・writer解放を終えること。
取得したcommit、照合結果、最終clean状態は実行完了報告で示す。

Missing Closureを分離する：保存作業は上記read-backとcleanupで閉じる。研究としては
R1の残部・R2–R5、独立した増分価値、行動改善と副作用の実証が未完。保存の完了は
Canon採用、検証開始、実装権限、次のGOを意味しない。

禁止境界：V13 Canonへの即時採用、新しいV15等への拡張、未検証のValue Pattern Memory追加、
公開論文・README・固定Canonの変更、SNS等への外部投稿・送信、新規課金、大規模実装実験、
routine cleanupのShinへの返却。研究候補として保存・再接続可能な状態で停止する。
