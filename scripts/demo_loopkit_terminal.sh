#!/usr/bin/env bash
set -euo pipefail

pause() {
  sleep "${1:-0.7}"
}

say() {
  printf '%s\n' "$1"
}

section() {
  printf '\n%s\n' "$1"
}

command -v clear >/dev/null 2>&1 && clear || true

say "LoopKit: boundary signals for AI coding loops"
pause 0.9

section "Pain"
say "AI coding sessions get expensive when every run has to rediscover context."
pause 1.0

section "Power Concepts"
say "🚦 Signals"
pause 0.35
say "🌱 Growth OS"
pause 0.35
say "💊 Setup Pill"
pause 0.9

section "Completed task"
say "Task: add a bounded examples pointer"
pause 0.9

section "LoopKit report"
say "V12 State: PASS"
say "V13 Next Loop Gate: CAP"
pause 0.9

section "Signals"
say "🟢 BLUE / BOUNDED-TASK-COMPLETE"
say "🟢 BLUE / WORKING-TREE-CLEAN"
say "🟡 YELLOW / NEXT-LOOP-CAP"
pause 1.0

section "Residue recommendation"
say "Detected reusable residue:"
say "The example pointer improved discoverability, but the change is already recorded in the committed index."
pause 0.45
say ""
say "Recommendation:"
say "Low"
pause 0.45
say ""
say "Expected effect:"
say "Mentioning this in the report is enough; no extra memory surface is needed."
pause 0.45
say ""
say "Suggested placement:"
say "no record"
pause 0.45
say ""
say "Owner choices:"
say "A. Record the minimal residue"
say "B. Skip for now"
pause 1.0

section "Stop condition"
say "Stopped after the bounded task. No new files, no AGENTS promotion, no automation."
pause 0.9

section "Exit gate"
say "LoopKit does not replace your loop. It adds an exit gate between loop runs."
