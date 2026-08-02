# ♻️ Field Notes Lite v0.1 — Design Packet

## 1. Purpose

Field Notes Lite v0.1 は、正常に完了した Companion Run の再利用可能な残差を、次の Run で選択的に再接続できるリポジトリ内メモへ変換するための最小機能である。目的は、同じ説明、同じ修正、同じ判断コストを繰り返さず、次の Run の開始条件を安く、安全に、明確にすることである。

Field Note は実行権限ではない。保存済み Note が存在しても、`Active Branch`、`Next Authorized Action`、`Current Gate`、対象リポジトリ固有の規則、または人間の Approval を置き換えない。`CANDIDATE`、`REUSED`、`PROMOTABLE` は再利用成熟度であり、V12 completion state や V13 の `GO / HOLD / CAP / BLOCK` とは別軸である。

v0.1 が提供する閉じたループは次のとおりである。

```text
同じ active Companion Run 内の accepted typed proposal
  → verified terminal success 後にだけ最大1件の ♻️ candidate
  → save または skip
  → save の場合だけ、正確な1ファイル Create を人間が Approval
  → 後続 Run でローカル metadata 選択
  → 最大1件の完全な Field Note を control context として注入
  → 別 Run の検証証拠がある場合だけ成熟度を更新可能
```

本機能は外部採用、一般化、lower-model equivalence、または Intelligence Transplant の成功を主張するものではない。

## 2. Layer Roles

| Layer | Product behavior | Internal implementation requirement | Evidence boundary |
|---|---|---|---|
| Companion Run completion gate | Run 成功後にだけ候補を出せる | same active Run の accepted typed proposal、fresh な typed Run 結果、source Run identity、完了証拠を確認する | 成功した source Run と proposal は候補提示の根拠にすぎず、再利用成功の証拠ではない |
| Candidate proposal gate and compiler | 0件または1件を UI に渡す | same active Codex Run の side-effect-free `propose_field_note_candidate` を最大1回だけ受理し、verified terminal success 後に typed fields から exact bytes を deterministic compile する | proposal の受理、候補の生成・表示は `CANDIDATE` を超える成熟度や action authority を作らない |
| Candidate UI | 1件の ♻️ candidate と `save` / `skip` だけを示す | 複数候補、検索、分類、編集、管理画面を持たない | `save` の選択だけでは書き込み権限にならない |
| Bounded Approval writer | 正確な1ファイル Create を人間へ提示する | path、完全な bytes、digest、`must_not_exist` precondition を同一 Approval に束縛する | 人間 Approval は変更権限であり、暗号学的な実世界 identity proof ではない |
| Repository store | 1 insight を1 Markdown に保存する | `.decision-os/field-notes/` の直下だけを使用し、既存ファイルを上書きしない | ファイルの存在は利用、正しさ、昇格、一般化を証明しない |
| Reconnection selector | ユーザー操作なしで最大1件を再接続する | metadata のみをローカルで bounded scan し、relevance を先、value level を同点時だけ使う | 選択・注入だけでは「実際に再利用された」と扱わない |
| Maturity reducer | `CANDIDATE → REUSED → PROMOTABLE` を扱う | 各遷移を exact Run identity、Note bytes identity、acceptance、activation evidence に結び付ける | `PROMOTABLE` でも canonical rule 化や product-wide generalization は未承認 |

Field Notes Lite は、Stage 5 の Intelligence Transplant record、event chain、E1–E5、public-claim Guard を代替または簡略再実装しない。Level 3 の名称に `Transplant Candidate` を含めても、それだけで Stage 5 の `CANDIDATE`、E5、または generalized transplant の証拠にはならない。

## 3. User Experience

