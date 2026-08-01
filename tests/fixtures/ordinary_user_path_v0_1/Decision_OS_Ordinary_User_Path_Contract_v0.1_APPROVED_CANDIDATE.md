# Decision-OS V9
# Ordinary User Path Contract v0.1 — APPROVED CANDIDATE

Status:
Product-path contract only.

Primary Layer:
V9 — Product Adoption

Supporting Layer:
V13 — Internal Governance

Decision Owner:
Shin

Implementation Authority:
NONE

This Contract does not authorize repository changes, implementation, merge,
release, publication, model invocation, or rollout.

---

## 1. Purpose

The Ordinary User Path must allow a person to preserve a Contract without
operating Decision-OS internal governance machinery.

The user must not be required to understand or manually operate:

- Guided Intake;
- Original Request capture;
- Copy for Pro;
- external model routing;
- strict JSON schemas;
- Producer labels;
- Request, Draft, or Freeze IDs;
- SHA-256 or byte counts;
- provenance atoms;
- support records;
- occurrence indexes;
- quoted-payload wrappers;
- Forward-only supersession;
- validator field paths;
- receipt serialization.

These mechanisms may remain internally necessary.

Their operational burden belongs to the product, not to the user.

---

## 2. Fixed Ordinary User Path

The standard path contains no more than three user actions.

### Action 1 — Select the Contract

User-visible action:

&gt; Select Contract

The user chooses one supported local Contract file.

Supported initial formats:

- `.md`
- `.txt`

After selection, Companion performs the remaining intake preparation without
requiring another routing action.

The user must not separately press:

- Import Contract;
- Use in Guided Intake;
- Capture Original Request.

---

### Action 2 — Review the Interpretation

Companion displays one review surface containing only:

1. What this Contract preserves;
2. What counts as completion;
3. What must not be changed;
4. What remains unresolved;
5. What this operation does not authorize.

The standard user-facing states are:

- `Ready to fix`
- `Needs your confirmation`
- `Cannot be fixed safely`

Internal terms must not appear in the standard surface, including:

- PRESERVED;
- TESTABLE;
- authority_claim;
- UNKNOWN type identifiers;
- schema_version;
- atom;
- support;
- occurrence;
- Producer label;
- Request ID;
- Draft ID;
- Freeze ID;
- SHA-256.

Those details may appear only in an optional advanced or receipt-details view.

The user reviews meaning, not transport or schema mechanics.

---

### Action 3 — Fix the Contract

User-visible action:

&gt; Fix this Contract

Before fixation, Companion performs one final validation.

When validation passes, Companion:

- freezes the reviewed interpretation;
- creates the native fixation receipt;
- preserves the receipt locally;
- displays the completed state.

User-visible completion message:

&gt; Contract fixed.
&gt;
&gt; This Contract can now be used to resume the same decision in this repository
&gt; without reconstructing its meaning from scratch.

The user must not separately operate:

- Import Strict JSON Draft;
- Freeze Guided Intake;
- receipt export;
- receipt hashing.

---

## 3. Product-Owned Internal Route

After Contract selection, the product owns the internal route:

```text
Read exact source
→ establish raw identity
→ classify source role
→ establish quoted-payload boundary when required
→ capture Forward-only request state
→ generate structured interpretation
→ validate schema and provenance
→ evaluate Objective fidelity
→ evaluate Completion testability
→ preserve Do Not Touch
→ preserve typed UNKNOWN
→ check authority inflation
→ prepare review surface
````

After human approval:

```text
revalidate current state
→ Freeze
→ generate native receipt
→ verify receipt identity
→ save locally
→ display completion
```

No ordinary-user action may be inserted between these internal steps unless a
material human decision is genuinely required.

---

## 4. Governance That Must Remain Intact

Simplification must not remove or weaken:

* exact raw-source identity;
* UTF-8 byte identity where applicable;
* SHA-256 binding;
* Forward-only history;
* supersession traceability;
* quoted-payload boundary validation;
* Objective fidelity evaluation;
* Completion testability evaluation;
* Do Not Touch preservation;
* typed UNKNOWN preservation;
* authority-inflation blocking;
* fail-closed validation;
* immutable Freeze identity;
* native receipt identity;
* repository As-of binding.

The product may hide these mechanisms from the ordinary surface.

It may not silently omit them.

---

## 5. Model and Draft Responsibility

The ordinary path must not require the user to:

* open an external Pro chat;
* attach a generated prompt;
* wait for a model-generated JSON object;
* paste JSON into Companion;
* repair schema fields;
* add provenance labels;
* diagnose model-format errors.

Structured generation and schema validation are product responsibilities.

A model-produced object must not become active merely because it is syntactically
valid.

It must pass the same fidelity, provenance, authority, and completion controls
before being shown as fixable.

---

## 6. Error Responsibility

A failed internal operation must remain visible until resolved or dismissed.

Errors must not disappear through automatic refresh.

The error must appear next to the action that failed.

The standard error surface contains:

```text
What failed
Current state
Whether anything was fixed
Whether user action is required
```

Example:

&gt; Contract could not be fixed.
&gt;
&gt; The Contract boundary could not be verified.
&gt;
&gt; Nothing was fixed.
&gt;
&gt; No action is required from you while Companion attempts a safe recovery.

The user must not be asked to inspect:

* browser developer tools;
* server logs;
* JSON paths;
* backend state files;
* hidden global error regions;
* hashes;
* schema definitions.

---

## 7. Automatic Recovery Boundary

Companion may automatically recover when the repair is deterministic and does
not change meaning.

Examples:

* reconstructing an internal transport object;
* regenerating schema-valid structure from already approved fields;
* retrying a transient local request;
* restoring a locally available native receipt;
* recreating an internal quoted-payload wrapper without changing source bytes.

Companion must stop and ask one bounded question when recovery would require:

* changing the Objective;
* changing the Completion Line;
* changing Do Not Touch;
* resolving a material UNKNOWN;
* expanding authority;
* choosing between conflicting meanings;
* accepting a changed Contract identity.

Only one active clarification question may be shown at a time.

---

## 8. Advanced and Audit Details

The ordinary surface remains meaning-first.

An optional details surface may expose:

* raw source identity;
* SHA-256;
* byte size;
* Request ID;
* Draft ID;
* Freeze ID;
* interpretation SHA-256;
* receipt SHA-256;
* repository identity;
* Forward-only history;
* quoted-payload verification;
* internal Gate;
* model and Producer identity.

Opening details must not be required to complete the ordinary path.

---

## 9. Fixed Exclusions

This Contract does not define or authorize:

* Transfer;
* Runner execution;
* Builder execution;
* Pro or Fable invocation policy;
* Verified Save;
* Verified Reuse;
* Never Again Mode;
* repository-default application;
* cross-repository portability;
* clone or fork semantics;
* reset or recount semantics;
* release or publication;
* external certification;
* third-party verification;
* account, billing, or cloud synchronization;
* mobile or cross-device behavior.

These remain separate paths or later contracts.

---

## 10. Initial Acceptance Conditions

The first implementation qualifies only when all of the following are proven.

### User-path conditions

1. A new user can complete fixation through no more than:

   * Contract selection;
   * interpretation review;
   * fixation approval.

2. No external chat is required.

3. No JSON is shown or pasted.

4. No Producer label is entered manually.

5. No manual Wrapper creation is required.

6. No hash, byte count, Request ID, Draft ID, or Freeze ID is required for
   ordinary completion.

7. No hidden or disappearing error is required to diagnose a failed action.

### Governance conditions

8. Exact raw identity remains preserved.

9. Forward-only history remains preserved.

10. Quoted payloads cannot become active execution authority.

11. Active text outside a quoted payload remains active.

12. Objective fidelity must be acceptable before fixation.

13. Completion must be testable before fixation.

14. Material UNKNOWN must block fixation unless resolved.

15. Authority inflation must block fixation.

16. Freeze and receipt identities remain verifiable.

### Regression conditions

17. The existing fixed Product Contract can complete through the new path.

18. Its resulting interpretation remains equivalent to the current frozen
    interpretation.

19. The simplified path does not alter:

    * Contract identity;
    * Objective;
    * Completion Line;
    * Do Not Touch;
    * authority boundary;
    * repository identity.

20. No Transfer, Run, model execution, release, or publication begins as a
    consequence of fixation.

---

## 11. Friction Evidence Requirement

The next implementation must record the ordinary-path run as friction evidence.

Record at minimum:

* visible user actions;
* repeated actions;
* waiting points;
* unclear states;
* user interventions;
* failed automatic recoveries;
* clarification questions;
* time to fixation;
* internal errors hidden from the standard surface;
* any step where the user must understand an internal Decision-OS term.

A newly observed problem does not automatically authorize expansion.

It becomes a candidate for the next Forward-only Product Contract delta.

---

## 12. Change Rule

This Contract may be changed only through a Forward-only delta stating:

* observed failure;
* affected user step;
* reason for change;
* governance impact;
* compatibility impact;
* rollback path;
* re-evaluation condition.

Do not rewrite this Contract retroactively merely because a later ordinary run
reveals another friction layer.

---

## 13. Gate

Current Gate:

`READY FOR FIXATION — IMPLEMENTATION HOLD`

Implementation remains blocked until this Contract is fixed and its exact
implementation boundary is separately authorized.

---

## 14. Completion Line

Ordinary User Path Contract v0.1 is complete when:

1. the ordinary surface is fixed to three user actions;
2. all other current fixation operations are assigned to the product;
3. internal governance invariants are explicitly preserved;
4. automatic-recovery and human-question boundaries are fixed;
5. implementation acceptance conditions are testable;
6. unobserved future problems remain outside the current scope.

---

## 15. Next Actor

Next Actor:

`AI / Companion fixation route`

Shin is not responsible for schema conversion, formatting, routing, hashing,
or routine fixation cleanup.

No implementation is authorized by this Contract alone.
