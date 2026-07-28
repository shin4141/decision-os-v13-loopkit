# Handoff Acceptance Guard v0.2 Repair Execution

## 1. Execution Identity

- Experiment: `V13-SDFP-001`
- Role: Codex 13-20, v0.2 Repair Executor
- Canonical repository: `shin4141/decision-os-v13-loopkit`
- Implementation branch:
  `codex/v13-sdfp-001-v0-2-repair-execution`
- Starting commit:
  `301bbfdc2d33272f2d58d795c916e5908e5c6995`
- Starting tree: clean, with the branch created directly at the frozen Repair
  Design commit
- Human Voluntary-Reuse Judgment: `YES UNDER CAP`
- Original C visibility: `NONE`
- Preserved Independent B/C Evaluation used: `NO`

The original C Artifact and the preserved Independent B/C Evaluation were not
opened, read, or used as implementation inputs. Only their path-level presence
in the frozen design commit delta was verified.

## 2. Frozen Repair Design Identity

The sole design input verified before implementation:

| Identity | Verified value |
|---|---|
| Commit | `301bbfdc2d33272f2d58d795c916e5908e5c6995` |
| Path | `validation/handoff_acceptance_guard_v0_2_forward_only_repair_design.md` |
| Blob SHA | `aab7d69d64cc03a3a9ffcefe9faa6855757f0bdf` |
| SHA-256 | `5443b2147025f38e03254dffbdffffe366ac61ea31dbff8834e0521af8716053` |
| Line count | `495` |

The design commit's sole parent verified as
`e87ee19f8e6ed014fe74110ece005c7f9b89ffd3`. Its two-path delta verified as:

- `validation/handoff_acceptance_guard_v0_1_independent_evaluation.md`
- `validation/handoff_acceptance_guard_v0_2_forward_only_repair_design.md`

No identity or input-boundary mismatch was found.

## 3. Pre-Execution Repository State

- The implementation branch started at the exact frozen design commit, without
  rebasing or modifying `main`.
- The initial worktree and index were clean.
- The protected v0.1 contract guard passed `1/1`.
- The unrelated CLI, scan, and distribution regression set passed `21/21`.
- The pre-repair full suite discovered `286` tests.
- Focused handoff acceptance coverage contained `42` tests.
- PR #38 was verified `OPEN / DRAFT / NOT MERGED` at
  `e87ee19f8e6ed014fe74110ece005c7f9b89ffd3`; it was not used as the
  implementation branch and was not modified.

## 4. Actual Changed Files

Modified:

- `decision_os/cli.py`
- `decision_os/handoff_acceptance.py`
- `tests/test_decision_os_handoff_acceptance.py`
- `tests/test_decision_os_handoff_acceptance_cli.py`

Deleted:

- `tests/fixtures/handoff_acceptance_v0_1/active_fenced.md`
- `tests/fixtures/handoff_acceptance_v0_1/active_mixed.md`
- `tests/fixtures/handoff_acceptance_v0_1/active_ordinary_cap.md`
- `tests/fixtures/handoff_acceptance_v0_1/closed_fenced.md`
- `tests/fixtures/handoff_acceptance_v0_1/closed_ordinary.md`
- `tests/fixtures/handoff_acceptance_v0_1/current_history_gap.md`
- `tests/fixtures/handoff_acceptance_v0_1/label_only_false_ready.md`

Added:

- `tests/fixtures/handoff_acceptance_v0_2/active_native.md`
- `tests/fixtures/handoff_acceptance_v0_2/active_native_variant.md`
- `tests/fixtures/handoff_acceptance_v0_2/closed_native.md`
- `tests/fixtures/handoff_acceptance_v0_2/closed_native_variant.md`
- `tests/fixtures/handoff_acceptance_v0_2/current_history_gap_native.md`
- `tests/fixtures/handoff_acceptance_v0_2/duplicate_conflict_native.md`
- `tests/fixtures/handoff_acceptance_v0_2/semantic_paraphrase_native.md`
- `validation/handoff_acceptance_guard_v0_2_repair_execution.md`

No README, Companion, narrow Runner, current signal, current handoff, packaging,
entry-point, dependency, protected-contract, distribution, or unrelated
command surface changed. The shared CLI diff is confined to the existing
handoff-acceptance command's trusted canonical-branch option and forwarding.

## 5. Retain / Remove Implementation Matrix

