# Handoff Acceptance Guard v0.1 — B Design

## 1. Artifact Identity

```text
Experiment ID: V13-SDFP-001
Role: B Planner
Design status: FROZEN
Selected task: Handoff Acceptance Guard v0.1
Current layer: V13 — Design / Execution Separation

Packet commit: 343684d8ce384cb543293968ad667222dc5bc958
Packet path: validation/handoff_acceptance_guard_v0_1_shared_evidence_packet.md
Packet blob SHA: 502ba73f643e8dabf19a2cbeaa06db3c910a32c5
Packet SHA-256: fff0b9b7394749556c7ee94184aebbd304f0b94c10222e8766806f672a8a62f2
Packet identity verification: PASS

Implementation status: NOT STARTED
C visibility: NONE
```

This Artifact is the one frozen B Design contract for the selected task. The
B Planner's authority is limited to producing, freezing, committing, and, when
available, pushing this file on
`codex/v13-sdfp-001-b-design`, starting from the Packet commit.

This Artifact is evidence, not absolute authority. It does not approve a
handoff, grant implementation authority, start execution, evaluate B or C,
authorize shell or Git work, authorize a merge, or support a public claim. A
fresh executor may adapt implementation methods only within section 12. A
material Plan Gap requires `HOLD`; the executor must not silently replace this
design.

The sole evidence used for this design is the frozen Shared Evidence Packet
identified above. No C Shadow Design, other planner output, later commit,
implementation output, or post-freeze PR discussion was used.

## 2. Fixed Purpose

Add a local, read-only, deterministic, fail-closed Guard that determines
whether one explicitly selected repository handoff Artifact is structurally
and semantically sufficient for the receiving AI to know:

1. what it now owns; and
2. how it may safely begin.

The Guard must not merely check that field labels exist. It must detect
material contradiction or ambiguity involving at least:

- Target Layer;
- repository identity or root;
- Current State;
- Current Gate;
- Active Branch;
- Next Authorized Action;
- Completion Line;
- Missing Closure;
- Next Owner;
- what the receiving AI now owns;
- First One Action;
- Do Not Continue Boundary; and
- routine work that must not return to the Decision Owner.

The Guard remains local, read-only against the target handoff, deterministic,
fail-closed, non-permissive under `UNKNOWN`, and safe against echoing untrusted
handoff content. It cannot rewrite a handoff, approve a transfer, or grant
implementation, shell, branch, commit, merge, or other authority.

This purpose is bounded to Handoff Acceptance Guard v0.1. It is not a handoff
roadmap and is not Design / Execution Separation product machinery.

## 3. Fixed Completion Line

This design does not replace or abbreviate the Packet's experiment Completion
Line. V13-SDFP-001 is complete only when all of the following later conditions
are established:

1. B and C receive the exact frozen Shared Evidence Packet.
2. C remains hidden from the B executor.
3. B Design is executed by a fresh Codex executor.
4. Required handoff structure and semantic contradictions are testable.
5. False-ready, false-incomplete, malformed, `UNKNOWN`, and ownership
   ambiguity are covered.
6. Focused and full suites pass.
7. Plan Gaps, deviations, drift, and rework are recorded.
8. B and C predictions are independently compared.
9. Human friction is measured.
10. Shin's voluntary-reuse judgment is recorded.
11. The Draft PR and all routine experiment cleanup are closed without
    returning them to Shin.
12. GPT 13-13 issues the next `GO / HOLD / CAP / BLOCK`.

Freezing this B Design establishes none of those later conditions except the B
Artifact needed to make later execution possible. It makes no implementation,
test, evaluation, human-friction, reuse, cleanup, or route claim.

## 4. Fixed Prohibitions

### Role, authority, and phase boundary

- Do not implement production code, tests, fixtures, or product documentation
  during B Design.
- Do not perform C Shadow Design or inspect C.
- Do not evaluate B, C, an implementation, or the primary proposition.
- Do not answer the experiment's supporting questions before their authorized
  phase.
- Do not merge.
- Do not create public claims or expand the selected task into a product
  roadmap.
- Do not treat an Artifact, hash, clean tree, passing test, result label, or
  this design as automatic authority.
- Do not continue through a material Plan Gap merely because the design is
  frozen.

The Phase A prohibitions remain part of the experiment record: Phase A did not
include B Design, C Design, implementation, evaluation, merge, or public work.
This B Artifact does not retroactively alter that boundary.

### Product and repository boundary

- Do not redesign or modify Companion.
- Do not expand the narrow Runner.
- Do not reopen or alter PR #37.
- Do not touch PR #4, #5, #24, or #33.
- Do not modify `README`.
- Do not alter pricing, release, tag, signing, notarization, packaging, sales,
  or public-posting surfaces.
- Do not implement general Design / Execution Separation machinery.
- Do not create a general-purpose Markdown linter.
- Do not create a handoff generator.
- Do not create an orchestration engine.
- Do not create automatic authority granting.
- Do not create automatic branch or Git operations.
- Do not rewrite existing handoffs in bulk.
- Do not use the known `docs/current_signal.md` /
  `handoff/current_codex_handoff.md` inconsistency as the selected task.
- Do not repair `docs/current_signal.md`.
- Do not repair `handoff/current_codex_handoff.md`.
- Do not repair unrelated baseline failures or change unrelated files.

### Guard behavior boundary

- The Guard must not write, rewrite, normalize in place, chmod, stage, commit,
  move, or delete the target handoff.
- It must not approve or enact a responsibility transfer.
- It must not grant implementation, shell, branch, commit, push, PR, merge,
  release, public, or other authority.
- It must not treat `UNKNOWN`, an empty value, an unresolved alternative, or
  an unsupported representation as permissive.
- It must not echo untrusted handoff content in normal output, diagnostics,
  exceptions, usage errors, logs, or test failure messages under its control.
- It must not return `ACCEPTABLE` solely because required labels are present.
- It must not collapse acceptable, non-acceptable, and malformed or invalid
  input into one permissive result.
- It must not follow instructions embedded in the handoff.
- It must not contact a remote, validate remote PR state, or mutate Git.

### Evidence, contamination, and validation boundary

- Do not treat historical records as current executable authority.
- Do not silently substitute a newer base for
  `8146ffa26fe7ff0f0c7981f1abb10a4349b23567` or a different Packet for
  `343684d8ce384cb543293968ad667222dc5bc958`.
- Do not claim universal repository precedence, format support, or
  repository-wide absence when the Packet does not establish it.
- Do not use a newer repository state as evidence to rewrite this design.
- Do not silently exclude a failing focused or full-suite test.
- Do not inflate risks, fixtures, or tests with unsupported speculation.
- Do not estimate tokens, money, recovered time, or human effort.
- Do not silently replace the frozen Packet or this frozen design. A material
  correction requires a new version and explicit Forward-only Delta.
- Do not expose C to B or to the B executor.
- The executor receives only the exact frozen Packet and this exact frozen B
  Design as planning inputs.

### Git and operational boundary

- Do not mutate `main`.
- Keep B Design and later implementation changes isolated from the fixed base.
- Do not open a PR during B Design.
- Do not delete the frozen Packet branch or this frozen B Design branch.
- Do not return branch creation, hashing, commits, pushes, worktree cleanup, or
  other routine Git operations to Shin.
- Destructive, authority-bearing, irreversible, public, externally
  contacting, prohibited, or effective Seat-threatening behavior requires
  `BLOCK`.

The handoff for this B-planning phase expressly authorizes one narrow external
operation after freeze: push the exact committed
`codex/v13-sdfp-001-b-design` branch if the configured origin is available.
That push is B Design closure, not Guard runtime behavior and not authority for
a later executor to push, open a PR, merge, or contact another system.

## 5. Fixed Rollback Conditions

The named restart identities are:

```text
Exact base:
8146ffa26fe7ff0f0c7981f1abb10a4349b23567

Packet freeze:
343684d8ce384cb543293968ad667222dc5bc958

Packet branch:
codex/v13-sdfp-001-shared-evidence-freeze

B Design branch:
codex/v13-sdfp-001-b-design
```

The later B implementation must be isolated and history-preservingly
revertible to the exact base, the Packet-freeze commit, or the frozen B Design
commit recorded in the B receipt. The Guard itself performs no rollback.

Apply these rollback conditions:

- If Packet, design, base, branch, isolation, or exact change-boundary identity
  cannot be established, stop with `HOLD` before implementation or freeze.
- If the separate control signal authorizing the later executor is absent or
  insufficient, remain stopped; before any authority-bearing action return
  `BLOCK / UNKNOWN`. Artifact identity is necessary but never supplies that
  authority.
- If implementation changes the fixed purpose, Completion Line, prohibitions,
  rollback identities, authorized scope, or contamination boundary, revert
  the out-of-contract isolated change to the frozen B Design restart point and
  return `HOLD` with `EXECUTION_DEVIATION` or `PLAN_GAP`.
- If an accepted case can PASS through label presence alone, unresolved
  `UNKNOWN`, ownership ambiguity, an unresolved closure contradiction, or an
  unsafe content echo, reverse the incomplete implementation change on its
  isolated branch and return `HOLD`; do not weaken the Completion Line.
- If a focused or full-suite regression is caused by unrelated edits, reverse
  those unrelated edits. Do not repair unrelated surfaces under this task.
- If the repository has materially changed such that the Packet-grounded
  integration cannot be implemented without changing the design contract,
  return `HOLD / CHANGED_CONDITION`.
- If correction of the frozen Packet or B Design is required, create an
  explicit new version and Forward-only Delta. Never amend the frozen bytes
  silently.
- No merge is allowed without a separate Shin decision.
- Before destructive, authority-bearing, irreversible, public, externally
  contacting, prohibited, or Seat-threatening action, stop with `BLOCK`
  rather than attempting rollback after the fact.