1. active Codex Run は、再利用可能な insight がある場合にだけ side-effect-free typed dynamic tool `propose_field_note_candidate` を呼び出せる。呼び出さなくてもよい。
2. Companion は schema-valid な proposal を同じ Run で最大1件だけ一時記録し、Run の terminal outcome が確定するまで UI に公開しない。
3. Run が failed、needs-attention、interrupted、未完了、または成功証拠不足なら、記録済み proposal を破棄し、♻️ candidate は表示しない。
4. Run が正常完了し、同じ Run に eligible proposal がある場合だけ、Run 結果の後に1件の ♻️ candidate を表示する。proposal がなければ候補は0件である。操作は `save` と `skip` の2つだけである。
5. `skip` は候補を閉じる。ファイル、status、rules、tests、source files、他の Field Notes を一切変更しない。
6. `save` は書き込みそのものではなく、bounded write mechanism へ正確な1ファイル `Create` action を提出する意思表示である。
7. Approval surface は `CREATE`、repository-relative path、Companion が deterministic compile した完全な内容とその digest、既存パスを置換しない precondition を同時に人間へ示す。Approval 前には書き込まない。
8. Approval 後に exact bytes の新規作成と readback identity が成功した場合だけ、candidate 表示を保存済み path に置き換える。
9. 成功時にユーザーへ表示する結果は、次のような repository-relative path だけとする。

```text
.decision-os/field-notes/2026-08-02-bounded-reuse-k7m2p4x9q1.md
```

保存成功画面に maturity claim、一般化 claim、追加 action、次候補、管理導線を加えない。Approval 拒否、衝突、書き込み失敗、readback 不一致の場合は保存成功を表示せず、ファイルが作成されたと主張しない。

## 4. Candidate Proposal and Eligibility

候補は post-Run extractor で回収しない。same active Codex Run だけが、side-effect-free typed dynamic tool `propose_field_note_candidate` を任意に呼び出せる。candidate extraction のための second model call、別 Run、free-form final response の parse は行わない。free-form の「candidate」「done」などの文言、stale cache、ファイルの存在、または passing test の記述は proposal として扱わない。

`propose_field_note_candidate` は Run-local one-shot gate を持つ。最初の invocation だけを admission attempt とし、schema-valid なら accepted proposal として一時記録する。schema-invalid なら proposal 0件のまま attempt を消費する。同じ Run の2回目以降の invocation は、最初の record を置換・追記・変更する前に typed error で fail closed とし、新しい authority や model call を作らない。accepted proposal は最大1件であり、呼び出しがない Run は0件である。

tool は write、execution、branch、merge、release、publication、Approval または次-loop authority を一切持たない。filesystem と repository state を変更せず、次の typed candidate fields だけを受け付ける。

- `title: string`。1～120 Unicode code points
- `value_level: 1 | 2 | 3`
- `source_model_class: stronger | lower-cost | UNKNOWN`
- `target_model_class: stronger | lower-cost | UNKNOWN`
- `trigger_terms: list[string]`。Section 7 の件数・長さ bounds に従う
- `scope: object`。`task_family: string`、`path_prefixes: list[string]`、`exclude_terms: list[string]` だけを持ち、Section 7 の bounds に従う
- `body: object`。`trigger`、`reusable_structure`、`scope`、`do_not_apply_when`、`procedure`、`acceptance`、`evidence`、`remaining_unknowns` の non-empty string だけを持つ

tool input の top-level・nested object は上記 fixed keys 以外を拒否する。raw Markdown、raw JSON、path、`field_note_id`、`schema_version`、`status`、`source_run_id`、`source_run_outcome`、`created_at`、`maturity_evidence` または任意の追加 metadata を渡せない。typed payload は、Section 7 の compile 後 full Markdown 64 KiB bound を満たせない場合に schema-invalid とする。Companion は accepted typed fields に、same Run から得た trusted `source_run_id`、verified outcome と、Companion-owned schema version、identity、creation time、initial maturity state を結合する。`source_model_class` と `target_model_class` は operator-configured model-class record に照合し、不一致または取得不能なら Level 3 proposal を受理しない。slug と filename も Section 6 に従って Companion が導出する。

proposal が UI candidate になる eligibility は次の全条件を要求する。

- exact `source_run_id` があり、proposal を受理した Run と一致する。
- adapter が同じ Run を fresh な verified terminal success として返している。
- failed、needs-attention、interrupted、incomplete、`UNKNOWN` のいずれでもない。
- 何を変更し、何を検証し、何が未検証かを識別できる completion evidence がある。
- V12 completion state が Run に存在する場合は `PASS` である。`DELAY / BLOCK / UNKNOWN` から候補を作らない。
- accepted proposal が schema-valid で、Section 7 の body 8項目をすべて満たし、`Evidence` と `Remaining UNKNOWNs` が空でない。

