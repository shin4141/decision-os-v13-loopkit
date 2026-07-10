# Handoff Command

When the user selects `Handoff`, generate a paste-ready handoff for the next chat, next AI, or next Codex session.

This command does not start new work.
This command does not make new judgments.
This command does not choose a new target.
This command only transfers the current operational state.

## Required Output Fields

- Target Layer
- Repo Root
- Current Gate
- Completion Line
- Missing Closure
- Next Owner
- First One Action
- Do Not Continue Boundary
- What must not be returned to the Decision Owner

## Rules

- Keep it compact.
- Make it paste-ready.
- Include only current state, not speculative plans.
- If a field is unknown, write `UNKNOWN` and explain why in one line.
- Do not hide missing closure.
- Do not return routine cleanup to the Decision Owner if an execution agent can close it.
- Do not authorize outreach, public posting, implementation, release, pricing, scraping, API, or automation unless already explicitly approved.
- End with a Completion Line.
