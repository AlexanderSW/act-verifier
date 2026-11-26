# Tracker — check-act-skill

> Status of every task in the epic. `implement` updates **Status** and **Step** after every
> subagent it runs (and commits them with the task), so this table shows where the run is right now.
> Status: `todo` · `in_progress` · `blocked` · `review` · `done`.
> Step: `SELECT` · `RED` · `GREEN` · `REFACTOR` · `GATE` · `REVIEW` · `COMMIT` (`—` before the task starts).
> A `blocked` row carries its reason in Step, e.g. `GATE — lint red after 3 retries`.

| # | Task | Layer | Owner | Estimate | Blocked by | Status | Step |
|---|---|---|---|---|---|---|---|
| T1 | Create the check-act skill file with its identity header and the identity drift tests | ports | AlexanderSW | S | — | done | — |
| T2 | Add the outcome-code map and run-command block, with drift tests against the verifier's contract | ports | AlexanderSW | M | T1 | done | — |
| T3 | Write the skill's run steps: collect inputs, run the verifier, apply the verdict-source rule | ports | AlexanderSW | S | T2 | done | — |
| T4 | Write the skill's red lines and the five-section reply format | ports | AlexanderSW | M | T3 | done | — |
| T5 | Write the skill's no-verification branch: input errors by kind and crashes | ports | AlexanderSW | S | T3 | done | — |
| T6 | Write the demo script demo.md with empty actual-result fields | docs | AlexanderSW | S | — | done | — |
| T7 | Add the README section «Агент L1: Skill check-act», mark the draft superseded | docs | AlexanderSW | S | — | todo | — |
| T8 | Rehearse the three demo scenarios and record actual results (manual) | tests | AlexanderSW | M | T4, T5, T6 | todo | — |

**Total:** 8 tasks, ~1 person-day (≈ 10.5 h; T8 is manual and needs the owner at the keyboard).
