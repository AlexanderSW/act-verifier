# Tracker — cli-verifier

> Status of every task in the epic. `implement` updates **Status** and **Step** after every
> subagent it runs (and commits them with the task), so this table shows where the run is right now.
> Status: `todo` · `in_progress` · `blocked` · `review` · `done`.
> Step: `SELECT` · `RED` · `GREEN` · `REFACTOR` · `GATE` · `REVIEW` · `COMMIT` (`—` before the task starts).
> A `blocked` row carries its reason in Step, e.g. `GATE — lint red after 3 retries`.

| # | Task | Layer | Owner | Estimate | Blocked by | Status | Step |
|---|---|---|---|---|---|---|---|
| T1 | Extend models with InputError, Skipped and per-value provenance | domain | AlexanderSW | S | — | done | COMMIT |
| T2 | Add layout map, expected_error and four layout scenarios to the generator | tests | AlexanderSW | M | — | done | COMMIT |
| T3 | Add empty-quantity, empty-amount and incomplete-previous-acts scenarios | tests | AlexanderSW | S | T2 | done | COMMIT |
| T4 | Implement the layout helper | infra | AlexanderSW | S | T1 | done | COMMIT |
| T5 | Implement load_contract and the shared cell readers | infra | AlexanderSW | S | T1, T4 | done | COMMIT |
| T6 | Implement load_act | infra | AlexanderSW | M | T2, T5 | done | COMMIT |
| T7 | Implement row checks C01–C06, C11 with skip rules and completeness | app | AlexanderSW | M | T1 | done | COMMIT |
| T8 | Implement act checks C07–C10, C12, C13 and assemble verify() | app | AlexanderSW | M | T7 | done | COMMIT |
| T9 | Implement the Excel report, the Markdown report and the evidence block | infra | AlexanderSW | M | T1 | done | COMMIT |
| T10 | Implement append_error_log with escaping | infra | AlexanderSW | S | T9 | done | COMMIT |
| T11 | Turn the scenario tests green | tests | AlexanderSW | S | T3, T6, T8, T9 | done | COMMIT |
| T12 | Implement cli.main | ports | AlexanderSW | M | T6, T8, T9, T10 | done | COMMIT |
| T13 | Add command-level tests | tests | AlexanderSW | M | T3, T12 | done | COMMIT |
| T14 | Update docs/checks.md with the spec's rules | docs | AlexanderSW | S | — | done | COMMIT |
| T15 | Show the previous-acts completeness reason in the evidence block | domain | AlexanderSW | S | — | done | COMMIT |
| T16 | Refuse abbreviated option names with outcome code 3 | ports | AlexanderSW | S | — | done | COMMIT |
| T17 | Cite the КБ-2в sheet title as found, not the literal «КБ-2в» | domain | AlexanderSW | S | T15 | done | COMMIT |
| T18 | Assert the test run leaves the tracked journal unchanged instead of empty | tests | AlexanderSW | S | — | done | COMMIT |
| T19 | Map the remaining argparse errors to Ukrainian messages naming the option | ports | AlexanderSW | S | T16 | done | COMMIT |
| T20 | Assert expected and actual values of the three combo fails | tests | AlexanderSW | S | — | done | COMMIT |
| T21 | Align ContractPosition types and record the duplicate-code rule | docs | AlexanderSW | S | T17 | done | COMMIT |
| T22 | Pin the empty contract quantity/price rule with tests | tests | AlexanderSW | S | — | done | COMMIT |
| T23 | Name a duplicated contract code as a code, with its own InputError kind | infra | AlexanderSW | S | — | done | COMMIT |
| T24 | List Act.sheet in data-model.md | docs | AlexanderSW | S | — | done | COMMIT |
| T25 | List every missing-data unknown under «Не перевірено» with its reason | domain | AlexanderSW | S | — | done | COMMIT |
| T26 | No act number when the КБ-2в header is in row 1 | infra | AlexanderSW | S | — | done | COMMIT |
| T27 | Align the ER diagram, the sync report and the cli.md changelog with the review-2 changes | docs | AlexanderSW | S | — | done | COMMIT |

**Total:** 27 tasks (T15–T21, T22–T24, T25–T27: review follow-ups), ~8.25 person-days (S ≈ 0.25 d, M ≈ 0.5 d).