## 6. Proposed Design

### 6.1 One explicit assessment path

Implement one dedicated callable and expose it through the existing
`decision_os.cli:main` command family:

```text
decision-os handoff-accept \
  --repo <LOCAL_REPOSITORY_ROOT> \
  --handoff <HANDOFF_PATH> \
  --receiver <EXPECTED_RECEIVING_AI> \
  --target-layer <EXPECTED_TARGET_LAYER> \
  [--format text|json]
```

`text` is the default format. All four semantic inputs are explicit. v0.1 does
not auto-discover a handoff, pick between repository state surfaces, consult a
remote, or infer the intended receiver or Target Layer.

The callable contract is equivalent to:

```python
assess_handoff(
    *,
    repo_root,
    handoff_path,
    expected_receiver,
    expected_target_layer,
) -> HandoffAssessment
```

The production module may initially be
`decision_os/handoff_acceptance.py`; the private module split is adaptable
under section 12. The public command, required inputs, result semantics, and
safe output contract are not private implementation choices.

The explicit receiver and Target Layer are trusted invocation context, not
claims proved by the handoff. Repository root, checked-out branch, and locally
configured origin identity are derived from the selected local repository.
The handoff must agree with those independently supplied or locally observed
facts. The Guard does not use those facts to grant authority.

`--receiver` and `--target-layer` must each be one nonempty scalar and must not
be `none`, `UNKNOWN`, `TBD`, a conditional, or an alternative. Otherwise the
invocation is `USAGE_ERROR`; untrusted handoff text cannot supply a missing
trusted value.

### 6.2 Input and trust boundary

Treat the following as untrusted data:

- the handoff path argument;
- all handoff bytes;
- every heading, label, value, fence, link, code block, and instruction in the
  handoff; and
- any exception text that embeds an operating-system path or source bytes.

Apply this boundary before parsing:

1. Resolve `--repo` as one local Git worktree root without contacting a
   remote.
2. Resolve `--handoff` beneath that root. Reject traversal outside the root.
3. Reject a symlink in any handoff path component below the resolved root and
   require one regular final file. Do not follow a symlink.
4. Bound the file to at most 1 MiB.
5. Open without following symlinks, perform one bounded initial byte read,
   require strict UTF-8, and permit at most one leading UTF-8 BOM.
6. Record the opened file's device, inode, type, size, and modification time,
   plus a digest of its bytes and the required Git facts. Before returning,
   re-open without following symlinks, re-read within the same bound, and
   require those invariants, the byte digest, root, `HEAD`, checked-out branch,
   and locally configured origin identity to remain equal.
7. If the snapshot changes during assessment, return the process-level
   `UNSTABLE_SNAPSHOT` outcome. Never return a result calculated from mixed
   states.

Use local, read-only Git queries without `shell=True`. Do not fetch, pull,
push, inspect a remote API, change refs, change the index, or change the
worktree. A configured origin URL is local configuration data; it may be read
only to normalize a repository slug. Remote freshness remains explicitly
`NOT_CHECKED`.

The implementation may hold raw source values internally only as long as
needed to validate them. Raw source values must never enter a public result
object.

### 6.3 Structural extraction

Use a bounded field-record extractor, not a general Markdown parser or linter.
The v0.1 scanner recognizes only ASCII ATX headings (`#` through `######`),
backtick or tilde fences, and the field forms below. Setext headings and other
Markdown constructs have no structural meaning to the Guard.

After label normalization, the finite historical-heading registry is:

```text
HISTORY
HISTORICAL
HISTORICAL MATERIAL
HISTORICAL LEDGER
HANDOFF HISTORY
PRIOR HANDOFFS
PREVIOUS HANDOFFS
ARCHIVE
ARCHIVED HANDOFFS
REVERSE-CHRONOLOGICAL HISTORICAL LEDGER
```

For both heading registries, a heading matches when its normalized title is
the exact registry entry or that entry followed by `:`, a spaced hyphen, or an
em dash and nonempty qualifier; the longest entry wins. The first matching ATX
heading outside a fence begins the historical region;
the entire remainder of the document has `HISTORICAL` provenance. This
whole-tail rule is intentionally conservative and independent of heading
level. Inner historical text calling itself current cannot promote itself.

The finite operative-envelope heading registry is:

```text
HANDOFF
CURRENT HANDOFF
CURRENT CODEX HANDOFF
REPOSITORY HANDOFF
HANDOFF ARTIFACT
RESPONSIBILITY TRANSFER
```

Envelope selection is deterministic:

1. Normalize line endings in memory and find the historical cutoff.
2. Before that cutoff, find ATX headings in the operative-envelope registry.
3. Exactly one such heading selects its Markdown section: from that heading
   through the next heading of equal or smaller numeric level, or the
   historical cutoff.
4. When no operative heading exists, determine the smallest numeric ATX
   heading level present before history. Content before the first heading is
   one root group; each heading at that smallest level begins one group through
   the next heading at that level, and deeper headings remain inside their
   group. If there are no headings, the whole pre-history region is one root
   group.
5. In fallback mode, exactly one group may contain recognized field
   occurrences; that group is the envelope. Zero field-bearing groups is
   `NOT_ACCEPTABLE / UNSUPPORTED_VARIANT`. Two or more are
   `NOT_ACCEPTABLE / CURRENT_RECORD_AMBIGUOUS`; their fields are never merged.
6. With a selected operative heading, any recognized field occurrence outside
   its section but before history also yields
   `NOT_ACCEPTABLE / CURRENT_RECORD_AMBIGUOUS`.
7. Two or more operative-envelope headings always yield
   `NOT_ACCEPTABLE / CURRENT_RECORD_AMBIGUOUS`.

Within the one envelope, both fenced and ordinary fields may contribute to the
same logical record. They are provenance adapters, not competing records.
This permits a fenced state summary plus ordinary ownership/action fields
without permitting a merge across envelopes or history.

A candidate field occurrence has one of these finite forms:

```text
[optional "-", "*", or "+"] [optional Markdown emphasis] Label: value
[optional "-", "*", or "+"] [optional Markdown emphasis] Label:
    one or more value lines
[optional "-", "*", or "+"] [optional Markdown emphasis] Label
    one or more value lines
```

`Label` must resolve exactly through the section 6.4 alias registry.
Markdown emphasis may be balanced `*`, `_`, `**`, `__`, or backticks around
only the label. A block value ends immediately before the next recognized
label, an ATX heading, a matching fence closer, or the envelope end; outer
blank lines are trimmed and internal line/list boundaries are retained. A
fence is a run of at least three identical backticks or tildes and closes only
with the same character and at least the opening length. A fence is a
candidate only when it contains a recognized field occurrence. An unclosed
candidate fence or a recognized label with no value is
`INVALID / MALFORMED_REPRESENTATION`; unrelated code fences are ignored.

Project every occurrence in the envelope to section 6.4. Exact duplicates
with the same normalized value fold once, including duplicates contributed by
different adapters. A same-field disagreement is
`NOT_ACCEPTABLE / FIELD_CONFLICT`. `repository_reference` alone may retain two
typed facets, repository identity and repository root, so both can be checked
conjunctively. Last-value-wins behavior is prohibited.

No label, heading, link, or fenced content is executed. Unrelated Markdown in
the selected envelope is ignored unless it makes a field value or envelope
ambiguous.

### 6.4 Canonical field model

Every supported documentary form projects to these thirteen canonical
semantic fields:

| Canonical field | Accepted v0.1 labels | Required meaning |
|---|---|---|
| `target_layer` | `Target Layer` | The one layer the receiving work targets |
| `repository_reference` | `Repository`, `Repository Identity`, `Repo Root`, `Repository Root` | One locally verifiable repository slug or root, or matching identity-and-root facets |
| `current_state` | `Current State` | One concrete nonterminal, restricted, or closed state |
| `current_gate` | `Current Gate`, `V13 Gate` | One concrete `GO`, `GO UNDER CAP`, `HOLD`, `CAP`, or `BLOCK` directive |
| `active_branch` | `Active Branch` | One concrete local branch, or legal closed-state `none` |
| `next_authorized_action` | `Next Authorized Action` | One bounded action, or legal closed-state `none` |
| `completion_line` | `Completion Line` | A bounded, observable completion predicate and whether it remains open or is met |
| `missing_closure` | `Missing Closure` | Explicit `none` or explicit unresolved closure items |
| `next_owner` | `Next Owner` | Exactly one next actor or legal closed-state `none` |
| `receiving_ownership` | `What You Own Now`, `Receiving AI Owns`, `Receiving Ownership` | Concrete responsibility transferred to the expected receiver, or legal closed-state `none` |
| `first_one_action` | `First One Action`, `First Action` | Exactly one safe starting action, or legal closed-state `none` |
| `do_not_continue_boundary` | `Do Not Continue Boundary`, `Stop Boundary` | An explicit stop/escalation boundary |
| `ai_retained_work` | `Work Not Returned to Decision Owner`, `AI-Retained Work`, `Work Retained by Receiving AI` | Routine work retained by the receiving AI, or legal closed-state `none` |

The table is the complete v0.1 label registry. Fuzzy label matching, arbitrary
synonyms, and a general user-defined schema are out of scope. Label case,
surrounding Markdown emphasis, colon placement, bullets, whitespace, and field
order are not semantic.

The `V13 Gate` label carries an implicit `V13` layer facet. It may project to
`current_gate` only when both `target_layer` and trusted `--target-layer`
normalize to `V13`; otherwise emit `TARGET_LAYER_MISMATCH`.

The required ownership concern is a derived relation, not a label-presence
shortcut. It is proven only by the conjunction of `next_owner`,
`receiving_ownership`, and `ai_retained_work`. A generic `Ownership` label or
actor name alone cannot satisfy it. The `ai_retained_work` slot requires one
of its own accepted labels; a clause embedded in another field is not split or
inferred.

