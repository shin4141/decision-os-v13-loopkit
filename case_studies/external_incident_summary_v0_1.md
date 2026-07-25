# External AI Workflow Incident Summary v0.1

Status: bounded public-source extraction

Primary layer: V13 Case-led Adoption

Supporting layer: V14 Resource Justice

Collection As-of: 2026-07-25 JST

Fixed repository base: `26cdc3bc306c8cc27ee54913e696a1abd2a58075`

## Boundary and method

This external corpus contains 17 distinct AI coding-workflow incident
worldlines drawn from public GitHub issues. Each case uses the existing
incident unit:

```text
one trigger
→ one bounded failure mechanism
→ one repair, restart result, or unresolved stop state
```

Cases were selected only when the public record identified a bounded trigger,
failure, and repair or stop state. Repeated reports of the same mechanism,
multiple affected files or worktrees, and linked repair pull requests were
deduplicated into the originating worldline.

The collection does not rewrite the existing nine-case internal corpus. It
does not support a population-frequency, product-quality, comparative-risk,
operator-trait, or marketing claim.

## Source-supported facts

- The corpus contains 17 cases from seven public GitHub repositories.
- All 17 primary URLs and three supporting pull-request URLs returned HTTP 200
  during collection.
- Eight cases contain repository-bound commands, transcripts, diffs, or
  before/after state strong enough for the existing `observed` evidence class.
- Nine cases remain `owner-reported` because the public issue author reports
  the event without a complete independently bound before/after artifact set.
- Two cases contain explicit burden-related quantities: 360 seconds of parent
  wait windows in `EXT-INC-003` and four hours of work reported lost in
  `EXT-INC-017`. These different quantities are not aggregated.

## Analyst mappings

The `what_broke` and `returned_human_burden` classes are analyst mappings from
the public evidence into the existing taxonomy. A mapped class is not a
source-authored diagnosis. Counts below mean only “N cases in this external
corpus.”

Affected artifact counts, worktree counts, language counts, key counts, and
agent retry counts were not converted into human-burden quantities. An
unverified proposed fix or a closed issue was not treated as a successful
restart.

## Source-domain counts

| Source domain | Cases in this external corpus |
|---|---:|
| `github.com` | 17 |
| **Total** | **17** |

## Repository counts

| Public repository | Cases in this external corpus |
|---|---:|
| `anthropics/claude-code` | 4 |
| `google-gemini/gemini-cli` | 3 |
| `openai/codex` | 3 |
| `RooCodeInc/Roo-Code` | 3 |
| `Aider-AI/aider` | 2 |
| `OpenHands/OpenHands` | 1 |
| `cline/cline` | 1 |
| **Total** | **17** |

## Evidence-class counts

| Evidence class | High confidence | Medium confidence | Low confidence | Cases in this external corpus |
|---|---:|---:|---:|---:|
| observed | 8 | 0 | 0 | 8 |
| owner-reported | 5 | 4 | 0 | 9 |
| inferred | 0 | 0 | 0 | 0 |
| unknown | 0 | 0 | 0 | 0 |
| **Total** | **13** | **4** | **0** | **17** |

This table is visual-ready for an evidence-strength chart. Confidence refers
to the bounded case record, not to the frequency of its pattern.

## What-broke counts

| What-broke class | Cases in this external corpus |
|---|---:|
| Evidence Chain | 15 |
| Restartability | 11 |
| Trust | 10 |
| Re-entry Capacity | 6 |
| Branch Integrity | 4 |
| Carrier Capacity | 4 |
| Seat | 4 |
| Time Anchor | 0 |

This table is visual-ready for a what-broke bar chart. One case may map to more
than one class, so column counts do not sum to 17.

## Returned-human-burden counts

| Returned-burden class | Cases in this external corpus |
|---|---:|
| Revalidation | 11 |
| Manual cleanup | 6 |
| Context reconstruction | 4 |
| Decision repetition | 2 |
| Lost session | 2 |
| Rollback | 2 |
| Re-explanation | 1 |
| Rereading | 0 |
| Branch comparison | 0 |
| Retesting | 0 |

This table is visual-ready for a returned-burden bar chart. The counts are
case-presence counts, not burden magnitude, and a case may map to more than one
class.

## Workflow types represented by at least two cases

| Observable workflow type | Cases in this external corpus |
|---|---:|
| Session continuity and resume | 4 |
| Structured edit application | 3 |
| IDE file editing and recovery | 2 |
| Multi-worktree repository orchestration | 2 |
| Repository shell mutation | 2 |

Four other workflow types have one case each: automated PR follow-up,
generated-artifact maintenance, multi-agent delegation, and session rollback
and recovery. These counts describe this selected external corpus only.

## Workflow type × incident type matrix

| Observable workflow type | Restartability | Seat | Trust | Evidence Chain | Branch Integrity | Time Anchor | Carrier Capacity | Re-entry Capacity | Cases |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| IDE file editing and recovery | 1 | 1 | 2 | 2 | 0 | 0 | 0 | 0 | 2 |
| Multi-worktree repository orchestration | 1 | 1 | 1 | 2 | 2 | 0 | 0 | 1 | 2 |
| Multi-agent delegation | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 |
| Repository shell mutation | 1 | 0 | 2 | 2 | 1 | 0 | 0 | 0 | 2 |
| Session continuity and resume | 3 | 0 | 1 | 3 | 0 | 0 | 1 | 4 | 4 |
| Session rollback and recovery | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| Generated-artifact maintenance | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 1 |
| Structured edit application | 2 | 0 | 1 | 3 | 0 | 0 | 2 | 0 | 3 |
| Automated PR follow-up | 1 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| **Total class assignments** | **11** | **4** | **10** | **15** | **4** | **0** | **4** | **6** | **17** |

This matrix is visual-ready. Each cell counts cases in this external corpus
with both the row workflow type and column analyst mapping.

## Unresolved evidence gaps

The following data would be required before any public frequency or prevalence
claim:

- a declared sampling frame and denominator, including exposure by tool,
  version, platform, repository size, and workflow duration;
- a reproducible search protocol that includes closed, transferred, duplicate,
  and privately reported cases without double counting;
- independent confirmation of owner-reported incidents and a stable severity
  rubric;
- comparable before/after evidence for proposed repairs and post-fix
  recurrence;
- consistently measured human time, attention, rollback cost, and recovery
  outcome;
- publication-bias and issue-discoverability estimates;
- stable linkage across cross-posts, mirrors, comments, and repair pull
  requests;
- negative or uneventful workflow observations needed for a denominator.

Within this external corpus, missing repair verification is especially common
for open issues and for issues closed through staleness or an indirectly
associated pull request. That observation is a limitation of these 17 records,
not a claim about the wider population.

## Interpretation boundary

These tables are descriptive outputs for this bounded extraction. A higher
count means only that an analyst mapping occurs in more of the 17 selected
cases. It does not establish real-world prevalence, comparative product risk,
causal importance, or a basis for outreach, marketing, rule promotion, or
automated enforcement.
