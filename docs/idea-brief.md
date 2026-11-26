---
status: Draft
owner: "AlexanderSW"
updated_at: "2026-11-26"
depth: "medium"
---

# Idea brief — agent-tool

## 1. Raw idea

The owner picked the interview option «Step 2: agent tool» — «A tool an assistant agent can call: «verify act» and «list checks» return the verdict, findings and evidence block (README, step 5; mcp_server.py).»

Asked what the tool should give that the command does not («Agents without a shell» / «Structured result» / «Portfolio demo»), the owner answered: «All of the above».

## 2. Problem

The verifier works only as a command today. An assistant agent can use it only if it can run shell commands and then read text output: the exit code plus the evidence block on stdout, or the Excel/Markdown files (source-verified: `README.md` «Коди виходу»; `src/act_verifier/cli.py:81-106`). The stage-2 tool exists only as a description; `src/act_verifier/mcp_server.py` holds a docstring and no code (source-verified: `mcp_server.py:1-9`).

The owner wants three things, all equally important (owner-reported, «All of the above»):
- **Agents without a shell can verify an act.** A client that cannot run commands but can call a tool should still be able to verify.
- **Structured result.** The agent gets the verdict, every finding and the evidence block as data. It does not parse stdout or open the Excel report.
- **Portfolio value.** A working assistant-tool integration is a visible part of the project for the employer's reviewer.

Desired observable outcome: an assistant client calls «verify act» on the files in `data/synthetic/` and gets back the same verdict, findings and evidence block the command produces for the same input. It can also call «list checks» to get the check catalogue (owner-reported intent; equivalence to the command is a proposal, see §7).

## 3. Users

- **Assistant agents in any client that supports the tool protocol**, not only Claude Code or Claude Desktop (owner decision). This includes agents with no shell.
- **The project owner.** Connects the tool and demonstrates it (owner-reported).
- **The employer's reviewer.** Sees the project in the test assignment (owner-reported, carried from step 1). Whether they will connect the tool live or only read the code is an assumption.
- **The person who accepts the act.** Still decides; the tool only reports («Агент готує, людина вирішує» — source-verified: `README.md:5`, `mcp_server.py:6`).

## 4. Why now

Same trigger as step 1 (owner-reported): the employer's test assignment, where real acts are expected to appear. The tool should be ready by then. No date has been set.

Order (owner decision): step 2 starts only after the 7 open cli-verifier review fixes have landed and been re-reviewed and step 1 has shipped. The tool returns the same evidence block that review finding 1 (missing AC-11 reason) changes (source-verified: `docs/features/cli-verifier/_review/review-2026-11-26.md`).

## 5. Out of scope

- **No writes to disk.** «verify act» writes no report, no Markdown and no journal; everything goes back in the tool result (owner decision). Anyone who needs files runs the command.
- **No input files are changed.** The tool only reads (source-verified: `CLAUDE.md`; `mcp_server.py:6`).
- **Step 1 rules carry over** (source-verified: `CLAUDE.md`): `Decimal` only; numbers only from files; missing data gives `unknown`, never `pass`; every result ends with an evidence block.
- **No new checks or reading rules.** The tool wraps the existing `load_contract`, `load_act` and `verify` (source-verified: `README.md` «План реалізації» step 2). Deferred scenarios remain roadmap step 3.
- **No changes to how an act is accepted.** The tool reports and the person decides (source-verified: `docs/roadmap.md` «Out of scope»).

## 6. Risks

1. **Weakest point: whether the demo will work for the reviewer at all.** The portfolio value depends on the tool working on the reviewer's machine at an unknown date. Nobody has confirmed that the reviewer will connect it live (assumption). The `mcp` dependency also has no upper bound (`pyproject.toml:14`, `mcp>=1.0`). A pip dry-run on 2026-11-26 resolved `mcp 2.3.0`, but nobody has checked whether the API named in the docstring («FastMCP», `mcp_server.py:8`) exists in 2.x. The check catalogue `docs/checks.md` is not part of the installed package (`pyproject.toml:19-20`). Mitigation (owner decision): pin a tested `mcp` range with an upper bound, run the tool tests in the default `pytest -q`, and ship the catalogue inside the package. Reversible.
2. **Reading files is a new capability.** Today the command reads any path (`loaders.py:28-36`, `cli.py:84-87`), which is harmless because the caller already has a shell with the same rights. A tool for clients without a shell removes that premise. The step-1 brief skipped independent critique because there was no new access (`docs/features/cli-verifier/idea-brief.md` §6), so that reasoning does not carry over. The error text «файлу немає або це не книга Excel» (`cli.py:66`) also reveals whether a file exists. Mitigation (owner decision): the tool reads only under a root folder set when the server starts; a path outside it is an input error. Local connection only, no network transport. Remote clients reading the server's disk are therefore excluded.
3. **The result shape becomes a public contract, and the input-error rule assumes one caller.** The CLI contract states it does not bind the tool (`contracts/cli.md:276-277`). ADR-0002 (`adr/0002-*.md:33`) and the `models.py:13` docstring make `cli.main` the only place that catches `InputError`. The existence check, overwrite guard and readable messages are private to `cli.py:61-93`. If the tool let `InputError` escape, the protocol would report a generic tool error. The agent could then not tell «fix the file» from «the verifier has a bug». This failure is hypothetical. Mitigation (owner decision): a versioned result contract with fixed fields and input-error kinds. An input error is a normal result carrying its kind and message, not a tool failure. This requires amending ADR-0002 to allow a second caller.