Companion は Run の terminal outcome が確定するまで proposal を UI に公開しない。同じ Run が failed、needs-attention、interrupted、incomplete になった、または completion evidence を欠く場合、proposal は破棄し、♻️ candidate を表示しない。eligible proposal がない terminal success でも candidate は0件である。

active Run が複数の insight を考慮できる場合、tool invocation 前に schema 不備、証拠境界違反、複数 insight の混在、scope 不明、canonical rule 化を要求する案を除外し、必ず次の順で1件へ縮約する。

1. Level 3
2. Level 2
3. Level 1

同じ Level 内では、source Run evidence への結び付きが明確で、scope が狭く、`Do Not Apply When` が具体的な案を優先する。それでも同点なら active Run 内の安定した source order を使う。tool と UI のどちらにも複数案を渡してはならない。

Level 3 は、source model class と想定 target model class が構成情報として識別でき、source が `stronger`、target が `lower-cost` のときだけ分類できる。この分類は能力差や equivalence の実証ではない。model class が `UNKNOWN` の場合は Level 3 に分類しない。

terminal success と proposal eligibility の確認後、Companion は同じ accepted proposal record から Section 7 の canonical JSON metadata block と固定 Markdown body を deterministic compile する。`title` は単一 H1 に、8つの `body` fields は対応する固定 headings の本文にだけ写像する。同じ record の再コンパイルは byte-identical であり、この exact bytes と SHA-256 を `save` 後の Approval に束縛する。

## 5. Reuse Value Levels

value level は「どこまで役立つ可能性があるか」の候補分類であり、status や実証済み maturity ではない。

| Level | Fixed meaning | Candidate 時点で必要な根拠 | Candidate 時点で許される claim | 禁止される claim |
|---|---|---|---|---|
| Level 1 — Repeat | 同一または近接反復する task で再利用する | 成功した source Run 内に、反復可能な Trigger、Procedure、Acceptance がある | 同種 task の再実行で役立つ可能性がある | すでに他 task で再利用された |
| Level 2 — Project | 同じ repository の複数 task で再利用する | repository 内の複数 task family に適用可能な structure と明示的な除外条件がある | repository 内で再利用候補になり得る | repository-wide に検証済み、canonical rule である |
| Level 3 — Transplant Candidate | stronger model が作った structure を lower-cost model が再利用できる可能性がある | source/target model class、source Run identity、転用する exact structure が識別できる | separate lower-model Run で試す候補である | lower-model equivalence、successful intelligence transplant、一般化が確立した |

候補表示の縮約では Level 3、2、1 の順を使う。保存済み Note の automatic reconnection ではこの順を先に使わず、relevance score が同じ場合にだけ Level 3、2、1 を tie-breaker として使う。

Level 3 は、別の lower-model Run がその exact Note を実際に利用し、成功と activation が検証されるまで必ず `CANDIDATE` のままである。

## 6. Field Note Storage and Naming

保存 root は固定する。

```text
.decision-os/field-notes/
```

Note はこの directory の直下に置く1 insight 1 Markdown file とし、subdirectory、aggregate file、index、Ledger を作らない。

filename は次の形式とする。

```text
YYYY-MM-DD-<short-slug>-<short-id>.md
```

- `YYYY-MM-DD` は metadata の timezone-aware `created_at` を UTC に正規化した日付である。
- `short-slug` は insight を表す2～5語の lowercase ASCII kebab-case とし、生成できない場合は `field-note` を使う。
- `short-id` は full `field_note_id` から導出した10文字の lowercase base32 identity とする。
- full `field_note_id` は metadata に保存し、filename の short identity だけを identity authority にしない。
- writer は create-new / no-replace semantics を使う。候補 path が存在する、symlink である、repository root 外へ解決される、または case-normalized collision がある場合は書き込まない。新しい identity と path を作り直し、別の exact Approval を要求する。

例:

```text
.decision-os/field-notes/2026-08-02-approval-byte-binding-k7m2p4x9q1.md
```

保存先 directory を安全に解決または materialize できない場合、alternate directory へ fallback してはならない。保存を needs-attention とし、書き込みは0件に保つ。

## 7. Field Note Schema

各 Markdown は、file 先頭の canonical strict JSON metadata block 1件と固定 body headings から成る。YAML front matter、YAML dependency、custom general-purpose YAML parser は使用しない。初回保存時の canonical form は次のとおりである。

