# External AI Workflow Incident Map v0.1

## Purpose

This artifact turns the merged external incident corpus and the internal Field
Note audit into one evidence-bounded editorial map. Its purpose is to make the
three-stage transformation legible:

```text
workflow failure
→ broken operational surface
→ returned human work
```

The SVG is canonical. The PNG is a same-aspect-ratio render for repository and
social-preview inspection. Neither image is published by this change.

## Source Tables Used

| Display surface | Source table or statement |
|---|---|
| External corpus label and collection date | `case_studies/external_incident_summary_v0_1.md` — Boundary and method / Source-supported facts |
| Repository count | `case_studies/external_incident_summary_v0_1.md` — Repository counts |
| Where it started | `case_studies/external_incident_summary_v0_1.md` — Workflow types represented by at least two cases |
| What broke | `case_studies/external_incident_summary_v0_1.md` — What-broke counts |
| What returned to the human | `case_studies/external_incident_summary_v0_1.md` — Returned-human-burden counts |
| Internal audit headline counts | `case_studies/incident_summary_v0_2.md` — opening corpus and audit counts |
| Internal exclusion counts | `case_studies/incident_summary_v0_2.md` — Candidate Audit Dispositions |
| Internal audit method and exclusion boundary | `case_studies/latent_incident_candidate_register_v0_1.md` — Audit boundary / Method and promotion threshold |

## Displayed Values

### Main Evidence Label

| Value | Display |
|---:|---|
| 17 | public incident worldlines |
| 7 | repositories |

### Where It Started

| Observable workflow type | Cases in the external corpus |
|---|---:|
| Session continuity and resume | 4 |
| Structured edit application | 3 |
| IDE file editing and recovery | 2 |
| Multi-worktree repository orchestration | 2 |
| Repository shell mutation | 2 |

Four additional workflow types contain one case each.

### What Broke

| Normalized class | Cases in the external corpus |
|---|---:|
| Evidence Chain | 15 |
| Restartability | 11 |
| Trust | 10 |
| Re-entry Capacity | 6 |

### What Returned to the Human

| Normalized returned-burden class | Cases in the external corpus |
|---|---:|
| Revalidation | 11 |
| Manual cleanup | 6 |
| Context reconstruction | 4 |
| Lost session | 2 |
| Rollback | 2 |

### Internal Audit Discipline

| Audit value | Count |
|---|---:|
| Field Notes scanned | 126 |
| Candidate worldlines reviewed | 91 |
| Confirmed incidents | 10 |
| Contained near-misses not counted as confirmed incidents | 11 |
| Controlled validations not counted as confirmed incidents | 26 |
| General risks not counted as confirmed incidents | 33 |
| Insufficient-evidence cases not counted as confirmed incidents | 7 |

The four displayed exclusion classes contain 77 candidates. They are not the
complete 90-candidate non-promotion accounting: the remaining candidates are
duplicates, parts of existing worldlines, or additional evidence for existing
cases. The image therefore does not present the four displayed classes as an
exhaustive partition.

### Collection Date

The selected public GitHub incident corpus was collected as of `2026-07-25`.

## Interpretation Boundary

- The external and internal corpus counts remain separate. The map does not
  combine 17 external and 10 internal cases into “27 incidents.”
- Counts are descriptive case-presence counts in selected corpora. They are not
  population frequency, probability, prevalence, average loss, comparative
  safety, product quality, or product ranking.
- One external case may map to more than one normalized what-broke or
  returned-burden class, so class counts do not sum to 17.
- Returned-burden counts indicate case presence, not burden magnitude.
- The title and subtitle are editorial framing, not source-authored causal or
  prevalence claims.
- The internal panel reports audit discipline. It does not imply that LoopKit
  prevented all listed incidents.
- The image is an artifact candidate only. It is not public copy and is not
  authorized for publication by this change.

## Alt Text

Editorial three-stage flow based on 17 public AI coding incident worldlines
across seven GitHub repositories. Five workflow types lead to broken
operational surfaces—Evidence Chain 15, Restartability 11, Trust 10, and
Re-entry Capacity 6—which return work to people: Revalidation 11, Manual
cleanup 6, Context reconstruction 4, Lost session 2, and Rollback 2. A separate
internal audit panel reports 126 Field Notes scanned, 91 candidate worldlines
reviewed, and 10 confirmed incidents, while excluding 11 contained
near-misses, 26 controlled validations, 33 general risks, and 7
insufficient-evidence cases. Internal and external corpus counts are not
combined.

## Artifact Paths

- Canonical SVG:
  `assets/incident-map/external-ai-workflow-incident-map-v0-1.svg`
- Rendered PNG:
  `assets/incident-map/external-ai-workflow-incident-map-v0-1.png`

Both artifacts use a `1600 × 1000` canvas and the same `8:5` aspect ratio.

## Rollback

Delete these three files:

1. `assets/incident-map/external-ai-workflow-incident-map-v0-1.svg`
2. `assets/incident-map/external-ai-workflow-incident-map-v0-1.png`
3. `case_studies/external_ai_workflow_incident_map_v0_1.md`

No corpus, canonical state, or runtime rollback is required.

## Reevaluation Condition

Reevaluate and regenerate both image formats when a source count changes or
the incident taxonomy changes. A visual-style preference alone does not change
the evidence layer.
