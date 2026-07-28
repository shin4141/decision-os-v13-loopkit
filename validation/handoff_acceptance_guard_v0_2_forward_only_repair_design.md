# Handoff Acceptance Guard v0.2 — Forward-only Repair Design

## 1. Artifact Identity

- Experiment: `V13-SDFP-001`
- Role: Forward-only Repair Designer
- Design status: `FROZEN`
- Starting commit: `e87ee19f8e6ed014fe74110ece005c7f9b89ffd3`
- Branch: `codex/v13-sdfp-001-forward-only-repair-design`
- Current layer: `V13 — Design / Execution Separation`
- Current gate: `HOLD — FORWARD-ONLY REPAIR DESIGN ONLY`
- Authority: design and evidence preservation only
- Implementation status: `NOT STARTED`
- PR #38 mutation: `NONE`
- C Live: `NOT AUTHORIZED`
- Source transport identity: `UNKNOWN — pasted chat transfer`
- Preserved evaluation:
  `validation/handoff_acceptance_guard_v0_1_independent_evaluation.md`

This design is bound to the frozen Packet, frozen B Design, B execution at the
recorded PR head, and the preserved Independent B/C Evaluation. The evaluation
was received after B execution closure. Its transport did not supply a
pre-transfer digest; its repository identities are recorded only after
preservation. The original C Artifact was neither requested nor inspected in
this phase.

This Artifact authorizes no production edit, test edit, fixture edit, merge,
publication, authority grant, remote claim, or PR mutation. The only files
created in this phase are the preserved evaluation and this design.

## 2. Accepted Route and Findings

The following judgment is fixed and is not reevaluated here:

- Route: `HOLD — FORWARD-ONLY REPAIR DESIGN DELTA`
- MI-09: `PLAN_GAP — closed-state local Git compatibility`
- MI-10: `FALSE_COMPLEXITY + PLAN_GAP — repository-native handoff was
  replaced by an artificial proof language`
- Primary Proposition: `PARTIAL PASS`
- C Unique Material Value: `PRESENT — one material issue`
- C Live: `NOT AUTHORIZED`
- PR #38: `HOLD_FOR_REPAIR`

MI-09 is closed at design level by requiring a locally established canonical
branch, an attached matching checkout, and a clean index and worktree before a
documentary closed state can be mechanically acceptable.

MI-10 is closed at design level by returning to the thirteen repository-native
fields, treating their prose as prose, and routing unprovable meaning to
`NOT_ACCEPTABLE / SEMANTIC_REVIEW_REQUIRED`. No new proof language is required
to manufacture an `ACCEPTABLE` result.

## 3. Repair Objective

The later v0.2 implementation must reconnect Handoff Acceptance to
`docs/handoff_command.md`, close the closed-state local Git false-ready path,
and retain local, read-only, deterministic, fail-closed, non-echo operation.

The repair succeeds only if it:

1. assesses one current repository-native handoff record;
2. proves only relations supported by local bytes, trusted invocation context,
   and local Git;
3. rejects local contradictions and unconditional-`none` violations;
4. declines automatic acceptance when native prose requires interpretation;
5. removes the v0.1 proof-language dependency and its protection-only surface;
6. changes no surface outside the minimal boundary in section 9; and
7. produces the validation evidence in section 10 before merge candidacy.

## 4. Preserved Contract

The repair must preserve:

- local operation with no network access;
- read-only behavior against the handoff, repository, index, refs, and
  worktree;
- deterministic results, issue order, rendering, and exits;
- fail-closed handling, with `UNKNOWN` always non-permissive;
- safe non-echo output containing only allowlisted computed facts;
- no handoff rewrite and no automatic handoff generation;
- no automatic transfer approval and no authority grant;
- no remote freshness claim and no automatic Git action;
- distinct `ACCEPTABLE`, `NOT_ACCEPTABLE`, and `INVALID` outcomes;
- current-operative versus historical separation;
- repository-root and checked-out-branch consistency checks;
- no routine executable work returned to the Decision Owner;
- explicit rollback and contamination evidence; and
- no exposure of the original C Artifact to an executor unless separately
  authorized.

