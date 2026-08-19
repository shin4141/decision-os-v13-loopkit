# External Intelligence Onboarding

このページは、自分のAIにどんな外部知能を持たせられるかを見るための
public showroomです。見るだけならFork、clone、Codex projectへの追加は
必要ありません。V13全体を学ぶための必修カリキュラムでもありません。

first contactは処方ではなくshowroomです。最初に何ができるかを見せ、
ユーザーが選ぶまで開始構造を決めません。

```text
Read the repository first. Show the map. Deep-read after selection.
```

## 日本語first-contact — External Intelligence Quest Board

日本語でExternal Intelligenceのtutorialや始め方を求められたら、まず同じ
public repositoryにある次の最小surfaceを実際に確認します。

- `README.md`
- `AGENTS.md`
- `docs/external_intelligence_onboarding.md`
- `docs/ai_reading_order.md`
- `docs/field_note_lifecycle.md`

その証拠だけを使い、External Intelligenceがこのrepositoryで何を意味し、実際に
どのsurfaceで支えられているかを短く説明します。次に、長い監査報告ではなく、
access boundaryを最大数行で示します。

```text
確認できたもの:
README / AGENTS / onboarding / reading order / Field Note lifecycle / <others actually inspected>

現在確認できないもの:
<あれば。なければ「上記first-contact範囲ではなし」>

したがって、この案内では
<supported boundary>までrepository根拠で説明できます。
```

アクセス不足を能力不足のように装いません。取得できなかったfile、privateまたは
separate artifact、未確認の実装は、推測で補いません。この短いorientationと
disclosureの後、質問やおすすめを先に出さず、次のparticipant-facing画面を
全文表示します。
`MEMORY / GROW / LIGHTEN / CONTINUE / PROTECT / CONNECT / GRADUATE`、
`Little OSI`、`Little Compactor`、Multi-AI Note候補、自由選択例を省略した
短い要約へ置き換えません。項目名は固定された導入順ではなく、選べる入口です。

---

# 🧠 External Intelligence

## 自分専用の外部知能を育てる

このrepositoryのV13 LoopKitは、AIとの仕事で生まれた記憶・再開点・再利用できる
知識を外部に残し、現在の作業が終わった後に次の作業へ進むべきかを判断するための
運用OSです。

External Intelligenceは、AIそのものを自動学習させる仕組みではありません。

AIとの仕事や会話から生まれた、記憶、学び、失敗、判断理由、お金の基準、
優先順位、譲れない条件、再開点、再利用できる知識などをチャットの外へ
残し、ChatGPT・Claude・Codexなどが必要な時だけ使えるようにする仕組みです。

何を育てるかは人によって違って構いません。

### 🧠 MEMORY — 覚える

- **次のAIに続きを渡す** — Handoff / Task Memory
- **自分にとって大事なことを残す** — Personal Decision Memory
  - お金、時間、仕事、家族、優先順位、譲れない条件など
- **なぜそう判断したか残す** — Decision Context

### 🌱 GROW — 育てる

- **学びや失敗をNoteとして残す**
  - 最初から一般化されたRuleである必要はありません。
- **AIにNote候補を見つけてもらう**
  - ChatGPT / Claude / Codexが「External Intelligence候補があります」と
    知らせます。
- **繰り返し現れた知識を育てる**
  - Observation → Reusable Intelligence → Promotion Candidate
  - 一度の観測を勝手に恒久Ruleにはしません。

### 🪶 LIGHTEN — 軽くする

- **必要な過去だけ読む** — Selective Recall
- **長くなったAI指示を軽くする** — Little Compactor
  - 毎回読む必要のない知識を外へ逃がし、`AGENTS.md`などを巨大な
    知識庫にしません。
- **古い情報を毎回全部読ませない**
  - 必要な時だけ接続します。

### 🔁 CONTINUE — 続ける・再開する

- **次のAIが迷わず再開できる最小情報を残す** — Little OSI
- **「終わったつもり」を防ぐ** — V12 Completion Integrity
- **次のloopを走らせるか決める** — V13 Loop Gate
  - V13 Loop Gateは、自動で作業を繰り返す機能ではありません。現在のtaskが
    終わった後、次の作業cycleを開始する正当性を`GO / HOLD / CAP / BLOCK`で
    判断する境界です。
  - `GO / HOLD / CAP / BLOCK`
  - 今の作業が終わっていても、次のloopを自動開始しません。

### 🛡️ PROTECT — 守る

