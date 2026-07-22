# Decision Lineage Reconnection Register v0.1

## Status

```text
Register specification: COMPLETE
Registered bindings: 1
First binding: PIC
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

## Completion Line

PIC is now reconnectable from its V13 use to verified V6, V7 Addendum, V8, and
V11 source identities, while its source definition remains separate from the
four bounded V13 operational witnesses and no Human Seat question is returned.