`ACCEPTABLE` means only that the bounded local profile below has no detected
contradiction and all required relations are mechanically established. It does
not establish truth, freshness, permission, transfer approval, or authority.

## 5. Repository-Native Acceptance Profile

### Minimum supported syntax

One current operative record must contain these fields:

1. `Target Layer`
2. `Repo Root`
3. `Current State`
4. `Current Gate`
5. `Active Branch`
6. `Next Authorized Action`
7. `Completion Line`
8. `Missing Closure`
9. `Next Owner`
10. `What the Receiving AI Now Owns`
11. `First One Action`
12. `Do Not Continue Boundary`
13. `What must not be returned to the Decision Owner`

Supported representation is ordinary UTF-8 Markdown: inline or following-line
values, ordinary bullet indentation, optional emphasis/backticks around a
label, and a bounded fenced or unfenced current section. Label matching is
case-insensitive and collapses spaces, hyphens, and underscores.

A small, documented alias registry may cover repository-observed labels such
as `Repository Root`, `Repository`, `V13 Gate`, `Receiving AI Owns`,
`Receiving Ownership`, `What You Own Now`, `First Action`, `Stop Boundary`,
`Work Not Returned to Decision Owner`, and `AI-Retained Work`. Adding an alias
requires a repository-native example and a non-conflict test; fuzzy label
matching is prohibited.

Values remain opaque native prose except for bounded scalar controls,
unconditional `none`, branch/ref comparison, unresolved markers, and
representation normalization. No Work IDs, ontology, key/value action
signature, predicate registry, boundary language, or reference graph is part
of v0.2.

### Current record and duplicates

The parser selects exactly one explicit current operative region using a
bounded heading registry and stops at an explicit historical/archive boundary.
If more than one region can claim current status, the result is
`NOT_ACCEPTABLE / CURRENT_RECORD_AMBIGUOUS`. Historical text cannot provide a
missing current field.

Equivalent duplicates are allowed only after field-appropriate representation
normalization. Conflicting duplicates are `NOT_ACCEPTABLE / FIELD_CONFLICT`.
Every required field must have a nonempty value in the selected region.

### Unresolved and `none` rules

`UNKNOWN`, `TBD`, `?`, unresolved alternatives, and conditional values fail
closed. Detection uses whole tokens or explicit conditional phrases, never
substrings; valid names such as `feature/or-fix` are not alternatives.

Unconditional `none` is the entire normalized scalar `none`. Values such as
`none unless approved`, `none if clean`, `none / later`, and `none or X` are
not `none`.

### Outcome model

- `INVALID`: unsafe or malformed input envelope, including path escape,
  symlink input, non-regular input, size overflow, invalid UTF-8, or malformed
  field representation.
- `NOT_ACCEPTABLE`: missing, unknown, ambiguous, conflicting, locally
  contradicted, incomplete, or semantically unprovable handoff.
- `NOT_ACCEPTABLE / SEMANTIC_REVIEW_REQUIRED`: the native structure is intact
  and no local contradiction was found, but one or more prose relations cannot
  be proven without interpreting meaning.
- `ACCEPTABLE`: every condition in a conservative mechanical profile is
  established. The result grants nothing.

### Mechanically provable relations

The Guard may prove:

- all thirteen fields occur in one selected current record;
- values are present and free of explicit unresolved markers;
- `Target Layer` equals trusted invocation context;
- `Repo Root` names the selected physical repository or its locally configured
  repository identity;
- current control tokens and Gate tokens are a permitted pair;
- active documentary branch equals the attached local checkout branch;
- the closed-state conjunction in section 6 is satisfied;
- `Next Owner` equals the trusted expected receiver where an active transfer
  requires an owner;