| v0.1 element | Execution result |
|---|---|
| Descriptor-based safe opening | Retained with containment, no-follow, regular-file, strict UTF-8, and size checks |
| Stable input snapshot | Retained through descriptor identity, digest, reread, and end-state comparison |
| Stable repository snapshot | Retained through two local observations and repository/invocation identity comparison |
| Read-only local Git observation | Retained and hardened against prompts, hooks, fetch, optional locks, fsmonitor, filters, hidden index flags, and stalled child processes |
| Current/history separation | Retained and simplified around native operative and historical headings |
| Deterministic issue ordering | Retained through one allowlisted order |
| Non-echo result rendering | Retained for callable, text, JSON, module, bin, and process-error paths |
| Work IDs and Work Item grammar | Removed |
| Work-kind ontology and owner/subject syntax | Removed |
| Action token/signature grammar | Removed |
| Completion witness/predicate language | Removed |
| Boundary clause language | Removed |
| `CAP_TO` and `RETAIN` tokens | Removed |
| Identifier-reference closure graph | Removed |
| DSL-specific issue staging | Removed |
| DSL-only tests and fixtures | Replaced with bounded repository-native cases |

No generator, replacement proof language, fuzzy classifier, LLM, embedding
system, remote service, authority system, or new public surface was introduced.

## 6. Deviation Log

Deviation count: `2`

1. `VALID_FORWARD_ONLY_DELTA-01` — The private v0.1 core was replaced as a
   cohesive native-field implementation instead of being incrementally
   modified. Public result/exit semantics and the retained safety properties
   remain bounded by the frozen design.
2. `VALID_FORWARD_ONLY_DELTA-02` — Local Git observation was hardened during
   adversarial implementation review. Repository-local filters and fsmonitor
   are neutralized, a fixed executable search path and process-group timeout
   are used, hidden index flags and in-progress operations fail closed, and
   gitlinks take a conservative dirty route. These are method-only,
   forward-safe additions to MI-09.

The sandbox's denial of ephemeral localhost binding was an execution
environment limitation explicitly anticipated by the handoff, not a design
deviation. It was preserved as failed-run evidence and resolved by the
authorized equivalent rerun. No `PLAN_GAP`, `CHANGED_CONDITION`,
`EXECUTION_DEVIATION`, `REQUEST_OMISSION`, or `UNKNOWN` remained at closure.

Two review-driven rework loops occurred. The first closed current/history,
read-only-snapshot, and semantic edge coverage. The second closed static local
Git execution vectors and same-size filter mutation coverage. The v0.1 private
core, focused tests, and seven artificial fixtures were rewritten or replaced;
no shipped repair work was discarded after final validation.

## 7. Complexity Before / After

| Measure | Before | After | Delta |
|---|---:|---:|---:|
| Production module, `handoff_acceptance.py` | 2,750 lines | 2,095 lines | -655 |
| Semantic focused test | 1,821 lines | 1,170 lines | -651 |
| CLI focused test | 738 lines | 433 lines | -305 |
| Focused tests combined | 2,559 lines | 1,603 lines | -956 |
| v0.1 fixtures | 7 files / 184 lines | 0 / 0 | -7 / -184 |
| v0.2 native fixtures | 0 / 0 | 7 files / 114 lines | +7 / +114 |

Final branch additions/deletions, including this evidence record:
`+2,497 / -3,883`.

The production reduction removes the artificial proof-language machinery
rather than merely renaming or relocating it. A scan across production, both
focused test modules, and all v0.2 fixtures found zero instances of the ten
removed mechanism families. The new semantic machinery is limited to native
field/heading recognition, conservative closed-value profiles, local
repository relations, and semantic-review routing.

## 8. Failed and Passing Test Progression

1. Pre-repair bounded guards passed: protected `1/1`, unrelated regression
   `21/21`; the exact full suite discovered `286` tests.
2. The first native semantic implementation passed `36/36` focused tests.
3. Callable and CLI parity expansion passed `46/46` focused tests.
4. An intermediate exact full sandbox run discovered `290` tests and produced
   only seven Companion localhost `PermissionError` errors; its authorized
   equivalent rerun passed `290/290`.
5. Review closure progressed through `47/47`, then `65/65`, focused passes.
6. The final focused run passed `66/66` in `97.751s` (`98.01s` wall).
7. The final exact sandbox run ran `310` tests in `147.005s` and failed only
   the same seven unchanged Companion server tests because binding
   `127.0.0.1` was denied (`147.41s` wall; zero assertion failures).
8. Without changing Companion or implementation, the authorized identical
   command passed `310/310` in `165.108s` (`165.45s` wall).

Failures were not omitted or converted into skips.

## 9. Focused, Full, Protected, and Regression Evidence

| Evidence | Command | Result |
|---|---|---|
| Focused repair suite | `python3 -B -m unittest -v tests.test_decision_os_handoff_acceptance tests.test_decision_os_handoff_acceptance_cli` | `66/66 PASS` |
| Exact full suite, sandbox | `python3 -B -m unittest discover -s tests` | `310 run; 7 environment-only bind errors` |
| Exact full suite, authorized equivalent | `python3 -B -m unittest discover -s tests` | `310/310 PASS` |
| Protected contract guard | `python3 -B -m unittest -v tests.test_decision_os_scan_cli.DecisionOsScanCliTest.test_protected_v01_blobs_and_modes_are_unchanged` | `1/1 PASS` |
| Unrelated regression set | `python3 -B -m unittest -v tests.test_decision_os_cli tests.test_decision_os_scan_cli tests.test_decision_os_distribution` | `21/21 PASS` |
| Bounded surface | `git diff --check` | `PASS` |

