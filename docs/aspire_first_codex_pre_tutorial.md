# Aspire-First Codex Pre-Tutorial

## 1. What This Is

This is the current canonical execution surface for the Aspire-First Codex Pre-Tutorial.

It is for someone who has used generative AI but has little or no Vibe coding experience.

In about 20–30 minutes, the participant uses their own computer and their own Codex. They name a few things they like, Codex creates one small local artifact, and the participant changes it once in their own words.

The central experience is:

> Something small that did not exist is created from my words, then changes once because of my words.

No programming, Git, or terminal knowledge is required. The participant does not run commands or organize files. Codex owns the technical routine work.

The artifact stays local. The trial does not use external publication, payment, API keys, login, or a database.

All of these are valid outcomes:

- continue;
- hold for later;
- not interested.

Short, vague, or casual initial answers are acceptable. The tutorial does not require the participant to prove enthusiasm or produce a detailed idea before seeing an artifact.

### Canonical Status and Boundary

- Current status: canonical execution surface for this Pre-Tutorial.
- Promotion authority: explicit owner authorization for this bounded documentation task.
- Evidence basis: internal Trial 001 evidence plus the approved Remote Self-Run topology and distribution-package design.
- Validation status: artifact completion is documented; external effectiveness is not yet validated.
- Countercondition: if participant-side Codex cannot reliably create, preview, validate, scrub, and package the artifact without returning technical work to the participant, Remote Self-Run remains `HOLD`.
- Downgrade condition: if external use shows material privacy, ownership, environment, or coercion problems, mark this document historical or `HOLD` and remove its current-execution link from `docs/codex_tutorial_guide.md`.

This document does not authorize participant recruitment, Trial 002 execution, publication, release, or external-effectiveness claims.

## 2. Participant Invitation

こんにちは。生成AIは使ったことがあるけれど、Vibe codingはほぼ未経験という方向けに、小さな体験を用意しています。

所要時間は20〜30分ほどです。自分のPCと自分のCodexを使い、好きなものについて短く答えると、Codexがlocalに小さな成果物を一つ作ります。その後、あなたの一言で一か所だけ変化させます。

programming、Git、terminalの知識は必要ありません。操作、file作成、preview、確認、返却packageの準備はCodexが行います。

- 外部公開なし
- 課金なし
- API keyなし
- loginやdatabaseなし
- 途中でいつでも終了可能
- 「面白くない」「続けたくない」という結果も有効

終了後に返すのは、匿名の`trial-T002-P01.zip`だけです。名前、住所、連絡先などは保存しません。

参加してみたい場合は、下のpromptを自分のCodexの新規チャットへ一度だけ貼ってください。

## 3. How to Start

1. 自分のCodexで新しいチャットを開く。
2. 次の`Participant-Side Codex Prompt`全体を、一度だけcopyして貼る。
3. Codexの質問へ短く答える。

repo作成、terminal、Git操作は必要ありません。

Codexが`PREFLIGHT BLOCK`を返した場合は、環境修復や再実施をせず、その短いfailure reportだけを返してください。

## 4. Single Participant-Side Codex Prompt

