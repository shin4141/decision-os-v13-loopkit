# Internal Incident Corpus v0.1 → v0.2 Delta

## Scope and Base

- Fixed audit base: `aac2d6c060586abaf9d3c8c521949dd874f2c1c4`
- Predecessor: Internal Incident Corpus v0.1
- Successor: Internal Incident Corpus v0.2
- v0.1 confirmed incidents: `9`
- v0.2 confirmed incidents: `10`
- Added confirmed incidents: `1`
- Existing case IDs retained unchanged in meaning: `V13-INC-001` through `V13-INC-009`
- New case ID: `V13-INC-010`

This is a Forward-only successor record. It does not rewrite, replace, or
retroactively strengthen Internal Incident Corpus v0.1.

## Immutable Predecessor Receipt

The following SHA-256 identities were read from the repository during this
audit. The predecessor files remain the immutable v0.1 evidence surface.

| v0.1 file | SHA-256 |
|---|---|
| `case_studies/incident_corpus_v0_1.jsonl` | `be5fd987710d010f92fdbc0a832f81c19b530ec4916b9b79acbd379af83f22f7` |
| `case_studies/incident_corpus_v0_1.csv` | `a44fb070c26d835f6912171bd08c9770fcf125cce206206f0d36e0ed56f0c8b5` |
| `case_studies/incident_taxonomy_v0_1.md` | `967c61ed1c9f9606fdef321bfcd27c1fc750b3f6bd419360744410035262041a` |
| `case_studies/incident_summary_v0_1.md` | `ade741cf83ed5e92dfda2b5782f5d5c076c010e204249a17027085646a5724b1` |

All nine predecessor cases retain their existing case IDs, meanings, evidence
classes, confidence levels, burden mappings, and deduplication boundaries.
Additional evidence identified by this audit is recorded below as a delta
decision only. It is not silently inserted into or used to strengthen a v0.1
record.

## Added Confirmed Incident

### V13-INC-010 — Tutorial onboarding request returned a repository summary

Sources:

- `field_notes/085_subthreshold_signal_integration.md:68-74`
- `handoff/current_codex_handoff.md:5348-5352`
- `AI_TUTORIAL_CAPSULE.md:7-21`
- repair commit
  `f2ff820ed3de6c8edfcf8cc0ae0544f089e097ca`
  (`2026-06-22`)

Bounded worldline:

1. A third-party fork user asked Codex to begin the repository tutorial or
   onboarding flow.
2. Codex understood the repository but returned a repository summary instead of
   printing the tutorial menu and waiting for the user's selection.
3. The first-response contract was repaired in `AI_TUTORIAL_CAPSULE.md`: route
   onboarding requests to the tutorial guide's `Exact First Response`, print the
   menu first, wait for selection, and do not edit files during onboarding.
4. The repair was committed at
   `f2ff820ed3de6c8edfcf8cc0ae0544f089e097ca`.
5. No post-fix third-party rerun is recorded.

Inclusion reason:

- bounded trigger: a third-party fork onboarding request;
- occurred failure: summary returned instead of the requested tutorial-menu
  entry flow;
- distinct mechanism: the user's onboarding intent was not bound to the exact
  first-response contract;
- repair: a repository-bound first-contact rule with a stable commit identity;
- exact evidence locations: Field Note, canonical handoff, capsule, and repair
  commit;
- deduplication separation: unlike `V13-INC-006`, this case concerns failure to
  enter a requested onboarding response contract, not completion-triggered
  branch succession or unauthorized continuation.

Evidence boundary:

- evidence class: `owner-reported`;
- confidence: `medium`;
- the original third-party transcript is not repository-bound;
- the original feedback date is not recorded, so the repair commit date is used
  as the As-of basis;
- the third-party fork identity and exact Codex model/version are not recorded;
- no independent post-repair rerun is available;
- no returned-human-burden class or burden quantity is inferred.

These missing bindings limit confidence and restart claims. They do not erase
the bounded failure and repository-bound repair, but they prevent any claim that
the repair is independently verified or generally effective.

## Additional Evidence Decisions Without Case-Count Increase

### V13-INC-001 — public-readiness misjudgment

#### Field Note 062

Evidence location:

- `field_notes/062_public_entry_friction_review.md:141-179`
- `field_notes/062_public_entry_friction_review.md:284-301`
- `field_notes/062_public_entry_friction_review.md:318-380`

Decision:

`ADDITIONAL EVIDENCE FOR EXISTING CASE`

Reason:

The read-only public-entry review again found that the README could be
understandable while public value and adoption impact remained unproven by real
reader behavior. This supports the evidence boundary already represented by
`V13-INC-001`; it is not a second readiness incident. No public edit was made,
and the note remained at `CAP` / public-edit `HOLD`.

Missing binding:

- no real-reader behavior or adoption attempt;
- no distinct occurred public-readiness advancement;
- no independent repair/restart worldline.

#### Field Note 077

Evidence location:

- `field_notes/077_precondition_delta_example_readme_pointer.md:17-53`
- `field_notes/077_precondition_delta_example_readme_pointer.md:55-108`
- `field_notes/077_precondition_delta_example_readme_pointer.md:110-168`

Decision:

`ADDITIONAL EVIDENCE FOR EXISTING CASE`

Reason:

The note compresses a known public-entry failure cluster into the precondition
“This is a pointer edit, not a framing rewrite.” It is an example extraction
that helps bound the same public/canonical promotion pressure surrounding
`V13-INC-001`. The note explicitly does not perform a README edit and does not
claim a proven governance pattern, so it is neither a new incident nor a new
repair outcome.

Missing binding:

- the example does not identify one distinct triggering execution;
- no actual pointer-edit expansion occurs in this note;
- the wedge has no independent forward-use result here.

The v0.2 record for `V13-INC-001` therefore retains the v0.1 meaning, evidence
class, confidence, and source boundary. Field Notes 062 and 077 are disclosed
only in this delta.

### V13-INC-006 — completion-to-expansion drift

#### Field Note 123

Evidence location:

- `field_notes/123_model_independent_gate_enforcement.md:110-133`
- `field_notes/123_model_independent_gate_enforcement.md:144-178`

Decision:

`ADDITIONAL EVIDENCE FOR EXISTING CASE`

Reason:

On later re-entry, completed character-count/output-surface findings were not
loaded as the active foundation, generic analysis restarted near the initial
state, and the prior foundation was recovered only after human intervention.
The source explicitly classifies this as another manifestation of the existing
`Rule-Knowledge / Action-Control Gap` and calls it supporting evidence. The
binding reuse rule is a Forward-only refinement of the existing mechanism, not
a distinct incident root.

Missing binding:

- no stable transcript or task identity for the later re-entry;
- no exact event commit is bound to the initial regression;
- multiple recurrence descriptions are not separated into independently
  evidenced worldlines.

#### Field Note 126, Case 002

Evidence location:

- `field_notes/126_high_leverage_definition_return.md:361-443`
- `validation/field_note_126_case_002_human_seat_distinguishability.md:23-78`
- source commit
  `af34776c51289da01299168d0b009f9bbaba8656`

Decision:

`ADDITIONAL EVIDENCE FOR EXISTING CASE`

Reason:

The AI returned an A/B/C operational menu even though existing gates already
made two routes unavailable and the residual choice did not require a material
Human Seat judgment. The Decision Owner delegated the indistinguishable choice,
after which the AI selected and parked route B. This is later evidence of the
routine branch-selection and Human-Seat over-return already present in
`V13-INC-006`, not a distinct completion or branch-succession mechanism.

Missing binding:

- the original live exchange is preserved through an owner-supplied bounded
  record rather than an independently reproduced transcript;
- future avoidance of the same menu and longitudinal burden reduction remain
  unverified;
- Case 002 is explicitly `PARTIAL`, and route B remained parked.

The v0.2 record for `V13-INC-006` therefore retains the v0.1 meaning, evidence
class, confidence, and source boundary. Field Note 123 and Field Note 126 Case
002 are disclosed only in this delta and do not increase the confirmed-incident
count.

## Candidate Audit Accounting

The candidate register contains repository-audit classifications only.

| Classification | Candidate records |
|---|---:|
| `NEW CONFIRMED INCIDENT` | 1 |
| `DUPLICATE OF EXISTING CASE` | 7 |
| `PART OF EXISTING WORLDLINE` | 2 |
| `ADDITIONAL EVIDENCE FOR EXISTING CASE` | 4 |
| `NEAR-MISS / SUCCESSFUL CONTAINMENT` | 11 |
| `CONTROLLED VALIDATION CASE` | 26 |
| `GENERAL RISK / HYPOTHESIS` | 33 |
| `INSUFFICIENT EVIDENCE` | 7 |
| **Total** | **91** |

These are counts in this bounded Field Note audit. They are not population
frequencies, prevalence estimates, reliability rates, or comparative product
claims.

## External Corpus Preservation Receipt

The external public-source corpus is outside this successor's scope and remains
unchanged. Its SHA-256 identities during this audit were:

| External corpus file | SHA-256 |
|---|---|
| `case_studies/external_incident_corpus_v0_1.jsonl` | `3faa03732c9bd95291123de6a3cd2fcade758f52ffdf2a4ca07229b5f4d976fa` |
| `case_studies/external_incident_corpus_v0_1.csv` | `db546a8756b852210d4d8850dd64bf8b4661d5368378f99a4aa03fce96cda7b1` |
| `case_studies/external_incident_summary_v0_1.md` | `1d53face34e9a78a447ff6c97292af71c7413ae9d52fbbec7cd808d12a7c4683` |
| `case_studies/external_incident_source_register_v0_1.md` | `dabc6a6b8b4d5ed3214b4440cc9f82eae3881f2c39a9712f169e2ccc9bc54c8b` |

No internal/external counts are combined.

## Authority and Non-Claims

- This delta does not modify or reinterpret Canon.
- It does not promote a Field Note, candidate rule, or incident pattern to
  Canon.
- It does not authorize README, Runner, service, pricing, marketing, outreach,
  visualization, automation, or public-post work.
- It does not claim that one added incident is common or representative.
- It does not claim that the tutorial onboarding repair has been independently
  verified.
- It does not convert additional evidence into new cases or higher-confidence
  predecessor records.

## Completion Line

Internal Incident Corpus v0.2 retains all nine v0.1 cases unchanged in meaning
and ID, adds exactly `V13-INC-010` from the bounded FN085 tutorial-onboarding
worldline, records four additional-evidence decisions without increasing case
count, preserves the immutable predecessor and external-corpus hashes, and makes
no population or Canon-promotion claim.
