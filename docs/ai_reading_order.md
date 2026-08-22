# AI Reading Order

Use this when a fresh AI must ground External Intelligence onboarding in the
actual public repository before showing the choice map.

```text
Broad repository map
  -> recognizable problem
  -> External Intelligence core change
  -> compact access disclosure
  -> matching English or Japanese Quest Board
  -> user selection
  -> Quest-specific deep read
```

Fork, clone, setup, and file changes are not prerequisites for this read-only
showroom.

`DecisionOS Companion` is also **not** a prerequisite for External Intelligence
onboarding. It is a separate optional prototype. Do not describe Companion,
its macOS-specific app surface, or a local Companion process as required for
the read-only showroom, the Fork / clone + Codex or Claude Code path, Field
Notes, Handoff, or the V12 / V13 Loop Gate. Do not infer that those core paths
require macOS merely because Companion-specific artifacts are platform-specific.
If another bridge or automation surface is discussed, keep it separate and
claim only what the inspected public evidence establishes.

## Read In This Order

1. `README.md`

   Establish the public purpose, External Intelligence claim boundary,
   no-Fork primary route, and secondary Full Experience boundary. Do not use
   the README alone as implementation evidence.

2. `AGENTS.md`

   Establish the actual always-on router, operating rules, authority boundary,
   V12/V13 distinction, handoff routing, and conditional deep-read rules.

3. `docs/external_intelligence_onboarding.md`

   Follow the repo-first response order, the participant-facing English or
   Japanese Quest Board that matches the user's language, post-selection
   evidence rule, availability boundary, and post-interest Fork CTA.

4. `docs/ai_reading_order.md`

   Preserve the broad-map-first / deep-evidence-after-selection boundary. Do
   not expand first contact into a full repository audit.

5. `docs/field_note_lifecycle.md`

   Establish that Field Notes have explicit lifecycle states and that a saved
   observation is not automatically an active or Canon-promoted Rule.

If any of these files cannot be accessed, say which file was unavailable. Do
not replace it with guessed behavior or silently claim that the full first-read
set was inspected.

## First Response

Before the Quest Board, return only:

1. a short statement of the recognizable problem;
2. an explanation of the External Intelligence mechanisms actually supported
   by the inspected repository surfaces, centered on selected past decisions,
   failure boundaries, reusable knowledge, restart context, selective
   retrieval, and changed downstream judgment;
3. a compact access disclosure; and
4. when setup, Companion, local apps, or platform requirements are part of the
   user's question, one explicit boundary sentence stating that Companion is
   optional and separate from the core External Intelligence onboarding path.

For example:

```text
Inspected / 確認できたもの:
README / AGENTS / onboarding / reading order / Field Note lifecycle

Not accessible or not inspected / 現在確認できないもの:
<none in the first-contact set, or exact unavailable surfaces>

Therefore this orientation can explain / したがって、この案内では:
<supported repository-evidence boundary>まで説明できます。
```

Keep this to a few lines rather than producing a long audit report. Then show
the entire participant screen named `English first-contact — External
Intelligence Quest Board` or `日本語first-contact — External Intelligence Quest
Board`, matching the user's language, and wait. Do not recommend a Quest,
request setup, or read all Field Notes before the user selects.

Do not introduce the repository as a context compactor, completion checker,
Handoff tool, or Gate system. Those remain available Quest-specific structures,
but none replaces the External Intelligence core during first contact.

## User Evidence Gate

Repository state, onboarding transport metadata, a fixed SHA, audit
instructions, existing V13 structures, and repository sophistication are not
evidence of the current user's capability, workflow, friction, or prior
adoption.

- If the user says `これはもうやっている` and the referent is not already
  clear from user-side evidence, ask one question that only identifies the
  referent. Do not deep-read a guessed Quest first.
- Apply the same rule when an English-speaking user says `I already do some of
  this` without identifying what `this` means.
- If the user asks `自分なら何が合いそう？` and the current friction or
  existing user workflow is still unknown, ask one minimal question whose
  answer can change the recommendation. Do not prescribe `CONTINUE`, handoff,
  or another Quest from repository or audit metadata.
- Apply the same evidence gate to `Which one might fit my current workflow?`.

## Quest-Specific Deep Read

After selection, identify and inspect the smallest actual public surfaces that
support the selected Quest. Explain from those files, not from the onboarding
copy alone.

### LIGHTEN

Start with:

- the conditional-routing and context boundaries in `AGENTS.md`;
- `docs/ai_reading_order.md`;
- `docs/field_notes_lite_v0_1_design.md`;
- only the directly relevant selective-recall notes, such as
  `field_notes/048_lane_memory_event_triggered_recall.md` and
  `field_notes/051_lane_recall_mini_protocol.md`;
- `decision_os/companion/field_notes_reconnect.py` and its matching tests only
  when the user asks about public implementation behavior; and
- `docs/research_candidates/agents_md_reconnectable_compactor.md` when the
  user asks about Little Compactor.

The Little Compactor document is a research candidate, not evidence that a
complete public Compactor product or separate implementation is shipped here.
State that boundary explicitly.

