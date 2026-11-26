---
status: Draft
owner: "AlexanderSW"
updated_at: "2026-11-26"
depth: "medium"
---

# Idea brief — check-act-skill

## 1. Raw idea

The owner's words, verbatim (answer to the opening interview question, 2026-11-26):

```text
Фіча: check-act-skill — агент рівня L1 «Перевірка актів» як Skill для Claude Code.Мета (демо до співбесіди, завтра):Показати ланцюжок плану «AI готує → код перевіряє → людина вирішує» без АВК.АВК замінено на xlsx-експорт (синтетичні файли з data/synthetic і tests/fixtures).Агент лише запускає наявний act-verifier, читає звіт і пояснює розбіжності людині.Рішення ухвалює людина.Що зробити:1. .claude/skills/check-act/SKILL.md — на основі чернетки нижче:   frontmatter name + description; червоні лінії; кроки; мапа кодів виходу 0/1/2/3;   формат відповіді (вердикт, розбіжності людською мовою, не перевірено,   що зробити людині, звідки числа).2. Тест tests/test_skill.py (без запуску LLM):   - SKILL.md існує, frontmatter валідний (name = check-act, description непорожній);   - мапа кодів виходу в SKILL.md збігається з реальними кодами CLI     (0 pass, 1 fail, 2 needs_review, 3 помилка входу) — звіряти з кодом cli.py,     щоб Skill не розійшовся з верифікатором;   - команда запуску в SKILL.md посилається на параметри, які реально є в CLI     (--contract, --previous, --act, --out, --journal).3. docs/features/check-act-skill/demo.md — сценарій ручного демо:   промпт → очікувана поведінка агента для ok_many (pass),   combo_three_errors (3 розбіжності) і missing_label (перевірки не було,   агент не вигадує результат і не правит файл). З полем «фактичний результат»   для заповнення після прогону.4. README: короткий розділ «Агент L1: Skill check-act» — як викликати і що він   робить і чого не робить.Червоні лінії (жорсткі вимоги до Skill):- агент не рахує сам, усі числа — тільки зі звіту act-verifier;- не змінює вхідні файли, не пише «акт прийнято»;- немає даних → «невідомо», не «все гаразд»;- журнал (--journal) лише на прохання людини;- на коді 3 може припустити назву мітки, але файл не править — питає людину.Out of scope (не робити в цій фічі):- зміни в src/act_verifier/ і scripts/generate_fixtures.py; нові фікстури;- MCP-сервер (roadmap крок 2) і Claude Desktop / Cowork;- генерація акта агентом (повний цикл «AI готує»);- відомі дрібні дефекти CLI (повідомлення «порожня ціна» для числа-тексту,  невідомий параметр не названо) — окремою задачею.Критерій готовності:- pytest -q зелений (272 + нові тести skill), реальні запуски: .venv/Scripts/python -m pytest -q;- ручне демо з demo.md пройдене на трьох сценаріях, фактичні результати записані;- оновлена очікувана кількість тестів у CLAUDE.md.Середовище: Windows, Git Bash. Команда верифікатора: .venv/Scripts/act-verifierЧернетка SKILL.md:
```

The owner chose the interview option «Skill alongside MCP»: the MCP server stays roadmap step 2 as a separate step. The message ends at «Чернетка SKILL.md:», and no draft followed it (see §8).

## 2. Problem

The plan's chain «AI готує → код перевіряє → людина вирішує» has a working middle link, the verifier. Nothing in the repo shows the agent link yet. No `.claude/skills/` folder exists. The stage-2 agent tool is still only a docstring (source-verified: `src/act_verifier/mcp_server.py:1-9`; repo search on 2026-11-26 found no skill).

Without written rules, an agent asked to «check this act» could recompute sums itself, read a stale report, edit an input file to get past an input error, or say «акт прийнято». The owner's red lines forbid all of this (owner-reported). Whether an unguided agent actually does it has not been observed (assumption).

Desired observable outcome (owner-reported): in Claude Code, the person asks the agent to check an act. The agent runs the existing `act-verifier` on the xlsx exports, reads the report and explains it to the person:
- the verdict;
- the discrepancies, in plain language;
- what was not checked;
- what the person should do;
- where the numbers come from.

The person makes the decision. The demo shows this on three scenarios: `ok_many` (pass), `combo_three_errors` (three discrepancies) and `missing_label` (no check happened).

The real АВК export is replaced by the synthetic xlsx files in `data/synthetic/` and `tests/fixtures/` (owner-reported).

## 3. Users

