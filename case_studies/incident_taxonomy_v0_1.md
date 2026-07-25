# Incident Taxonomy v0.1

Status: extraction-only working taxonomy

Primary layer: V13 Case-led Adoption

Supporting layers: V12 Completion Integrity / V14 Resource Justice

Extraction As-of: 2026-07-25 JST

Repository base inspected: `6c481a837a2bb36355c6fc2f24e54c1efc555035`

## Boundary

This taxonomy normalizes existing repository evidence. It does not promote a
canonical rule, claim population frequency, or authorize automation, runtime
behavior, public-data collection, marketing language, or external action.

The corpus unit is one distinct incident worldline:

```text
one trigger
→ one bounded failure mechanism
→ one repair or unresolved stop state
```

Multiple records that describe the same worldline are one case. Failures inside
the same workflow remain separate only when their trigger, broken surface,
repair, and restart result are independently identifiable.

## Record schema

| Field | Extraction rule |
|---|---|
| `case_id` | Stable corpus identifier; it does not imply chronology beyond this extraction. |
| `source_path` | One or more repository paths or PR descriptions supporting the deduplicated case. |
| `as_of_date` | Explicit source date when available; otherwise the first repository commit or PR date, with the basis stated separately. |
| `observable_operator_workflow_type` | Observable role and workflow only; no operator personality or demographic traits. |
| `agent_tool` | Named agent/tool when the evidence names it; otherwise `not identified`. |
| `repo_workflow_shape` | The bounded repository or workflow topology in which the incident occurred. |
| `trigger` | The event or condition immediately preceding the failure. |
| `observed_failure` | What the source records as having happened. |
| `what_broke` | One or more normalized what-broke classes below. |
| `returned_human_burden` | Zero or more normalized burden classes below. Empty means the evidence did not support a human-burden mapping. |
| `burden_quantity` | A number only when the source explicitly records human burden as time, count, tokens, or another quantity; otherwise `null`. |
| `ai_execution_agent_should_have_owned` | The bounded responsibility the source assigns to the agent. |
| `minimum_repair` | Smallest source-supported repair or safe stop. |
| `restart_result` | Recorded post-repair state; unresolved or untested states remain explicit. |
| `evidence_quote_or_exact_location` | Short quote context or exact path/heading/line location. |
| `evidence_class` | `observed`, `owner-reported`, `inferred`, or `unknown`. |
| `confidence` | `high`, `medium`, or `low`, based on source identity and repair/restart binding. |
| `directly_observed_facts` | Facts stated in the evidence without taxonomy interpretation. |
| `inferences` | Analyst mappings, provenance-derived dates, or stated evidence limits. |
| `deduplication_note` | Why related records were joined or kept separate. |

## What-broke classes

| Class | Operational meaning in this corpus |
|---|---|
| Restartability | The workflow could not safely resume from the recorded completion or pause state. |
| Seat | Judgment or executable ownership was routed to the wrong actor. |
| Trust | A visible claim or validation receipt was stronger than the evidence supported. |
| Evidence Chain | The link from source state through validation to conclusion was missing, reversed, incomplete, or misleading. |
| Branch Integrity | A parked, branch-local, or adjacent line was treated as the authorized active/canonical line. |
| Time Anchor | The failure depended on an absent or invalid As-of/current-state anchor. No case in v0.1 met this threshold. |
| Carrier Capacity | Avoidable context, choice, correction, or routing work consumed finite operator capacity. |
| Re-entry Capacity | The receiving context could not reconnect to the bounded state, lineage, ownership, or safe next action. |

These labels describe the nine cases in this corpus only. They are not
population categories with known prevalence.

## Returned-burden classes

| Class | Evidence threshold |
|---|---|
| Re-explanation | The human had to restate existing intent, meaning, or instructions. |
| Rereading | The human had to re-parse an already available record or completion line. |
| Branch comparison | The human explicitly had to compare competing branches. |
| Retesting | The human explicitly had to rerun a test the agent should have owned. |
| Rollback | The human explicitly had to reverse an agent change. |
| Manual cleanup | The human explicitly had to perform mechanical cleanup. |
| Revalidation | The human explicitly had to verify a claim or surface the agent should have verified. |
| Context reconstruction | The human had to rebuild current state, source lineage, or ownership context. |
| Decision repetition | The human had to revisit an already-set decision or answer an avoidable choice. |
| Lost session | The evidence explicitly records losing a session or its usable state. |

Agent correction work, evaluator work, workflow duration, and hypothetical
future burden are not human burden unless the source explicitly attributes them
to the human.

## Evidence classes

| Class | Meaning |
|---|---|
| observed | Repository or PR evidence binds the failure and its validation or correction closely enough to inspect the event directly. |
| owner-reported | A field note or operating record reports the event, but the original live exchange or all underlying artifacts are not independently bound. |
| inferred | The incident itself is reconstructed from indirect evidence rather than directly reported. |
| unknown | Available evidence cannot support one of the other classes. |

An evidence class applies to the case record overall. Mixed evidence is
preserved in `directly_observed_facts` and `inferences`.

## Confidence levels

| Confidence | Threshold |
|---|---|
| high | Stable source identity plus explicit trigger/failure and a bounded repair, result, or stop state. |
| medium | The case is explicit, but transcript identity, exact action attribution, date, or restart evidence is incomplete. |
| low | The case boundary depends heavily on reconstruction or unresolved source identity. |

Confidence is confidence in the bounded record, not confidence that the same
pattern is frequent elsewhere.

## Deduplication decisions

- Field Notes 112 and 113 are one Entry Window Radar re-entry case. Field Note
  113 explicitly corrects the success-first framing and supplies the incident
  boundary.
- The Entry Window Radar rendered-badge miss remains separate because it has a
  different trigger, evidence surface, repair, and restart result.
- PR #4 and PR #5 are one executor/evaluator stress-run selection incident.
- The validator argument reversal inside PR #4 remains separate from the
  selection incident because it had an independent trigger, one permitted
  correction, and a passing restart receipt.
- Repeated examples and manifestations inside Completion-to-Expansion Drift
  remain one silent branch-succession case.

## Exclusion decisions

- `MISTAKEN.md`'s 2026-06-12 README entry is explicitly an example entry, so it
  is not treated as a confirmed incident.
- The 2026-06-29 local-fix-before-scope-audit entry records a caught impulse and
  safer audit order, but not a completed failure worldline with a distinct
  restart result; it remains a near-miss outside v0.1.
- Field Note 127 names a Completion Line contamination incident and O's
  split-instruction delivery failure only to exclude them. No primary,
  repository-bound incident evidence was found in the authorized sources, so
  neither is counted.
- Checklists, hypothetical failure modes, prevention claims, and prevented
  worldlines are not counted as incidents.

## Interpretation boundary

Class assignment is an extraction aid. A high count means only that a class was
mapped to more of the nine cases in this bounded corpus. It does not establish
real-world frequency, risk, causation, or comparative prevalence.
