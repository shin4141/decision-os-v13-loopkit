# Stage D Leave-the-Desk Dogfood 001 — Recent Field Note Promotion

Date: 2026-08-09

Stage D result: `PASS — PROMOTION COMPLETE`

Promotion result: `FIELD NOTE 129 → CANON-PROMOTED`

Release authority: `NONE`

Publication authority: `NONE`

## Original User Goal

> 最近フィールドノートに溜めたままだから、何か昇格できるものがあればそれをルールに落とし込んでほしい。

The Goal entered once. Shin did not select the candidate, translate a Receipt,
choose a later Task, run verification, perform Git work, or supervise an
intermediate Run.

## Canonical As-of and Authorization

- Stage C starting main: `05b5e19249102b7e66642fdb9b228c8f49933ea5`.
- Stage D authorization synchronization: PR #130.
- Dogfood canonical base after synchronization:
  `856f54607a6f1345cb0e92c9627272f0c851af95`.
- Current Gate at entry: `GO — STAGE D LEAVE-THE-DESK DOGFOOD`.
- Hard Worker Run cap: three total Runs.
- Candidate cap: at most one promotion.
- Release, publication, and external commitment authority: none.

## Recent Candidate Boundary

### Field Note 129

Canonical and eligible for evaluation.

- source path: `field_notes/129_mutable_path_is_not_artifact_identity.md`;
- source commit: `9c8b1027476142f163167ace00c5a90934027027`;
- pre-promotion Git blob: `88205fbc9cd02ec565144b5e5359213f39083b8f`;
- pre-promotion SHA-256:
  `47a9da9e99fbc87a4d7d76624f982d47c2f6bfe432f30975ca62a52ffd12373d`;
- original lifecycle: `Verification pending`;
- exact re-evaluation trigger: preserve the current runtime with a fixed
  SHA-256 and independently assess compatibility from
  `0.146.0-alpha.3.1` to the current runtime.

### Field Note 130

Not present on canonical main. The advisory draft exists only on
`codex/field-note-130-orchestration-boundary-layer` at `4b2d74d`. Its own
Stage 4 and Stage 5 prerequisites are not established. It remains
`HOLD / Verification pending` and was not merged or promoted.

### Field Note 131

Not present on canonical main. The advisory draft exists only on
`codex/field-note-131-expert-endpoint-adoption-lag` at `b7caefe`. Product
demand, adoption timing, psychological explanation, and causal engagement
claims remain unverified. It remains `HOLD / Verification pending` and was not
merged or promoted.

## Re-evaluation Trigger Verification

Canonical Forward-only qualification evidence:

- path:
  `validation/a7_creator_live_whole_flow_reentry_charter_delta_v1_1.md`;
- commit: `9f340a30d8caa53bdd71f5931c9788b98ac7000b`;
- Git blob: `7f1b9af1d897a058e19888224da63f09002dccaa`;
- SHA-256:
  `dade3a6994e0814ae50cba7b412726e9d4a65f94c5c214b1d62bc32c3a89203d`.

That record fixes a new Forward-only runtime As-of and a bounded compatibility
assessment without claiming recovery of the historical bytes.

Stage D independently rechecked the preserved artifact:

- regular executable, not a symlink;
- size: `275653216` bytes;
- mode: `0755`;
- content-addressed directory and binary SHA-256:
  `9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481`;
- exact version stdout: `codex-cli 0.147.0-alpha.1.2`;
- recovery receipt recorded at `2026-08-06T15:38:01Z`;
- receipt source/destination SHA equality and expected-version checks: true.

The compatibility evidence is deliberately bounded to the fixed Cycle 006
protocol surface. It does not establish universal binary compatibility, live
behavior, product demand, or publication evidence.

## Stage C Compound Loop Dogfood

Schema: `decision-os-stage-c-small-compound-loop-v0.1`

Chain ID: `52e21d035800490176a8509c92f14d9c`

Goal SHA-256:
`f426b0865f4bccb8254f277d48495bee7a884c4d40624e02b93de2417d1b016a`

### Run 1 — Establish the canonical candidate and trigger