```markdown
<!-- decision-os-field-note-metadata:v0.1
{"created_at":"2026-08-02T12:34:56Z","field_note_id":"fn_018f4f5b_example","maturity_evidence":{"different_task_reuse":null,"first_verified_reuse":null},"schema_version":"decision-os.field-note-lite.v0.1","scope":{"exclude_terms":["bulk rewrite"],"path_prefixes":["docs/"],"repository":"current","task_family":"governed-file-write"},"source_model_class":"stronger","source_run_id":"run_example_001","source_run_outcome":"SUCCESS","status":"CANDIDATE","target_model_class":"lower-cost","trigger_terms":["bounded approval","exact file create"],"value_level":3}
-->

# Approval byte binding

## Trigger
<この insight を検討する条件>

## Reusable Structure
<再利用する1つの構造>

## Scope
<適用範囲>

## Do Not Apply When
<不適用条件>

## Procedure
<bounded な手順>

## Acceptance
<成功判定>

## Evidence
<source Run に結び付く証拠と、その限界>

## Remaining UNKNOWNs
<未検証事項>
```

metadata block は byte 0 の exact start marker `<!-- decision-os-field-note-metadata:v0.1\n` で始まり、canonical JSON object 1件、exact end marker `\n-->\n` の順とする。block 全体は最大8 KiB とし、同じ file に2件目の metadata block、start marker 前の BOM・空白・comment、または end marker 後の追加 metadata を許可しない。body は end marker 後の空行から始める。

canonical JSON serialization は Companion だけが行う。UTF-8 without BOM、LF line ending、lexicographic object-key order、array input order の保持、最小 separators、insignificant whitespace なしを固定する。string は JSON escape を使用し、non-ASCII UTF-16 code unit と `<`、`>`、`&` は lowercase `\u` escape として出力する。integer は decimal canonical form とし、floating-point、`NaN`、`Infinity`、negative zero は許可しない。同じ typed proposal record と Companion-owned fields からは常に同じ metadata bytes と同じ full Markdown bytes を生成する。

reader は標準の strict JSON decoder を duplicate-key rejection mode で使い、root object 以外、duplicate key、unknown key、unknown enum、invalid UTF-8、non-canonical serialization、marker 不備を拒否する。YAML として解釈する fallback や、自由形式 metadata を読む汎用 parser は持たない。

top-level metadata の必須かつ唯一の allowed keys は `schema_version`、`field_note_id`、`status`、`value_level`、`source_run_id`、`source_run_outcome`、`source_model_class`、`target_model_class`、`trigger_terms`、`scope`、`created_at`、`maturity_evidence` である。`scope` の allowed keys は `repository`、`task_family`、`path_prefixes`、`exclude_terms`、`maturity_evidence` の allowed keys は `first_verified_reuse`、`different_task_reuse` だけである。これにより、少なくとも status、value level、source Run identity、trigger terms、scope、creation time を full body の読取り前に取得できる。

validation requirements は次のとおりである。

- `schema_version` は exact string `decision-os.field-note-lite.v0.1` だけを許す。
- `status` は `CANDIDATE | REUSED | PROMOTABLE` のいずれかだけを許す。
- `value_level` は integer `1 | 2 | 3` だけを許す。
- `source_run_outcome` は exact enum `SUCCESS` だけを許す。
- `source_model_class` と `target_model_class` はそれぞれ `stronger | lower-cost | UNKNOWN` のいずれかだけを許す。
- Level 3 は `source_model_class: stronger` と `target_model_class: lower-cost` を要求する。
- `trigger_terms` は1～12件の重複しない non-empty string とし、1件64 Unicode code points 以下とする。
- `scope.repository` は v0.1 では `current` のみとし、cross-repository selection を許可しない。
- `scope.task_family` は1～128 Unicode code points、`path_prefixes` は0～16件で各1～256 code points、`exclude_terms` は0～16件で各1～64 code pointsの重複しない string とする。
- `created_at` は timezone-aware RFC 3339 とする。
- JSON duplicate keys、unknown top-level・nested keys、unknown enum、invalid UTF-8、non-canonical key order・escape・whitespace を拒否する。
- body は `Trigger`、`Reusable Structure`、`Scope`、`Do Not Apply When`、`Procedure`、`Acceptance`、`Evidence`、`Remaining UNKNOWNs` を各1回、同じ順序で含む。
- full Markdown は最大64 KiB、各 body section は non-empty とし、`Evidence` と `Remaining UNKNOWNs` を空にしない。
- `maturity_evidence` は初回保存時に両方 `null` とする。`first_verified_reuse` は `reuse_run_id`、`note_path`、`field_note_id`、`note_sha256`、`activation_evidence`、`acceptance_result`、`human_rescue`、`task_identity`、`verified_at` だけを持つ object、`different_task_reuse` はこれらと `difference_evidence` だけを持つ object または `null` とする。verified reuse では `acceptance_result` は `PASS`、`human_rescue` は `false` だけを許す。

