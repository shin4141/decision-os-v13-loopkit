# Field Note 114 — Incident: Screenshot-dependent Gate Signal Miss

## Layer

V13 / Loop Gate / Public Surface Integrity

Adjacent layers:
- V9 As-of / Release integrity
- V12 Completion Integrity / false closure prevention
- V13 Loop Gate / GO-HOLD-CAP-BLOCK-PATCH-DROP
- V14 Resource Justice / avoiding Decision Owner inspection burden

## As-of Context

As-of date:

```text
2026-07-04 JST
```

Case:

```text
Entry Window Radar README public-surface closure
```

Decision Owner:

```text
Decision Owner
```

Related Entry Window Radar correction:

```text
Badge patched from “Status: FULL GO” to “Public surface: SOFT GO” at commit 796ee6f.
```

## Observed Failure

A README first-screen badge still displayed:

```text
Status: FULL GO
```

even though the actual gate state was:

```text
Public surface: SOFT GO
External posting: HOLD
```

This created a public-surface gate mismatch.

The rendered first screen signaled stronger permission than the actual gate ledger allowed.

## Detection

The issue was detected by the Decision Owner through a rendered GitHub screenshot.

It was not detected by the AI/Codex audit process before closure.

This matters because a public-surface PASS should not depend on the Decision Owner manually catching rendered gate-signal mismatches.

## Audit Failure

Codex later identified the badge, but downgraded it to WATCH.

The audit overweighted:

```text
body text
adjacent External posting HOLD badge
source-level README consistency
```

and underweighted:

```text
first-screen badge semantics
rendered public-surface impression
the strength of the phrase FULL GO
```

The adjacent HOLD signal did not neutralize the stronger FULL GO signal.

## Root Cause

The audit treated README text/source consistency as sufficient.

It did not enforce rendered first-screen gate-signal inspection.

First-screen badges were treated as decorative or secondary, rather than as primary gate claims.

In V13 terms:

```text
The audit checked source consistency, but missed rendered gate salience.
```

## Correction

The visible badge was patched from:

```text
Status: FULL GO
```

to:

```text
Public surface: SOFT GO
```

at commit:

```text
796ee6f
```

This patched the public surface.

However, the process failure remains important.

The correction should not be counted as a successful original audit.

It should be recorded as a human-detected process miss.

## V13 Interpretation

First-screen visible elements are gate signals.

The following are not decorative when they appear on a public project surface:

```text
badges
titles
subtitles
thumbnails
video first frames
GitHub About text
release labels
status labels
launch wording
ready wording
```

If these visible elements imply a stronger gate than the actual ledger, the public surface is not PASS.

## New Rule

```text
First-screen visible elements are gate signals.
```

Before declaring public-surface PASS, the receiving or executing AI must check rendered first-screen gate signals against the current gate ledger.

A public-surface PASS cannot rely only on README source, body text, or adjacent caveats.

## Prevention Checklist

Before public-surface PASS:

```text
1. Compare every visible badge against Current Gate.
2. Treat FULL GO / GO / ready / launch / public / release as high-risk words.
3. Inspect the rendered GitHub first screen, not only README source.
4. If rendered inspection is unavailable, declare UNKNOWN and do not close PASS.
5. Do not rely on adjacent HOLD text to neutralize a stronger GO signal.
6. If a human screenshot reveals the issue, classify it as a process failure, not successful audit.
```

## Public Surface Integrity Rule

A public surface is judged by what a first-time viewer sees first.

If the first screen says or implies GO, while the current ledger says SOFT GO / HOLD / CAP, the surface contains a gate-signal defect.

This is true even if lower sections contain the correct caveat.

## What V13 Must Learn

V13 must not only govern internal loop decisions.

It must also govern public-facing gate signals.

A repo can be internally correct and still externally misleading if the rendered first screen presents the wrong gate.

## One-line Lesson

```text
A first-screen badge is not decoration; it is a gate claim.
```

Japanese:

```text
ファーストスクリーンのバッジは装飾ではない。Gate主張である。
```

## Do Not Use This Note To Claim

Do not use this note to claim:

```text
the original audit succeeded
the issue was minor because body text was correct
adjacent HOLD text cancels FULL GO
screenshots are optional for public-surface closure
public-surface PASS can be closed from source text alone
```

## Future Rule Candidate

Possible future rule:

```text
Rendered Gate Signal Check:
Before public-surface PASS, inspect the rendered first screen and compare visible badges, titles, thumbnails, video frames, and About text against the current gate ledger.
```

This may later become a checklist or MISTAKEN entry if repeated.

For now, keep it as an incident Field Note.

## Completion Line

This incident note records a screenshot-dependent gate-signal miss:

```text
A first-screen README badge displayed FULL GO even though the actual gate was Public surface SOFT GO and External posting HOLD.
```

The badge was patched at commit `796ee6f`, but the important V13 lesson is that public-surface PASS must include rendered first-screen gate-signal inspection.

Current status:

```text
Incident Note: PASS
Entry Window Radar badge patch: PASS
Public-surface process lesson: RECORDED
External posting: HOLD
MISTAKEN promotion: HOLD
Rendered inspection automation: BLOCK
```