Every canonical field is represented internally as exactly one of:

```text
ABSENT
KNOWN(value)
EXPLICIT_NONE
UNKNOWN
AMBIGUOUS
CONFLICT
```

Only `KNOWN(value)` and a field-legal `EXPLICIT_NONE` can discharge an
obligation. `ABSENT` never defaults to `none`. `UNKNOWN`, even with a reason,
never becomes permissive.

### 6.5 Normalization

Normalization is field-specific and must not erase material meaning:

- Strip Markdown decoration around recognized labels, case-fold labels, and
  collapse label whitespace and hyphen/underscore differences.
- Trim scalar values and normalize their internal horizontal whitespace for
  comparison. Preserve item boundaries in lists.
- Normalize enum tokens without deleting suffixes. `GO UNDER CAP` remains
  distinct from unrestricted `GO`; only the bounded qualified-control suffix
  in section 6.6 may parse, and every other suffix remains visible and fails.
- Normalize a local root with real-path rules and compare it to the selected
  Git top-level.
- Normalize supported local origin forms (`https`, `ssh`, or scp-like) to an
  exact `owner/repository` slug without network access.
- Normalize a branch by removing an optional `refs/heads/` prefix, but retain
  case and every other branch character.
- Normalize receiver identifiers only for surrounding whitespace and
  documentary case. Do not resolve pronouns or infer that `Decision Owner`
  means the expected receiver.
- Recognize unconditional, whole-value `none` only. `none unless ...`,
  `none?`, `none or ...`, empty values, alternatives, and conditional
  statements are not `EXPLICIT_NONE`.
- Recognize explicit unresolved markers such as `UNKNOWN`, `TBD`, `?`,
  alternatives, or undecided placeholders as `UNKNOWN` or `AMBIGUOUS`.
- Preserve negation, conditions, alternatives, actor names, branch tokens,
  action verbs, closure item boundaries, and Completion status through
  normalization.

Normalization must not use an LLM, embeddings, network service, locale,
wall-clock time, random value, or fuzzy similarity. When a value cannot be
classified by the bounded deterministic rules, record `UNKNOWN`; do not guess.

### 6.6 Normative v0.1 proof grammar

The rules in this subsection freeze acceptance semantics. Private parser
mechanics remain adaptable, but an executor may not substitute intuitive
natural-language judgment. This is a closed, non-extensible grammar for the
thirteen v0.1 semantics, not a general document-schema language.

#### Scalar control fields

After whitespace normalization, a State or Gate control value is either an
exact token from its finite table or:

```text
CONTROL_TOKEN [":", spaced "-", or em dash] QUALIFIER
```

`QUALIFIER` is 1–8 semantic-atom words separated by spaces. It normalizes to a
scope atom by joining the words with `_`. It may not contain a registered
State, Gate, action, owner, authority, boundary, `UNKNOWN`, `TBD`, `none`,
negation, condition, alternative, slash, or shell/control token. A qualified
control value is proven only when `do_not_continue_boundary` contains the
exact matching `SCOPE: ATOM` clause and every active receiving-ownership work
item contains that same `scope=ATOM` facet. If both State and Gate are
qualified, their scope atoms must be identical. No qualifier text is ignored.

For example, `GO UNDER CAP — B DESIGN ONLY` projects to Gate
`GO_UNDER_CAP` plus scope `B_DESIGN_ONLY`; it still requires both
`SCOPE: B_DESIGN_ONLY` and `CAP_TO`.

The State control token comes from this mapping:

| Accepted whole value | State class |
|---|---|
| `ACTIVE`, `OPEN`, `IN PROGRESS`, `NOT STARTED`, `READY` | `ACTIVE` |
| `RESTRICTED`, `HOLD`, `BLOCKED`, `CAPPED`, `AWAITING AUTHORIZATION` | `RESTRICTED` |
| `CLOSED`, `COMPLETE`, `COMPLETED` | `CLOSED` |

An unlisted token, nonconforming qualifier, unmatched scope, or bare `FROZEN`
is `UNKNOWN`.

The Gate control token comes from this registry:

| Accepted whole value | Gate class | Continuation class |
|---|---|---|
| `GO` | `GO` | advancing |
| `GO UNDER CAP` | `GO_UNDER_CAP` | advancing and capped |
| `HOLD` | `HOLD` | non-advancing |
| `CAP` | `CAP` | non-advancing |
| `BLOCK` | `BLOCK` | non-advancing |

The longest table token wins before qualifier parsing, so `GO UNDER CAP` is
never parsed as `GO` plus a qualifier. `GO_UNDER_CAP` also requires a
`CAP_TO` boundary clause below.

The allowed state/Gate pairs are:

```text
ACTIVE + GO or GO_UNDER_CAP       -> ACTIVE_TRANSFER candidate
ACTIVE + HOLD, CAP, or BLOCK      -> ACTIVE_TRANSFER candidate limited to a
                                     non-advancing first action
RESTRICTED + HOLD, CAP, or BLOCK  -> ACTIVE_TRANSFER candidate limited to a
                                     non-advancing first action
CLOSED + HOLD, CAP, or BLOCK      -> CLOSED_STATE candidate
```

Every other pair, including `RESTRICTED + GO`, `RESTRICTED + GO_UNDER_CAP`,
and either advancing Gate with `CLOSED`, is `STATE_GATE_CONFLICT`.

`target_layer` must equal the normalized trusted `--target-layer` scalar.
`next_owner` must equal the normalized trusted `--receiver` scalar in an
active transfer. In a closed state it may instead be exact `none`. Pronouns,
lists, slash alternatives, `or`, and generic role substitution do not prove
either equality.

In an active transfer, `active_branch` is one scalar that passes the local
equivalent of `git check-ref-format --branch` and equals the checked-out branch
after the normalization in section 6.5. In a closed state it is exact `none`.
A detached checkout, invalid ref syntax, or alternative branch value cannot
prove the relation.

#### Work and closure claims

A semantic atom is 1–64 ASCII letters, digits, `.`, `_`, or `-`, begins with
an alphanumeric character, and contains no whitespace, slash, `..`, control
character, or shell metacharacter. Atoms compare after ASCII uppercasing. A
work item has the finite form:

```text
- [WORK_ID] WORK_KIND; owner=OWNER; subject=ATOM [; scope=ATOM]
```

The bullet is optional for a single item. `WORK_ID` is 1–32 ASCII uppercase
letters, digits, `_`, or `-`, beginning with a letter; comparison is
case-insensitive. The finite `WORK_KIND` registry is:

```text
INVESTIGATION
IMPLEMENTATION
VALIDATION
TEST
REVIEW
GIT
CLEANUP
DOCUMENTATION
DECISION
AUTHORITY
```

The first eight kinds are routine AI work. `DECISION` and `AUTHORITY` are
Decision Owner items and are never receiving-AI authority.

`OWNER` is exactly `RECEIVER` or `DECISION_OWNER`. `RECEIVER` denotes the
trusted `--receiver`; it is not copied from handoff prose. Both owner tokens
parse, then the kind/owner relation is checked: a routine item with
`DECISION_OWNER` is `ROUTINE_WORK_RETURNED`; a `DECISION` or `AUTHORITY` item
with `RECEIVER` is `OWNER_MISMATCH`. No actor assignment may appear outside
this facet.

`missing_closure` is either exact unconditional `none` or one or more work
items. `receiving_ownership` is one or more work items in an active transfer
and exact `none` in a closed state. Every receiving-ownership item must use
`owner=RECEIVER` and a routine kind; another parsed combination is
`OWNER_MISMATCH` in addition to any routine-return issue. `ai_retained_work`
is:

```text
RETAIN: WORK_ID[, WORK_ID ...]
```

In a closed state, `ai_retained_work` is exact `none`. In an active transfer,
every routine Missing Closure ID must occur identically in receiving
ownership, and every routine ID in either Missing Closure or receiving
ownership must occur in `RETAIN`. A `DECISION` or `AUTHORITY` closure item
uses `owner=DECISION_OWNER` and remains outside `RETAIN`, subject to the
action relation below. Reusing one ID with different kind, owner, or subject
or scope is `FIELD_CONFLICT`. When a State or Gate qualifier establishes a
scope atom, every receiving-ownership item must carry the identical `scope=`
facet; otherwise the qualifier relation is `FIELD_UNKNOWN`.

#### Actions and exact containment

An action has one finite form:

```text
ACTION_TOKEN [WORK_ID[, WORK_ID ...]]
    [; closure=WORK_ID[, WORK_ID ...]]
    [; branch=BRANCH]
```

The finite mapping is:

| Action class | Accepted `ACTION_TOKEN` values |
|---|---|
| `OBSERVE` | `READ`, `INSPECT`, `VERIFY`, `VALIDATE`, `COMPARE`, `CALCULATE` |
| `REPORT` | `REPORT`, `RETURN` |
| `LOCAL_CHANGE` | `IMPLEMENT`, `ADD`, `CREATE`, `EDIT`, `MODIFY`, `REMOVE` |
| `TEST` | `TEST`, `RUN` |
| `GIT_LOCAL` | `BRANCH`, `SWITCH`, `CHECKOUT`, `STAGE`, `COMMIT` |
| `EXTERNAL` | `FETCH`, `PULL`, `PUSH`, `OPEN_PR`, `SEND`, `DEPLOY` |
| `IRREVERSIBLE` | `MERGE`, `RELEASE`, `PUBLISH`, `DELETE`, `RESET`, `FORCE_PUSH` |
| `STOP` | `STOP`, `WAIT`, `HOLD` |

At least one primary Work ID is required in every active action. Tokens are
compared case-insensitively; underscores and hyphens are equivalent only
inside a registered action token. An unlisted token, missing ID, duplicate
facet, extra text, or unconsumed character is `FIELD_UNKNOWN`. Alternatives
are `FIELD_AMBIGUOUS`.

