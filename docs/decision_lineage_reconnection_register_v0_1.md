# Decision Lineage Reconnection Register v0.1

## Status

```text
Register specification: COMPLETE
Registered bindings: 2
First binding: PIC
Second binding: Guard Continuity
Automatic lineage scan: BLOCK
Automatic Canon propagation: BLOCK
Runtime: BLOCK
```

## Purpose

This is a reconnectable source register for
[Minimum Autonomous Loop v0.2](minimum_autonomous_loop_v0_2.md). It records the
minimum verified source identities needed to distinguish:

```text
Local undefined
≠
Lineage undefined
≠
Human unanswered
```

The register is not a full ontology, a copy of the Decision-OS Canon, an
automatic search index, or permission to modify a source. It preserves bounded
source pointers and labels current-layer mappings separately from
source-defined meaning.

## Register Boundary

- Use only a decision-relevant entry.
- Prefer verified source pointers over full-history reload.
- Preserve the source's As-of and later Forward-only deltas.
- Mark an unverified identity or pointer `UNKNOWN`.
- Do not infer a missing source identity.
- Do not quote a V13 mapping as an earlier source axiom.
- Do not silently reconcile two materially valid authoritative meanings.
- Do not execute a local binding or propagate it automatically.

## Lineage Classification Values

```text
LOCAL-CLOSED
LINEAGE-CLOSED
CONFLICT
UNANSWERED
UNKNOWN
```

`UNKNOWN` routes to `SOURCE-PROOF-INSUFFICIENT / HOLD` in MAL v0.2. A
lineage-closed entry may require bounded local binding, but it does not require
another Human Seat answer.

`/ LOCAL-BINDING-REQUIRED` is an operational routing suffix, not a sixth
lineage classification value. It may qualify `LINEAGE-CLOSED` when the source
meaning is closed but bounded current-layer witnesses, falsifiers, or source
binding are still required.

## Verified Source Authority for PIC

The following public primary-source identities were retrieved and checked on
2026-07-22. File hashes identify the exact retrieved artifacts used for this
binding.

Gateway retrieval anchor:

- Repository: [`shin4141/decision-os-paper`](https://github.com/shin4141/decision-os-paper)
- Fixed retrieval commit:
  [`07f20eb5bbea1e49d0b5f60fc4962c45ddcd3704`](https://github.com/shin4141/decision-os-paper/commit/07f20eb5bbea1e49d0b5f60fc4962c45ddcd3704)
- Lineage map:
  [`docs/research_timeline.md`](https://github.com/shin4141/decision-os-paper/blob/07f20eb5bbea1e49d0b5f60fc4962c45ddcd3704/docs/research_timeline.md)

### Decision-OS V6 — Historical PIC Origin

- Title: *Decision-OS V6 (PIC): Canonical Memory Architecture for
  Self-Recursive Intelligence*
- Role: historical Phase-Invariant Core definition; preserved As-of, not the
  current governing formulation
- Version DOI: [10.5281/zenodo.17717518](https://doi.org/10.5281/zenodo.17717518)
- Concept DOI: [10.5281/zenodo.17547566](https://doi.org/10.5281/zenodo.17547566)
- Publication date: 2025-11-26
- Record description: Version 3 / complete English canonical edition
- Gateway source path:
  [`notes/v6/Decision-OS_V6_PIC_English-Edition.pdf`](https://github.com/shin4141/decision-os-paper/blob/07f20eb5bbea1e49d0b5f60fc4962c45ddcd3704/notes/v6/Decision-OS_V6_PIC_English-Edition.pdf)
- Git blob: `6d77a7eaf94197e1151a7585d2386c95d979d1b9`
- Zenodo file checksum: `md5:7e069b5600ebc9a73a848fbf4d8faca3`
- Verified retrieval SHA-256:
  `fa1184fe6cd5d58c64bcfe717f1fb3056b8f94d33029aea1ee547b4b141d209a`
- Relevant source section: pp. 1–3, `Phase-Invariant Memory Architecture
  (PIC)`

V6 defines a commutative, associative, and idempotent join, monotone updates,
idempotent and order-compatible canonicalization, order-independent merging,
canonical convergence, and monotone Safety Triplet aggregation.

This original formulation remains historical evidence. The gateway's V6
README states that V6 v2 introduces commitment-boundary formalization and
replaces earlier formulations.

### Decision-OS V6 v2 — Current Commitment-Bounded PIC

- Title: *Decision-OS V6 (PIC): Canonical Commitment for Non-Destructive
  Integration*
- Role: current governing PIC formulation for this binding
- Artifact label: `V6 v2`
- Zenodo version: `V4`
- Version DOI: [10.5281/zenodo.19433866](https://doi.org/10.5281/zenodo.19433866)
- Concept DOI: [10.5281/zenodo.17547566](https://doi.org/10.5281/zenodo.17547566)
- Publication date: 2026-04-06
- Gateway source path:
  [`notes/v6/Decision-OS_V6_v2.pdf`](https://github.com/shin4141/decision-os-paper/blob/07f20eb5bbea1e49d0b5f60fc4962c45ddcd3704/notes/v6/Decision-OS_V6_v2.pdf)
- Git blob: `2e444243b0f2ba70abb96d9f19e2e44b8ca7d77f`
- Zenodo file checksum: `md5:e7779b39b3fa8edc556b5b59a8651a03`
- Verified retrieval SHA-256:
  `417cb9f7de6461208f4ee2971609382e53e12ec68a80a93d441804dd29149b0b`
- Relevant source sections: pp. 1–2, commitment boundary, PIC conditions,
  and propositions P1–P3

V6 v2 limits PIC's conservative integration claim to the commitment boundary.
It requires commutative / associative / idempotent join, admissible and
inflationary updates, idempotent Canon, commitment-relevant equivalence,
and conservative Safety Triplet aggregation. Its operational propositions are
order independence, idempotent stability, and safety non-dilution.

### Decision-OS V7 Addendum V2 — Why Aspire and Why PIC

- Title: *Decision-OS V7 Addendum V2: Why Aspire, Why PIC*
- Role: necessity, naive-merge failure modes, and minimal PIC requirements
- Version: `v2`
- Version DOI: [10.5281/zenodo.18896167](https://doi.org/10.5281/zenodo.18896167)
- Concept DOI: [10.5281/zenodo.18220350](https://doi.org/10.5281/zenodo.18220350)
- Publication date: 2026-03-07; PDF header date: 2026-03-06
- Gateway source path:
  [`notes/v7-addendum/Decision_OS_V7_Addendum_V2__Why_Aspire_Why_PIC.pdf`](https://github.com/shin4141/decision-os-paper/blob/07f20eb5bbea1e49d0b5f60fc4962c45ddcd3704/notes/v7-addendum/Decision_OS_V7_Addendum_V2__Why_Aspire_Why_PIC.pdf)
- Git blob: `8e98854ad0dc8b4a7cb134df17539c84132e22d3`
- Zenodo file checksum: `md5:0ec8010283cbcd0f7ee8bf035dfed248`
- Verified retrieval SHA-256:
  `a0f94c36cf69ad8e33406f7cd6bf5616f2c31df6cc224a79375febaddb72e1e4`
- Historical As-of: Addendum 0.3, DOI
  [10.5281/zenodo.18220351](https://doi.org/10.5281/zenodo.18220351),
  remains preserved but is superseded for current use by V2
- Relevant source sections: p. 2, `Why PIC`; p. 4, PIC-to-self-recursion
  bridge

V7 Addendum V2 preserves last-write-wins and averaging as failure modes and
fixes monotone integration, idempotence, and order independence as minimal
requirements. It presents commutative / associative / idempotent plus
inflationary / monotone merge and conservative `max / max / set union`
aggregation as a sufficient practical PIC form.

### Decision-OS V8 — Inherited PIC-Compatible Operation

- Title: *Decision-OS V8: Time-Tube Control for Self-Safe AGI*
- Role: operational inheritance of PIC-compatible merging; not a PIC
  redefinition
- Version: `v3`
- Version DOI: [10.5281/zenodo.19690553](https://doi.org/10.5281/zenodo.19690553)
- Concept DOI: [10.5281/zenodo.17970577](https://doi.org/10.5281/zenodo.17970577)
- Publication date: 2026-04-22
- Gateway source path:
  [`notes/v8/Decision_OS_V8_Time_Tube_Control_for_Self_Safe_AGI__EN２.pdf`](https://github.com/shin4141/decision-os-paper/blob/07f20eb5bbea1e49d0b5f60fc4962c45ddcd3704/notes/v8/Decision_OS_V8_Time_Tube_Control_for_Self_Safe_AGI__EN%EF%BC%92.pdf)
- Git blob: `7e9ffaff6bffe3e11654f6bd489a341109eb9ffa`
- Zenodo file checksum: `md5:7c4d47f8b315ba1ea66b2ceb30d32953`
- Verified retrieval SHA-256:
  `2a19708db164e2c5a02afafad41151cbf689c0bd891a144e32b633a53b78c36a`
- Relevant source sections: p. 3, `PIC-Compatible Merge Rules`; p. 7,
  `PIC Recap`; p. 8, `COD vs. PIC`

V8 preserves risk-side monotonicity, commutative / associative / idempotent
merge, ordinal severity, maximum `until`, and evidence set union.

### Decision-OS V11 — Reconnectable Forgetting

- Title: *Decision-OS V11: Forget for Future — Reconnectable Forgetting for
  Long-Horizon Agentic AI*
- Role: provenance, historical As-of, and source re-entry requirements for the
  V13 `Canonical Reconnection` witness; not a PIC redefinition
- Version: `v2.0`
- Latest verified version DOI:
  [10.5281/zenodo.20301056](https://doi.org/10.5281/zenodo.20301056)
- Concept DOI: [10.5281/zenodo.19872063](https://doi.org/10.5281/zenodo.19872063)
- Publication date: 2026-05-20
- Gateway source path:
  [`notes/v11/Decision_OS_V11___Forget_for_Future.pdf`](https://github.com/shin4141/decision-os-paper/blob/07f20eb5bbea1e49d0b5f60fc4962c45ddcd3704/notes/v11/Decision_OS_V11___Forget_for_Future.pdf)
- Git blob: `7939df5c03cad37c92cbbaab9418f7bf0ce0db7e`
- Zenodo file checksum: `md5:ba7c7998910a50093c5846c173f7b355`
- Verified retrieval SHA-256:
  `58f089213c85553fe0451ce574a172a43c6cd5243ad716c784acf6a269268356`
- Relevant source sections: pp. 3–5, `Reconnectable Forgetting` and
  `Provenance-Key Layer`

V11 requires compressed residue to retain source or evidence anchors, an As-of
condition, scope, stop / recheck conditions, unresolved deltas, and a re-entry
path. Its Origin Identity check may include a source reference, timestamp,
version, commit, artifact ID, hash, retrieval path, or author / system
boundary. A source pointer proves origin identity, not judgment fidelity by
itself.

### Decision-OS V7 Final — Later Reinforcing Delta

- Title: *Decision-OS V7 Final: Guardable Self-Recursive Evolution*
- Role: later adoption of the V6 v2 commitment-bounded reading; reinforcing
  delta, not replacement for the V7 Addendum and not a conflict
- Version: `V7 Final EN v1.0`
- Version DOI: [10.5281/zenodo.20422099](https://doi.org/10.5281/zenodo.20422099)
- Publication date: 2026-05-28
- Gateway source path:
  [`notes/v7-final/Decision-OS_V7_Final_EN_v1.0.pdf`](https://github.com/shin4141/decision-os-paper/blob/07f20eb5bbea1e49d0b5f60fc4962c45ddcd3704/notes/v7-final/Decision-OS_V7_Final_EN_v1.0.pdf)
- Git blob: `1892d785d7d6b824355b9996bdee8e2a69f0f448`
- Zenodo file checksum: `md5:4be252431ce0d6b2a1de85df41c11496`
- Verified retrieval SHA-256: `UNKNOWN`
- Relevant source sections: PIC/non-destructive integration, Intelligence as
  self-recursion on PIC, and C3 PIC failure modes

V7 Final reinforces order-independent integration, idempotent Canon,
commitment boundaries, conservative safety aggregation, and the exclusion of
rupture, order-dependent merge, last-write-wins, and commitment destruction.
It does not conflict with the four V13 operational witnesses.

## Entry 001 — PIC

```text
Term / Joint:
PIC / Phase-Invariant Core preservation in V13 self-update evaluation

Current Local Use:
validation/field_note_126_case_004_aspire_anchored_independent_evaluation.md;
field_notes/126_high_leverage_definition_return.md;
docs/roadmap_anchors.md;
docs/aspire_oriented_loop_map.md;
docs/minimum_autonomous_loop_v0_2.md;
handoff/current_codex_handoff.md

Lineage Classification:
LINEAGE-CLOSED

Authoritative Source:
Decision-OS V6 v2 / Canonical Commitment, DOI 10.5281/zenodo.19433866,
with the original V6 PIC definition preserved as historical As-of and
supported by the verified V7 Addendum V2, V8 v3 operational inheritance,
V11 reconnectability, and V7 Final source pointers recorded above

Source As-of / Version:
Original V6 historical As-of / 2025-11-26 /
DOI 10.5281/zenodo.17717518;
V7 Addendum V2 / 2026-03-07 / DOI 10.5281/zenodo.18896167;
V6 v2, Zenodo V4 / 2026-04-06 / DOI 10.5281/zenodo.19433866;
V8 v3 / 2026-04-22 / DOI 10.5281/zenodo.19690553;
V11 v2.0 / 2026-05-20 / DOI 10.5281/zenodo.20301056;
V7 Final EN v1.0 / 2026-05-28 / DOI 10.5281/zenodo.20422099;
gateway retrieval commit 07f20eb5bbea1e49d0b5f60fc4962c45ddcd3704

Later Forward-only Deltas:
V7 Addendum V2 states PIC necessity and naive-merge failure modes;
V6 v2 replaces earlier formulations for current use and narrows conservative
PIC integration to the commitment boundary;
V8 v3 inherits PIC-compatible operation without redefining PIC;
V11 adds reconnectable source identity and re-entry requirements;
V7 Final reinforces the V6 v2 commitment-bounded reading without conflict;
FN126 Case 004 introduces PIC as a V13 self-update preservation condition;
the current Forward-only correction classifies the local work as AI-owned
lineage binding rather than a new Human Seat question

Source-Defined Core:
At the commitment boundary: order-independent integration through a
commutative, associative, and idempotent join; admissible and inflationary
updates; idempotent commitment-bounded Canon; risk-side monotone
integration as preserved by V7 Addendum V2 and V8;
commitment-relevant equivalence and canonical stability; and conservative,
non-dilutive Safety Triplet aggregation using severity max, until max, and
evidence set union. The original V6 canonical-convergence formulation remains
historical As-of. Last-write-wins and averaging are not admissible substitutes.

Current-Layer Operational Mapping:
V13 maps the source-defined core to four minimum witnesses: Order
Independence, Idempotence, Monotone Safety Preservation, and Canonical
Reconnection. This is a V13 evaluation mapping, not a local redefinition of
PIC. Canonical Reconnection maps V6 canonical convergence together with V11
reconnectability, subject to the later V6 v2 commitment-boundary scope; it is
not presented as a newly discovered V6 axiom. The four witnesses apply when an
update is integrated into a commitment-ready canonical judgment, not while
competing frontier candidates remain uncommitted.

Minimum Witnesses:
- Order Independence: the same update set does not produce a different
  canonical result merely because arrival order changes.
- Idempotence: reprocessing the same update does not further distort the
  state.
- Monotone Safety Preservation: added information does not silently weaken
  Severity, Until, Evidence, BLOCK, or material counterevidence.
- Canonical Reconnection: verified source, As-of, update set, and evidence
  pointers allow the current canonical judgment to be reconstructed or
  audited.

Falsifiers / Break Conditions:
- Order Independence fails if reordering the same update set changes the
  canonical judgment without a source-defined ordering rule.
- Idempotence fails if replaying the same update changes or further distorts
  the state.
- Monotone Safety Preservation fails if added information lowers Severity,
  shortens Until, removes Evidence, suppresses BLOCK, or hides material
  counterevidence without an authoritative Forward-only decision.
- Canonical Reconnection fails if the verified source, As-of, update set, or
  evidence path cannot reconstruct or audit the current canonical judgment.
- PIC BROKEN if any one of the four operational witnesses fails at the
  commitment boundary.

Reopen If:
A later explicit Human Seat delta changes PIC semantics; an authoritative
source identity or artifact hash no longer matches; source proof becomes
insufficient; two valid lineage meanings conflict after As-of precedence; or
evidence falsifies one of the four V13 witness mappings.

Human Seat Required:
no
```

## Entry 001 Routing Receipt

```text
PIC lineage classification:
LINEAGE-CLOSED / LOCAL-BINDING-REQUIRED

Established Context Check:
CLOSED

Decision Route:
AI-OWNED

Human Seat Question:
none

PIC break rule:
PIC BROKEN if any one of the four V13 operational witnesses fails at the
commitment boundary

Propagation:
NOT EXECUTED BY THIS REGISTER
```

The binding closes the semantic source gap. It does not validate FN126 Case
004 against a real self-update, establish MAL v0.2 generalization, authorize a
fresh validation, implement runtime, or permit automatic lineage scanning or
Canon propagation.

## Entry 002 — Guard Continuity

```text
Term / Joint:
Guard Continuity for Case 004

Current Local Use:
Necessary condition in self-update evaluation in
validation/field_note_126_case_004_aspire_anchored_independent_evaluation.md

Lineage Classification:
LINEAGE-CLOSED / LOCAL-BINDING-REQUIRED

Authoritative Source:
1. Current explicit Human Seat / Forward-only delta preserved in FN126 Case
   004;
2. Decision-OS V7 Final EN v1.0, DOI 10.5281/zenodo.20422099,
   gateway path notes/v7-final/Decision-OS_V7_Final_EN_v1.0.pdf,
   Git blob 1892d785d7d6b824355b9996bdee8e2a69f0f448;
3. Decision-OS V7 Core, DOI 10.5281/zenodo.17932554,
   gateway path notes/Decision_OS_V7__Aspire_Intelligence_for_AGI__EN_Core.pdf,
   Git blob 13e60a16cd69e2dc9f31e8e9dcd14237ce70a820;
4. Decision-OS V5 Revised, DOI 10.5281/zenodo.19828435,
   gateway path notes/v5/Decision_OS_V5_Revised_SiriusA2_2026-04-28.pdf,
   Git blob c6163eddb58a1bb94154608e511cb1c0e641e124,
   only for the explicitly inherited outer irreversible-execution and
   human-control boundary.

Source As-of / Version:
FN126 Case 004 Forward-only Human Seat delta / 2026-07-22;
V7 Final EN v1.0;
V7 Core;
V5 Revised SiriusA2 / 2026-04-28;
gateway retrieval commit 07f20eb5bbea1e49d0b5f60fc4962c45ddcd3704

Later Forward-only Deltas:
The current explicit Human Seat / FN126 Case 004 delta has first precedence.
V7 Final is the current authoritative V7 formulation; V7 Core is preserved as
its earlier formulation. V5 Revised is consulted only for the outer boundary
that V7 inherits. No older source may overwrite the current Human Seat delta,
and no V13 mapping may be restated as a V5 or V7 source axiom.

Source-Defined Core:
Guard is a non-negotiable and constitutive admissibility boundary. It inherits
from V5 an outer irreversible-execution and human-control boundary and is
extended by V7 into internal self-update and recursive operation. Guard
determines how far updating may proceed and where it must stop, and remains
distinct from Guardian and PIC.

The bounded V5 outer boundary preserves only: life-first orientation; human
final consent and responsibility; Hold-first confirmation; rejection and
revoke availability; no bypass into protected irreversible execution; no
automatic execution without required confirmation; and no score-only Stop or
Freeze without an independent non-score condition.

The bounded V7 inner boundary preserves only: prevention of short-horizon noise
and reward capture; unsafe optimization and uncontrolled divergence;
self-preserving closure becoming the recursive objective; loss of external
anchoring or safety-signal visibility; Carrier-destroying and non-recoverable
recursive regimes; and loss of the proceed/stop boundary under recursion.

Current-Layer Operational Mapping:
V13 maps the source-defined Guard core to four operational witnesses: Boundary
Persistence / Non-Vacuity, Human-Governed Irreversibility, Inner-Guard
Non-Capture, and Recursive Enforceability / Recoverable Control. These are V13
evaluation mappings, not V5 or V7 source axioms. Passing them is necessary, not
sufficient, for Case 004; it is neither runtime validation nor proof of
self-evolution.

Minimum Witnesses:
- Boundary Persistence / Non-Vacuity: every applicable proceed/stop boundary
  remains explicit before and after the update, is not silently weakened, and
  retains an operative witness, mechanism, or downstream Gate.
- Human-Governed Irreversibility: protected irreversible execution cannot
  bypass Human Seat, confirmation, Hold, rejection, or revoke. Stop or Freeze
  cannot be justified by a score alone when an independent non-score condition
  is required.
- Inner-Guard Non-Capture: short-horizon reward, local optimization,
  self-preservation, self-expansion, or narrative coherence cannot justify
  bypassing Guard, hiding safety evidence, destroying the Carrier, or refusing
  independent anchoring.
- Recursive Enforceability / Recoverable Control: after repeated or
  internalized updating, Guard still blocks prohibited paths and preserves
  refusal, control, recovery, rollback, or safe stabilization before a
  non-recoverable regime.

Falsifiers / Break Conditions:
- Boundary Persistence / Non-Vacuity fails when an applicable proceed/stop
  boundary disappears, is silently weakened, or lacks an operative witness,
  mechanism, or downstream Gate.
- Human-Governed Irreversibility fails when protected irreversible execution
  bypasses Human Seat, confirmation, Hold, rejection, or revoke, or when a
  score alone produces Stop or Freeze despite a required independent non-score
  condition.
- Inner-Guard Non-Capture fails when a listed short-horizon or self-preserving
  driver is accepted as justification for Guard bypass, hidden safety evidence,
  Carrier destruction, or refusal of independent anchoring.
- Recursive Enforceability / Recoverable Control fails when recursion or
  internalization makes Guard unable to block a prohibited path or removes
  refusal, control, recovery, rollback, or safe stabilization before a
  non-recoverable regime.
- GUARD BROKEN when any applicable minimum Guard witness is lost or becomes
  vacuous and thereby reopens at least one source-grounded failure region:
  unsafe attractor, irreversible harm, unguardable update, or loss of execution
  boundary.
- GUARD UNKNOWN / HOLD when evidence is insufficient to establish preservation
  or breakage. Unknown is not preservation and is not permission.

Required Distinctions:
Guard is the invariant boundary condition. Guardian in V7 is an observed
long-horizon behavior under Guard. A V5 policy-defined guardian or verifier is
an external confirmation actor. Neither Guardian meaning is the V7 Guard
predicate itself.

Guard is the admissibility and stopping boundary. PIC is non-destructive
committed integration and canonical convergence. A Guard failure is not
inferred from PIC failure alone, and a PIC pass does not imply Guard
preservation.

Import Boundary:
Import from V5 only the explicitly inherited outer-boundary functions listed
above. Do not import the full SiriusA architecture, V5 scoring, duress model,
UI, ZK, multisig, deployment details, or the full C1–C9 failure map. Do not turn
V13 guard-like mechanisms into source definitions, invent numeric thresholds,
or claim runtime verification.

Reopen If:
A later explicit Human Seat / Forward-only delta changes Guard semantics or the
outer/inner boundary precedence; an authoritative source identity, artifact
blob, or gateway As-of no longer verifies; source proof becomes insufficient;
two materially valid authoritative meanings remain after As-of precedence;
evidence falsifies one of the four V13 witness mappings or shows that a witness
is vacuous; or an authorized real self-update exposes that preservation versus
breakage cannot be classified without revising the bounded mapping. UNKNOWN
routes to HOLD and never supplies permission.

Human Seat Required:
no
```

## Entry 002 Routing Receipt

```text
Guard lineage classification:
LINEAGE-CLOSED / LOCAL-BINDING-REQUIRED

Established Context Check:
CLOSED

Decision Route:
AI-OWNED

Human Seat Question:
none

Guard break rule:
GUARD BROKEN when any applicable minimum witness is lost or becomes vacuous
and reopens a source-grounded failure region

Guard unknown rule:
GUARD UNKNOWN / HOLD

Propagation:
NOT EXECUTED BY THIS REGISTER
```

This binding closes the Guard semantic and local-binding gap only. It does not
prove Guard preservation for an actual self-update, validate the four
witnesses, run Case 004, establish self-evolution, authorize runtime, or permit
automatic lineage scanning or Canon propagation.

## Completion Line

PIC and Guard Continuity are now reconnectable from their V13 uses to verified
lineage sources. Their source definitions remain separate from their bounded
V13 operational witnesses, and neither binding returns a Human Seat question
or claims runtime validation.
