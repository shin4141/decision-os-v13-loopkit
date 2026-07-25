# Incident Corpus Summary v0.1

Extraction As-of: 2026-07-25 JST

Repository base inspected: `6c481a837a2bb36355c6fc2f24e54c1efc555035`

Corpus size: **9 cases in this corpus**

## Result

The extraction produced nine deduplicated cases from repository field notes,
validation evidence, and the existing descriptions of Draft PR #4 and PR #5.
This is a bounded repository sample. It is not a population study and does not
support claims about how often these failures occur elsewhere.

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

## Observed corpus counts

These are case-presence counts. A case contributes at most one count to a class,
even if the source repeats the symptom.

### Evidence class

| Evidence class | Cases |
|---|---:|
| observed | 3 |
| owner-reported | 6 |
| inferred | 0 |
| unknown | 0 |

### Confidence

| Confidence | Cases |
|---|---:|
| high | 6 |
| medium | 3 |
| low | 0 |

### What broke

| Class | Cases in this corpus |
|---|---:|
| Restartability | 3 |
| Seat | 3 |
| Trust | 5 |
| Evidence Chain | 6 |
| Branch Integrity | 3 |
| Time Anchor | 0 |
| Carrier Capacity | 3 |
| Re-entry Capacity | 3 |

### Returned human burden

| Class | Cases in this corpus |
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

Five cases contain at least one source-supported normalized human-burden class.
Four cases leave the normalized burden list empty because the evidence records
agent/evaluator work or remediation but does not attribute a qualifying burden
to the human.

No case explicitly quantifies returned human burden. The roughly 3.5-day
duration in the Entry Window Radar record describes the workflow, not human
burden, and is therefore not copied into `burden_quantity`.

## Direct fact and inference separation

Each JSONL record separates:

- `directly_observed_facts`: statements carried by the repository or PR record;
- `inferences`: taxonomy mappings, provenance-derived dates, or evidence limits.

The CSV preserves the required incident fields, including evidence class and
confidence. Detailed fact/inference separation remains in the JSONL records.
The normalized what-broke and burden labels are analyst mappings. They do not
replace the source's own diagnosis and are not proposed as Canon.

Dates for V13-INC-002, V13-INC-005, V13-INC-006, and V13-INC-007 come from the
first repository commit containing the source because those notes have no
explicit As-of line. The date basis is explicit in every record.

## Deduplication receipt

- Field Notes 112 and 113 were joined into V13-INC-003.
- The rendered gate-signal miss remained V13-INC-004 because it had a distinct
  trigger, repair, and restart result.
- PR #4 and PR #5 were joined into V13-INC-009.
- PR #4's validator defect remained V13-INC-008 because it had an independent
  correction and passing restart receipt.
- Repeated tutorial-branch steps in Field Note 122 were treated as one incident.

## Missing fields for future cases

Future incident records would be materially stronger with:

1. an explicit As-of date in every source;
2. stable transcript or event identity for the original failure;
3. exact repository, branch, commit, and file identities for both failure and repair;
4. explicit agent/tool identity and which actor performed detection, repair, and validation;
5. an explicit restart test and post-repair result;
6. human-burden attribution separated from agent/evaluator work;
7. burden quantity only when directly measured, including unit and measurement method;
8. a counterfactual or comparison condition when burden reduction is claimed;
9. independent reproduction status;
10. an explicit deduplication key when several notes describe the same worldline.

## Excluded material

The corpus does not count:

- the explicitly labeled README example in `MISTAKEN.md`;
- the local-fix-before-scope-audit near-miss, which lacks a completed failure and
  restart worldline;
- the Completion Line contamination and split-instruction incidents named only
  as excluded material in Field Note 127;
- generic checklists, hypothetical risks, prevented failures, or repeated
  references to an already-counted case.

## Gate

This extraction creates Draft artifacts only.

```text
External public-data collection: HOLD
Canonical rule promotion: BLOCK
README or marketing claim changes: BLOCK
Merge: HOLD
```
