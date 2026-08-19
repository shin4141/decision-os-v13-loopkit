# 13-189 Repo-Grounded External Intelligence Onboarding Validation

Date: 2026-08-20 (Asia/Tokyo)

## Scope

Validation covers only the 13-189 onboarding repair:

- primary copy prompt;
- repository-grounded first response and access disclosure;
- post-selection LIGHTEN and CONTINUE deep reads;
- availability boundary; and
- post-interest Full Experience Fork CTA.

It does not validate a new External Intelligence implementation, private
surface access, Compactor implementation, runtime expansion, Canon change,
trajectory change, or 13-190.

## Candidate Under Test

- Repository: `shin4141/decision-os-v13-loopkit`
- Base: `main` at `29dde9e2af09e30efbe132ddde0be5120da77bf6`
- Candidate branch: `codex/13-189-repo-grounded-onboarding`
- Fresh equivalent: ephemeral Codex CLI `0.147.0-alpha.6.5`
- Model reported by runner: `gpt-5.6-sol`
- Sandbox: read-only
- File changes by fresh runs: none

The fresh runs read the local candidate checkout. This proves candidate
behavior against actual repository files, but not post-merge retrieval through
the public GitHub URL. A public-URL rerun remains a post-publication check.

## Automated Contract Test

Command:

```sh
python3 -m unittest tests.test_external_intelligence_onboarding -v
```

Result: `PASS` — 5 tests.

The tests bind:

- one README primary copy block to the repository URL and five required files;
- complete Quest Board markers and compact access disclosure;
- LIGHTEN to actual selective-recall evidence and the Compactor research
  boundary;
- CONTINUE to actual V12/V13, handoff, and context-compression rules; and
- the Fork CTA to post-interest timing and public/private availability limits;
  and
- V13 Loop Gate to next-cycle authorization rather than automatic repetition.

An additional `python3 -m unittest discover -v` run was attempted. The run was
not used as 13-189 acceptance evidence: unrelated Companion server tests could
not bind `127.0.0.1` in the managed sandbox (`PermissionError: [Errno 1]
Operation not permitted`), and a Chrome layout probe exited `-6`. The long
remaining suite was interrupted after those environment failures. The focused
13-189 contract test was rerun afterward and remained green.

## Fresh Test A — First Contact

Prompt state: no Quest selected.

Observed:

- read all five required first-contact files;
- explained repository-backed external memory, selective reuse, and Field Note
  authority boundary;
- listed inspected and uninspected surfaces in a compact disclosure;
- rendered all seven Quest areas and the full Choose Your Quest content;
- did not recommend a Quest;
- did not offer Fork / clone as the next step; and
- made no file change.

Result: `PASS`.

## Fresh Test B — LIGHTEN

Prompt state: Quest Board already shown; `LIGHTEN` selected.

Observed additional reads:

- `AGENTS.md`
- `docs/ai_reading_order.md`
- `docs/field_notes_lite_v0_1_design.md`
- `field_notes/048_lane_memory_event_triggered_recall.md`
- `field_notes/051_lane_recall_mini_protocol.md`
- `decision_os/companion/field_notes_reconnect.py`
- `tests/test_field_notes_reconnect.py`
- `docs/research_candidates/agents_md_reconnectable_compactor.md`

The response identified public Selective Recall code and tests, stated that the
test file was inspected but not executed in that fresh run, and kept Little
Compactor at `HOLD — SAVED ONLY / NO IMPLEMENTATION AUTHORITY`. It did not
reinterpret Selective Recall as a shipped Little Compactor implementation.

Result: `PASS`.

## Fresh Test C — CONTINUE

Prompt state: Quest Board already shown; `CONTINUE` selected.

Observed additional reads:

- `AGENTS.md`
- `docs/handoff_command.md`
- `docs/context_compression.md`
- `field_notes/022_v12_to_v13_mapping.md`
- `field_notes/099_handoff_responsibility_transfer.md`

The response used `PASS / DELAY / BLOCK / UNKNOWN` for V12 and
`GO / HOLD / CAP / BLOCK` for V13, stated that `PASS` does not automatically
produce `GO`, and explained that handoff transfers responsibility rather than
information alone.

Result: `PASS`.

## Fresh Test D — Fork CTA

Prompt state: repository-grounded explanation and trial complete; user
explicitly interested in growing their own External Intelligence.

Observed:

- presented the Full Experience Fork CTA;
- limited the Fork to public `AGENTS.md`, notes, handoff, docs, and user-created
  new state;
- excluded private repositories, separate unpublished implementations,
  Shin-specific private memory, and internal trajectory absent from public
  `main`; and
- did not execute Fork, clone, setup, or file changes.

Result: `PASS`.

## Fresh UX Delta Test — V13 Loop Meaning

Prompt:

```text
ループ機能もついているんですか？
```

The fresh equivalent read only the participant-facing V13 LoopKit introduction
and `CONTINUE` section. It answered that the repository does not automatically
repeat work and that V13 Loop Gate judges, through
`GO / HOLD / CAP / BLOCK`, whether beginning the next work cycle is justified.
It also stated that even `GO` does not automatically start the next loop.

Result: `PASS`.

## Remaining Boundary

The candidate meets the repository-local acceptance tests. After publication,
the README copy block should be pasted into a fresh external AI once more to
verify GitHub URL access, current public `main` identity, and public rendering.
That check must not be represented as complete before the candidate is on the
public branch.