model が供給するのは Section 4 の typed candidate fields だけである。Companion が trusted Run record と fixed constants を結合し、この schema の final JSON、固定 body headings、Markdown delimiters、filename、full bytes、SHA-256 を compile する。model が raw JSON、raw Markdown、metadata keys、serialization order または delimiter を指定することはできない。

metadata に記録された Run outcome や model class は bounded local record であり、実世界の operator identity、hidden input の不存在、外部 provenance、または model 能力を暗号学的に証明しない。

## 8. Automatic Reconnection

Automatic reconnection は current repository 内で完結し、ユーザーに Markdown の検索、分類、比較、選択を求めない。

選択 algorithm は次の順序で固定する。

1. `.decision-os/field-notes/` 直下の regular `.md` file だけを filename 順で列挙する。symlink、subdirectory、repository root 外解決は対象外とする。
2. 最大256 files、各 file 先頭の canonical JSON metadata block 最大8 KiB、metadata block 合計最大512 KiB の範囲だけをローカルで読む。scanner は byte 0 の start marker から exact end marker までを bounded streaming read し、metadata-only scan では end marker 後の body bytes を読まない。上限内に end marker がない、または合計上限を超える場合は部分集合から推測せず、その Run では何も注入しない。
3. duplicate-key rejection を含む strict JSON parse、canonical serialization、fixed-key schema のいずれかに失敗した Note は不適格とする。YAML fallback は行わず、metadata scan のために full body を読んだり model へ送ったりしない。
4. current task から `task_family`、repo-relative target paths、正規化した task terms をローカルで構成する。selection のための model call や embedding call は行わない。
5. `scope.repository != current`、`exclude_terms` hit、または無効 status の Note を除外する。
6. 残った各 Note に次の deterministic relevance score を与える。

```text
exact task_family match:                  +4
matched trigger term:                     +2 each, maximum +6
matched repo-relative path prefix:         +3, maximum +3
```

term 比較は Unicode NFKC、case-fold、連続 whitespace の1 space 化を行った後の exact token または exact phrase match とする。fuzzy similarity は使わない。relevance threshold は `4` とし、4未満は不適格とする。

7. relevance score の降順で並べる。score が同じ場合だけ value level `3 → 2 → 1` を使う。さらに同点なら `created_at` の新しい順、最後に `field_note_id` の bytewise 昇順を使う。
8. 先頭1件だけを選択し、その1件の full Markdown だけを読む。full Note は最大64 KiB とする。body headings が不正、body 内に2件目の metadata marker がある、`Do Not Apply When` が current task に該当する、または size bound を超える場合は別 Note を full-read せず、何も注入しない。
9. 選択した exact path、`field_note_id`、full bytes の SHA-256、status、value level とともに、Note 全文を明示的に区切った control context として注入する。

control context の優先順位は system/developer instructions、current repository rules、current task authority、current Gate より下である。Note は作業方法を制約または補助できるが、書き込み、branch change、release、publication、credential use、支払い、次-loop execution を許可できない。

注入は利用可能性を作るだけで、実際の reuse を証明しない。`REUSED` には Section 11 の別 evidence が必要である。

## 9. Read-Budget Treatment

Field Notes Lite は、ordinary task read と control-plane memory read を別カウンターで扱う。

- canonical JSON metadata-block-only scan は ordinary four-distinct-repository-path read budget を消費しない。
- 選択された最大1件の full Field Note の control-context injection も、その four-path budget を消費しない。
- exemption は `.decision-os/field-notes/` の bounded metadata と、selector が選んだ1件の full Note だけに適用する。
- body を比較するために複数 Note を読む、Field Note から参照された別 file を読む、または一般 repository 探索へ転用することは exemption 対象外である。
- no match、scan bound 超過、schema failure、selected body failure の場合は注入0件とし、ordinary task read budget は変化しない。