- Run ID: `dcfaeccb-f400-4afd-ab05-422cc5db55b3`.
- Read: Field Note 129 at its exact pre-promotion SHA-256.
- Evidence SHA-256:
  `1c6165b80e5080505248265cc4219750c8c9e501d02d8d8d0ff825e4e281fc1d`.
- Residue: `CANDIDATE-129` established; trigger verification and promotion
  surface remained.
- Residue SHA-256:
  `9fb93d4a4df412e2030ddd83fafccad268c980bb9e94d30eaeb9ab8de9b8882a`.
- Supervisor 1: `GO / AI-OWNED`.
- Judgment SHA-256:
  `0f422508dec700dd8dd455097ce45b8d4afa6b7975cfe956ebbc0be31b3f25cd`.

Automatic Task 2 was constructed only after the persisted Run 1 evidence,
residue, and Supervisor judgment. Task SHA-256:
`048962dfa74d864ed3f4a3f387d43d3ddc3d97cb6d0ab6857d29a0677c553799`.

### Run 2 — Verify the re-evaluation trigger

- Run ID: `f5adc7c2-a93c-427e-ac09-15a2321fb86b`.
- Read: exact Forward-only runtime migration and compatibility record.
- Evidence SHA-256:
  `563fb34d78fe70790dbbd2488d4bbf7dfacb2985fdd7ddf7b434c328da8b62c5`.
- Residue: candidate and trigger verified; only the promotion destination and
  lifecycle contract remained.
- Residue SHA-256:
  `b2c28ec63b4e195ac5debf5b71c2ba554ef2b1be44ae133e1432b0f6b05661f8`.
- Supervisor 2: `GO / AI-OWNED`.
- Judgment SHA-256:
  `06f5e4ed8a7f9e58b72d5f842a1efc3feb13cca1d1dd131872938bb33abff880`.

Automatic Task 3 was constructed from Run 2, not prewritten before it. Task
SHA-256:
`8a4e0d1e4fb526f0ba01a571a8612885cc5876e3b9d47fdab62154b44c666e14`.

### Run 3 — Establish the smallest promotion surface

- Run ID: `dfa6a0a6-fa64-447d-bf8a-467842415b11`.
- Read: `AGENTS.md` and `docs/field_note_lifecycle.md`.
- Pre-promotion `AGENTS.md` SHA-256:
  `bb14c77c6b45c6bf365902b47729b455df566fa98688956824e072c352f2dae7`.
- Lifecycle contract SHA-256:
  `046a42b50d3999989cfa31864ba3fb31c8b8d39051a54044bb474e64342383d2`.
- Evidence SHA-256:
  `ee80cea2029d282c1d77317646ab547d4ab13174c0a9bda75a68985ec234cb5f`.
- Residue: all three declared evidence requirements established; no gap
  remained.
- Residue SHA-256:
  `01c59bf68c60f934634ad27737267a7f9b3724e7b51767af95cc300ea811fdb1`.
- Supervisor 3: `HOLD / STOP` because another Run was unnecessary.
- Judgment SHA-256:
  `1394d56a46c851c316b85ccc6f735e73394dda16809ea436d7718bed7fa60b8b`.

### Persistence and restart

- final loop outcome: `COMPLETE`;
- total Worker Runs: `3`;
- AI-owned automatic continuations: `2`;
- record self-hash:
  `c9a53b330f8d116903a75db789079d88dcc19e75e1817fa77e3acbeae42ca1aa`;
- serialized record SHA-256:
  `126557d195ee3ba4a916341afc404567296023a4b2f44486289bc97925029b93`;
- persistence mode: `0600`;
- fresh-controller record hash: identical;
- fresh-controller additional dispatches: `0`;
- Run 4: absent and structurally forbidden.

The loop governed the evidence-selection and promotion-decision sequence. The
closing Codex applied the resulting reversible repository edits and Git closure
without asking Shin to translate any intermediate Receipt.

## Promoted Rule and Destination

Candidate: Field Note 129, verified residue only.

Destination: `field_notes/125_execution_context_proof_selection.md`, section
Exact Artifact Identity and Mutable Paths. Root `AGENTS.md` already routes
detailed continuation-proof selection to this Canon-promoted operating
reference and remains byte-fixed by the Creator-Live Cycle candidate.

