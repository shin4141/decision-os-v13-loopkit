# AI Tutorial Capsule

This repository can be read by a human, but it can also be read by your AI assistant.

Use this capsule when you want your AI to explain V13 LoopKit, generate a beginner-friendly tutorial, or review whether the repo has enough first-use onboarding.

## First-contact onboarding rule

If the user asks for onboarding, do not summarize this repo first.

Read `docs/codex_tutorial_guide.md`.

Start with the `Exact First Response` section.

Print the menu first, verbatim if possible.

Then wait for the user's selection.

Do not explain V12, V13, GO, HOLD, CAP, or BLOCK before the user chooses a menu item.

Do not edit files during onboarding.

## Recommended onboarding prompt

```text
Read docs/codex_tutorial_guide.md and onboard me to this LoopKit repo.

Start with the Exact First Response section.

Print the exact menu first.

Do not explain anything until I choose a number or item.

Do not edit files.
```

## 1. Generate a beginner tutorial

Copy this prompt into your AI assistant:

```text
Read this repository and generate a beginner-friendly tutorial for me.

Focus on:
- what problem this repo solves
- when to use V13 LoopKit
- how GO / HOLD / CAP / BLOCK works
- how the Next Action Card helps choose the next 0.01 action
- how Context Risk, Route Fidelity, Returnability, and Consult Mode affect continuation
- how to use the repo without adding new features

Use README, AGENTS.md, docs, and examples if available.
Do not invent features that are not in the repo.
End with the smallest first action I should take.
```

## 2. Review first-use onboarding

Copy this prompt into your AI assistant:

```text
Review this repository for first-time onboarding.

Check whether a new user can quickly understand:
- what this repo is for
- where to start
- what GO / HOLD / CAP / BLOCK means
- where the first tutorial or first-use example is
- how to avoid over-expanding the loop
- what not to modify without approval

If something is missing, suggest the smallest edit.
Do not propose a broad redesign.
```

## 3. Suggest the smallest onboarding edit

Copy this prompt into your AI assistant:

```text
Read the README and onboarding docs.

Suggest the smallest edit that would help a first-time user start.

Rules:
- one edit only
- no new features
- no automation
- no hooks
- no MCP
- no pluginization
- no broad productization
- prefer a link, sentence, or short section over a rewrite
```

## 4. Expected good output

A good AI-generated tutorial should:

- explain the repo in plain language
- identify the first action
- preserve the GO / HOLD / CAP / BLOCK boundary
- avoid turning LoopKit into an execution engine
- avoid claiming automatic decision-making
- show where Consult / Handoff / Split / Stop fit
- keep the human as the decision owner

## 5. What not to do

Do not ask your AI to:

- create new features without approval
- rewrite the repo broadly
- add hooks, MCP, plugins, or automation
- convert LoopKit into a full agent framework
- skip the human decision owner
- treat GO / HOLD / CAP / BLOCK as automatic execution