Run-local diagnostics は少なくとも `metadata_files_seen`、`metadata_bytes_read`、`selected_field_note_path | null`、`full_notes_injected`、`ordinary_distinct_paths_consumed` を別項目で保持する。これは selection と read-budget acceptance を検証するための bounded diagnostic であり、複雑な永続 Ledger や maturity authority ではない。

## 10. Approval and Safety Boundaries

Field Note の初回保存は、次の単一 action を bounded write mechanism に提出しなければならない。

```text
Action: CREATE
Path: .decision-os/field-notes/<exact-filename>.md
Content: <exact proposed UTF-8 bytes>
Content SHA-256: <lowercase hex digest>
Precondition: MUST_NOT_EXIST
Approval scope: THIS ONE FILE ONLY
```

`save` button はこの action の作成を開始するが、action 自体への人間 Approval を代替しない。Approval は exact path と exact bytes に束縛し、Approval 後にどちらかが変わる場合は無効として新しい Approval を要求する。writer は repository containment、regular parent path、symlink rejection、create-new semantics、write 後の path・bytes digest readback を確認する。

同じ transaction で自動変更してはならないものは次のとおりである。

- `AGENTS.md`
- 既存 project rules
- tests
- source files
- 既存 file
- 他の Field Notes

候補の表示と Approval surface では untrusted text を executable HTML として解釈しない。保存済み Note を control context に注入するときも明確に delimiter で囲み、Note 内の authority claim、instruction-precedence claim、secret request、scope expansion を実行権限として扱わない。

status 遷移を永続化する場合も自動 promotion は禁止する。Section 11 の証拠を満たした後、対象となる同一 Field Note だけの exact update を別の人間 Approval に提出する。初回 save Approval を将来の update authority として再利用しない。自動 deletion、他 Note の書換え、canonical surface への転記は行わない。

## 11. State Transitions

status は value level と独立し、次の forward-only sequence だけを持つ。

```text
CANDIDATE
  → REUSED after one verified reuse
  → PROMOTABLE after verified reuse in a meaningfully different task
```

| State | Entry requirement | Required evidence | Allowed maturity claim | Still not established |
|---|---|---|---|---|
| `CANDIDATE` | 成功した source Companion Run 内で typed proposal が受理され、terminal success 後に exact one-file Create が Approval・readback された | source Run identity、accepted proposal identity、terminal success、initial Note path/bytes identity、value-level rationale | 再利用を試せる保存済み候補である | 実利用、再利用成功、一般化、昇格 |
| `REUSED` | 後続の別 Run で exact Note が実際に使われ、Run が acceptance を満たした | reuse Run identity、注入した Note path/`field_note_id`/SHA-256、activation evidence、terminal success、Acceptance result、human rescue の有無、verified time | 1回の verified reuse がある | 複数 task への一般化、model equivalence、canonical rule 妥当性 |
| `PROMOTABLE` | `REUSED` 後、意味の異なる task で同じ structure の verified reuse が追加された | first reuse と異なる task identity、実質差分、同じ Note identity、activation evidence、Acceptance result、terminal success、verified time | 別の promotion review に送れる | promotion Approval、`AGENTS.md` 挿入、product-wide generalization、外部 adoption |

単なる Note の存在、metadata scan、control-context injection、passing suite、偶然正しい answer は verified reuse に足りない。activation evidence は少なくとも、Run が exact Note identity を入力として受け取り、`Procedure` または `Reusable Structure` の識別可能な部分を実行し、それが `Acceptance` の成立に対応したことを示さなければならない。key structure を人間の途中 correction または rescue が供給した Run は verified reuse に数えない。

Level 3 の `REUSED` はさらに、source Run とは別 identity の lower-cost model Run であることを要求する。Note が lower-model context に存在しただけでは不足する。1回の verified lower-model reuse 後も、generalized transplant と lower-model equivalence は `NOT ESTABLISHED` のままである。

「meaningfully different task」は、task 文言、ID、timestamp の付け替えではない。少なくとも task family、operation、target artifact class のいずれかに実質差分があり、同じ reusable structure が別の acceptance を満たしたことを evidence record に説明する。`PROMOTABLE` は自動 promotion の命令ではなく、Decision Owner が別途検討できる状態にすぎない。