- `Next Authorized Action` and `First One Action` are both unconditional
  `none`, or are representation-normalized equal native phrases;
- explicit unresolved `Missing Closure` cannot coexist with a closed transfer;
- duplicate current values do not conflict; and
- historical values did not complete the current record.

For an active transfer, normalized equality proves only that two fields state
the same words. It does not prove that the words are sufficient, safe, or
authorized.

### Conservative automatic profiles

A closed record may be `ACCEPTABLE` only under section 6 and this exact small
profile after case/space/trailing-period normalization:

- Completion Line is `complete`, `completed`, `closed`, `pass`, or `satisfied`;
- `Next Owner`, receiving ownership, and work not returned are each `none`;
- the boundary is `do not continue without a new gate`,
  `new work requires a new gate`, or
  `stop; new work requires a new gate`.

Meaning-preserving closed prose outside that set routes to semantic review,
not false incompletion. Every well-formed active transfer in v0.2 also routes
to `NOT_ACCEPTABLE / SEMANTIC_REVIEW_REQUIRED` after mechanical contradictions
are reported: natural ownership, action safety, Completion, and boundary
sufficiency cannot all be proven without interpreting prose. A future broader
profile requires a separate design decision, not executor adaptation.

Label presence alone can never produce `ACCEPTABLE`.

## 6. Closed-State Local Git Compatibility

### Trusted canonical branch source

Closed-state assessment requires trusted explicit invocation context:
`canonical_branch=<short local branch name>`. A bounded CLI form such as
`--canonical-branch main` may carry it. The value must pass local ref-name
validation and resolve to an existing `refs/heads/<name>`.

The Guard must not guess from the names `main` or `master`, global Git config,
the current branch, a remote call, or a missing/stale remote default. If the
trusted value is absent, invalid, or does not resolve locally, the closed
record is `NOT_ACCEPTABLE / CANONICAL_BRANCH_UNKNOWN`.

### Local observations

Using Git with prompts, optional locks, hooks, and lazy fetch disabled, capture
at both assessment boundaries:

- physical repository root and identity;
- `HEAD` object identity;
- attached branch from local symbolic `HEAD`, or detached state;
- canonical local branch and its resolved tip;
- `git status --porcelain=v1 -z --untracked-files=all`;
- derived index-dirty, worktree-dirty, untracked, and unmerged flags; and
- local origin identity only when needed for `Repo Root`.

Any changed input or repository observation produces the existing separate
`UNSTABLE_SNAPSHOT` process outcome. No cleanup or Git mutation is attempted.

### Complete closed conjunction

All of the following are required:

1. `Current State` is exactly `CLOSED`, `COMPLETE`, or `COMPLETED`.
2. `Current Gate` is exactly `HOLD` or `BLOCK`; `GO` and `CAP` are not closed.
3. `Active Branch`, `Next Authorized Action`, `First One Action`, and
   `Missing Closure` are each unconditional `none`.
4. Completion Line is unambiguously terminal under the bounded native profile.
5. No active owner, executable receiving ownership, routine work, `UNKNOWN`,
   conditional, or unresolved alternative remains.
6. `HEAD` is attached to the trusted canonical branch.
7. Actual branch name equals the canonical branch name.
8. `HEAD` equals the resolved canonical local branch tip.
9. Porcelain status is empty: index clean, worktree clean, no untracked files,
   and no unmerged paths.

Expected case routing:

| Documentary/local case | Required route |
|---|---|
| closed + clean attached canonical branch | continue profile evaluation |
| closed + attached feature branch | `NOT_ACCEPTABLE / CLOSED_BRANCH_MISMATCH` |
| closed + dirty worktree or untracked file | `NOT_ACCEPTABLE / WORKTREE_DIRTY` |
| closed + dirty index | `NOT_ACCEPTABLE / INDEX_DIRTY` |
| closed + unmerged path | `NOT_ACCEPTABLE / LOCAL_CHANGES_UNRESOLVED` |
| closed + detached `HEAD` | `NOT_ACCEPTABLE / DETACHED_HEAD` |
| closed + canonical branch unknown | `NOT_ACCEPTABLE / CANONICAL_BRANCH_UNKNOWN` |
| active + documentary branch matches checkout | branch relation passes; semantic profile still applies |

