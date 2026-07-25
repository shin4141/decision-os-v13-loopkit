# Internal Incident Corpus Summary v0.2

Extraction As-of: 2026-07-25 JST

Repository base inspected: `aac2d6c060586abaf9d3c8c521949dd874f2c1c4`

Confirmed corpus size: **10 cases in this internal corpus**

Field Note audit: **126 Field Notes scanned**

Candidate audit: **91 candidate worldlines deep-read**

## Result

Internal Incident Corpus v0.2 preserves the nine v0.1 cases without changing
their meaning and adds one confirmed incident, `V13-INC-010`. The added case is
the third-party fork onboarding worldline recorded in Field Note 085: Codex
understood the repository but summarized it instead of entering the requested
tutorial-menu flow.

This is a bounded internal repository corpus. Counts below describe only these
10 confirmed cases and the 91 audited candidate worldlines. They do not
establish population frequency, comparative prevalence, product reliability,
or a marketing claim.

| Case | Bounded incident | Evidence | Confidence | What broke | Returned human burden |
|---|---|---|---|---|---|
| V13-INC-001 | Internal utility mistaken for public readiness | owner-reported | high | Trust; Evidence Chain | none explicitly mapped |
| V13-INC-002 | Handoff moved information without routine-cleanup ownership | owner-reported | medium | Restartability; Seat; Re-entry Capacity | Re-explanation; Rereading; Context reconstruction; Decision repetition |
| V13-INC-003 | Parked Entry Window Radar loop reopened without a re-entry gate | owner-reported | high | Re-entry Capacity; Restartability; Branch Integrity; Carrier Capacity | Context reconstruction; Decision repetition |
| V13-INC-004 | Rendered README badge overstated the actual gate | observed | high | Trust; Evidence Chain | Revalidation |
| V13-INC-005 | Internal dogfood context reached a public-surface remediation boundary | owner-reported | medium | Trust; Evidence Chain | none explicitly mapped |
| V13-INC-006 | Completion activated a parked tutorial branch without authority | owner-reported | high | Branch Integrity; Seat; Restartability; Carrier Capacity | Rereading; Context reconstruction; Decision repetition |
| V13-INC-007 | Local PIC absence was misrouted as a Human Seat question | owner-reported | medium | Seat; Evidence Chain; Re-entry Capacity; Carrier Capacity | Re-explanation; Context reconstruction; Decision repetition |
| V13-INC-008 | Reversed validator arguments produced a false-positive receipt | observed | high | Evidence Chain; Trust | none explicitly mapped |
| V13-INC-009 | Branch-only intake artifact was treated as default-branch usable | observed | high | Evidence Chain; Branch Integrity; Trust | none explicitly mapped |
| V13-INC-010 | Fork onboarding request returned a repository summary instead of the tutorial menu | owner-reported | medium | Evidence Chain | none explicitly mapped |

## Observed Corpus Counts

All counts are case-presence counts. A case contributes at most once to a class,
even when its sources repeat the symptom.

### Evidence Class

| Evidence class | Confirmed cases |
|---|---:|
| observed | 3 |
| owner-reported | 7 |
| inferred | 0 |
| unknown | 0 |
| **Total** | **10** |

### Confidence

| Confidence | Confirmed cases |
|---|---:|
| high | 6 |
| medium | 4 |
| low | 0 |
| **Total** | **10** |

### What Broke

| Class | Cases in this internal corpus |
|---|---:|
| Restartability | 3 |
| Seat | 3 |
| Trust | 5 |
| Evidence Chain | 7 |
| Branch Integrity | 3 |
| Time Anchor | 0 |
| Carrier Capacity | 3 |
| Re-entry Capacity | 3 |

The only confirmed-count change introduced by `V13-INC-010` is Evidence Chain,
which rises from six cases in v0.1 to seven cases in v0.2.

### Returned Human Burden

| Class | Cases in this internal corpus |
|---|---:|
| Re-explanation | 2 |
| Rereading | 2 |
| Branch comparison | 0 |
| Retesting | 0 |
| Rollback | 0 |
| Manual cleanup | 0 |
| Revalidation | 1 |
| Context reconstruction | 4 |
| Decision repetition | 4 |
| Lost session | 0 |

Five confirmed cases contain at least one source-supported normalized
returned-human-burden class. Five leave the burden list empty because the
sources do not explicitly attribute a qualifying burden to the human. No
confirmed case records a numeric human-burden quantity.

## Candidate Audit Dispositions

The 126-note audit produced 91 deduplicated candidate worldlines. Candidate
discovery was lexical; every candidate was deep-read before classification.
Only `NEW CONFIRMED INCIDENT` records increase the confirmed corpus count.

