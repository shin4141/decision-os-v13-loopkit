# Field Note 142 — Risk-Bounded Authority Freshness

Status: Verification pending

Classification: Field Note / design candidate

Promotion: NONE

Implementation authority: NONE

Layer: V13 — Compound Loop / Authority / Multi-Runtime Control

## Idea Provenance

An external technical discussion surfaced the candidate recorded here. The
discussion is idea provenance, not operational proof, external qualification,
or evidence that current V13 already implements the candidate.

## Existing V13 Evidence Boundary

Canonical repository evidence already establishes bounded, local, or
supplied-state authority checks in specific supported paths.

Already present or partially related:

- Role Contracts bind task, Role, assignee, execution context, exact target,
  typed operations, lifecycle, and completion;
- Role validation uses explicit snapshot identity, `as_of`, and revocation
  fields;
- missing, unknown, stale, revoked, mismatched, or internally conflicting Role
  inputs do not become validator-level `ACTIVE`;
- supported Companion file-mutation paths can apply an active compound
  authority-envelope preflight before a typed Create or Modify decision is
  reused or executed; and
- Verified Save has bounded typed operations, repository/path identity, local
  revocation, and explicit unsupported cases.

These boundaries are evidenced by the
[Role-bound Specialist System](../docs/role_bound_specialist_system_v0_1.md),
the [Role validator](../decision_os/role_contract.py), the
[Acceleration Engine](../decision_os/acceleration/engine.py), the
[Companion controller](../decision_os/companion/controller.py), and the
[Verified Save boundary](../docs/verified_save_claude_mvp_v0_1.md).

They do not establish that supplied state is authentic, globally complete, or
atomically shared across independent runtimes. The Role-bound specification
explicitly limits `ACTIVE` to validator-level consistency at the supplied
validation snapshot, and the
[current audit ledger](../docs/audit/v13_stage5_audit_coverage_ledger_v0_1.md)
records distributed multi-machine transaction as not established.

## Surfaced Problem

Two genuinely independent runtimes may hold different views of the same
authority state.

Conceptual example:

```text
Runtime A: REVOKED
Runtime B: still sees VALID
```

Even if each local validator applies its rules correctly to the state it sees,
Runtime B may retain usable stale authority unless the consequential execution
path establishes sufficiently current authority before effect.

This shifts the research question from only:

```text
How should permission be defined?
```

toward:

```text
How fresh must authority evidence be at the moment of effect?
```

The example is a problem statement, not evidence that this divergence has been
reproduced in current V13 runtimes.

## Core Distinctions

```text
Purpose continuity
!=
Authority continuity
```

and:

```text
Permission exists
!=
Permission is sufficiently fresh for this effect
```

An unchanged task purpose does not prove that execution authority remains
current. Likewise, physically present permission state does not by itself make
that state sufficient for a consequential action.

## Design Candidate

```text
Authority may need a freshness requirement, not only a validity state.
```

Candidate authority evidence may include:

- authority-state identity or version;
- last validated `as_of`;
- freshness age;
- revocation visibility;
- authority-state source or provenance; and
- execution-time validation status.

A consequential action could then require a freshness boundary appropriate to
that effect.

Conceptual direction:

```text
risk increases
-> required authority freshness increases
-> required freshness cannot be established
-> fail closed / HOLD
```

No threshold, field schema, ordering rule, or enforcement mechanism is selected
by this note.

## Risk Is Not Reversibility Alone

Do not reduce the candidate to:

```text
reversible = low risk
```

Freshness requirements may depend on multiple dimensions, including:

- operation risk;
- reversibility;
- protected-object impact;
- authority sensitivity;
- external side effects;
- owner-intent sensitivity; and
- ability to reconstruct or compensate after failure.

Examples only, not fixed policy:

- read-only inspection of non-sensitive local material may justify a different
  freshness requirement from deployment or publication;
- a Git-revertible file change can still violate current owner intent; and
- a read can still be high-risk when protected or private information is
  involved.

Repository evidence does not authorize a numeric risk lattice, so none is
created here.

## Effect-Time Sufficiency Rather Than Perfect Propagation

This candidate is not merely a proposal to distribute revocation faster.

An alternative control strategy is:

> Old permission may still exist in a runtime, but existence alone should not
> make it sufficient for a consequential effect.

Stale authority state could remain physically present while the execution path
fails closed unless the required current authority can be established at the
moment of effect. Whether that boundary should use authoritative lookup, a
lease, version, epoch, TTL, or another mechanism remains unresolved.

## Not Established

Current canonical evidence does not establish:

- one authoritative cross-runtime authority source;
- guaranteed immediate revocation propagation to every runtime;
- end-to-end distributed authority-state consistency;
- a risk-tiered authority-freshness policy;
- permission TTL semantics by operation class;
- proof that stale authority cannot be consumed by every possible independent
  runtime; or
- a production-grade distributed authorization protocol.

Existing validator and preflight behavior must not be expanded into any of
these claims.

## Unresolved Research Questions

1. Should every consequential effect require fresh authoritative lookup, or can
   some bounded operations use leased or time-bounded authority?
2. Should freshness requirements differ by operation class?
3. Which dimensions should determine freshness: risk, reversibility, protected
   objects, externality, owner-intent sensitivity, or another factor?
4. Is authority freshness better represented by TTL, version, epoch, lease,
   revocation generation, authoritative lookup, or another mechanism?
5. How should an offline or partitioned runtime behave when it cannot establish
   sufficiently fresh authority?
6. Can “stale authority may exist but cannot produce a high-risk effect” provide
   a safer and cheaper boundary than perfect instantaneous revocation
   propagation?

These questions preserve the candidate surface. They do not authorize research
expansion, implementation, or policy selection.

## Claim Boundary

This Field Note does not claim:

- that Risk-Bounded Authority Freshness is canonical V13 architecture;
- that stale low-risk authority is currently allowed;
- that a freshness threshold has been chosen;
- that distributed revocation is solved;
- that external OS or multi-runtime qualification is complete;
- that existing validators provide end-to-end runtime independence; or
- that this candidate should automatically become implementation work.

## Re-Evaluation Triggers

Re-evaluate this candidate only when bounded evidence supplies at least one of:

- an inspectable independent-runtime authority divergence;
- a comparison of effect-time lookup and bounded lease behavior;
- an operation-specific freshness requirement with an explicit falsifier; or
- contrary evidence showing that existing authority identity and revocation
  boundaries already prevent the identified stale-effect path.

Until then, keep verification pending and promotion at `NONE`.

## Gate

```text
Field Note record: PASS
Verification: Pending
Promotion: NONE
Implementation authority: NONE
Canonical behavior change: BLOCK
Current Gate after recording: HOLD — no automatic next loop
```

## Completion Line

V13 now preserves Risk-Bounded Authority Freshness as a verification-pending
design candidate, distinguishes it from current bounded validator/preflight
behavior, and grants no implementation, promotion, or canonical authority.