An action signature is:

```text
(action class, registered leading token, ordered WORK_ID tuple,
 ordered closure-ID tuple, optional normalized branch)
```

`next_authorized_action` and `first_one_action` each contain exactly one
unnumbered action. Containment is proven only when their signatures are
identical. A list, second action, looser paraphrase, substring, token subset,
or inferred “strict first step” is `ACTION_RELATION_UNPROVEN`.

Every First One Action work ID must occur in `receiving_ownership`. If Missing
Closure is nonempty, the First One Action must name at least one exact Missing
Closure ID in its `closure=` facet. A routine closure ID also remains subject
to the receiving-ownership/retention rule. A `DECISION` or `AUTHORITY` item
owned by `DECISION_OWNER` may appear in `closure=` without becoming a primary
owned Work ID only when the action class is `OBSERVE`, `REPORT`, or `STOP`.
Any explicit action branch must equal `active_branch`.

The Gate/action matrix is:

| Gate class | First-action classes that can prove consistency |
|---|---|
| `GO` | `OBSERVE`, `REPORT`, `LOCAL_CHANGE`, `TEST`, `GIT_LOCAL` |
| `GO_UNDER_CAP` | the same classes, restricted by `CAP_TO` |
| `HOLD`, `CAP`, `BLOCK` | `OBSERVE`, `REPORT`, `STOP` |
| closed state | exact `none` only |

Each primary action Work ID must also have a compatible receiving-ownership
kind:

| Action class | Compatible `WORK_KIND` values |
|---|---|
| `OBSERVE` | `INVESTIGATION`, `VALIDATION`, `REVIEW` |
| `REPORT` | `DOCUMENTATION`, `REVIEW` |
| `LOCAL_CHANGE` | `IMPLEMENTATION`, `CLEANUP`, `DOCUMENTATION` |
| `TEST` | `TEST`, `VALIDATION` |
| `GIT_LOCAL` | `GIT`, `CLEANUP` |
| `STOP` | any registered kind |

An incompatible pair is `ACTION_RELATION_UNPROVEN`.

`EXTERNAL` and `IRREVERSIBLE` never qualify as the safe First One Action in
v0.1. This is an acceptance-boundary rule, not a claim that another actor
lacks authority. The grammar has no ignored action prose.

#### Completion predicates

`completion_line` must use exactly one status marker followed by one or more
predicate items:

```text
OPEN:
- [PREDICATE_ID] WITNESS_KIND; subject=ATOM; expected=ATOM

MET:
- [PREDICATE_ID] WITNESS_KIND; subject=ATOM; expected=ATOM
```

`PREDICATE_ID` follows the Work ID grammar. The finite `WITNESS_KIND` registry
is:

```text
FILE
GIT
COMMAND
TEST
RESULT
RECEIPT
REVIEW
CLEANUP
DECISION
```

This structure makes the Completion Line bounded and observable without
asking the Guard to prove the condition's factual truth. `OPEN` is required
for an active transfer. `MET` is required for a closed state. `MET` with
nonempty Missing Closure or routine work is
`COMPLETION_CLOSURE_CONFLICT`.

Across every proof-bearing value, the grammar must consume the entire value.
No summary, description, object, comment, second action, conditional,
alternative, actor assignment, authority claim, shell/control separator, or
other semantic tail is ignored. Any nonempty unconsumed material is
`FIELD_UNKNOWN`; a parsed alternative is `FIELD_AMBIGUOUS`; two parsed claims
that disagree are `FIELD_CONFLICT`.

#### Boundary predicates

`do_not_continue_boundary` contains one or more of these finite clauses:

```text
PROHIBIT: ACTION_CLASS[, ACTION_CLASS ...]
STOP_BEFORE: ACTION_CLASS[, ACTION_CLASS ...]
REQUIRE_SEPARATE_AUTHORITY_BEFORE: ACTION_CLASS[, ACTION_CLASS ...]
CAP_TO: WORK_ID[, WORK_ID ...]
SCOPE: ATOM
REQUIRE_NEW_GATE
```

`ACTION_CLASS` is one of the eight classes in the action table. A first-action
class named by `PROHIBIT`, `STOP_BEFORE`, or
`REQUIRE_SEPARATE_AUTHORITY_BEFORE` creates `BOUNDARY_CONFLICT`; the Guard
does not infer that the requirement has been met. Under `GO_UNDER_CAP`, every
First One Action work ID must occur in `CAP_TO`. A closed state requires
`REQUIRE_NEW_GATE` or a prohibition covering every advancing class.
`SCOPE` has proof force only for the qualified State/Gate relation above and
must occur at most once. It is supplemental and never by itself satisfies the
Do Not Continue Boundary. Every active or closed record requires at least one
operative clause: `PROHIBIT`, `STOP_BEFORE`,
`REQUIRE_SEPARATE_AUTHORITY_BEFORE`, `CAP_TO` under `GO_UNDER_CAP`, or
`REQUIRE_NEW_GATE`. The exact advancing-class set for the closed prohibition
alternative is `LOCAL_CHANGE`, `TEST`, `GIT_LOCAL`, `EXTERNAL`, and
`IRREVERSIBLE`. `CAP_TO` outside `GO_UNDER_CAP`, `REQUIRE_NEW_GATE` outside a
closed state, `SCOPE` without a qualified State or Gate, or a `SCOPE`-only
value is `FIELD_UNKNOWN`.

All identifier references are closed over the canonical record:

- every `RETAIN` ID resolves exactly once to a routine
  receiving-ownership item;
- every action `closure=` ID resolves exactly once to a Missing Closure item;
- every `CAP_TO` ID resolves exactly once to a receiving-ownership item and,
  when a scope qualifier exists, that item carries the matching scope; and
- every primary action ID resolves exactly once to receiving ownership, as
  required above.

An undefined or repeated reference is `FIELD_UNKNOWN` during canonical
projection, before dependent relation checks.

A well-formed structure outside the section 6.3 adapters is
`NOT_ACCEPTABLE / UNSUPPORTED_VARIANT`. A recognized canonical field whose
value does not parse under this subsection is
`NOT_ACCEPTABLE / FIELD_UNKNOWN`. Two successfully parsed actions whose exact
signatures or required relations do not agree are
`NOT_ACCEPTABLE / ACTION_RELATION_UNPROVEN`. These categories are exclusive
for that failing element; none can become an intuitive PASS. Documentary
layout may vary under section 8; these proof relations do not.

#### Frozen issue-code registry

Artifact assessments use only these issue codes:

```text
INPUT_MISSING
INPUT_OUTSIDE_ROOT
INPUT_SYMLINK
INPUT_NOT_REGULAR
INPUT_TOO_LARGE
INPUT_UNREADABLE
INPUT_INVALID_UTF8
MALFORMED_REPRESENTATION
UNSUPPORTED_VARIANT
CURRENT_RECORD_AMBIGUOUS
REQUIRED_FIELD_ABSENT
FIELD_UNKNOWN
FIELD_AMBIGUOUS
FIELD_CONFLICT
TARGET_LAYER_MISMATCH
REPOSITORY_REFERENCE_UNRESOLVED
REPOSITORY_MISMATCH
STATE_GATE_CONFLICT
ACTIVE_BRANCH_MISMATCH
ACTION_BRANCH_MISMATCH
OWNER_MISMATCH
ROUTINE_WORK_RETURNED
ACTION_RELATION_UNPROVEN
GATE_ACTION_CONFLICT
FIRST_ACTION_NONE_ACTIVE
FIRST_ACTION_UNSAFE
BOUNDARY_CONFLICT
COMPLETION_CLOSURE_CONFLICT
MISSING_CLOSURE_UNASSIGNED
MISSING_CLOSURE_NO_ACTION
CLOSED_STATE_INCOMPLETE
```

Process-only errors use exactly:

```text
USAGE_ERROR
REPOSITORY_CONTEXT_UNAVAILABLE
INTERNAL_ERROR
UNSTABLE_SNAPSHOT
```

Adding or changing a proof marker, mapping, relation, or issue code after
freeze changes acceptance semantics and therefore requires `HOLD`, not an
implementation-method `CONTINUE`.

### 6.7 Semantic validation pipeline

The callable executes fixed stages in this order:

1. validate the local input and stable-snapshot boundary;
2. select the current region;
3. extract exactly one record;
4. project aliases to canonical fields;
5. normalize field values;
6. classify each field state;
7. determine candidate mode (`ACTIVE_TRANSFER` or `CLOSED_STATE`);
8. evaluate all field and cross-field obligations in section 7;
9. collect allowlisted issue codes;
10. fold the assessment using the precedence
    `INVALID` → `NOT_ACCEPTABLE` → `ACCEPTABLE`;
11. render JSON or text from the same safe result object; and
12. recheck input and repository snapshot stability before emitting success.

An input-stage `INVALID` stops before semantic projection and includes only
applicable input or malformed-representation codes. A process-only error emits
no Artifact result. Semantic issue collection occurs only for a stable,
well-formed record.

The validator evaluates internal and local consistency. It does not prove that
the handoff's factual claims are true outside the selected local snapshot, that
a remote is fresh, that a transfer is approved, or that any authority exists.

### 6.8 Determinism

For identical handoff bytes, trusted invocation values, local root identity,
`HEAD`, checked-out branch, and configured local origin, the callable result,
issue ordering, JSON bytes, text bytes, and exit status must be identical.

Use:

- a versioned alias registry;
- a versioned issue-code registry;
- fixed result precedence;
- fixed field order;
- deduplicated issue codes in frozen registry order;
- stable JSON key order and separators;
- one trailing newline;
- no timestamps, durations, locale-sensitive formatting, absolute diagnostic
  paths, random IDs, or raw exception text.

