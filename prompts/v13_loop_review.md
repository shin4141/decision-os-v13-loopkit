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

Return this exact structure:

# V13 Loop Record

## 1. Previous Loop
<what was just completed>

## 2. V12 Status
PASS / DELAY / BLOCK / UNKNOWN

## 3. Residue
- <reusable artifact, learning, template, decision, evidence, or capability>

## 4. Next Variable
<the one variable the next loop would test or improve>

## 5. Carrier Impact
- Fatigue: low / medium / high / unknown
- Money: low / medium / high / unknown
- Attention: low / medium / high / unknown
- Credibility: low / medium / high / unknown
- Trust: low / medium / high / unknown

## 6. Re-entry Capacity
Preserved / Reduced / Damaged / Unknown

Notes:
<whether the operator/system can restart cleanly>

## 7. Gate
GO / HOLD / CAP / BLOCK

## 8. Cap or Recheck
<concrete cap, recheck condition, or reconsideration requirement>

## 9. Next Loop Command
<the exact next action allowed by the gate>

Completed work state:
<paste the completion record, agent summary, project note, or finished work report here>
```
