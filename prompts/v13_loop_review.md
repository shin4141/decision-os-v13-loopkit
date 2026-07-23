# V13 Loop Review Prompt

Copy and paste this prompt after a completed work report, V12 Completion Record, agent summary, or project update.

```text
You are reviewing a completed loop using Decision-OS V13.

V12 asks whether the work is actually complete and restartable.
V13 asks whether the next loop should be run, held, capped, or blocked.

Canon:
Capability without controllability is not intelligence.

Principle:
A Compound Loop improves the condition from which the next loop begins.

Task:
Convert the completed work state below into a V13 Loop Record.

Use only these gate outcomes:
GO / HOLD / CAP / BLOCK

Gate rules:
- GO only if the next loop is positive-EV, controllable, residue-producing, and Carrier-preserving.
- HOLD if sign, cost, residue, or Carrier impact is unclear.
- CAP if the loop is valid only under a fixed limit.
- BLOCK if the loop damages Aspire, Carrier, or re-entry capacity.
- If uncertainty is high, prefer HOLD or CAP over GO.
- If using CAP, specify a concrete limit.
- If using BLOCK, state what must change before reconsideration.

After inspecting the completed outcome and residue, and before selecting the
next variable or granting compound-loop improvement credit, answer:

1. What principle or improvement does the loop claim to have learned?
2. Was that claim tested under a comparable implementation-load condition?
3. What behavior changed?
4. Which protected object could have been sacrificed under load?
5. Was that protected object preserved?
6. What cost was deferred to the next subject?
7. Who owns that cost?
8. Was receipt or acceptance confirmed?
9. Does the next loop begin lighter, neutral, heavier, or unknown?
10. What closure or re-evaluation condition exists?

Do not grant improvement credit because the agent states the correct principle,
apologizes, summarizes the failure, or promises future compliance.

Use `NOT TESTED / WITHHELD` when only statement-layer understanding exists.
Use `PROVISIONAL` only when changed behavior exists but the load is lower,
materially different, or not yet shown to be comparable. Use `PASS CANDIDATE /
GRANTED — CASE-BOUNDED` only when comparable-load changed behavior preserves
the protected object, creates no unowned Successor Debt, and cites its evidence
source. A Successor Debt candidate does not automatically require `BLOCK`.

Improvement Credit is evidence classification, not execution authority. The
classification block below does not replace the existing `GO / HOLD / CAP /
BLOCK` decision.

Return this exact structure:

# V13 Loop Record

## 1. Previous Loop
<what was just completed>

## 2. V12 Status
PASS / DELAY / BLOCK / UNKNOWN

## 3. Residue
- <reusable artifact, learning, template, decision, evidence, or capability>

## 4. Load-Bearing Improvement Evidence
- Declared principle or claimed improvement: <claim>
- Comparable implementation-load condition: <condition or not observed>
- Observed behavior under load: <behavior or not observed>
- Protected object preserved: <object and evidence>

## 5. Deferred Cost / Successor Debt
- Deferred cost left to the next subject: <cost or none>
- Successor owner: <owner or unknown>
- Receipt / acceptance: <confirmed, absent, or unknown>
- Effect on next-loop starting condition: LIGHTER / NEUTRAL / HEAVIER / UNKNOWN
- Disclosure status: <status>
- Closure / repayment / re-evaluation condition: <condition or none>

Load-Bearing Compliance:
<NOT TESTED / PROVISIONAL / PASS CANDIDATE / FAIL>

Successor Transfer:
<VALID TRANSFER / SUCCESSOR DEBT CANDIDATE / NONE / UNKNOWN>

Improvement Credit:
<WITHHELD / PROVISIONAL / GRANTED — CASE-BOUNDED>

Evidence:
<source references>

## 6. Next Variable
<the one variable the next loop would test or improve>

## 7. Carrier Impact
- Fatigue: low / medium / high / unknown
- Money: low / medium / high / unknown
- Attention: low / medium / high / unknown
- Credibility: low / medium / high / unknown
- Trust: low / medium / high / unknown

## 8. Re-entry Capacity
Preserved / Reduced / Damaged / Unknown

Notes:
<whether the operator/system can restart cleanly>

## 9. Gate
GO / HOLD / CAP / BLOCK

## 10. Cap or Recheck
<concrete cap, recheck condition, or reconsideration requirement>

## 11. Next Loop Command
<the exact next action allowed by the gate>

Completed work state:
<paste the completion record, agent summary, project note, or finished work report here>
```