- **高リスク時だけGateを強くする**
  - 公開、API、外部repository、資金、不可逆操作など
- **疲れている時はCarrierを守る**
  - 無理に全部進めず、restartableな状態を残します。
- **古い成功を現在の正解にしない** — Re-entry / Direction Re-evaluation

### 🔗 CONNECT — AIをつなぐ

- ChatGPTとCodexで同じExternal Intelligenceを使う
- Claudeも参加させる
- 複数AIからNote候補を集める

どのAIが発見しても、その人自身のExternal Intelligenceへ戻せます。

### 🎓 GRADUATE — Tutorialを卒業する

External Intelligenceの使い方が分かってきたら、Tutorialをどうするか自分で
選べます。

- **KEEP**
  - Tutorial入口をそのまま残します。
  - 「外部知能を教えて」と言えば、いつでもQuest Boardへ戻れます。
- **MANUAL**
  - 常時routerを外します。
  - Tutorial本体は残し、必要な時だけ自分で開きます。
- **REMOVE**
  - Tutorialの入口とTutorial用surfaceを自分のForkから外します。
  - 育てたmemory、notes、handoff、rulesなどのExternal Intelligence本体は
    削除しません。
- **NOT NOW**
  - 今は何も変えません。

Tutorialは補助輪であり、External Intelligence本体ではありません。

## 🎮 Choose Your Quest

気になるものを一つ選んでください。例えば、次のように自由に聞けます。

- 「全部ざっと見たい」
- 「これはもうやっている」
- 「自分なら何が合いそう？」
- 「Little OSIって何？」
- 「Little Compactorを見たい」
- 「お金の判断を覚えさせたい」
- 「ChatGPTとCodexをつなぎたい」
- 「チュートリアルを卒業したい」

見るだけでもOKです。選んでも自動導入されません。

---

ユーザーが選択するまでは、file変更、handoff作成、Note保存、Rule promotion、
setup、Fork、cloneを開始せず、特定Questを推薦しません。

## Quest選択後 — evidence first

Questが選ばれた後にだけ、そのQuestを支える実ファイル、rules、docs、関連する
Field Notes、公開実装を必要な範囲で追加確認します。onboarding本文だけを根拠に
説明せず、存在を確認したsurfaceと、そこから言える境界を先に揃えます。

```text
Broad map first. Deep evidence after selection.
```

repository state、onboarding transport metadata、fixed SHA、audit instructions、
既存のV13構造、repositoryの高度さは、現在のユーザーの能力、workflow、摩擦、
導入済み状態の証拠ではありません。

ユーザーが「これはもうやっている」と言い、何を指すかが会話から確定できない
場合は、deep readより先に、その対象だけを一問で確認します。「自分なら何が
合いそう？」と聞かれ、user-sideの既存運用や現在の摩擦がまだ分からない場合は、
recommendationより先に、結果を変える最小質問を一つだけ返します。user evidenceが
ないまま`CONTINUE`、handoff、その他のQuestを処方しません。

全Field Notesを先読みしません。Quest名やtutorial上の説明だけを根拠に、実装済み、
自動化済み、publicに利用可能と推測しません。例えば次のようにrouteします。

- `LIGHTEN`:
  `AGENTS.md`、`docs/ai_reading_order.md`、
  `docs/field_notes_lite_v0_1_design.md`、関連するselective-recall Field Notes、
  必要なら`decision_os/companion/field_notes_reconnect.py`や対応testを確認します。
  `Little Compactor`については
  `docs/research_candidates/agents_md_reconnectable_compactor.md`を確認し、
  research candidateと公開実装済み機能を混同しません。
- `CONTINUE`:
  `AGENTS.md`のV12 / V13 / handoff rules、`docs/handoff_command.md`、
  `docs/context_compression.md`、`field_notes/022_v12_to_v13_mapping.md`、
  `field_notes/099_handoff_responsibility_transfer.md`など、現在の質問に必要な
  rulesと例だけを確認します。
  `Little OSI`について聞かれた場合は、このrouteに加えて
  `docs/osi_parallel_compounding_lane_v0_1.md`を確認します。repository evidenceが
  明示しない限り、Little OSIがその別OSI surfaceと同一、簡易実装、または完全に
  無関係だと推測しません。

他のQuestも同じ原則で、まず実在する最小surfaceを特定し、そのQuestの説明に
必要な範囲だけ読みます。選択されたQuestと無関係なruntime、Canon、trajectory、
research frontierへ広げません。

## Availability boundary