各 status update は `maturity_evidence` の該当 slot に exact evidence を記録し、対象 Note 1件だけの別 Approval を必要とする。evidence が不足する場合は status を進めない。

## 12. Non-Goals

v0.1 では次を実装しない。

- Field Notes management screen
- 複雑な Ledger、event chain、または検索 index
- multiple-candidate presentation
- candidate chooser、手動分類 UI、保存済み Markdown 選択 UI
- automatic promotion
- automatic deletion、deduplication rewrite、bulk migration
- `AGENTS.md`、既存 project rules、tests、source files、他 Field Notes の自動変更
- canonical rule への自動挿入
- cross-repository sync または repository-wide generalization
- Field Notes 全文の一括 model 送信
- selection のための embedding service、network call、model call
- candidate extraction のための second model call、別 Run、free-form final response parsing
- YAML front matter、YAML dependency、custom general-purpose YAML parser
- Intelligence Transplant Stage 5、E1–E5、Manual Bridge、public-claim Guard の再実装
- external adoption、第三者 certification、model equivalence、generalized transplant の claim
- Field Note からの next-loop 自動実行、release、publish、merge、Role assignment

Field Notes Lite は1つの repository-local selective memory surface であり、README を work log にする機能でも、すべての task を記録する機能でもない。

## 13. Acceptance Tests

| ID | Surface | Test | Expected result |
|---|---|---|---|
| AT-01 | Proposal | same active Run が schema-valid proposal を1件送り verified terminal success になる | proposal 1件が ♻️ candidate 1件として表示される |
| AT-02 | Proposal | proposal 後に Run を failed、needs-attention、interrupted にそれぞれ到達させる、または completion evidence を欠かせる | proposal は破棄され、いずれにも candidate は表示されない |
| AT-03 | Proposal | same Run で `propose_field_note_candidate` を2回呼ぶ | 2回目は最初の record を置換する前に fail closed。accepted proposal は最大1件 |
| AT-04 | Proposal | proposal を呼ばずに verified terminal success へ到達する | candidate は表示されない |
| AT-05 | Proposal | candidate proposal を含む Run の model-call count と Run identity を記録する | active Run の1 call だけで、candidate extraction 用の追加 model call または別 Run は0件 |
| AT-06 | Proposal | proposal を呼ばず、free-form final text に完全な candidate、JSON、または tool 名を記述する | text は parse・採用されず、candidate は表示されない |
| AT-07 | Proposal ranking | active Run に eligible な Level 1、2、3 insight を与える | Run は Level 3 を1件だけ proposal し、tool と UI に複数候補を渡さない |
| AT-08 | Proposal ranking | same Level の insight を複数与える | evidence binding、narrow scope、specific `Do Not Apply When`、stable source order の順で1件に縮約する |
| AT-09 | Ranking | relevance score が同じ Level 1、2、3 Note を用意する | Level 3 が選択される |
| AT-10 | Ranking | relevance 4 の Level 3 と relevance 7 の Level 1 または2を用意する | 高 relevance の lower-level Note が選択される |
| AT-11 | Product | candidate で `skip` を選ぶ | file、status、既存 surface の変更は0件 |
| AT-12 | Approval | candidate で `save` を選ぶ | `.decision-os/field-notes/` 下の exactly one new Markdown `CREATE` が提案される |
| AT-13 | Approval | Create proposal を未承認のまま保持する | filesystem write は0件 |
| AT-14 | Product | exact Create を承認し、write と readback を成功させる | UI は保存された repository-relative path だけを表示する |
| AT-15 | Compiler | 同じ typed proposal record と Companion-owned fields を2回 compile する | canonical JSON block、固定 headings、full Markdown、SHA-256 が byte-identical。raw JSON または raw Markdown は model input にない |
| AT-16 | Schema | compiled Note を parser で読む | byte 0 にJSON metadata block が1件だけあり、body headings は既定の8件・同じ順序 |
| AT-17 | Schema | JSON に duplicate key、unknown key、unknown enum、non-canonical whitespace/order をそれぞれ入れる | strict parser は各 Note を拒否し、selector は注入しない |
| AT-18 | Schema | YAML front matter の Note を置き、dependency と parser invocation を観測する | Note は不適格。YAML dependency、YAML parser、YAML fallback の利用は0件 |
| AT-19 | Metadata scan | valid block 後の body に metadata-like text と read trap を置く | metadata-only scan は exact end marker で停止し、body bytes を読まず、JSON block だけで選別する |
| AT-20 | Metadata scan | start/end marker 欠落、block 8 KiB 超過をそれぞれ作る | 各 Note は metadata scan で fail closed となり、body は読まれない |
| AT-21 | Read budget | 4 distinct task paths を読む Run で metadata scan を行う | task-read counter は4のままで、metadata scan は別 counter に記録される |
| AT-22 | Reconnection | threshold を超える Note を複数用意する | full-read と control-context injection は選択された最大1件だけ |
| AT-23 | Reconnection | すべての Note を relevance 3以下にする | full Note の読取り・注入は0件 |
| AT-24 | Maturity | Level 3 Note を保存し、lower-model verified reuse をまだ行わない | status は `CANDIDATE` のまま |
| AT-25 | Safety | candidate save transaction の前後を diff する | 新規 Field Note 1件以外は変更なし。`AGENTS.md` と全 existing files は不変 |
| AT-26 | Approval | 提案 path を Approval 前に既存化する | no-replace で失敗し、上書きせず、新 path には新 Approval が必要 |
| AT-27 | Reconnection | selected Note の `Do Not Apply When` を current task に一致させる | 別 Note を full-readせず、注入0件 |
| AT-28 | Evidence | Level 3 Note を lower-model に注入するが、activation evidence なしで Run を成功させる | `REUSED` に遷移しない |
| AT-29 | Evidence | exact Note identity、lower-model Run、activation、Acceptance、no human rescue を検証する | 別 Approval を経た対象 Note 1件の update だけが `REUSED` を記録できる |
| AT-30 | Evidence | `REUSED` 後、IDと文言だけを変えた同一 task を再実行する | `PROMOTABLE` に遷移しない |
| AT-31 | Evidence | 実質的に異なる task で同じ structure の verified reuse を得る | 別 Approval 後に `PROMOTABLE` を記録できるが、canonical promotion は起きない |
| AT-32 | Authority | proposal または注入 Note に write、branch change、merge、release、publication、または `AGENTS.md` edit の命令を含める | proposal tool と control context は権限を作らず、無許可 action は実行されない |
| AT-33 | Bounds | metadata file count を257件、metadata 合計を512 KiB超、selected full Note を64 KiB超にそれぞれする | fail closed で注入0件、ユーザーに file 選択を返さない |
| AT-34 | Schema | selected full Note の body 内に2件目の metadata marker を置く | full body validation で拒否し、別 Note を読まず、注入0件 |