Thus documentary `Active Branch: none` is never substituted for physical Git
evidence.

## 7. Semantic Review Boundary

The Guard uses no LLM, fuzzy score, embedding, remote service, or learned
classifier.

For `What the Receiving AI Now Owns`, `Completion Line`,
`Do Not Continue Boundary`, and
`What must not be returned to the Decision Owner`, it may determine only:

- value presence;
- explicit `UNKNOWN`, conditional, or alternative markers;
- exact unconditional `none`;
- exact bounded terminal, open, stop, and new-gate native variants;
- normalized equality where two native fields repeat the same prose;
- explicit mention that routine work is assigned to the Decision Owner; and
- consistency with mechanically established active versus closed state.

It must not infer unstated ownership, decide whether arbitrary prose is
complete, equate paraphrases, classify work into a new ontology, or decide
whether an action is authorized from its verb. Any relation that needs those
steps is `SEMANTIC_REVIEW_REQUIRED`, not `ACCEPTABLE`.

Known local contradiction has priority over semantic review. For example, an
active documentary branch that disagrees with Git reports the branch mismatch;
semantic uncertainty must not hide it. Conversely, well-formed native prose
outside the small profile is not `INVALID` merely because it differs from a
fixture.

## 8. v0.1 Retain / Remove Matrix

| v0.1 element | Decision | Completion-Line reason |
|---|---|---|
| safe descriptor-based file opening | RETAIN | protects local, read-only input identity |
| path containment, symlink rejection, regular-file checks | RETAIN | protects the selected repository boundary |
| strict UTF-8 and size bound | RETAIN | preserves deterministic invalid-input handling |
| input reread and stable snapshot | RETAIN | prevents stale-byte assessment |
| local Git environment isolation | RETAIN | prevents prompts, locks, hooks, and fetch |
| repository/root/origin comparison | RETAIN, SIMPLIFY | proves local repository consistency |
| current versus historical region selection | RETAIN, SIMPLIFY | prevents historical false-ready |
| deterministic issue ordering and safe result objects | RETAIN | preserves result/exit parity |
| text/JSON non-echo rendering | RETAIN | protects untrusted content |
| process-error separation | RETAIN | keeps unstable/internal failures distinct |
| read-only and mutation tests | RETAIN | proves preserved contract |
| Work Item grammar and Work IDs | REMOVE — `FALSE_COMPLEXITY` | not repository-native |
| Work-kind and owner/subject ontology | REMOVE — `FALSE_COMPLEXITY` | forces invented semantics |
| Action token/signature grammar | REMOVE — `FALSE_COMPLEXITY` | replaces native action prose |
| Completion witness/predicate DSL | REMOVE — `FALSE_COMPLEXITY` | not required by Completion Line |
| Boundary clause DSL | REMOVE — `FALSE_COMPLEXITY` | replaces native boundary prose |
| identifier-reference closure graph | REMOVE — `FALSE_COMPLEXITY` | exists only for the invented language |
| DSL-specific issue staging | REMOVE — `FALSE_COMPLEXITY` | protects artificial dependencies |
| DSL-only tests and fixtures | REPLACE — `FALSE_COMPLEXITY` | do not resemble repository handoffs |

The Independent Evaluation supports each `FALSE_COMPLEXITY` classification.
Retention does not freeze v0.1 private function names or module organization.

## 9. Minimal Change Boundary

The smallest later implementation surface is:

- modify or replace `decision_os/handoff_acceptance.py`;
- adjust only the existing handoff-acceptance CLI parsing needed to carry the
  trusted canonical branch;
- replace artificial v0.1 handoff fixtures with bounded repository-native
  examples;
