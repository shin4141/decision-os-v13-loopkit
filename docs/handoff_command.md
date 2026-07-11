# Handoff Command

When the user selects `Handoff`, generate a paste-ready handoff for the next chat, next AI, or next Codex session.

This command does not start new work.
This command does not make new judgments.
This command does not choose a new target.
This command only transfers the current operational state.

## Required Output Fields

- Target Layer
- Repo Root
- Current State
- Current Gate
- Active Branch
- Next Authorized Action
- Completion Line
- Missing Closure
- Next Owner
- What the Receiving AI Now Owns
- First One Action
- Do Not Continue Boundary
- What must not be returned to the Decision Owner

## Rules

- Keep it compact.
- Make it paste-ready.
- Include only current state, not speculative plans.
- If a field is unknown, write `UNKNOWN` and explain why in one line.
- Do not hide missing closure.
- `Current State` must distinguish completed work, unresolved work, and routine cleanup. `What the Receiving AI Now Owns` must assign the unresolved executable responsibility; `Next Owner` alone is not a substitute for that transfer.
- If current-state ownership cannot be established, write `UNKNOWN`. Do not imply accepted transfer, PASS, or closure.
- Do not return routine cleanup to the Decision Owner if an execution agent can close it.
- `First One Action: none` is valid only when `Active Branch: none` and `Next Authorized Action: none` are both explicit, no unfinished work or `UNKNOWN` ownership remains, and no routine investigation, diff, verification, Git operation, or cleanup remains executable by the receiving AI.
- If any such work remains, name its earliest bounded step as `First One Action` and assign its owner. Do not use `none` to make an incomplete transfer appear closed.
- Do not authorize outreach, public posting, implementation, release, pricing, scraping, API, or automation unless already explicitly approved.
- End with a Completion Line.
