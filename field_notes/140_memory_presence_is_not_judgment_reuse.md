# Field Note 140 — Memory Presence Is Not Judgment Reuse

Status: Verification pending

As-of: 2026-08-20 JST

## Observation

An external practitioner described a long-running AI coding workflow that had already accumulated substantial external memory and operational records.

Reported one-day snapshot:

- memory (`.md`): 1,488 files
- OK wiki: 472 entries
- judgment-miss ledger: 410 entries
- automatic recall triggers: 5
- triggers whose underlying memory was actually opened and used for judgment: 1

The practitioner reported that the other four recall events surfaced only a filename and one-line summary. Reading the underlying memory required another explicit action, and those memories were not opened.

The same report contained two stronger failure observations.

First, an old memory claimed that `MEMORY.md` was Git-managed. That mutable-state claim had become stale: the file had later been explicitly untracked. The stale memory induced a long `git log` investigation before the practitioner established that the historical record was wrong and corrected the comment.

Second, an index had a 200-line / 25 KB ceiling. Material beyond the ceiling was silently omitted, leaving a large fraction of stored material outside the effective recall surface.

The practitioner therefore summarized the current result conservatively: stored memory changed one judgment that day, but the observed automatic-recall path was much weaker than expected, and stale memory could actively increase search cost or induce a wrong expectation.

## Structural distinction

This suggests a useful separation:

```text
memory exists
  != memory is routed
  != source is actually read
  != source is still current
  != source legitimately changes judgment
```

The existence of a record is therefore not enough to call it reusable intelligence.

A practical reuse chain is closer to:

```text
store
-> route
-> inspect source
-> revalidate current applicability
-> apply to the present judgment
```

Failure at any joint can turn memory into inert storage or, in the stale-memory case, into negative guidance.

## Candidate implications

These are candidates, not promoted rules.

1. **Routing should lead to the actual source when the judgment depends on it.**
   Surfacing only a filename or one-line summary can create nominal recall without real reuse.

2. **Mutable present-state claims need an expiry or revalidation boundary.**
   A statement that was true at one As-of can become false while remaining linguistically plausible.

3. **Immutable facts and As-of facts are safer memory surfaces than unqualified present-tense status.**
   When mutable status is preserved, the memory should retain the As-of date and a recheck condition rather than pretending to be permanently current.

4. **Index truncation is a memory-integrity problem, not only a capacity problem.**
   Silent omission can make stored memory appear available when it is not actually reachable through the active route.

5. **More stored memory does not imply better judgment.**
   Recall quality depends on selection, freshness, source inspection, and present-use admission.

## V11 connection

The observation is consistent with the V11 Reconnectable Forgetting problem: long-horizon memory must become lighter without losing the path back, while compressed or retained memory must not silently upgrade stale conditions into current permission.

This Field Note does not claim that V11 solves the practitioner’s workflow. A useful next test would be to let the practitioner’s AI read V11 and then re-evaluate a bounded sample of existing memories for:

- active / still current
- revalidation required
- compressible
- superseded or stale
- archive / downgrade candidate

The output should remain advisory unless separately verified.

## Relation to existing V13 structure

This observation supports, but does not prove, the current V13 separation between Field Notes as advisory memory and current execution authority.

It also strengthens the practical reason for a small `AGENTS.md` router: when a judgment depends on a historical structure, the router should point to the relevant source and require actual inspection before a permissive current Gate is inferred.

## Non-claims

This note does not establish:

- a population-level failure rate for memory systems;
- that automatic recall is generally ineffective;
- that the practitioner’s 1,488 memories are badly designed as a whole;
- that stale memory is more harmful than missing memory in general;
- that any specific retention or deletion policy is optimal;
- that V11 or V13 improves memory quality without a separate test.

## Re-evaluation trigger

Re-evaluate this note when either:

- another independent external workflow shows the same store -> route -> read -> revalidate -> judgment failure chain;
- a bounded V11-style memory review materially changes downstream decisions or reduces stale-memory search cost; or
- contrary evidence shows that summaries without source inspection preserve current judgment reliably enough that the extra read/revalidation step is unnecessary.