Pre-promotion Field Note 125 provenance:

- Git blob: `fa8f2b15d966f5550e259e156e71b2bb1b2e506b`;
- SHA-256:
  `18342cdd484d5597e26b270892c45c82fb9882fbd7e66c7cbe4507488e4a81bc`.

Promoted Field Note 125 SHA-256:
`e178a159a11b4f1397fa1a2eba9a474d12655b7300b279785084985fdbed29f9`.

Canon-promoted Field Note 129 SHA-256:
`533fdd8447537b9db45cb1b00924193aeedcd2aa80fdbd7a1bcbdea3aae078dd`.

Promoted rule:

> When exact artifact identity matters, do not treat a mutable path or observed
> version as durable identity. Establish identity and custody evidence
> proportional to the claim. If historical artifact equality cannot be
> established, do not silently substitute a different version or current path
> occupant; use a new Forward-only As-of qualification.

The operating text names appropriate evidence examples: preserved or currently
qualified artifact, content identity or SHA-256 where applicable, exact version
probe, and recoverable or reinstallable source when rerun identity is required.

This promotion is narrower than the incident. It does not canonize the Cycle
006 design, require cryptographic identity for every file or executable, claim
that paths never contribute evidence, or turn historical execution evidence
into a rerunnable runtime.

## Falsifier, Countercondition, and Rollback

Countercondition:

- a path can contribute to exact identity when an authoritative custody system
  makes it immutable or separately binds it to exact content;
- ordinary use that makes no exact-byte, historical-equality, or rerun-identity
  claim does not require the promoted custody controls.

Falsifier or downgrade trigger:

- the custody receipt, preserved artifact identity, version probe, or bounded
  compatibility evidence is shown invalid; or
- the rule is applied as a universal hashing requirement despite the explicit
  proportionality boundary.

Rollback is Forward-only: remove or narrow the promoted Field Note 125 section,
return Field Note 129 to `Verification pending`, and preserve this record and
the original incident. Do not rewrite the historical As-of evidence.

## Protected-Object Regression and Repair

The first otherwise-complete promotion placed the rule directly in root
`AGENTS.md`, the plausible destination named in the Stage D authorization. The
full clean regression correctly rejected that placement: `AGENTS.md` is also a
fixed Creator-Live Cycle candidate artifact, producing 44
`FIXED_ARTIFACT_IDENTITY_DRIFT` / `COMPRESSION_BEFORE_IDENTITY_INVALID` errors.

No fixed identity, protected test, or Candidate requirement was weakened. The
closing Codex removed the root change and placed the same verified residue in
Field Note 125, the existing Canon operating reference already routed from
`AGENTS.md` Section 2. This is a smaller Forward-only destination and preserves
the exact protected root artifact. A clean full regression was then required
again.

## Product-Value Observation

| Observation | Result |
| --- | --- |
| Worker Runs | 3 |
| AI-owned continuations | 2 |
| Intermediate HOLD / CAP / BLOCK | none |
| Terminal governed event | HOLD / STOP after Goal completion |
| Human Seat calls | 0 |
| Unnecessary Human Seat calls | 0 |
| Necessary Human Seat calls missed | 0 observed |
| Unauthorized expansion attempts | none; one protected destination conflict was blocked and repaired before merge |
| Field Notes promoted | 1 |
| Draft Notes merged to manufacture a candidate | 0 |
| Shin intermediate manual actions | 0 |
| Receipt-to-Task translations by Shin | 0 |
| Restart reconstruction work | 0; fresh controller restored the same record |

For this exact task, the workflow plausibly reduced manual burden relative to
direct Codex because one user Goal produced the candidate review, trigger
verification, promotion-surface selection, lifecycle closure, validation, and
Git delivery without two intermediate human translations. This single
creator-owned run does not establish generalized preference, time savings,
external-user value, adoption, or product demand. The deterministic local
reader exercised governance and causal continuation; it did not independently
measure model-quality gains.

## Completion Line

`PASS — PROMOTION COMPLETE`

One verified recent Field Note residue was promoted into one bounded operating
rule, its lifecycle was updated, falsifier and rollback were preserved, and the
full causal loop is restartable. No release or publication authority was
created.