## 7. Semantic Acceptance Model

### 7.1 Result classes and precedence

| Result | Meaning |
|---|---|
| `INVALID` | The selected target cannot be safely and deterministically interpreted as one input record, including unsafe path/type, over-limit bytes, invalid UTF-8, or malformed delimiters or field syntax. |
| `NOT_ACCEPTABLE` | A stable record exists, but a required fact or relation is absent, unresolved, `UNKNOWN`, ambiguous, contradictory, unsupported, or unproven. |
| `ACCEPTABLE` | Every required field has a legal concrete state and every required relation below is proven within the bounded local model. |

`INVALID` takes precedence over `NOT_ACCEPTABLE`, which takes precedence over
`ACCEPTABLE`. A well-formed semantic contradiction is `NOT_ACCEPTABLE`, not
`INVALID`.

This separates:

- structural absence:
  `NOT_ACCEPTABLE / REQUIRED_FIELD_ABSENT`;
- malformed representation:
  `INVALID / MALFORMED_REPRESENTATION`;
- unresolved `UNKNOWN`:
  `NOT_ACCEPTABLE / FIELD_UNKNOWN`;
- semantic contradiction:
  `NOT_ACCEPTABLE` with a specific conflict code;
- valid active transfer:
  `ACCEPTABLE / ACTIVE_TRANSFER`; and
- valid closed state:
  `ACCEPTABLE / CLOSED_STATE`.

### 7.2 Obligations common to both valid modes

Both valid modes require all thirteen canonical semantic slots to be
established from the one current operative record; this does not require
thirteen exact labels. Both modes require:

1. `target_layer` to equal `--target-layer`.
2. `repository_reference` to be locally verifiable. A root must resolve to the
   selected Git top-level. A repository slug must match the normalized locally
   configured origin. If both are supplied, both must match each other and the
   selected repository. Missing local evidence is unresolved, not a guessed
   match.
3. `current_state` to classify concretely as active, restricted, or closed
   through the exact token or bounded qualified-control grammar.
4. `current_gate` to classify as `GO`, `GO UNDER CAP`, `HOLD`, `CAP`, or
   `BLOCK` through that same grammar. A qualifier must prove the matching
   structured scope relation; no Gate suffix is ignored.
5. `completion_line` to satisfy the finite status/predicate grammar in section
   6.6. A bare label, `done`, `looks good`, a hash alone, or an authority claim
   alone is not a Completion Line.
6. `do_not_continue_boundary` to contain at least one operative section 6.6
   boundary clause; supplemental `SCOPE` alone is insufficient. The boundary
   cannot authorize the same action class it prohibits.
7. No required value may be `ABSENT`, `UNKNOWN`, `AMBIGUOUS`, or `CONFLICT`.
8. No current obligation may be satisfied by material from a historical
   region.
9. The expected receiver, Target Layer, repository, state, Gate, branch,
   action, closure, ownership, and boundary relations must be mutually
   consistent.

The semantic implementation uses bounded token classes and exact normalized
relations, not fuzzy prose scoring. When compatibility cannot be proven, the
relation is unresolved and the result is `NOT_ACCEPTABLE`.

### 7.3 Valid active transfer

An `ACTIVE_TRANSFER` is acceptable only when all of these are true:

- `current_state` is explicitly nonterminal or restricted rather than closed.
- `active_branch` names exactly one concrete branch and matches the selected
  local checkout. A detached checkout cannot prove an active-branch match.
- `next_owner` names exactly one actor and matches `--receiver`.
- `receiving_ownership` contains section 6.6 work items assigned to that same
  receiver. Naming only the Decision Owner or Next Owner is not receiving
  ownership.
- `next_authorized_action` and `first_one_action` each contain one section 6.6
  action, not a list, alternatives, or an open-ended program.
- Their signatures are identical. Their Work IDs occur in receiving
  ownership, their optional branch equals `active_branch`, their class passes
  the Gate/action table, and they do not match a prohibiting boundary clause.
  No looser paraphrase or inferred scope relation proves containment.
- Under `GO UNDER CAP`, every First One Action Work ID occurs in `CAP_TO`.
- A first action classified `EXTERNAL` or `IRREVERSIBLE` is not a safe First
  One Action for v0.1. Separate authority cannot be inferred from handoff
  prose.
- If `missing_closure` is `EXPLICIT_NONE`, the record must not describe an
  unresolved closure item elsewhere in the canonical fields.
- If `missing_closure` contains items, every routine Work ID occurs in both
  receiving ownership and AI-retained work, and at least one Missing Closure
  ID occurs in the First One Action's `closure=` facet. A `DECISION` or
  `AUTHORITY` item may remain with the Decision Owner only under the exact
  action-class exception in section 6.6.
- `completion_line` has status `OPEN`.
- `ai_retained_work` cites every routine receiving-ownership Work ID. A vague
  owner label, silence, or transfer of routine cleanup to the Decision Owner
  is insufficient.
- `do_not_continue_boundary` passes the exact action-class and Work-ID checks
  in section 6.6.

Classification describes the text; it grants no permission.

### 7.4 Valid closed state

A `CLOSED_STATE` is acceptable only under this explicit conjunction:

- `current_state` states that the work is closed or complete.
- `current_gate` is `HOLD`, `CAP`, or `BLOCK`; both `GO` and
  `GO UNDER CAP` contradict closure.
- `completion_line` has status `MET` with at least one structured predicate.
- `active_branch` is unconditional `EXPLICIT_NONE`.
- `next_authorized_action` is unconditional `EXPLICIT_NONE`.
- `missing_closure` is unconditional `EXPLICIT_NONE`.
- `first_one_action` is unconditional `EXPLICIT_NONE`.
- `receiving_ownership` and `ai_retained_work` are unconditional closed-state
  `EXPLICIT_NONE`.
- `next_owner` is the expected receiver for a closure handoff, or explicit
  closed-state `none`; it cannot silently substitute the Decision Owner as the
  owner of omitted routine closure.
- `do_not_continue_boundary` contains `REQUIRE_NEW_GATE` or prohibits every
  advancing action class.
- No canonical field describes remaining investigation, validation, branch,
  Git, implementation, or cleanup work.

`none unless ...` never satisfies the closed conjunction. A record with
`First One Action: none` but an active branch, active action, unresolved
Missing Closure, open Completion Line, or remaining routine work is
`NOT_ACCEPTABLE`.

### 7.5 Required contradiction checks

The implementation emits every applicable issue below, then sorts and
deduplicates by the frozen registry order:

| Relation | Issue code |
|---|---|
| Target Layer differs from trusted Target Layer | `TARGET_LAYER_MISMATCH` |
| repository identity/root lacks the local fact needed to compare | `REPOSITORY_REFERENCE_UNRESOLVED` |
| repository identity/root differs locally | `REPOSITORY_MISMATCH` |
| current occurrences disagree for one canonical field | `FIELD_CONFLICT` |
| State/Gate pair is outside the section 6.6 matrix | `STATE_GATE_CONFLICT` |
| concrete Active Branch differs from checkout | `ACTIVE_BRANCH_MISMATCH` |
| an action's explicit branch differs from Active Branch | `ACTION_BRANCH_MISMATCH` |
| Next Owner differs from trusted receiver, or a parsed work item violates the kind/owner matrix | `OWNER_MISMATCH` |
| active First One Action is exact `none` | `FIRST_ACTION_NONE_ACTIVE` |
| First One Action signature does not equal the sole authorized signature or its Work IDs are outside ownership | `ACTION_RELATION_UNPROVEN` |
| Gate/action pair is outside the section 6.6 matrix | `GATE_ACTION_CONFLICT` |
| First One Action is `EXTERNAL` or `IRREVERSIBLE` | `FIRST_ACTION_UNSAFE` |
| First One Action matches a stop-boundary clause or exceeds `CAP_TO` | `BOUNDARY_CONFLICT` |
| `MET` coexists with Missing Closure or routine work | `COMPLETION_CLOSURE_CONFLICT` |
| routine Missing Closure ID is absent from ownership or retained work | `MISSING_CLOSURE_UNASSIGNED` |
| Missing Closure is nonempty but First One Action is `none` or cites no closure ID | `MISSING_CLOSURE_NO_ACTION` |
| any required closed-state conjunct is absent | `CLOSED_STATE_INCOMPLETE` |
| routine work is assigned to the Decision Owner or omitted from AI-retained work | `ROUTINE_WORK_RETURNED` |
| a required value is absent | `REQUIRED_FIELD_ABSENT` |
| a required value is an explicit unknown, conditional `none`, or outside a finite semantic grammar | `FIELD_UNKNOWN` |
| a required scalar/action contains unresolved alternatives | `FIELD_AMBIGUOUS` |

Issue staging is exclusive for each field: absence emits
`REQUIRED_FIELD_ABSENT` and skips value parsing; a present value that fails its
grammar emits only `FIELD_UNKNOWN` or, for parsed alternatives, only
`FIELD_AMBIGUOUS`; relations involving that field are not evaluated. Relation
codes are evaluated only after all participating fields parse successfully.
Multiple independently true relation codes may then coexist and are emitted
in frozen registry order.

The Guard need not prove arbitrary natural-language truth. It must fail closed
when one of these bounded relations cannot be proved.

## 8. Compatibility and Variant Policy

Compatibility is semantic, not template-specific. v0.1 supports bounded
documentary variation through adapters that all project to the same canonical
model.

The finite labels and proof grammar define a bounded v0.1 acceptance profile;
this design does not claim to accept every historical or repository-local
handoff form. A well-formed structure outside the adapters is
`UNSUPPORTED_VARIANT`. A recognized field whose value is meaningful prose but
outside the finite value grammar is `FIELD_UNKNOWN`. False-incomplete
protection applies to the supported meaning-preserving renderings below, not
to unbounded prose equivalence.