- replace/focus the handoff semantic and CLI tests;
- add one repair execution record.

The executor may delete private v0.1 machinery made unreachable by this design.
It must not modify README, Companion, the narrow Runner, `current_signal`,
current handoff, packaging, entry points, dependencies, unrelated commands, or
protected contracts. It must not add a generator, orchestrator, authority
automation, distribution surface, or public claim.

## 10. Validation Design

Named completion conditions:

- `RC-01`: repository-native parsing without a proof language;
- `RC-02`: current/history and duplicate integrity;
- `RC-03`: local repository and active-branch consistency;
- `RC-04`: complete closed-state Git conjunction;
- `RC-05`: unconditional `none`, closure, and `UNKNOWN` fail closed;
- `RC-06`: semantic uncertainty routes to review;
- `RC-07`: safe input, non-echo, and read-only behavior;
- `RC-08`: deterministic stable-snapshot and exit/render parity;
- `RC-09`: bounded regression and protected-contract integrity.

Required evidence:

| Test family | Expected protection |
|---|---|
| repository-native active transfer | local relations pass, then `SEMANTIC_REVIEW_REQUIRED` (`RC-01`, `RC-03`, `RC-06`) |
| repository-native closed state | closed native fields are recognized without DSL (`RC-01`, `RC-04`) |
| clean canonical closed state | positive closed conjunction (`RC-04`) |
| stale feature branch, detached HEAD, unknown canonical branch | distinct fail-closed outcomes (`RC-04`) |
| dirty worktree, untracked file, dirty index, unmerged path | distinct local-change outcomes (`RC-04`) |
| active branch mismatch | documentary/local contradiction (`RC-03`) |
| unconditional versus conditional `none` | only exact `none` closes (`RC-05`) |
| unresolved Missing Closure and any `UNKNOWN` | cannot coexist with acceptance (`RC-05`) |
| conflicting duplicate current fields | conflict is not normalized away (`RC-02`) |
| historical complete/current incomplete | history cannot fill current gaps (`RC-02`) |
| native label/layout/fence/bullet variants | same mechanics without false-invalid (`RC-01`) |
| meaningful native paraphrases outside profile | `SEMANTIC_REVIEW_REQUIRED`, not DSL rejection (`RC-06`) |
| safe opening, containment, symlink, UTF-8, size | stable `INVALID` classes (`RC-07`) |
| source values, paths, Git values, exceptions | absent from stdout/stderr in every result (`RC-07`) |
| before/after repository and artifact snapshots | no write by Guard or harness (`RC-07`) |
| repeated stable invocation | byte-identical result and issue order (`RC-08`) |
| input/Git/status mutation during assessment | separate `UNSTABLE_SNAPSHOT` (`RC-08`) |
| API, text, JSON, module, and bin | result/render/exit parity (`RC-08`) |
| focused repaired suite | all `RC-01` through `RC-08` pass (`RC-09`) |
| exact full suite | no repository regression (`RC-09`) |
| existing CLI/scan/distribution regression set | unrelated commands remain stable (`RC-09`) |
| protected contract guard | protected identities and modes remain intact (`RC-09`) |
| `git diff --check` and exact changed-file list | bounded implementation surface (`RC-09`) |

Test count is not a goal. Each case must name at least one `RC-*` condition.
Recorded localhost-bind limitations must be handled as environment evidence,
not by changing Companion or omitting the exact full-suite rerun.

A repaired PR is not a merge candidate until the focused suite, exact full
suite, existing regression set, protected guard, non-echo/read-only checks,
stable repetition, changed-file check, and execution record all pass, and
MI-09/MI-10 are independently confirmed closed.

## 11. Executor Adaptation Authority

`CONTINUE` without returning for approval:

- private module organization and parser mechanics;
- fixture organization and focused test structure;
- result data structures that preserve public semantics and parity;
- equivalent local Git commands that prove the same facts without writes;
- exact issue-code names with one-to-one meaning;
- removal of unreachable v0.1 false-complexity code; and
- bounded CLI mechanics for trusted canonical-branch context.

