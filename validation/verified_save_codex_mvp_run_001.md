# Verified Save Codex MVP — Validation Run 001

## Receipt Identity

```text
Packet:
V13-VERIFIED-SAVE-CODEX-SOL-MVP-001

Correction Amendment:
V13-VERIFIED-SAVE-CODEX-SOL-MVP-001-A2

Live-Proof Closure:
V13-VERIFIED-SAVE-CODEX-SOL-LIVE-CLOSURE-001

Starting main:
02ddd7af50e2366eac0c042ae3671050df5e21e0

Branch:
codex/verified-save-codex-sol-mvp-v0-1

Approved pre-closure head:
c0ecd71f1ecad0692566ad831aca8268b72adc17

Validation date:
2026-07-27
```

## Classification

```text
LIVE_PROOF:
PASS

DETERMINISTIC_ENGINE:
PASS

CODEX_ADAPTER:
PASS

DEMO_GIF:
NOT_CREATED
```

`LIVE_PROOF=PASS` means the creator completed the bounded human-owned two-Run
demo. Run 1 created one Repository Default only after an explicit option-2
selection. A separate fresh Wrapper Run reused it without a second human
interrupt and reached `VERIFIED_SAVE` at the Wrapper-owned `turn/completed`
checkpoint.

`CODEX_ADAPTER=PASS` applies only to the companion-owned Codex app-server
surface tested here. It does not claim interception of an existing native
Codex Desktop session.

## Runtime Identity

```text
Adapter surface:
bundled Codex app-server over stdio

Authentication:
ChatGPT subscription

Model:
gpt-5.6-sol

Reasoning effort:
ultra

Service tier:
priority

Codex CLI/app-server version:
0.146.0-alpha.3.1
```

The runtime identity came from machine-readable app-server, account, model,
and adapter validation surfaces rather than agent prose.

## Human-Owned Two-Run Result

```text
Run 1 human selection:
explicit option 2 — Use for this repository

Run 1 status:
NORMAL_TERMINAL

Run 1 turn status:
completed

Run 1 model / effort / tier / CLI:
gpt-5.6-sol / ultra / priority / 0.146.0-alpha.3.1

Run 1 error type:
NONE

Run 2:
fresh Wrapper Run

Repeated human interrupt:
skipped / no second option prompt

Run 2 status:
VERIFIED_SAVE

Run 2 turn status:
completed

Run 2 model / effort / tier / CLI:
gpt-5.6-sol / ultra / priority / 0.146.0-alpha.3.1

Run 2 error type:
NONE

Verified Save counter:
1 Save

Verified Reuse counter:
1 Verified Reuse
```

Shin explicitly selected option `2` in Run 1. The fresh second Run reached the
same mechanically derived decision key, matched the active Repository Default,
skipped the repeated interrupt, completed normally, and produced
`VERIFIED_SAVE`. No agent, fixture, timeout, or automatic input substituted for
the human selection.

## Sanitized Receipt

```text
VERIFIED

1 Save
1 Verified Reuse

ESTIMATED RECOVERED

7.5 minutes
¥625
UNKNOWN tokens

Calculated from:
1 verified reuse × 7.5 estimated minutes per reuse × ¥5,000 per hour
tokens remain UNKNOWN until tokens_per_reuse is configured

Verified Save is a locally recorded proof-of-use event, not third-party
certification.
```

```text
Sanitized receipt path:
/var/folders/8p/njjq3zy14slbn9jvv4tt82dm0000gn/T/decision-os-verified-save-receipt-5f3e1db436bc.txt

Receipt SHA-256:
23c6ced038a0ca2b963ed84463fe25181bbc52dddf08b052e6f6725fb3c40780
```

This is creator-owned human live proof. It is not external-user adoption,
native Codex Desktop interception, or third-party certification. The 7.5
minutes and ¥625 human-time value remain estimates. Tokens are `UNKNOWN`
because `tokens_per_reuse` was not configured. The 1 Save and 1 Verified Reuse
counters are observed protocol results alongside the recorded Run statuses and
runtime identities.

## Validation Receipt

```text
Pre-closure focused Codex adapter tests / Python 3.14:
24 / 24 PASS

Pre-closure focused Codex adapter tests / Python 3.13:
24 / 24 PASS

Closure full suite:
220 / 220 PASS

Changed Markdown heading/fence and introduced local-link validation:
PASS / 0 introduced links / 0 missing introduced targets

Historical unresolved local-link references:
2 / pre-existing at the approved head / unchanged and out of scope

Protected v0.1 blobs and modes:
14 / 14 PASS

git diff --check:
PASS
```

No source or test file changed in the live-proof closure.

## Exact Closure File Boundary

### Create

1. `validation/verified_save_codex_mvp_run_001.md`

### Update

1. `docs/current_signal.md`
2. `handoff/current_codex_handoff.md`

The closure boundary is exactly these three evidence files. The pre-closure
implementation boundary remained exactly four files. No README, pricing, GIF,
release, tag, package, source, test, or public-post surface changed.

## Git and Draft PR State

```text
Draft PR:
#36 / OPEN / DRAFT

Approved pre-closure head:
c0ecd71f1ecad0692566ad831aca8268b72adc17

Merge:
NOT AUTHORIZED / NOT PERFORMED
```

The final branch-head SHA is verified after the closure commit and reported in
the completion receipt. A commit cannot safely embed its own hash as content,
so no self-referential SHA is claimed here.
