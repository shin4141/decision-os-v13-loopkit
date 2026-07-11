# New Repo Scaffold Standard

When creating a new repo/workspace capsule, include the minimal restartability scaffold.

## Required Files

- README.md
- AGENTS.md
- handoff/current_handoff.md
- docs/handoff_command.md

If the repo may involve external contact, also include:

- docs/contact_readiness_card.md

If the repo may involve audit work, also include:

- docs/audit_card_template.md

## Handoff Command Requirement

- `docs/handoff_command.md` must define how to produce a compact, paste-ready next-chat handoff.
- `AGENTS.md` must include:

```text
When the user selects `Handoff`, follow `docs/handoff_command.md`.
```

## Required Handoff Fields

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

`Current State` must distinguish completed work, unresolved work, and routine cleanup. `What the Receiving AI Now Owns` must assign the unresolved executable responsibility; `Next Owner` alone is not a substitute for that transfer. If ownership cannot be established, write `UNKNOWN` and do not imply accepted transfer, PASS, or closure.

`First One Action: none` is valid only when `Active Branch: none` and `Next Authorized Action: none` are both explicit, no unfinished work or `UNKNOWN` ownership remains, and no routine investigation, diff, verification, Git operation, or cleanup remains executable by the receiving AI. Otherwise the handoff must name the earliest bounded action and its owner.

## Do Not Authorize

Adding this scaffold does not authorize implementation, outreach, public posting, pricing, release, scraping, API, automation, or target selection.
