# External Intelligence First-Contact Prompt

Use this read-only prompt to let ChatGPT, Claude, or Codex inspect the public
repository before you decide whether any part of it is useful. No fork, clone,
installation, account, repository attachment, or file change is required.

## Copy-paste prompt

```text
Inspect the actual public repository before explaining External Intelligence:

https://github.com/shin4141/decision-os-v13-loopkit

At minimum, inspect these public files:

- README.md
- AGENTS.md
- docs/external_intelligence_onboarding.md
- docs/ai_reading_order.md
- docs/field_note_lifecycle.md

Then respond in this order:

1. Briefly state the recognizable problem this repository addresses and what
   External Intelligence changes. Explain only mechanisms supported by the
   repository files you actually inspected. Center selected past decisions,
   failure boundaries, reusable knowledge, restart context, selective
   retrieval, and changed downstream judgment—not context compaction.

2. State exactly which requested files or surfaces you could access and which
   you could not access. Do not infer unseen code, private implementation, or
   unavailable behavior. Do not present creator-owned observations as
   third-party certification, and do not claim cache or quota causality.

3. Show the complete participant-facing section named
   "English first-contact — External Intelligence Quest Board" from
   docs/external_intelligence_onboarding.md.

Until I select a Quest, do not fork or clone the repository, begin setup,
modify files, create a handoff, save a Note, promote a Rule, recommend a
specific Quest, or make External Intelligence depend on an optional Companion.

After I select a Quest, inspect only the actual public files, rules, docs,
relevant Field Notes, and implementation needed to explain that Quest. State
any remaining evidence or availability boundary instead of guessing.
```

## What to expect

The first response should be a short repository-grounded orientation, a compact
access disclosure, and the English Quest Board. Viewing or choosing a Quest does
not authorize setup or file changes. Forking is a later, optional step only if
you want to grow the public structures in your own workspace.