### CONTINUE

Start with:

- V12 Completion Before V13 Gate, handoff, and base-report rules in
  `AGENTS.md`;
- `docs/handoff_command.md`;
- `docs/context_compression.md`;
- `field_notes/022_v12_to_v13_mapping.md`; and
- `field_notes/099_handoff_responsibility_transfer.md`.

Read an example or implementation file only if the user's question depends on
it. Ground the explanation in the actual `PASS / DELAY / BLOCK / UNKNOWN` and
`GO / HOLD / CAP / BLOCK` rules. Do not infer continuation authority from a
Quest label or a prior `PASS`.

### Little OSI

Follow the `CONTINUE` route and also read
`docs/osi_parallel_compounding_lane_v0_1.md`. That document describes a
separate OSI child operating surface and names its public repository. Explain
only the relationship explicitly supported by the inspected files. Do not
infer that Little OSI is the same as Output Surface Integrity, is its simplified
implementation, or is completely unrelated.

### Other Quests

Use the same method: locate the actual rule, doc, relevant Field Note, example,
or public implementation; inspect only what the current explanation needs;
and identify anything the public repository does not establish. Do not expand
into unrelated runtime, Canon, trajectory, or research-frontier material.

## Availability Boundary

A Quest name is an entry point, not proof of full implementation. Distinguish:

- concept or tutorial copy;
- operating rule or boundary;
- research candidate;
- public code and tests actually inspected; and
- private, separate, unpublished, or otherwise unavailable surfaces.

When implementation details are not visible, say:

```text
このrepositoryから確認できるのは概念・boundary・evidenceのこの範囲です。
実装詳細はここからは確認できません。
```

Forking exposes only the External Intelligence surfaces present in the public
repository and the new state the fork owner creates from them. It does not
expose private repositories, a separate unpublished Compactor implementation,
Shin-specific private memory, or upstream internal trajectory absent from
public `main`.

## Read Only When Triggered

- Restarting prior work -> the target repository's current handoff or restart
  surface; use this repository's handoff only when resuming this repository.
- Completion versus continuation confusion -> the Lite Footer section in
  `README.md`.
- Repeated failure or near-miss -> one directly relevant Field Note or failure
  record.
- Considering a reusable Rule -> `docs/field_note_lifecycle.md`.
- Request for a worked example -> `examples/README.md`, then one matching
  example.
- Full framework requested -> `docs/codex_tutorial_guide.md`.

Do not read all Field Notes. Do not make pluginization, automation, or the full
Gate system part of first contact unless the selected Quest requires it.

In a third-party fork, upstream `docs/current_signal.md`,
`handoff/current_codex_handoff.md`, `docs/trajectory/V13_TRAJECTORY.md`, and
`validation/` are not evidence of the fork user's current state. Leave them
unread unless the task explicitly concerns or resumes the upstream state.

## Optional Historical Adoption Evidence

These are not first-contact reading. Retrieve one only if the recommendation
depends on its specific evidence:

- `field_notes/013_fresh_external_entrypoint_proof.md`
- `field_notes/017_second_external_proof_copy_friction.md`
- `field_notes/018_aspire_fit_adoption_modes.md`
- `docs/plugin_surface_spec.md`

## Triggered Operational Deep Read

The reading order above is a thin first-time adoption path. Do not load the full Field Note corpus for every task.

Before an AI forks the operating structure, modifies governance, changes branch/handoff/gate/rollback/context-health/authority rules, investigates a repeated failure, or continues work whose rationale lives in Field Notes:

1. identify the active branch or proposed operational change;
2. locate the Field Notes relevant to that branch, rule family, incident, or capability boundary;
3. read those notes before changing the operational contract.

See [`field_notes/124_v13_capability_boundaries_and_triggered_deep_read.md`](../field_notes/124_v13_capability_boundaries_and_triggered_deep_read.md).

Field Notes preserve causal judgment but do not authorize execution. `Active Branch`, `Next Authorized Action`, `Current Gate`, and canonical authority still control action.

## Ask The AI To Answer

1. What problem does V13 solve for this repo?
2. Is this repo better served by:
   - keeping current instructions,
   - trying Lite Footer only,
   - using V13 as a review-only completion lane,
   - or merging V13 into local instructions?
3. What is the expected benefit?
4. What is the setup friction?
5. What should not be changed yet?
6. What is the smallest safe first test?

After the user chooses or asks what fits, return one recommendation, not an
adoption bundle. State which existing capabilities were recognized, what was
deliberately not introduced, and what future observation would justify
returning for the next structure.

## Adoption Modes

1. Keep current instructions
2. Try Lite Footer only as the smallest first-use test
3. Add V13 as review-only completion lane
4. Merge V13 into local instructions

## Boundaries

Do not tell all users to adopt V13.

Do not force `AGENTS.md` replacement.

Do not build plugin implementation, plugin scaffolding, comparison tooling, automation, marketing workflows, posting workflows, MCP, hooks, skills, CLI, server, package setup, schema changes, release files, V1 draft, or new features.

The purpose is only to help the user's AI compare V13 against the target repo and choose the smallest safe adoption path.