Critique: independent, by `sdd:devils-advocate` in interview mode (3 findings, all hypothetical failures grounded in repo evidence; it did not install `mcp` or check the 2.x API). The owner resolved all three; the accepted mitigations are listed above.

| Claim / question | Class | Source | Finding / limit |
| --- | --- | --- | --- |
| The tool exists only as a description | source-verified | `src/act_verifier/mcp_server.py:1-9` | Docstring only |
| Agents can use the verifier today only through the command and its text output | source-verified | `README.md` «Коди виходу»; `cli.py:81-106` | — |
| `mcp` extra is declared without an upper bound and is not installed | source-verified | `pyproject.toml:14`; `docs/architecture-map.md:24` | — |
| `mcp>=1.0` resolves on Python 3.14.2 | source-verified | `pip install --dry-run "mcp>=1.0"` in `.venv`, 2026-11-26 → `mcp 2.3.0`, wheels for every dependency | Resolution only; nothing was installed or imported |
| «FastMCP» exists in `mcp` 2.x | unknown | `mcp_server.py:8` (docstring) | Not checked |
| Loaders read any path | source-verified | `loaders.py:28-36`; `cli.py:84-87` | — |
| Only `cli.main` catches `InputError` | source-verified | ADR-0002 `:33`; `models.py:13` | — |
| The CLI contract does not cover the tool | source-verified | `contracts/cli.md:276-277` | — |
| `docs/checks.md` is not in the package | source-verified | `pyproject.toml:19-20` | No package-data is declared |
| Value: agents without a shell, structured result, portfolio | owner-reported | owner answer, 2026-11-26 | Equal weight |
| The reviewer will connect the tool live | assumption | — | Unconfirmed |

## 7. Recommendation

**Direction (owner-accepted, 2026-11-26).** Build roadmap step 2 as a local assistant-tool server with two tools:

- **«verify act»** takes the contract, previous acts and the act under check by path, all under the configured root. It returns the verdict, every finding with its expected and actual value and sources, the skipped checks, and the evidence block, all as data. It writes nothing to disk.
- **«list checks»** returns the check catalogue, shipped inside the package.
- **Results follow a versioned contract** with fixed fields and input-error kinds. An input error is a normal result carrying its kind and message; ADR-0002 is amended for the second caller.
- **Files are read only under a root folder** set at server start. The connection is local; no network transport.
- **A tested `mcp` version range** with an upper bound. The tool tests run in the default `pytest -q`, so the expected test count in `CLAUDE.md` changes.
- **The tool wraps the existing `load_contract`, `load_act` and `verify`.** No new checks; the `CLAUDE.md` rules apply unchanged.

**Observable result.** On `data/synthetic/` and on every fixture scenario, «verify act» gives the same verdict, findings and evidence block as the command does for the same input. This is a proposal for specify to turn into acceptance criteria. An input-error scenario returns its kind and the label that was not found, and a path outside the root is refused as an input error. «list checks» returns every check ID from `docs/checks.md`.

**Main trade-off.** A versioned contract, a path root and a pinned dependency all add scope, compared with a thin wrapper. In exchange, the tool is safe to hand to a client without a shell, and it can be relied on by a client the owner does not control.

**Rejected alternatives.**
- **No change: agents with a shell run the command.** Rejected because it leaves out clients without a shell, which the owner explicitly wants.
- **Optional report files, or the same outputs as the command.** Rejected because the tool returns data only (owner decision).
- **Any path, or only `data/synthetic/`.** Any path makes the tool a general file reader. Only `data/synthetic/` rules out real acts.
- **Best-effort result shape.** Rejected because input errors and verifier bugs would look the same to the agent.
- **Tool tests outside the default run.** Rejected because the demo could break without the suite noticing.

**Outcome: ready-for-specify.**

Next action, in the owner-decided order:
1. Land the 7 cli-verifier fixes (`/sdd:implement cli-verifier`) and re-review them.
2. Ship step 1.
3. Run `/sdd:specify agent-tool`.

## 8. Open questions

| Unknown | Consequence | Blocking? | Verification | Owner |
| --- | --- | --- | --- | --- |
| Does the API the docstring names («FastMCP») exist in `mcp` 2.x, and which range is tested? | Decides the version bound and the server's entry point | non-blocking (design) | Install into a scratch venv and read the package docs during design | AlexanderSW |
| Will the employer's reviewer connect the tool live, and from which client? | Decides how much effort the setup instructions and a client smoke check need | non-blocking | Ask when the test assignment arrives; until then the README covers a generic local client | AlexanderSW |
| How is the root folder supplied (startup argument, environment variable, default)? | Usability of setup, and what happens when no root is given | non-blocking (specify) | Decide in the spec | AlexanderSW |
| Field set and version scheme of the result contract | Becomes public once another client relies on it | non-blocking (specify / api) | Derive from `models.py` / `data-model.md` in the spec | AlexanderSW |