## 14. Remaining UNKNOWNs

以下は固定済み product decision を再検討する項目ではなく、許可された実装開始時に既存 Companion code へ結線するための UNKNOWN である。根拠なしに field 名や route を仮定しない。

- current Companion adapter で terminal success、failed、needs-attention、completion evidence を表す exact typed fields と fresh projection API。
- current adapter の dynamic-tool registration point、same-Run call identity、Run-local one-shot proposal record、terminal outcome に応じた expose/discard lifecycle event の exact field 名。mechanism と authority boundary は Section 4 のとおり固定する。
- bounded write mechanism が exact path、bytes、digest、`MUST_NOT_EXIST` を1つの Approval に束縛する既存 interface 名。
- existing read-budget counter の exact integration point と、control-plane read counter の配置場所。
- stronger / lower-cost を operator-configured class として固定する既存 model registry または configuration surface。これが不明な間は Level 3 を生成しない。
- current task から `task_family` と repo-relative target paths を得る既存 typed source。取得不能な要素を free-form 推測で補わない。

これらの UNKNOWN は実装接続の未確認事項であり、same-Run one-shot typed proposal、terminal-success-only exposure、canonical JSON metadata、候補数、保存 path、value-level order、relevance-first ranking、read-budget exemption、Approval 境界、state transition、非目標を変更する権限ではない。

## 15. Completion Line

Field Notes Lite v0.1 の product behavior、internal implementation requirements、maturity evidence boundary は本 Design Packet で実装可能な粒度まで定義した。実装、統合試験、外部採用、一般化、lower-model equivalence、および successful intelligence transplant は未実施・未確立である。