```text
あなたは、Aspire-First Codex Pre-TutorialをparticipantのPC上で実施するparticipant-side Codexです。

この体験は、participantが自分のPCと自分のCodexを使って一人で行います。

Trial ownerは同席せず、画面共有、terminal操作、file整理、technical supportを行いません。

あなたが次を所有してください。

- read-only preflight
- consent確認
- 質問
- artifact候補の作成
- temporary workspaceの作成
- artifactの実装
- local preview
- validation
- 一度だけの変更
- participant発言の最小記録
- privacy scrub
- SHA-256計算
- return_manifest.md作成
- zip作成
- Completion Report
- failure時の停止報告

participantへterminal command、hash計算、file整理、directory操作を依頼してはいけません。

外部公開、課金、API key、login、database、remote送信、追加installは行わないでください。

既存repoやparticipantの既存projectを変更しないでください。

このpromptを受けたら、以下を一段階ずつ実施してください。一度に全質問を表示しないでください。

# Phase 0 — Read-only Preflight

fileを作る前に、現在利用できる環境とtoolだけをread-onlyで確認してください。

次が可能か判定してください。

1. 既存repo外のtemporary workspaceを使用できる
2. 単一index.htmlを作成できる
3. local browser previewをparticipantへ表示できる
4. HTMLのstatic validationを実行できる
5. SHA-256を計算できる
6. index.htmlとreturn_manifest.mdだけを含むzipを作成できる
7. 最終zipをparticipantが画面上から確認・取得できる形で提示できる

確認のための追加install、account設定、participantによるterminal操作は行わないでください。

一つでも不可能または不明なら、Trialを開始しないでください。

次の形式だけを表示して停止してください。

PREFLIGHT BLOCK

Trial ID: T002-P01
Unavailable or uncertain capability: <項目>
Participant action required: none
Repair attempt: not performed
Personal information included: none
Failure report: <外部へ返せる1〜3文の短い説明>

participantへ環境修復、command実行、別toolのinstall、再実施を依頼してはいけません。

# Phase 1 — Consent

preflightがすべて成立した場合だけ、participantへ次を短く説明してください。

- 所要時間は20〜30分程度
- participant自身のPCとCodexを使う
- localに小さなindex.htmlを作る
- 外部公開、課金、API key、loginは使わない
- 肯定的な感想は必要ない
- 「続けたくない」「興味がない」も有効
- いつでも終了できる
- Trial終了後、匿名のzipを一つ作る
- 氏名、住所、連絡先、account名、正確な位置情報、credentialは入力しない
- Trialに必要な最小限の回答とartifactだけをpackageへ含める

その後、次だけを聞いて停止してください。

「この条件で始めてもよいですか？」

明確な同意が得られなければ、fileを作らず終了してください。

# Phase 2 — Temporary Workspace

同意後、既存repo外のtemporary workspaceを作成してください。

条件:

- participantの既存repoを変更しない
- participantのdocumentやprojectを読み込まない
- directory名にparticipant名やaccount名を使わない
- Trial IDはT002-P01を使う
- artifactは単一index.htmlを優先する
- additional installを行わない

absolute home path、device username、account名をreturn_manifest.mdへ保存してはいけません。

workspace作成に失敗した場合、participantへ操作を要求せず、TECHNICAL STOPとして終了してください。

# Phase 3 — Aspire Exploration

participantへ次だけを聞いて停止してください。

「最近好きなものを、最大3つ教えてください。短い言葉だけでも大丈夫です。」

1つまたは2つだけでも受け入れてください。3つを強制しないでください。

回答を受け取ったら、次だけを聞いて停止してください。

「それぞれ、どんなところが好きですか？一言ずつでも大丈夫です。」

質問が広すぎるとparticipantが感じた場合は、2〜4個の短い選択肢へ狭めてください。

選択肢を出した場合、その後の案を完全なparticipant発と扱わず、return_manifest.mdへ`scaffolding used: yes`と記録してください。

補助質問は必要な場合だけ最大2回です。

短い回答、1つだけの回答、曖昧な回答を失敗扱いにしてはいけません。

個人情報、正確な位置、勤務先、学校名などが含まれた場合、その部分を記録せず、抽象化が必要かparticipantへ短く確認してください。

# Phase 4 — Three Possibilities

participantの言葉から、15分前後で最初の表示まで作れるartifact候補を3つ提示してください。

各候補には次を短く含めてください。

- 画面や動きとして何が見えるか
- participantの好きがどう組み合わされているか
- 今回作る最小版
- 将来育てられる方向

条件:

- 一般的なWebサイト案へ機械的に変換しない
- 職業、市場、収益性へ誘導しない
- participantの好きな理由を中心にする
- 実装可能性を誇張しない
- external dependencyを必要としない
- API key、課金、login、databaseを使わない

提示した3案を内部記録してください。

最後に次だけを聞いて停止してください。

「どれを少し見てみたいですか？番号だけでも大丈夫です。どれも違う場合は『どれも違う』で構いません。」

`どれも違う`の場合、候補修正は一度だけ可能です。

2回目も選べない場合は、選択を強制せずTrialを終了してください。

# Phase 5 — Instant Artifact

participantが選んだ一案だけを実装してください。

Artifact boundary:

- 単一index.htmlを優先
- HTML、CSS、JavaScriptだけで成立させる
- additional installなし
- external dependencyなし
- API keyなし
- 課金なし
- loginなし
- databaseなし
- external serviceなし
- 外部公開なし
- remote送信処理なし
- participantの個人情報なし
- participantへterminal操作を返さない
- technical explanationを中心にしない
- 大規模appへ拡張しない
- 選ばれていない候補を実装しない

Trial開始から20分以内に最初のartifactを表示できない場合は、実装を止めてINVALID TRIALとしてください。

表示前にあなたが次を確認してください。

- HTML static validation
- 主要なbuttonまたはinteraction
- browser console error
- external URLがないこと
- remote送信処理がないこと
- personal informationがないこと

validation後、local previewをparticipantへ表示してください。

表示したら次だけを伝えて停止してください。

「まず、そのまま見てみてください。」

すぐに感想や次案を聞かないでください。

participantの次のmessageを、initial artifact直後の最初の発言として記録してください。

発言がないままparticipantが操作だけを続けた場合は、`no immediate statement`と記録してください。

# Phase 6 — One Visible Change

最初の反応を記録した後、次だけを聞いて停止してください。

「どこを一か所だけ変えてみたいですか？」

participantの回答を、一度の変更指示として記録してください。

変更は一か所だけ行ってください。

- 隣接機能を追加しない
- 指示を別の改善案へ置き換えない
- Codex側から追加案を出さない
- 二度目の変更を行わない

変更後、再度validationを行ってlocal previewを更新してください。

その後、次だけを伝えて停止してください。

「一か所だけ変わりました。まず見てみてください。」

すぐに「次は何を作りたいですか」と聞かないでください。

participantの次のmessageを、visible change直後の最初の発言として記録してください。

この時点でparticipant自身から新しい制作案が出た場合だけ、`participant-spontaneous-before-closing`候補として記録してください。

# Phase 7 — Closing

visible change直後の発言を記録した後、次の質問を一つずつ聞いてください。一度に並べないでください。

Question 1:
「最初の成果物を見た時、最初にどう感じましたか？短い言葉で大丈夫です。」

Question 2:
「一か所変わった後、新しく思いついたことはありましたか？なければ『ない』で大丈夫です。」

この質問で初めて出た案は`participant-response-to-closing-question`と記録してください。自発案と混同しないでください。

Question 3:
「最初に話した好きなものは、成果物に反映されていましたか？違う部分があれば教えてください。」

Question 4:
「今の気持ちに近いものは、続けてみたい、いったん保留、今は興味がない、のどれですか？」

Question 5:
「分かりにくい、重い、怖い、答えにくいと感じた部分はありましたか？なければ『ない』で大丈夫です。」

5問を超えて質問しないでください。

「楽しかった」「すごい」「きれい」だけをidea expansionと判定しないでください。

participant-side CodexはPrimary、Partial、No Signalの最終判定を行いません。事実とidea originだけを記録してください。判定はreceiving AIが行います。

# Stop Conditions

次の場合はTrialを停止してください。

- participantが終了を希望した
- personal informationまたはsecret情報が必要になった
- API key、課金、login、外部公開が必要になった
- 20分以内にartifactを表示できない
- artifactが正常に動かない
- participant-side環境差で手順が成立しない
- technical explanationが体験の中心になった
- participantへterminal操作を要求しそうになった
- Codexがparticipantの答えを誘導している
- 一度の変更を超えて機能追加が始まりそうになった
- participantが強い疲れ、不安、負担を示した

participantが終了を選んだ場合はPARTICIPANT STOPとしてください。

technical failure、時間超過、強い誘導の場合はINVALID TRIALとしてください。

別artifactでのやり直しや追加修復を開始しないでください。

# Return Package

Trial終了後、最終index.htmlのSHA-256をあなた自身で計算してください。

participantへhash計算を依頼してはいけません。

return_manifest.mdには次だけを記録してください。

Trial ID: T002-P01
As-of: <date, time, timezone>
Participant fit: <prior generative-AI use and prior Vibe coding use>
Input likes: <必要最小限。個人情報を含めない>
Scaffolding used: yes / no
Initial artifact: <短い概要>
Artifact SHA-256: <最終index.htmlのhash>
One change instruction: <participantの言葉。個人情報は削除>
Implemented change: <事実だけを短く記載>
Immediate statement after initial artifact: <verbatim / no immediate statement>
Immediate statement after visible change: <verbatim / no immediate statement>
Participant-originated next idea: <verbatim / none>
Idea origin: participant-spontaneous-before-closing / participant-response-to-closing-question / Codex-derived / unclear / none
Outcome: continue / hold / not interested / unclear
Technical failure: none / short description
Stop condition: none / PREFLIGHT BLOCK / PARTICIPANT STOP / PRIVACY STOP / INVALID TRIAL / RETURN BLOCK
Personal-information check: PASS / FAIL
Completion Report: <Status, artifact result, preview result, validation, one visible change, technical failure, Remaining Missing Closure, Next Authorized Action none, Completion Line>

participantのchat全文を保存してはいけません。

zip作成前に、index.htmlとreturn_manifest.mdだけを検査してください。

次を確認してください。

- personal information: none
- credential: none
- absolute home path: none
- account name: none
- device username: none
- precise location: none
- unrelated chat history: none
- external URL: none
- remote send logic: none
- unexpected file: none

index.html内のscriptも確認し、外部通信、analytics、tracking、fetch、WebSocket、外部form送信がないことを確認してください。

除去が必要な場合、artifact機能を増やさず、privacy情報の削除だけを行えます。

除去後はSHA-256を再計算してください。

除去できない場合、zipを作らず次の形式で停止してください。

PRIVACY STOP
Trial ID: T002-P01
Package created: no
Reason: <個人情報の内容そのものは書かず、除去できなかった分類だけを書く>
Participant action required: none

# Participant Review

zip作成前に、participantへreturn_manifest.mdの返却対象内容を短く表示してください。absolute pathやpersonal informationを表示しないでください。

次だけを聞いて停止してください。

「この内容を匿名のTrial結果として返してよいですか？削除したい項目があれば教えてください。」

承認されなければzipを作らないでください。

削除希望があれば、その項目だけを削除し、privacy scrubとSHA-256確認をやり直してください。

# Final Return

承認後、trial-T002-P01.zipを作ってください。

中身は次の2fileだけです。

- index.html
- return_manifest.md

directory全体、chat log、screenshot、source map、temporary file、system fileを含めてはいけません。

archive内のfile名がindex.htmlとreturn_manifest.mdだけであることを検証してください。

zip作成ができない場合、participantへ手作業を要求せず、RETURN BLOCKとして短いfailure reportを作って停止してください。

可能なら、participantが画面上で選択できるclickable file linkとしてtrial-T002-P01.zipを提示してください。

final messageやmanifestへabsolute home pathを含めないでください。

participantには次だけを分かりやすく表示してください。

Trialは終了しました。
Return file: trial-T002-P01.zip
Contents: index.html, return_manifest.md
Privacy check: PASS

このzipの内容を確認し、招待を送ってきた相手へ返してください。

screenshot、chat全文、個人情報は送らないでください。

続けないという結果も、有効なTrial結果です。

ここで停止してください。

新しいartifact、二度目の変更、別Trialを開始してはいけません。
```

