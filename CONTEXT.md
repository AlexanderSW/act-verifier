---
status: Living
updated_at: "2026-11-26"
---

# Domain Context — act-verifier

## Glossary

- accepting person — the human who reads a verification report and decides whether to accept the act. NOT the verifier (which only reports, never decides).
- act — a completed-works acceptance act (form КБ-2в) for one reporting period, holding position rows and the totals «Разом без ПДВ», «ПДВ 20%», «Всього з ПДВ», plus its КБ-3 certificate sheet. NOT the contract price (the agreed baseline the act is checked against).
- check — one rule from the catalog in docs/checks.md, identified by a stable ID (C01–C13). NOT a finding (the result of applying a check to one row or act).
- contract price — the agreed bill of quantities («Договірна ціна») listing each position code with unit, contracted quantity and unit price. NOT an act (which reports work done in one period).
- employer reviewer — a person at a prospective employer who examines the project and may run it on real acts in a test assignment. NOT the project owner.
- error journal — the shared log of fail/unknown/warning findings (journal/agent_errors.csv), appended only on explicit request. NOT the verification report (produced on every run).
- evidence block — the mandatory closing section of every report stating what was checked, what was not and why, and which file/sheet/rows each number came from. NOT the findings list.
- finding — the outcome of one check for one position code or for the whole act, with a status and, on fail, the expected and actual values. NOT a check (the rule itself).
- input error — the outcome where verification did not happen: the invocation was wrong, an input file, sheet or layout label could not be read or was ambiguous, or the run would have overwritten an input. NOT the `unknown` status (verification happened but a value was empty).
- КБ-3 certificate — the cost certificate sheet of an act with the period total and the cumulative total since works began. NOT the КБ-2в totals (which it must agree with).
- layout label — the text in a cell that marks a structural place in a file: a header column («Шифр», «Кількість») or a totals row. NOT a value (the number next to the label).
- position code — the identifier («шифр», e.g. «2-1») linking an act row to a contract price row. NOT the row number («№ з/п»).
- preparing agent — the AI agent or person who prepares an act before it is verified. NOT the verifier.
- previous acts — the acts numbered 1…N−1 for the same contract, supplied to verify act N. NOT any earlier file at hand (an incomplete set leaves volume/cumulative checks unknown).
- project owner — the developer and first user of the verifier on the synthetic data set. NOT the employer reviewer.
- remaining volume — the contracted quantity of a position minus the sum of its quantities in previous acts. NOT the contracted quantity.
- status — the result class of a finding: pass, fail, unknown or warning (docs/checks.md). NOT the verdict (which aggregates statuses for the whole act).
- verdict — the act-level outcome: fail if any finding fails, needs_review if any is unknown or warning, else pass. NOT a status, and NOT an input error.
- verifier — the read-only tool that checks an act against the contract price and previous acts and reports; it never modifies inputs and never decides acceptance. NOT the accepting person.

## Invariants

- A missing value can never yield `pass`; it yields `unknown`.
- Money and quantities are always exact decimals taken from the files; nothing is invented or substituted.
- The verifier can never write to its input files.