- **The interviewer or employer audience.** They watch the demo tomorrow (owner-reported: «демо до співбесіди, завтра»). Whether they will run it themselves is not established.
- **The project owner.** Runs the demo in Claude Code on Windows / Git Bash (owner-reported).
- **The Claude Code agent.** Follows the skill. It runs only the existing command and explains the result (owner-reported).
- **The person who accepts the act.** Makes the decision; the agent never writes «акт прийнято» (owner-reported; consistent with `README.md:5` «Агент готує, людина вирішує»).

## 4. Why now

There is a job-interview demo tomorrow, 2026-11-27 (owner-reported). That is the whole trigger. It also sets the size: the feature must fit in about a day, using only what already exists.

The agent-tool brief puts step 2 after step 1 ships (`docs/idea-brief.md` §4). This skill wraps the command as it is today rather than the MCP tool, so that ordering does not hold it back (inference from the owner's scope; the roadmap still shows step 1 as «building»).

## 5. Out of scope

These exclusions are owner decisions, from §1:
- **No changes to the verifier.** Nothing in `src/act_verifier/` or `scripts/generate_fixtures.py` changes, and no new fixtures are added.
- **No MCP server, Claude Desktop or Cowork.** The MCP server stays roadmap step 2 (`docs/idea-brief.md`).
- **No act generation by the agent.** The full «AI готує» cycle is not part of this feature.
- **No fixes to known CLI defects.** The «порожня ціна» message for a number stored as text, and the unnamed unknown parameter, go to a separate task.

Constraints that still apply (source-verified: `CLAUDE.md`):
- Numbers come only from files.
- Missing data gives `unknown`, never `pass`.
- Input files are never written to.
- Every report ends with an evidence block.
- The expected test count in `CLAUDE.md` is updated after the change.

## 6. Risks

1. **Weakest point: whether the live agent keeps to the red lines in front of the audience.** `tests/test_skill.py` checks only structure; no LLM runs in it (owner decision). The only behaviour check is the manual demo, one pass per scenario before tomorrow. A model can still word a pass as «можна підписувати» or quote a number that is not in the report (assumption; not observed). Mitigation (owner-reported): the red lines come first in SKILL.md, and demo.md records the actual behaviour of each run. Fully reversible: the skill is one text file.
2. **A stale report after code 3.** All three demo acts are named `act_03.xlsx`, so every run writes the same `reports/act_03_report.md` (source-verified: `report.py:30-34`; `tests/fixtures/*/act_03.xlsx`). Code 3 writes no report (source-verified: `cli.py:10`). The draft's step 3 says to read `reports/<акт>_report.md` after checking the code. Running `missing_label` after `combo_three_errors` would therefore surface three discrepancies from a check that never happened. This failure is hypothetical, inferred from the code. Mitigation (owner decision):
   - SKILL.md reads a report only on codes 0/1/2; on code 3 it relays only the error message.
   - demo.md gives each scenario its own `--out` folder.
3. **The drift test needs a map that a test can parse.** The draft's code list writes «0 — розбіжностей немає» and «2 — потрібен перегляд (unknown / warning)». Neither line contains the verdict token the CLI uses (`pass`, `needs_review`) (source-verified: `docs/features/check-act-skill/SKILL.md`, step 3; `cli.py:25-26`). A test comparing SKILL.md with `cli.EXIT` cannot match these lines reliably. Proposal for specify: every map line carries the code and the verdict token. The test compares them with `EXIT` / `EXIT_INPUT_ERROR`, and every `--option` in SKILL.md with the options the parser defines (`cli.py:56-61`).
4. **Code 3 is broader than a missing label.** Code 3 also covers an invalid invocation, an unreadable file, a refused overwrite, a repeated position code and an ambiguous label (source-verified: `cli.py:72-99`). Some of these have no label or sheet. The draft says «назви мітку, файл і аркуш з повідомлення». Proposal for specify:
   - relay the message as the CLI wrote it;
   - offer a label guess only for a missing or ambiguous label;
   - never edit the file.
5. **The done criterion names the wrong baseline.** It says «272 + нові тести»; the suite has 304 today (source-verified: `.venv/Scripts/python -m pytest -q` → `304 passed`, 2026-11-26; `CLAUDE.md`). The new count is 304 plus the skill tests.

Critique: done inline, not by an independent critic. Nothing here adds access or touches data or a public contract, the change is a reversible text file plus tests, and the deadline is tomorrow. Risk 2 came from probing the code. I ran the verifier once, on `combo_three_errors`, into a temporary folder outside the repo (exit 1).

| Claim / question | Class | Source | Finding / limit |
| --- | --- | --- | --- |
| No skill or agent link exists in the repo | source-verified | repo search, 2026-11-26; `mcp_server.py:1-9` | Only the owner's draft at `docs/features/check-act-skill/SKILL.md` plus two empty `SKILL.md` files |
| Exit codes are 0 pass, 1 fail, 2 needs_review, 3 input error | source-verified | `cli.py:25-26`, `cli.py:9-10` | — |
| Options `--contract --previous --act --out --journal` exist | source-verified | `cli.py:56-61` | `--journal` takes an optional path |
| The three demo fixtures exist with the expected outcomes | source-verified | `tests/fixtures/{ok_many,combo_three_errors,missing_label}/expected.json` | pass / fail with 3-2, 2-1, КБ-3 / `missing_label` «Разом без ПДВ» |
| Stdout carries only the evidence block; findings are in the .md report | source-verified | probe run on `combo_three_errors`, 2026-11-26 | One run |
| `.venv/Scripts/act-verifier` is installed | source-verified | `.venv/Scripts/act-verifier.exe` | — |
| Test baseline is 304 | source-verified | `pytest -q` run, 2026-11-26 | The owner's 272 is out of date |
| Demo is tomorrow, for a job interview | owner-reported | owner answer, 2026-11-26 | — |
| An unguided agent would break the red lines | assumption | — | Not observed |
| The audience will run the skill themselves | unknown | — | — |

## 7. Recommendation

**Direction (owner-accepted, 2026-11-26).** Ship the check-act skill as an L1 agent over the existing command, alongside, not instead of, the MCP tool in step 2:

- **`.claude/skills/check-act/SKILL.md`**, built from the owner's draft. It has:
  - the red lines;
  - the steps;
  - the 0/1/2/3 map;
  - the reply format: verdict, discrepancies in plain language, what was not checked, what the person should do, where the numbers come from.
- **A report is read only on codes 0/1/2** (owner decision). On code 3 the agent relays the CLI message and asks the person; it never edits the file.
- **`tests/test_skill.py`, with no LLM.** It checks:
  - the file exists;
  - the frontmatter is valid: `name: check-act` and a non-empty description;
  - the exit-code map matches `cli.py`;
  - every option in the run command exists in the parser.
- **`docs/features/check-act-skill/demo.md`.** For `ok_many`, `combo_three_errors` and `missing_label` it gives the prompt, the expected behaviour and a field for the actual result. Each scenario has its own `--out` folder (owner decision).
- **A short README section, «Агент L1: Skill check-act».** It covers how to call the skill, what it does and what it does not do.
- **`CLAUDE.md` expected count becomes 304 + the new skill tests.**

**Observable result.** `pytest -q` is green at the new count. In Claude Code the three demo runs then behave as follows:
- `ok_many` gets verdict pass, with no claim that the act is accepted.
- `combo_three_errors` gets three discrepancies, with numbers matching its report.
- `missing_label` gets «перевірки не було», names «Разом без ПДВ», and the input file is unchanged.

The actual results are written into demo.md.

**Main trade-off.** Tests can only show that the skill text and the CLI agree. The agent's behaviour is shown by one manual demo pass per scenario, not proven. That is enough for an interview demo tomorrow, but it is not a regression guarantee.

**Rejected alternatives.**
- **Do the MCP tool first.** Rejected: larger scope, and it does not fit before tomorrow. It stays step 2.
- **Change the CLI to name reports uniquely or delete old ones.** Rejected: `src/` is out of scope; the skill rule and per-scenario `--out` close the gap without code.
- **Test behaviour by running an LLM.** Rejected by the owner: no LLM in tests.

The verdict-token map (§6 risk 3) and relaying the code-3 message as written (§6 risk 4) are proposals; specify decides them.

**Outcome: ready-for-specify** (owner accepted the summary, 2026-11-26).

Next action: `/sdd:specify check-act-skill`. Size is likely XS (one text file, one test file, two docs), so the quick route fits the deadline.

## 8. Open questions

| Unknown | Consequence | Blocking? | Verification | Owner |
| --- | --- | --- | --- | --- |
| Will the interview audience run the skill themselves, or only watch? | Decides whether the README needs setup steps beyond «how to call it» | non-blocking | Ask the interviewer; until then the README covers calling it from this repo | AlexanderSW |
| Should SKILL.md pre-allow the verifier command (an `allowed-tools` frontmatter entry), so the demo has no permission prompt? | A prompt mid-demo is friction, not a failure | non-blocking (specify) | Decide in the spec; test it in one dry demo run | AlexanderSW |
| What happens to the draft at `docs/features/check-act-skill/SKILL.md` and the two empty `SKILL.md` files (`.claude/SKILL.md`, `docs/features/check-act/SKILL.md`) once the real skill exists? | A second copy can drift from the loaded skill | non-blocking | The owner decides at implement: keep the draft as history, or delete the copies | AlexanderSW |