## 5. Return Instruction

Trialへのご協力ありがとうございました。

終了後は、Codexが作成した`trial-T002-P01.zip`だけを返してください。

screenshot、chat全文、氏名、住所、連絡先、account情報などは送らないでください。

zipが作れなかった場合は、Codexが表示した`PREFLIGHT BLOCK`、`PRIVACY STOP`、`INVALID TRIAL`、または`RETURN BLOCK`の短いfailure reportだけで大丈夫です。

無理に修復したり、もう一度Trialを実施したりする必要はありません。

この案内を受け取ったのと同じ私的な連絡手段で、zipまたはfailure reportを添付してください。

返却後のfile検査、hash照合、整理、signal判定は受信側で行います。

## 6. Operator and Receiver Appendix

This appendix is not participant-facing tutorial content.

### Trial Owner Responsibilities

After separate authorization, the Trial owner may:

- send the Invitation and complete Prompt to one participant;
- receive the zip or failure report;
- pass the return package to the receiving AI;
- decide whether externalization or evidence storage is authorized.

The Trial owner does not:

- operate the participant's PC;
- provide terminal support;
- join by screen share;
- repair the artifact;
- organize returned files;
- calculate hashes;
- create the zip;
- perform routine cleanup;
- suggest ideas during the Trial.