Meaning-preserving variation includes:

- fenced or ordinary-Markdown field records;
- recognized direct label equivalents;
- field reordering;
- heading depth;
- bullets;
- label emphasis;
- colon placement;
- line-ending, case, and whitespace variation;
- single-line or bounded multiline values; and
- repository root versus locally verifiable repository slug.

These variations are accepted only when the same current record, canonical
values, and relations remain unambiguous. Tests must include at least two
different supported renderings of the same acceptable active semantics and
two renderings of the same acceptable closed semantics. Their raw bytes may
differ; their canonical result, mode, and issue set must agree.

### Label-only false-ready control

- All required fields must occur in one current operative record.
- Historical fields cannot fill current gaps.
- Presence does not discharge `UNKNOWN`, ambiguity, ownership, action,
  closure, or relation obligations.
- Placeholder values and conditional `none` are non-permissive.
- Cross-field and local-repository relations run after structural extraction.
- The result cannot be `ACCEPTABLE` until every obligation is proven.

### Over-rigid false-incomplete control

- Formatting is separated from semantics.
- Direct aliases project to canonical fields before validation.
- Equivalent scalar, list, root/slug, and active-record forms normalize before
  relation checks.
- Unrelated Markdown style is ignored.
- No prescribed field order or exact heading prose is required.
- Positive compatibility fixtures protect each intentionally supported form.
- A well-formed but unsupported documentary form is
  `NOT_ACCEPTABLE / UNSUPPORTED_VARIANT`, not falsely described as malformed.

This policy does not make the Guard a general Markdown linter. It does not
check spelling, prose quality, arbitrary heading structure, links, tables,
code style, or documents unrelated to the thirteen canonical semantics.

Because the Packet establishes no universal precedence between
`handoff/current_codex_handoff.md` and `docs/current_signal.md`, v0.1 invents
none. It validates only the explicitly selected target plus direct local Git
facts. Adding cross-surface precedence is outside this design.

## 9. Result and Exit Contract

### Machine-readable result

Every completed Artifact assessment emits one JSON object with this stable
shape:

```json
{
  "schema_version": "handoff-acceptance/v0.1",
  "result": "ACCEPTABLE",
  "mode": "ACTIVE_TRANSFER",
  "issue_codes": [],
  "approval_performed": false,
  "authority_granted": false,
  "writes_performed": false,
  "remote_freshness": "NOT_CHECKED"
}
```

`mode` is `ACTIVE_TRANSFER` or `CLOSED_STATE` only for `ACCEPTABLE`; otherwise
it is `null`. `issue_codes` contains only deduplicated identifiers in frozen
registry order. The JSON key order shown above is normative. The other boolean
and freshness fields always preserve the claim boundary.

The JSON contains no raw field value, source excerpt, untrusted path, branch,
owner, action, repository text, parser fragment, exception string, or
traceback.

### Human-readable result

Text is rendered from the same result object in fixed order:

```text
HANDOFF_ACCEPTANCE: ACCEPTABLE
MODE: ACTIVE_TRANSFER
ISSUES: NONE
APPROVAL_PERFORMED: NO
AUTHORITY_GRANTED: NO
WRITES_PERFORMED: NO
REMOTE_FRESHNESS: NOT_CHECKED
```

For non-acceptance, `MODE` is `NONE` and `ISSUES` contains only allowlisted
codes in frozen registry order. It never contains source values or excerpts.

### Exit mapping

| Exit | Outcome |
|---:|---|
| `0` | completed assessment: `ACCEPTABLE` |
| `4` | completed assessment: `NOT_ACCEPTABLE` |
| `5` | completed assessment: `INVALID` |
| `2` | usage error; no Artifact assessment |
| `3` | required local repository context unavailable; no Artifact assessment |
| `6` | internal error; no Artifact assessment |
| `7` | input or repository snapshot changed during assessment; no Artifact assessment |

The input boundary maps exactly as follows:

| Condition | Outcome / code | Exit |
|---|---|---:|
| required CLI option missing, duplicated, or syntactically invalid; invalid `--format` | process `USAGE_ERROR` | `2` |
| path named by `--repo` does not exist, is unreadable as a directory, is not a Git worktree, or is not resolvable to one local top-level | process `REPOSITORY_CONTEXT_UNAVAILABLE` | `3` |
| handoff path missing | `INVALID / INPUT_MISSING` | `5` |
| handoff resolves outside the selected root | `INVALID / INPUT_OUTSIDE_ROOT` | `5` |
| any handoff path component below the root is a symlink | `INVALID / INPUT_SYMLINK` | `5` |
| handoff is not a regular file | `INVALID / INPUT_NOT_REGULAR` | `5` |
| handoff exceeds 1 MiB | `INVALID / INPUT_TOO_LARGE` | `5` |
| initial handoff open/read is denied or fails with a recognized filesystem I/O error | `INVALID / INPUT_UNREADABLE` | `5` |
| handoff bytes are not strict UTF-8 | `INVALID / INPUT_INVALID_UTF8` | `5` |
| candidate fence, field delimiter, or field value is malformed | `INVALID / MALFORMED_REPRESENTATION` | `5` |
| a stable, well-formed structure is outside the supported adapters | `NOT_ACCEPTABLE / UNSUPPORTED_VARIANT` | `4` |
| a recognized field value is outside its finite proof grammar | `NOT_ACCEPTABLE / FIELD_UNKNOWN` | `4` |
| parsed action signatures or required action relations disagree | `NOT_ACCEPTABLE / ACTION_RELATION_UNPROVEN` | `4` |
| re-open, re-read, file identity, digest, root, `HEAD`, branch, or local-origin identity changes after initial capture | process `UNSTABLE_SNAPSHOT` | `7` |
| an unclassified implementation exception occurs | process `INTERNAL_ERROR` | `6` |

Completed Artifact assessments, including `INVALID`, emit the selected JSON or
text result on stdout and emit nothing on stderr. Process-only exits `2`, `3`,
`6`, and `7` emit nothing on stdout and exactly one fixed ASCII line on
stderr, irrespective of `--format`:

```text
HANDOFF_ACCEPTANCE_ERROR: USAGE_ERROR
HANDOFF_ACCEPTANCE_ERROR: REPOSITORY_CONTEXT_UNAVAILABLE
HANDOFF_ACCEPTANCE_ERROR: INTERNAL_ERROR
HANDOFF_ACCEPTANCE_ERROR: UNSTABLE_SNAPSHOT
```

Only the line matching the actual process error is emitted. Argument-parser
defaults must be overridden so they do not echo a supplied path or value.
Unexpected exception text is never printed.

JSON and text must describe the same result and issue set. Callable result,
module entry, repository-local executable, text, JSON, and exit behavior must
remain in parity.

`ACCEPTABLE` means only that the selected bytes satisfy this bounded local
contract. It is not transfer approval, factual truth, remote freshness,
implementation authorization, a Gate change, or a grant of shell or Git
authority. The command has no performative side effect.

## 10. Planned Change Boundary

This is a planned surface, not an immutable file list. The executor may adapt
private placement under section 12 while preserving the exact scope.

### Files likely required

- One new production module, initially proposed as
  `decision_os/handoff_acceptance.py`, containing the input boundary,
  canonical model, adapters, semantic validator, result object, and safe
  renderers.
- `decision_os/cli.py`, only to register and dispatch
  `handoff-accept` through the existing command family.
- One new focused semantic test module, initially proposed as
  `tests/test_decision_os_handoff_acceptance.py`.
- One new focused CLI test module, initially proposed as
  `tests/test_decision_os_handoff_acceptance_cli.py`.
- One new fixture family beneath
  `tests/fixtures/handoff_acceptance_v0_1/`.

### Files optional under executor adaptation

- A small private helper module if separating input safety or rendering makes
  the implementation clearer without creating a framework.
- A new bounded product document such as
  `docs/handoff_acceptance_guard_v0_1.md` if CLI help and module documentation
  cannot fully record the input/result/claim boundary.
- A later validation or execution record required by GPT 13-13 for experiment
  evidence.
- Changes to new test-module or fixture names and organization that preserve
  the same minimum case matrix.

### Prohibited files and surfaces

- `README`;
- `docs/current_signal.md`;
- `handoff/current_codex_handoff.md`;
- Companion and narrow Runner production or test surfaces;
- existing handoffs in bulk;
- release, pricing, tag, signing, notarization, packaging, sales, and public
  surfaces;
- PR #37 and PRs #4, #5, #24, and #33;
- protected v0.1 files when a new path or existing dispatch-only integration
  can satisfy the design;
- `main`; and
- any file unrelated to the Guard's production path, focused tests, fixtures,
  bounded documentation, or required experiment evidence.

The existing `bin/decision-os` and `decision_os.__main__` already route to
`decision_os.cli:main` according to the Packet. They should not need changes.
Do not add a new distribution entry point or dependency.

If an existing protected contract makes the minimal dispatch change
impossible, the executor must return `HOLD`; it must not silently weaken or
rewrite the protected contract.

## 11. Validation Design

Use the smallest matrix that protects the Completion conditions. Tests operate
on temporary repositories and temporary copies; no test mutates a canonical
handoff.

### Required semantic evidence

1. **Acceptable active transfer**
   - One canonical fenced form, one meaning-equivalent ordinary-Markdown form,
     and one form mixing both adapters inside a single operative envelope
     return `ACCEPTABLE / ACTIVE_TRANSFER`.
   - At least one positive form uses the evidenced qualified-Gate style
     `GO UNDER CAP — B DESIGN ONLY` with matching `SCOPE: B_DESIGN_ONLY`,
     scoped work items, and `CAP_TO`.
   - Expected receiver, Target Layer, root or slug, branch, Gate, ownership,
     action, open Completion Line, closure, and boundary relations all agree.