| Candidate classification | Candidate worldlines | Corpus effect |
|---|---:|---|
| NEW CONFIRMED INCIDENT | 1 | Added as V13-INC-010 |
| DUPLICATE OF EXISTING CASE | 7 | No new case |
| PART OF EXISTING WORLDLINE | 2 | No new case |
| ADDITIONAL EVIDENCE FOR EXISTING CASE | 4 | No new case |
| NEAR-MISS / SUCCESSFUL CONTAINMENT | 11 | Excluded from confirmed incidents |
| CONTROLLED VALIDATION CASE | 26 | Excluded from confirmed incidents |
| GENERAL RISK / HYPOTHESIS | 33 | Excluded from confirmed incidents |
| INSUFFICIENT EVIDENCE | 7 | Excluded from confirmed incidents |
| **Total** | **91** | **1 added case** |

The table separates one confirmed incident candidate from 11 near-misses and 26
controlled validation cases. A prevented failure, a successful validation, or a
plausible risk is not counted as an occurred incident.

## Confirmed Case Source Ranges

The source bands below count each confirmed case once by its primary incident
source.

| Primary source range | Confirmed cases |
|---|---:|
| Field Notes 001–029 | 0 |
| Field Notes 030–059 | 1 |
| Field Notes 060–089 | 1 |
| Field Notes 090–109 | 1 |
| Field Notes 110–127 | 5 |
| PR descriptions without a Field Note primary source | 2 |
| **Total** | **10** |

## Direct Facts and Analyst Inference

The JSONL records keep source-supported facts separate from analyst mappings:

- `directly_observed_facts` preserves statements carried by repository,
  Field Note, handoff, artifact, or PR evidence;
- `inferences` preserves taxonomy mappings, provenance-derived dates, and
  explicit evidence limits;
- `what_broke` and `returned_human_burden` are normalized analyst mappings, not
  source-authored population categories.

For `V13-INC-010`, the sources directly state that Codex summarized the
repository instead of starting the tutorial, that a first-contact onboarding
rule was added, and that no post-fix third-party rerun is recorded. Mapping that
failure to Evidence Chain and using the repair commit date as the As-of date are
analyst decisions kept explicit in the record.

## Deduplication Receipt

- All nine v0.1 case IDs and meanings are preserved.
- Field Notes 112 and 113 remain one parked-loop re-entry case,
  `V13-INC-003`.
- PR #4's validator argument reversal remains separate from the PR #4/#5
  default-branch selection incident because each has an independent trigger,
  failure mechanism, and repair or evaluator result.
- Repeated descriptions of public-readiness, handoff, branch-drift, rendered
  gate, private-context, and lineage incidents do not create additional cases.
- Field Note 085, the current handoff, and `AI_TUTORIAL_CAPSULE.md` describe one
  onboarding worldline and are joined as `V13-INC-010`.
- `V13-INC-010` remains separate from `V13-INC-006`: onboarding failed to enter
  a requested first-response contract, while `V13-INC-006` concerns
  unauthorized completion-to-expansion branch succession.

## Exclusion Boundary

The 90 candidate worldlines not added as new confirmed incidents remain visible
through their classifications and reasons. They are not promoted when they are:

- another description of an existing case or one part of its worldline;
- additional evidence that does not create a distinct trigger and mechanism;
- a near-miss where the unsafe outcome was successfully contained;
- a controlled validation or deliberate test;
- a checklist, general principle, hypothetical risk, or candidate rule;
- missing stable source identity, an occurred failure, a bounded repair or stop,
  or sufficient separation from an existing case.

No exclusion is evidence that a risk is impossible. It means only that the
available repository record does not satisfy the confirmed-incident threshold.

## Evidence Gaps

Future internal incident records would be materially stronger with:

1. an explicit As-of date in every primary source;
2. stable transcript, session, repository, branch, commit, and file identities;
3. exact actor attribution for detection, repair, validation, and restart;
4. direct before/after evidence for the failed and repaired states;
5. an explicit post-repair restart or recurrence check;
6. human-burden attribution separated from agent and evaluator work;
7. quantity, unit, and measurement method when burden is measured;
8. independent reproduction status;
9. an explicit deduplication key for multi-note worldlines;
10. for `V13-INC-010`, the original third-party transcript, original feedback
    date, exact Codex version, and a post-fix third-party rerun.

These gaps prevent public frequency, prevalence, comparative reliability, or
burden-reduction claims.

## Immutability and Scope Boundary

- `incident_corpus_v0_1.jsonl`, `incident_corpus_v0_1.csv`,
  `incident_summary_v0_1.md`, and `incident_taxonomy_v0_1.md` remain the
  immutable v0.1 layer.
- External corpus v0.1 files remain a separate, byte-unchanged corpus. Internal
  and external counts are not combined.
- v0.2 is a successor artifact. It does not rewrite v0.1, silently strengthen
  old evidence, promote canonical rules, or authorize runtime behavior.
- This summary prepares factual Markdown tables only. It creates no image,
  visualization, headline, public copy, or marketing claim.

## Gate

```text
Field Note audit and Draft artifacts: GO
Visualization, public posting, marketing, and outreach: HOLD
README, Canon, Runner, pricing, service, and external corpus changes: BLOCK
Merge: HOLD
```
