# External AI Workflow Incident Source Register v0.1

Status: bounded public-source register

Collection As-of: 2026-07-25 JST

Fixed repository base: `26cdc3bc306c8cc27ee54913e696a1abd2a58075`

## Collection boundary

This register contains public GitHub material only. It records 17 primary issue
URLs and three supporting pull-request URLs. Every listed URL returned HTTP
200 at collection time.

GitHub repository, issue number, and GraphQL node ID form the stable identity
when the public API supplied one. Linked pull requests are supporting repair
evidence, not additional incident units. No private, gated, deleted, or
identity-dependent source was collected, and usernames, email addresses, and
unnecessary personal details are omitted.

## Primary source register

| Case | Public repository | Primary source and stable identity | Source date | State at collection | Exact evidence location | Supporting source |
|---|---|---|---|---|---|---|
| `EXT-INC-001` | `openai/codex` | [Issue #7291](https://github.com/openai/codex/issues/7291); `I_kwDOOYsS4c7aVsrQ` | 2025-11-25 | Open | Issue body: “Steps to reproduce” and “What actually happened” | None |
| `EXT-INC-002` | `openai/codex` | [Issue #34828](https://github.com/openai/codex/issues/34828); `I_kwDOOYsS4c8AAAABJzweaQ` | 2026-07-22 | Open | Issue body: “Reproduction,” “Evidence,” “Recovery,” and “Controlled validation” | None |
| `EXT-INC-003` | `openai/codex` | [Issue #26822](https://github.com/openai/codex/issues/26822); `I_kwDOOYsS4c8AAAABEnx38A` | 2026-06-06 | Open | Issue body: reproduction, wait windows, and rollout-reference sections | None |
| `EXT-INC-004` | `google-gemini/gemini-cli` | [Issue #15580](https://github.com/google-gemini/gemini-cli/issues/15580); `I_kwDOObWEYM7gTv1E` | 2025-12-26 | Closed as not planned | Issue body: rebase transcript, destructive reset, and reflog recovery update | None |
| `EXT-INC-005` | `google-gemini/gemini-cli` | [Issue #1504](https://github.com/google-gemini/gemini-cli/issues/1504); `I_kwDOObWEYM69Uck-` | 2025-06-25 | Closed as not planned | Issue body: recursive-deletion command transcript and operator response | None |
| `EXT-INC-006` | `google-gemini/gemini-cli` | [Issue #28036](https://github.com/google-gemini/gemini-cli/issues/28036); `I_kwDOObWEYM8AAAABGCHiUA` | 2026-06-19 | Open | Issue body: resume-only reproduction and version notes | None |
| `EXT-INC-007` | `anthropics/claude-code` | [Issue #64615](https://github.com/anthropics/claude-code/issues/64615); `I_kwDON91aY88AAAABEEIYDQ` | 2026-06-02 | Open | Issue body: “What happened” and “Suggested fix” | None |
| `EXT-INC-008` | `anthropics/claude-code` | [Issue #75861](https://github.com/anthropics/claude-code/issues/75861); `I_kwDON91aY88AAAABII7xmg` | 2026-07-08 | Open | Issue body: “What happened,” “Evidence,” and “Impact” | None |
| `EXT-INC-009` | `anthropics/claude-code` | [Issue #53717](https://github.com/anthropics/claude-code/issues/53717); `I_kwDON91aY88AAAABAkJsZQ` | 2026-04-27 | Open | Issue body: troubleshooting steps and local transcript-file inspection | None |
| `EXT-INC-010` | `anthropics/claude-code` | [Issue #70749](https://github.com/anthropics/claude-code/issues/70749); `I_kwDON91aY88AAAABGpQfFg` | 2026-06-25 | Open | Issue body: “CLASS B — Ephemeral fixes to generated files,” event dated 2026-06-19 | None |
| `EXT-INC-011` | `Aider-AI/aider` | [Issue #3257](https://github.com/Aider-AI/aider/issues/3257); `I_kwDOJhC06c6qNOth` | 2025-02-15 | Open | Issue body: prompt, model edit blocks, and two-file apply receipts | None |
| `EXT-INC-012` | `Aider-AI/aider` | [Issue #4153](https://github.com/Aider-AI/aider/issues/4153); `I_kwDOJhC06c65Q2Z5` | 2025-06-02 | Open | Issue body: full architect/editor transcript and `SearchReplaceNoExactMatch` loop | None |
| `EXT-INC-013` | `OpenHands/OpenHands` | [Issue #12950](https://github.com/OpenHands/OpenHands/issues/12950); `I_kwDOLfkiw87sY1S0` | 2026-02-20 | Closed as not planned | Issue body: “Root cause” and “Concrete example” | None; the cited concrete PR is evidence within the issue |
| `EXT-INC-014` | `RooCodeInc/Roo-Code` | [Issue #12087](https://github.com/RooCodeInc/Roo-Code/issues/12087); `I_kwDONIq5lM78G56c` | 2026-04-09 | Open | Issue body: Task A, Task B, provider-error, rollback, and false-completion sequence | [Draft PR #12090](https://github.com/RooCodeInc/Roo-Code/pull/12090) and [Draft PR #12091](https://github.com/RooCodeInc/Roo-Code/pull/12091) |
| `EXT-INC-015` | `RooCodeInc/Roo-Code` | [Issue #4603](https://github.com/RooCodeInc/Roo-Code/issues/4603); `I_kwDONIq5lM67PbnQ` | 2025-06-12 | Closed as completed | Issue body cancellation sequence and closing comment associating a repair | [Merged PR #4733](https://github.com/RooCodeInc/Roo-Code/pull/4733) |
| `EXT-INC-016` | `RooCodeInc/Roo-Code` | [Issue #113](https://github.com/RooCodeInc/Roo-Code/issues/113); `I_kwDONIq5lM6jU-yx` | 2024-12-14 | Closed as completed; later recurrence comment | Issue body reproduction and out-of-sync error sequence | None |
| `EXT-INC-017` | `cline/cline` | [Issue #679](https://github.com/cline/cline/issues/679); `I_kwDOMSqWwc6czeUw` | 2024-11-02 | Closed | Issue body deletion list and explicit four-hour impact statement | None |

## URL resolution receipt

| URL class | URLs checked | HTTP 200 | Non-200 |
|---|---:|---:|---:|
| Primary issue URLs | 17 | 17 | 0 |
| Supporting pull-request URLs | 3 | 3 | 0 |
| **Total** | **20** | **20** | **0** |

Resolution proves that the public page was reachable at collection time. It
does not independently validate every claim on the page or guarantee future
availability.

## Deduplication register

| Case | Joined or excluded evidence | Deduplication decision |
|---|---|---|
| `EXT-INC-001` | Later comments about failed recovery | Continuing evidence for the same edit-and-revert mechanism |
| `EXT-INC-002` | 115 affected worktrees | One shared-configuration mutation, not 115 incidents |
| `EXT-INC-003` | Initial scout loss and later worker no-result reproduction | One child-result lifecycle mechanism |
| `EXT-INC-004` | 42 lemmas, 10 tests, documentation, and safety fixes | Consequences of one destructive reset |
| `EXT-INC-005` | Potential individual deleted files | Unconfirmed consequences of one deletion boundary |
| `EXT-INC-006` | Reports across four CLI versions | Recurrence of one resumed-session stop mechanism; separate session-file loss excluded |
| `EXT-INC-007` | Workaround and unofficial-patch comments | Same unresolved rewind worldline; no verified restart |
| `EXT-INC-008` | Four deleted agent worktrees | One unauthorized recursive deletion |
| `EXT-INC-009` | Later platform recurrence comments | Supporting evidence for one update-and-transcript-loss worldline |
| `EXT-INC-010` | Roughly five earlier direct-fix cycles and other classes in the source | Only the 2026-06-19 generated-artifact wipe is counted |
| `EXT-INC-011` | Second reproduction with different filenames | Confirmation of one path-binding mechanism |
| `EXT-INC-012` | Three repeated failed delete attempts | One retry-loop worldline |
| `EXT-INC-013` | Concrete pull request cited in the issue | Evidence for one wrong-diff-base completion mechanism |
| `EXT-INC-014` | Two competing draft repair pull requests | Supporting repairs for one provider-error rollback |
| `EXT-INC-015` | Merged atomic-write pull request | Indirect repair evidence for one cancel-and-history-loss event |
| `EXT-INC-016` | Three-to-five retries and a later recurrence comment | One external-modification conflict mechanism |
| `EXT-INC-017` | Multiple deleted project paths | Consequences of one cleanup action |

## Evidence limits

- Public issue authors are treated as observable workflow operators, not as
  evidence about personality, competence, demographics, or mental state.
- `observed` means the public record binds commands, transcript, diff logic, or
  before/after state closely enough to inspect the bounded event. It does not
  mean the collector reproduced the product failure.
- Closed status alone does not prove repair. Draft, merged, stale, completed,
  and not-planned states remain explicit in each record.
- The register contains no population denominator and cannot support a
  prevalence or comparative-risk claim.