2. **Acceptable closed state**
   - Two meaning-equivalent forms satisfy the complete closed conjunction and
     return `ACCEPTABLE / CLOSED_STATE`.

3. **Label-only false-ready prevention**
   - A fixture contains every label but placeholders, owner substitution, and
     contradictory action/closure values.
   - Separate cases append contradictory text after valid State/Gate tokens,
     add an extra action/control tail, and assign a routine work item to
     `DECISION_OWNER`; no leading safe marker hides the tail.
   - It returns `NOT_ACCEPTABLE`; labels in a historical ledger cannot repair
     it.

4. **False-incomplete prevention**
   - Equivalent formatting, ordering, aliases, bullets, multiline values, and
     root/slug representations project to the same semantic mode and issues.
   - This protects supported variants, not arbitrary Markdown.

5. **Malformed input**
   - Invalid UTF-8, oversized input, symlink/out-of-root input, unterminated
     candidate fence, and an un-tokenizable field record fail closed.
   - Artifact-level malformed cases return `INVALID`; process-boundary cases
     use their fixed exit.

6. **`UNKNOWN`**
   - A table-driven case replaces each decision-bearing canonical value with
     `UNKNOWN`, an empty value, an alternative, or a conditional value.
   - No case returns `ACCEPTABLE`.

7. **Ownership ambiguity**
   - Next Owner alone, two possible owners, owner/receiver mismatch, vague
     receiving ownership, and routine work returned to the Decision Owner each
     return a specific `NOT_ACCEPTABLE` issue.
   - A table-driven reference-integrity case injects an undefined or repeated
     ID into `RETAIN`, `closure=`, and `CAP_TO`; every case fails closed before
     dependent relation checks.

8. **Branch and action contradiction**
   - A recorded branch that differs from the local checkout, an action that
     names another branch, a restricted Gate with a mutating action, and a
     first action outside the authorized action each fail.

9. **Unresolved Missing Closure**
   - Nonempty Missing Closure with `First One Action: none`, a first action
     unrelated to closure, claimed completion, or routine closure assigned
     back to the Decision Owner fails.

10. **Invalid `First One Action: none`**
    - `none` fails in every active mode and passes only with the full closed
      conjunction.
    - `none unless ...` never counts as closed `none`.

11. **Current versus historical**
    - A complete self-described current record inside a historical ledger
      cannot fill an incomplete current record.
    - Two plausible current records fail as ambiguous.

### Required safety and contract evidence

12. **Non-echo**
    - Put a unique sentinel in each raw value, path, malformed fragment, and
      induced operating-system error.
    - Assert the sentinel and raw exception text are absent from stdout,
      stderr, JSON, text, and normal caught error objects for every result and
      process exit.

13. **Read-only behavior**
    - Compare handoff bytes, file type/mode/size/mtime, worktree/index/ref
      digest, and Git status before and after acceptable, non-acceptable,
      invalid, and process-error runs.
    - Those mutation-relevant invariants remain identical. Access time is
      excluded because a read may update it without a Guard write.

14. **Deterministic repetition**
    - Repeat callable, JSON, and text assessments against an unchanged
      snapshot and assert byte-identical outputs, issue order, and exits.
    - Mutating the temporary input during assessment yields exit `7`, never a
      mixed-state result.

15. **CLI/result/exit parity**
    - Assert the callable result, module entry, repository-local executable,
      JSON, text, and exit mapping agree for all three Artifact results and
      process errors.
    - Assert `ACCEPTABLE` still reports no approval, authority, write, or
      remote freshness.

### Suites

The focused suite is the new semantic and CLI modules, plus only an existing
distribution/dispatch test if the minimal CLI registration requires it. The
executor records the exact focused command.

The full suite remains:

```text
python3 -B -m unittest discover -s tests
```

The Packet baseline is 244 / 244 PASS under an environment that permits the
existing localhost-bound Companion tests. A sandbox-denied localhost bind is
an environment issue to record, not permission to omit those tests or modify
Companion.

Do not add a combinatorial synonym suite, Markdown conformance suite, remote
test, performance benchmark, generative fuzzing system, or unrelated
regression test unless a concrete Completion condition cannot otherwise be
protected.

## 12. Adaptable Implementation Methods

The fresh executor may use `CONTINUE` without seeking new approval for an
implementation-method adaptation that leaves purpose, Completion Line,
prohibitions, rollback, authorized scope, evidence boundary, result semantics,
and contamination boundary unchanged.

Allowed adaptations include:

- one module versus a small set of private modules;
- dataclasses, named tuples, or equivalent immutable result structures;
- a line scanner, small state machine, or bounded parser combinators;
- private helper names and boundaries;
- regular expressions versus explicit token loops for the same bounded
  grammar;
- fixture directory and builder organization;
- table-driven versus individually named tests;
- safe local Git queries through an existing helper or argument-vector
  subprocess calls;
- renderer placement;
- the mechanics used to detect a stable file and repository snapshot;
- the exact focused-test command composition; and
- lookup-table, branch, or equivalent mechanics for implementing the frozen
  v0.1 label registry, protected by the required compatibility cases.

The planned private production filename and optional documentation filename
may change under `CONTINUE` if the public command and bounded change surface
remain the same.

The executor may not use `CONTINUE` to change:

- fixed purpose or the Packet's experiment Completion Line;
- result meanings, non-permissive `UNKNOWN`, or result precedence;
- the active and closed semantic obligations;
- no-echo, read-only, deterministic, local, or fail-closed behavior;
- the public authority/approval disclaimer;
- the required explicit receiver, Target Layer, repository, and handoff
  inputs;
- the prohibition on auto-discovery or invented cross-surface precedence;
- authorized repository scope or prohibited files;
- rollback identities;
- C isolation or the executor evidence boundary; or
- any behavior that turns the Guard into generation, orchestration, authority
  automation, Git automation, or a general Markdown linter.

An adaptation that changes which semantic handoffs are accepted, rather than
only how the frozen obligations are implemented, is not a method change. It
requires `HOLD`.

The frozen Deviation Protocol is:

```text
CONTINUE:
An implementation-method adaptation that does not alter purpose, Completion
Line, prohibitions, rollback, authorized scope, or evidence boundary.

HOLD:
A Plan Gap, changed condition, contradiction, validation problem, or scope
question that materially affects correctness or Completion.

BLOCK:
A destructive consequence, irreversible risk, insufficient authority,
prohibited scope, human value judgment, or effective Seat threat.
```

Use the Packet's exact later-event vocabulary:

```text
PLAN_GAP
EXECUTION_DEVIATION
CHANGED_CONDITION
HUMAN_DIRECTION_CHANGE
VALID_FORWARD_ONLY_DELTA
FALSE_COMPLEXITY
REQUEST_OMISSION
REVIEW_ATTRIBUTION_CONFLICT
UNKNOWN
```

The vocabulary classifies a deviation record; it does not by itself authorize
continuation.

## 13. HOLD Conditions

Stop before continuing and return one exact classification plus evidence when:

- the Packet commit, path, blob, SHA-256, design identity, base identity,
  branch isolation, or change boundary does not match;
- absence of C cannot be established before the B executor begins; confirmed
  C exposure is the prohibited condition in section 14;
- repository conditions have materially changed from the Packet in a way that
  affects minimal integration (`CHANGED_CONDITION`);
- a required semantic relation cannot be implemented deterministically from
  the selected target and trusted local context (`PLAN_GAP` or `UNKNOWN`);
- implementation would need a cross-surface precedence rule not established
  by this design (`PLAN_GAP`);
- an executor proposes changing result meaning, public command contract,
  active/closed obligations, no-echo behavior, or acceptance semantics
  (`EXECUTION_DEVIATION`);
- a meaning-preserving repository form cannot be supported without weakening
  false-ready prevention (`PLAN_GAP`);
- the 1 MiB, UTF-8, symlink, stable-snapshot, or local Git boundary conflicts
  with an established required repository convention (`CHANGED_CONDITION`);
- a protected v0.1 identity blocks the minimal integration and no new-path or
  dispatch-only route satisfies the design (`PLAN_GAP`);
- focused or full tests reveal a validation problem, unexplained baseline
  failure, false-ready, false-incomplete, nondeterminism, write, or echo;
- a scope question materially affects correctness or the Completion Line
  (`REQUEST_OMISSION`);
- human direction changes the task (`HUMAN_DIRECTION_CHANGE`); or
- a proposed delta is not demonstrably implementation-only. Classify a
  legitimate additive correction as `VALID_FORWARD_ONLY_DELTA`; otherwise
  keep `HOLD`.

`HOLD` is not permission to ask Shin to perform routine implementation, Git,
validation, or cleanup work.

## 14. BLOCK Conditions

Stop before acting and return `BLOCK` when continuation would require or cause:

- destructive or irreversible behavior;
- a write or rewrite of the target handoff;
- mutation of `main`;
- merge, release, tag, signing, notarization, pricing, sales, or public action;
- remote fetch, push, PR mutation, message, publication, deployment, or other
  external contact not separately authorized for the later phase;
- automatic transfer approval or a grant of implementation, shell, branch,
  commit, merge, or other authority;
- modification of Companion, the narrow Runner, README, the two known
  inconsistent current-state surfaces, named protected PRs, or another
  prohibited surface;
- deletion of the Packet or B Design branches;
- concealment of a failure, silent replacement of a frozen Artifact, or
  contamination through C exposure;
- a human value judgment made on Shin's behalf;
- returning routine transfer, implementation, validation, Git, or cleanup
  work to Shin in a way that creates an effective Seat threat; or
- any other prohibited, authority-bearing, public, externally contacting, or
  insufficiently reversible condition.

The only exception in this B-planning phase is the exact isolated B Design
branch push explicitly authorized in section 4 and required for this receipt
when the origin is available. That exception expires at B Design closure and
does not authorize Guard runtime network access or later executor Git/PR work.

