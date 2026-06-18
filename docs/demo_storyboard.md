# LoopKit Terminal Demo Storyboard

Purpose: turn `scripts/demo_loopkit_terminal.sh` into a short terminal-screen video plan.

Claim level: demo material / observed behavior, not proof.

Target length: 30-45 seconds.

| Scene | On screen | Zoom / focus | Caption / subtitle | Purpose | Duration |
| --- | --- | --- | --- | --- | --- |
| 1 | `LoopKit: boundary signals for AI coding loops` followed by `AI coding sessions get expensive when every run has to rediscover context.` | Start full terminal, then slow zoom toward the pain sentence. | AI work gets costly when each session has to rediscover context. | Establish the user pain quickly. | 5s |
| 2 | `🚦 Signals`, `🌱 Growth OS`, `💊 Setup Pill` | Keep terminal centered; briefly highlight the three lines as they appear. | Three concepts: read loop state, leave useful residue, and start safely in one repo. | Show the demo vocabulary without overexplaining. | 5s |
| 3 | `Task: add a bounded examples pointer` then `V12 State: PASS` and `V13 Next Loop Gate: CAP` | Zoom into the V12/V13 footer. | V12 checks completion. V13 decides whether the next loop should run, pause, cap, or block. | Make the visible output format concrete. | 6s |
| 4 | `🟢 BLUE / BOUNDED-TASK-COMPLETE`, `🟢 BLUE / WORKING-TREE-CLEAN`, `🟡 YELLOW / NEXT-LOOP-CAP` | Tight crop on the signal lines. | BLUE means useful progress. YELLOW means continue only with bounds. | Show how terminal signals summarize loop state. | 6s |
| 5 | `Recommendation: Low` and `Suggested placement: no record` | Scroll or crop to the residue recommendation block; emphasize `Low` and `no record`. | Not every useful observation needs a new file. | Show token/memory discipline and reduced record bloat. | 6s |
| 6 | `Owner choices:` then `A. Record the minimal residue` and `B. Skip for now` | Focus on the two choices. | The agent gives bounded choices instead of asking a heavy open-ended question. | Show Owner control and low-friction decision making. | 5s |
| 7 | `Stop condition:` then `Stopped after the bounded task. No new files, no AGENTS promotion, no automation.` | Zoom in on `Stop condition:` and the three boundary lines. | The loop stops here. | Show that LoopKit defines why the loop should stop instead of expanding. | 4s |
| 8 | `LoopKit does not replace your loop. It adds an exit gate between loop runs.` | End on the final line, with the terminal still visible. | Keep your workflow. Add an exit gate. | Close with the core positioning. | 5s |

## Recording Notes

- Use a clean terminal theme with readable contrast.
- Run the script once from the repo root:

```bash
./scripts/demo_loopkit_terminal.sh
```

- Keep edits minimal in post-production: crop, light zooms, and short captions only.
- Do not imply the behavior is proven or automated.
- Do not show secrets, live network calls, commits, or file edits.