Quest名が存在することは、完全なimplementationがpublic repositoryに含まれる
証拠ではありません。確認できるのが概念、boundary、research candidate、test、
または一部のpublic implementationだけなら、その粒度を維持します。

特に現在のpublic surfaceで`Little Compactor`として確認できるのは、Quest上の
entry conceptとreconnectable compactorのresearch-candidate文書です。別の実装本体
や非公開artifactの詳細は、このrepositoryから確認できたものとして説明しません。

確認できない時は、次のように明示します。

```text
このrepositoryから確認できるのは概念・boundary・evidenceのこの範囲です。
実装詳細はここからは確認できません。
```

Forkしても、public repositoryに存在しないprivate repository、separate unpublished
implementation、Shin固有のprivate memory、public `main`にないupstream internal
trajectoryが自動的に見えるようになるとは説明しません。

## 🔓 Full Experience — Forkして体感する

これはfirst responseやQuest選択直後の自動CTAではありません。public repositoryを
根拠にQuestの説明または小さなtrialを受けた後、ユーザーが自分用に育てたいと
興味を示した時にだけ、`🔓 Full Experience — Forkして体感する`の見出しを保って
次のsecondary CTAを提示できます。

ここまでは公開repositoryをAIに読ませたShowroomです。

自分のExternal Intelligenceとして実際に育ててみたくなったら、このrepositoryを
Fork / cloneしてCodexまたはClaude Codeでrepository rootを開いてください。
そうすると`AGENTS.md`、notes、handoff、docs等を実際のworkspaceとして使いながら、
自分のExternal Intelligenceを育てられます。

気に入らなければ採用を続ける必要はありません。Forkは理解するための前提ではなく、
体感して育てるための次段階です。得られるのはpublic repositoryに含まれるExternal
Intelligence surfaceと、その人がそこから育てる新しい状態です。

Fork後はrepository rootのtiny routerがこのページへ案内します。通常taskでは
tutorialを読み込みません。Fork、clone、setup、file変更はユーザーの明示した
次段階として扱い、CTAを見せたこと自体を実行authorityにしません。

## Graduationの境界

AIがユーザーの能力を推測して、自動的にTutorialを卒業、軽量化、削除しては
いけません。Graduationはユーザー自身の選択です。

`KEEP / MANUAL / REMOVE / NOT NOW`を提示し、`MANUAL`または`REMOVE`でfile変更が
必要な場合は、変更対象と残るsurfaceを短く示し、明示承認を得てから実行します。

Graduationで削除してよい対象は、ユーザーが承認したTutorial入口または
Tutorial専用surfaceだけです。memory、notes、handoff、reusable intelligence、
rules、V12/V13 operationをTutorialと一緒に削除してはいけません。

## 選択後の案内

Questが選ばれた後、Codexは試験のような質問を並べません。現在の会話と
repositoryから、次のうち判断に必要なことだけを確認します。

- 今解きたい摩擦や目的
- AI、repository、Git、Codexの現在の使い方
- すでにあるinstruction、memory、handoff
- 誰が変更やpromotionを決めるか

分かっていることは説明し直さず、分からない点だけ短く確認します。
相手を根拠なく「初心者」と呼びません。高い能力を大量の説明への同意と
みなしません。

ユーザーが「自分なら何が合いそう？」と聞いた場合も、Quest Boardを見せた
後の会話から既存運用、興味、理解、現在の摩擦を観測してから、初めて一つを
提案できます。

第三者のForkでは、そのForkのownerまたはmaintainerがDecision Ownerです。
upstream canonical repositoryにShinと書かれていることだけを理由に、
第三者のForkへ同じOwnerを継承しません。

最初の案内では、必須の5 surfaceでrepositoryのbroad mapを確認します。
`README.md`ではpublic purpose、External Intelligence入口、claimとForkの境界を
確認し、無関係な後続sectionを全て読み込む必要はありません。
upstreamの`docs/current_signal.md`、`handoff/current_codex_handoff.md`、
`docs/trajectory/V13_TRAJECTORY.md`、`validation/`は第三者Forkの現在状態では
ありません。upstream自体を再開・評価する依頼がある時だけ読みます。
ユーザーが具体例をすでに提示した場合は、別のexample fileを追加で読まず、
提示された一件をそのまま最小exerciseに使います。

ユーザーが選んだQuest、または選択後に依頼された提案から、現在役立つ構造を
原則一つだけ使います。例えば、次のどれか一つで十分です。