## 15. Predicted Execution-Stage Issues

Only material predictions grounded in the Packet are recorded.

### B-P01 — Current and historical record confusion

- **Predicted issue:** A simple whole-document field search will find a
  complete historical example and may combine it with an incomplete current
  record.
- **Packet evidence:** The current handoff has a top record and a
  reverse-chronological historical ledger; historical sections repeat fields
  and can describe themselves as current. The Packet names label-only
  false-ready and current-versus-historical confusion as known risks.
- **Why material:** This can return `ACCEPTABLE` for a transfer whose current
  ownership or action is absent.
- **Expected observable manifestation:** The historical-ledger negative
  fixture passes, or values from different regions appear in one canonical
  model.
- **Recommended executor response:** `CONTINUE` with the single-current-record
  and historical-provenance design; return `HOLD` if current-region selection
  cannot remain deterministic.

### B-P02 — Direct variants rejected by an exact-template parser

- **Predicted issue:** A parser copied from the current narrow first-fence,
  two-line state parser will reject ordinary-Markdown or direct-label variants
  with the same semantics.
- **Packet evidence:** Repository handoff and restart forms use different
  labels and shapes; the Packet names over-rigid false-incomplete and parser
  ambiguity across formats as known risks.
- **Why material:** A frozen design that accepts only one spelling or layout
  fails the required false-incomplete evidence.
- **Expected observable manifestation:** One of the meaning-equivalent positive
  fixtures returns `REQUIRED_FIELD_ABSENT` or `UNSUPPORTED_VARIANT`.
- **Recommended executor response:** `CONTINUE` by keeping bounded adapters
  separate from the canonical semantic validator; do not expand into a general
  Markdown parser.

### B-P03 — Conditional `none` hides unresolved closure

- **Predicted issue:** Generic truthiness or prefix matching will normalize
  `none unless ...` to closed `none`, allowing an active or incomplete
  handoff to appear closed.
- **Packet evidence:** Whether conditional `none unless ...` counts as closed
  is explicitly `UNKNOWN`; the Packet identifies conditional-none ambiguity
  and unresolved Missing Closure with `First One Action: none`.
- **Why material:** It directly creates false-ready behavior at the Completion
  and ownership boundary.
- **Expected observable manifestation:** A fixture with nonempty Missing
  Closure and conditional or bare `First One Action: none` returns
  `ACCEPTABLE / CLOSED_STATE`.
- **Recommended executor response:** `CONTINUE` using unconditional
  whole-value `none` and the full closed conjunction; unresolved conditional
  forms remain non-acceptable.

### B-P04 — Owner naming substitutes for responsibility transfer

- **Predicted issue:** The implementation will treat a matching `Next Owner`
  as sufficient even when the receiving AI's work and retained routine closure
  are omitted or returned to the Decision Owner.
- **Packet evidence:** The Packet distinguishes information movement from
  responsibility movement and names ownership continuity reduced to memory,
  owner substitution, and AI-owned routine cleanup as risks.
- **Why material:** The receiver still cannot know what it owns or how to
  begin, which defeats the fixed purpose.
- **Expected observable manifestation:** A fixture containing only a matching
  owner and action passes without receiving ownership or AI-retained work.
- **Recommended executor response:** `CONTINUE` with conjunctive owner,
  ownership, first-action, Missing Closure, and retained-work checks.

### B-P05 — Documentary repository or branch state diverges locally

- **Predicted issue:** A structurally complete handoff may name a stale
  repository or branch, while a parser-only validator has no independent
  comparison.
- **Packet evidence:** Existing `check` does not compare textual
  repository/root identity or operational branch with the inspected checkout.
  The Packet observes stale current surfaces and names branch/action
  contradiction as a risk.
- **Why material:** The first action may begin in the wrong repository or
  branch.
- **Expected observable manifestation:** A positive-looking fixture remains
  `ACCEPTABLE` after the temporary repository branch or root identity is
  changed.
- **Recommended executor response:** `CONTINUE` with explicit local root,
  origin-slug, branch, and stable-snapshot relations. Do not repair or use the
  repository's known stale current surfaces as positive fixtures.

### B-P06 — Useful diagnostics leak untrusted content or become nondeterministic

- **Predicted issue:** Parser errors, argument-parser messages, paths, raw
  values, or exception strings will be included for convenience; unordered
  issue collection will change repeated output bytes.
- **Packet evidence:** Untrusted-content echo is a named risk. Existing
  validators intentionally emit stable no-echo results, and existing tests
  cover repeated byte identity.
- **Why material:** Echo violates a fixed prohibition; nondeterminism defeats
  the fixed future behavior.
- **Expected observable manifestation:** A sentinel appears on stdout/stderr or
  two unchanged runs return a different issue order or JSON byte sequence.
- **Recommended executor response:** `CONTINUE` with one allowlisted result
  object, fixed error codes, fixed ordering, and renderers that never receive
  raw source values.

### B-P07 — Minimal CLI integration collides with protected v0.1 contracts

- **Predicted issue:** Registering the command or adding tests may tempt edits
  to protected v0.1 files or a protected identity test may fail.
- **Packet evidence:** The Packet reports a passing protected-v0.1 blob/mode
  guard over fourteen paths, including strict-check code, tests, fixtures,
  `bin/decision-os`, `decision_os/__main__.py`, and a v0.1 document.
- **Why material:** Silently weakening the protected contract would create
  unrelated drift and invalidate a clean full-suite claim.
- **Expected observable manifestation:** The protected identity test fails or
  implementation changes a protected legacy path beyond the minimal dispatch
  surface.
- **Recommended executor response:** `HOLD` if a new production path plus
  dispatch-only integration cannot pass the protected contract. Do not edit
  the guard or protected paths merely to make it green.

## 16. False-Complexity Control

The following are deliberately excluded because they do not improve the fixed
Completion Line:

- a CommonMark-complete parser or general Markdown AST framework;
- a general document-schema language or user-configurable alias system;
- an LLM, embedding model, fuzzy semantic scorer, or network classifier;
- cross-surface precedence between the canonical handoff and current signal;
- repository-wide handoff discovery;
- remote branch, PR, issue, or authority freshness checks;
- a handoff generator, formatter, migration tool, or bulk rewrite;
- an approval workflow, authority engine, policy engine, or orchestration
  service;
- automatic checkout, branch creation, staging, commit, push, PR, merge, or
  rollback;
- a daemon, watcher, cache, database, telemetry, or analytics surface;
- plugins, new dependencies, or a new distribution entry point;
- generalized natural-language truth verification;
- synonym cartesian products, Markdown conformance testing, broad fuzzing,
  performance benchmarking, or test-count maximization;
- repair of the known current-state inconsistency; and
- future format/version architecture not needed by v0.1.

A small bounded parser, canonical model, semantic relation layer, and safe
renderer are sufficient. Complexity that does not protect a named Completion
condition must be classified `FALSE_COMPLEXITY` and omitted.

## 17. Executor Start Contract

The fresh B executor must initially receive only:

1. the exact frozen Shared Evidence Packet at commit
   `343684d8ce384cb543293968ad667222dc5bc958`, blob
   `502ba73f643e8dabf19a2cbeaa06db3c910a32c5`, SHA-256
   `fff0b9b7394749556c7ee94184aebbd304f0b94c10222e8766806f672a8a62f2`;
   and
2. this exact frozen B Design, using the commit, blob, and SHA-256 recorded in
   the B Design receipt.

C must not be present, summarized, hinted, or exposed.

The executor's First One Action is:

> Verify the Packet and B Design commit, path, blob, and SHA-256 identities,
> confirm isolated branch state and no C visibility, and return `HOLD` on any
> mismatch before inspecting implementation surfaces or changing a file.

Passing identity verification is necessary but not sufficient authority.
Remain at `HOLD — B DESIGN FROZEN / AWAIT C SEAL AND EXECUTOR AUTHORIZATION`
until GPT 13-13 separately confirms that C is sealed and authorizes the fresh
B executor. That control signal is not added planning evidence, and C remains
hidden. Only after that separate authorization may the executor inspect
Packet-listed, Design-scoped implementation surfaces, create an isolated
implementation branch from the frozen B Design commit, and proceed under the
Deviation Protocol.

## 18. B Design Completion Line

This B Design is complete and ready for a fresh executor only when:

1. the Packet commit, path, blob, and SHA-256 all verify;
2. C visibility is `NONE`;
3. this file is the only changed file from the Packet commit;
4. sections 1 through 18 preserve the fixed purpose, exact experiment
   Completion Line, applicable prohibitions, rollback identities, local /
   read-only / deterministic / fail-closed behavior, non-permissive
   `UNKNOWN`, safe non-echo, and no-authority boundary;
5. one coherent implementable design defines input, trust, extraction,
   normalization, semantic validation, classification, rendering,
   determinism, callable/CLI integration, compatibility, exits, change scope,
   validation, adaptation, deviations, and executor start;
6. the design distinguishes structural absence, malformed representation,
   unresolved `UNKNOWN`, semantic contradiction, valid active transfer, and
   valid closed state;
7. predictions are Packet-grounded and bounded;
8. no implementation, test, evaluation, merge, public claim, or product
   expansion has begun;
9. `git diff --check` passes;
10. the design is committed on
    `codex/v13-sdfp-001-b-design`, which starts at the Packet commit;
11. the B Design commit, blob SHA, and SHA-256 are recorded in the receipt;
12. the isolated branch is pushed if available and local/remote identity is
    checked; and
13. the worktree and index are clean.

At that point the Gate is:

```text
HOLD — B DESIGN FROZEN / AWAIT C SEAL AND EXECUTOR AUTHORIZATION
```

The next actor is GPT 13-13. No operational cleanup is returned to Shin.
