# V13 LoopKit Use Cases

This layer makes Decision-OS V13 usable by copy-paste prompt.

Use it when a loop is complete, but the next loop is not automatically admissible.

```text
Completed work
        ↓
Copy-paste V13 Loop Review prompt
        ↓
GO / HOLD / CAP / BLOCK
        ↓
Next Loop Command
```

## Copy-Paste Prompt

Use [`prompts/v13_loop_review.md`](prompts/v13_loop_review.md) after a V12-style completion record, project summary, or finished work report.

The prompt asks for:

- previous loop
- residue
- next variable
- Carrier impact
- re-entry capacity
- gate
- cap or recheck condition
- next loop command

## Practical Use Cases

- [`use_cases/ai_coding_after_completion.md`](use_cases/ai_coding_after_completion.md): decide whether an AI coding agent should continue after completing a task.
- [`use_cases/public_posting_loop.md`](use_cases/public_posting_loop.md): decide whether public posting should continue, pause, cap, or stop.
- [`use_cases/research_loop.md`](use_cases/research_loop.md): decide whether research should deepen, pause for synthesis, run under limits, or stop.

## Gate Reminder

- GO: run the next loop because it is positive-EV, controllable, residue-producing, and Carrier-preserving.
- HOLD: wait because sign, cost, residue, or Carrier impact is unclear.
- CAP: run only under a fixed exposure limit.
- BLOCK: do not run the current loop form because it damages Aspire, Carrier, or re-entry capacity.

Do not treat completion as permission to repeat.