`CONTINUE` requires preservation of the native field contract, outcomes,
Repair Completion Line, prohibitions, rollback, Git compatibility,
semantic-review boundary, changed-file boundary, and non-echo behavior. It may
not reintroduce a proof language.

`HOLD` is required for a Plan Gap, changed identity/condition, correctness
contradiction, validation failure, scope question, required new field,
ambiguous canonical-branch source, or proposed relaxation of the semantic
review boundary.

`BLOCK` is required for destructive or irreversible action; authority grant;
public or external contact; network access by the Guard; PR #38 mutation
without separate authority; merge; C-live execution; original C Artifact
exposure without authorization; Seat threat; or any prohibited surface.

The fresh executor receives this frozen design and the repository starting
state. The preserved evaluation and original C Artifact are not implementation
inputs unless separately authorized.

## 12. HOLD / BLOCK Conditions

HOLD when:

- a frozen commit, blob, evaluation, branch, or PR identity changes;
- canonical branch or clean state cannot be established locally;
- repository-native fields cannot be selected deterministically;
- a requested acceptance relation requires new semantic machinery;
- validation is incomplete, nondeterministic, or contradictory;
- the smallest implementation boundary is insufficient; or
- Completion, rollback, contamination, or executor authority becomes unclear.

BLOCK when:

- the Guard would write the assessed handoff, index, refs, or worktree during
  assessment;
- a dependency, remote service, LLM, fuzzy classifier, or network lookup is
  introduced into assessment;
- authority, approval, merge, release, publication, outreach, automation, or
  destructive action is attempted;
- PR #38 is changed, marked ready, closed, or merged in this phase;
- the original C Artifact is requested or C Live is started; or
- work would be returned to Shin that an authorized executor can close.

## 13. Rollback

Design-phase rollback anchor is
`e87ee19f8e6ed014fe74110ece005c7f9b89ffd3`. This isolated branch adds only the
preserved evaluation and this design; PR #38 and its branch remain untouched.
Abandoning this branch therefore restores the exact prior repository state
without rewriting any frozen Artifact.

Later repair execution must record its start commit, exact changed files,
opening and closing snapshots, test evidence, commit/blob/SHA-256 identities,
and C-visibility statement. If repair validation fails, preserve the failure
record and restore production/test/fixture surfaces to the recorded execution
start on the repair branch; do not rewrite B evidence or the preserved
evaluation, and do not mutate PR #38 as rollback.

Contamination boundary: this design legitimately incorporates the accepted
post-execution evaluation findings. It does not retroactively alter B. A later
executor must not inspect the original C Artifact and must record any
unplanned exposure as `HOLD — CHANGED CONDITION`.

## 14. Repair Completion Line

MI-09 and MI-10 are closed at design level only when this Artifact:

1. binds acceptance to all thirteen repository-native fields;
2. removes any requirement for the artificial Work, Action, Completion,
   Boundary, and reference-closure languages;
3. routes unprovable native semantics to
   `NOT_ACCEPTABLE / SEMANTIC_REVIEW_REQUIRED`;
4. makes closed acceptance depend on a trusted local canonical branch,
   attached matching checkout, terminal Completion, unconditional `none`
   conjunction, and an entirely clean index/worktree;
5. preserves local/read-only/deterministic/fail-closed/non-echo behavior and
   the no-approval/no-authority boundary;
6. defines the smallest later change and named validation conditions;
7. preserves rollback, contamination separation, executor adaptation, and
   HOLD/BLOCK routing; and
8. remains at or below 500 lines with no implementation begun.

Repair Completion Line: `PASS — one bounded repository-native v0.2 repair
design closes MI-09 and MI-10 at design level without recreating an artificial
proof language; implementation remains unauthorized pending GPT 13-13 review.`