The focused families map native parsing, duplicate/history integrity, local
repository relations, the complete closed Git conjunction, unconditional
closure, semantic review, safe non-echo/read-only input, and stable parity to
`RC-01` through `RC-08`. The focused/full/regression/protected and changed-file
checks close `RC-09`.

## 10. Non-Echo, Read-Only, and Determinism Evidence

- Non-echo tests cover source values, filesystem paths, Git values, and
  exception text for all assessment and process result classes.
- Callable, text, JSON, module, bin, and exit-code tests establish common
  result/render/exit behavior for `ACCEPTABLE`, `NOT_ACCEPTABLE`, `INVALID`,
  and process errors.
- Before/after byte and metadata snapshots cover the selected artifact,
  repository files, and `.git`; the Guard performs no Git or artifact write.
- Optional locks, hooks, prompts, credential helpers, lazy fetch, fsmonitor,
  configured clean/smudge/process filters, submodule filter paths, hostile
  inherited executable search paths, hidden index flags, and in-progress Git
  operations are covered by adversarial tests.
- Repeated stable invocations are byte-identical. Input, HEAD, branch-tip,
  status, filter, and repository-alias instability route separately to
  `UNSTABLE_SNAPSHOT` or fail closed.
- A blocked FIFO child proves the bounded Git process-group timeout.

Result: `NON-ECHO PASS / READ-ONLY PASS / DETERMINISM PASS`.

## 11. MI-09 Implementation Closure

Closed-state `ACCEPTABLE` now requires the exact conservative documentary
profile plus all local repository relations:

- explicit trusted canonical-branch context;
- the canonical local branch exists;
- attached HEAD on that exact canonical branch;
- HEAD equals the canonical local branch tip;
- clean index and worktree;
- no untracked or unmerged paths;
- exact unconditional `none` for Active Branch, Next Authorized Action, First
  One Action, and Missing Closure;
- terminal Completion Line;
- no unresolved ownership, routine work, alternatives, conditions, or
  `UNKNOWN`.

Distinct fail-closed coverage exists for an unknown canonical branch, detached
HEAD, closed-branch mismatch, dirty index, dirty worktree, untracked content,
and unresolved/unmerged state. No network access or default-branch guessing is
used. MI-09 result: `PASS`.

## 12. MI-10 Implementation Closure

The implementation recognizes the frozen repository-native field family and
bounded aliases. Current native content is separated from fenced or historical
content, and conflicting current duplicates are not normalized away.

Structurally valid active prose always remains
`NOT_ACCEPTABLE / SEMANTIC_REVIEW_REQUIRED` after local checks. Meaningful
native prose outside the conservative mechanical closed profile also routes to
semantic review; it is not rejected merely for lacking an invented grammar and
cannot become acceptable through label presence.

The v0.1 artificial mechanisms and their seven fixtures are absent, and no
replacement DSL exists in production, focused tests, or v0.2 fixtures. MI-10
result: `PASS`.

## 13. Claim Boundary

This execution claims only deterministic assessment of one bounded local
artifact and local repository snapshot against the frozen v0.2 design. It does
not claim remote freshness, transfer approval, authority grant, branch
publication, merge safety, semantic truth for active prose, original-C
comparison, product expansion, or a public evaluation result. The Guard does
not fetch, mutate Git, rewrite a handoff, select a default branch, or perform an
authorized action.

PR #38 remains a held independent artifact. This repair has no merge authority,
and a formal independent repair review remains pending.

## 14. Remaining Debt

No required implementation or validation closure remains.

Two bounded, non-permissive limitations are recorded for later reviewers:

- A repository containing an index gitlink is conservatively routed through
  `WORKTREE_DIRTY` so that status cannot invoke an untrusted submodule filter.
  Broader clean-submodule support would require a separate design.
- Stable endpoint comparison does not claim protection against a hostile
  concurrent configuration ABA that is inserted and removed entirely between
  observations. No static repository-config execution vector remains in the
  covered model; stronger hostile-process isolation would require an OS-level
  execution sandbox or a separately designed shadow Git context.

These limitations can only create conservative non-acceptance within the
frozen contract; neither creates a false-ready path in the validated model.

## 15. Restart Point

Restart from the commit containing this record on
`codex/v13-sdfp-001-v0-2-repair-execution`. Verify the record blob, local/remote
branch match, clean worktree/index, the new Draft PR state, and unchanged
`OPEN / DRAFT / NOT MERGED` state of PR #38. GPT 13-13 then authorizes exactly
one independent repair review before any merge decision. Do not mark ready,
merge, enable auto-merge, expose original C, or broaden the claim.