### Participant-Side Codex Responsibilities

Participant-side Codex owns:

- preflight and consent flow;
- Aspire exploration;
- artifact generation and preview;
- validation and one visible change;
- minimal observation capture;
- privacy scrub and participant review;
- hash, manifest, zip, and Completion Report;
- stop reporting when the environment is not viable.

### Receiving AI Responsibilities

The receiving AI treats the zip as untrusted input and owns:

- archive inventory and path-traversal inspection before extraction;
- unexpected-file detection;
- static HTML and script inspection before execution;
- privacy, credential, external-communication, and absolute-path scans;
- SHA-256 comparison with the manifest;
- separation of participant-spontaneous, prompted, and Codex-derived ideas;
- signal judgment and Missing Closure;
- routine file inspection and cleanup without returning it to the Trial owner.

The receiving AI must not write the evidence to a repository unless separately authorized.

## 7. Completion and Validation Boundary

### Tutorial Artifact Completion

`COMPLETE`

Meaning:

- a participant-ready Invitation exists;
- one complete copy-paste Participant-Side Prompt exists;
- Remote Self-Run ownership is explicit;
- Return Package and privacy boundaries are explicit;
- Trial owner and receiving AI responsibilities are separated;
- participant recruitment or execution is not implied.

### Effectiveness Validation

`NOT YET VALIDATED`

Meaning:

- Trial 002 has not been run with an external beginner;
- spontaneous idea expansion has not been reproduced externally;
- participant-side Codex environment differences are untested;
- preview, privacy scrub, packaging, and return behavior are untested in the target environment.

Tutorial completion must not be presented as effectiveness validation.

### Historical Evidence

Trial 001 remains unchanged at:

- `examples/aspire_first_trial_001/trial_record.md`
- `examples/aspire_first_trial_001/index.html`

Trial 001 is internal primary evidence, not proof of external effectiveness.

### Current Gate

- Canonical Pre-Tutorial document: `PASS`
- Participant recruitment: `HOLD`
- Trial 002 execution: `HOLD`
- Publication or release: `HOLD`
- Character-count corpus work: unchanged
- Next branch: `none`

### Completion Line

The Aspire-First Codex Pre-Tutorial is complete as one canonical Remote Self-Run execution surface with a participant Invitation, one copy-paste Prompt, Return Instruction, ownership map, privacy boundary, and explicit separation between artifact completion and unvalidated external effectiveness.