- 新しいsessionへ戻るためのhandoff
- 同じ失敗を繰り返さないための一件のfailure memory
- `AGENTS.md`を小さな常時indexに保つ分離
- task完了と次loopの許可を分けるV12/V13 Footer

ユーザーが選んだ一つを実際の小さな例で使い、restart pointを残したら、
初回onboardingは終了です。

この案内全体を一つのbounded taskとして扱います。途中の質問ごとに完全な
V12/V13 reportを付けず、一つの実使用とrestart pointが閉じた時、または
実際のblockerで終了する時に一度だけ報告します。

## Note Candidate Rule — Multi-AI

ChatGPT / Claude / Codexなどは、作業や相談の中で、未来のこのユーザーの
判断を変えそうな情報を見つけた場合、自然な区切りで最大1件だけ、次のように
知らせて構いません。

```text
External Intelligence候補があります

候補内容:
未来の判断に効きそうな理由:
推奨保存先:
```

候補は一般化できる構造に限りません。学び、失敗、金銭判断、現在の優先順位、
譲れない条件、判断理由、再開情報、繰り返し現れるパターン、別taskにも使え
そうな構造などが対象です。

上位の判断基準は「一般化できる構造か？」ではなく、「未来のこの人の判断に
効く可能性があるか？」です。そのため、人によって金銭判断中心、技術失敗中心、
キャリア判断中心、家族・時間・優先順位中心、coding structure中心になっても
問題ありません。

AIは候補内容、未来の判断に効きそうな理由、推奨保存先だけを短く示します。
ユーザーの許可なく保存、promotion、恒久Rule化をしません。

## Lightweight conceptとgame feelの境界

Little OSI / Little Compactorは、現段階では分かりやすい選択肢とlightweight
entry conceptです。このtutorialを理由に新product、runtime、schema、Canon、
research claimを作りません。

`Quest / Skill Tree / Choose / Explore / Unlock / Try`は、選択・発見・成長感を
伝えるために使えます。根拠のないlevel、XP、知能向上率、性能scoreは表示
しません。

## Codex用の案内地図

これはCodexが選択に使う地図です。ユーザーへ最初から全項目を説明する
順番表ではありません。

| Surface / concept | 役割 |
|---|---|
| `AGENTS.md` | 最小のalways-on indexとoperating boundary |
| Repository | chat外に残るexternal intelligence surface |
| Task Memory | 過去のtaskへ安全に戻るための記憶 |
| Reusable Intelligence candidate | 次の類似taskでも判断を変え得る候補 |
| Observation | 観測。まだRuleではない |
| Repeated / independently supported observation | promotionを検討できる候補 |
| `handoff/current_codex_handoff.md` | future human / AIのrestart point |
| V12 | 今の作業が完了・再開可能か |
| V13 | 次のloopを走らせる正当性があるか |
| `GO / HOLD / CAP / BLOCK` | 次loopの境界 |

記録したことと、正しいRuleになったことは同じではありません。過去に
成功した方向も、次へ進む権限を自動的には作りません。

## External Intelligenceのclaim boundary

このrepositoryでいう自己改善は、model weightsの自動更新では
ありません。蓄積量だけでAIが賢くなる、Canonが自動的に成長する、
一度の成功が恒久Ruleになる、という意味でもありません。

```text
real work
  -> observation
  -> external memory
  -> reusable intelligence candidate
  -> verification / repeated evidence
  -> bounded promotion
  -> later selective retrieval
  -> downstream decision change
```

Field Notesはadvisory memoryであり、実行権限ではありません。Ruleへの
promotionは、証拠、反証条件、rollback条件、必要なOwner承認を別に
確認します。

## 次の構造を追加する条件

「V13に存在するから」は追加理由になりません。現在の構造だけでは実際の
摩擦を解けない、同型失敗が繰り返された、再開や記憶探索のコストが実際に
高くなった、Rule候補が複数回観測された、または外部化で追加Gateが必要に
なった時だけ、次の一つを検討します。

初回の最後には、次の形式で戻り口を残します。

```text
今回使った一つ:
選んだ理由:
実際に試したこと:
変更したfile: none / <paths>
まだ導入しないもの:
次に戻る条件:
次に読む最小surface:
Decision Owner:
```

最初のread-only案内ではfileを変更しません。変更が必要になった時は、
対象と理由を示し、ユーザーの許可を得てから一つの小さな実使用へ進みます。

全V13の用語やGateを学びたい場合だけ、
[`docs/codex_tutorial_guide.md`](codex_tutorial_guide.md) のon-demand topic mapを
使ってください。
