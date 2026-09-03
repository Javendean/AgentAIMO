# AgentAIMO

A math-competition solver for the [AI Mathematical Olympiad Progress Prize 3](https://aimoprize.com/),
plus the offline audit substrate I built to figure out why it was getting problems wrong.

The competition runs an open-weights model on a single H100 with no internet, and scores
exact-match integer answers on 50 olympiad-level problems. Two halves of the repo:

- **The solver** (`agent/`, `notebook/`, `supply_chain/`) — runs on Kaggle. Samples solutions
  from gpt-oss-120B, executes the Python the model writes, votes on an answer, and stops early
  when the vote is already decisive.
- **The audit substrate** (`src/`, `data/verification/`) — runs offline on my laptop. Takes the
  JSONL traces the solver produced and re-derives, from the text alone, what was actually
  verified, what answer each attempt really committed to, and what went wrong. This is the half
  I spent most of the time on and it is the more interesting half.

159 tests pass from a clean clone in about 7 seconds:

```bash
pip install -e ".[dev]"
python -m pytest tests/ -q
```

## The audit substrate (`src/`)

The problem this solves: a model writes four pages of reasoning, runs some code, the code exits
zero, and the model announces an answer. None of that tells you whether the math was checked.
"The code ran" and "the answer is verified" are different claims, and treating them as the same
thing is how you end up confidently wrong.

**Typed confidence, not a boolean.** `src/models/verification.py` defines a `ConfidenceLevel`
enum that every checker must return — it is not allowed to collapse to true/false:

| Level | Meaning |
|---|---|
| `LEVEL_0_EXACT` | A deterministic recomputation reproduced the claimed number |
| `LEVEL_1_SYMBOLIC` | SymPy confirmed an algebraic identity |
| `LEVEL_2_FORMAL` | Lean kernel acceptance (reserved; not wired up) |
| `ENUMERATED` | Brute force checked every case in a bounded domain |
| `NL_JUDGMENT` | An LLM said it looked right — weakest signal, never the sole selector |
| `UNVERIFIED` | Nothing mechanical was attempted |

**The hierarchy drives vote weight.** `src/solver/answer_selector.py` maps each level to a
weight — 10.0 for `LEVEL_0_EXACT` down to 0.1 for `UNVERIFIED` — and votes with those weights
instead of counting heads. One attempt whose arithmetic was independently recomputed outvotes
several that merely asserted a number. If no attempt carries strong verification, it falls back
to a weak weighted vote and then to a plain majority, and reports which of the three it used
(`confidence_weighted_vote`, `weak_weighted_vote`, `majority_vote`) so the selection is auditable
after the fact.

**A flaw taxonomy over the traces.** `src/models/critique.py` defines 21 flaw codes on a 1–5
severity scale, derived from hand-annotating real traces. Eight of them are detected
automatically by `src/critique/flaw_detector.py` — `CHANNEL_LEAKAGE` (raw reasoning-channel
tokens bleeding into the answer), `PSEUDO_VERIFICATION` (printing "PASSED" without ever showing
the computed value), `MISSING_FINAL_COMMIT` (deriving the right number and then never putting it
in the answer field), `MALFORMED_TOOL_CALL`, `NON_EXECUTABLE_CODE`, `CONTEXT_CONFABULATION`,
`PROMPT_LEAKAGE`, `REDUNDANT_RECOMPUTATION`. The remaining thirteen are math-correctness codes
used for manual annotation; they are not auto-detectable and the code does not pretend otherwise.

**The pipeline.** `src/runner/audit_problem.py` runs the whole thing over one problem record:
parse the trace into steps and calculations, recompute every extracted calculation, extract a
canonical integer answer, detect flaws, then select across attempts. `src/runner/batch_audit.py`
streams that over a JSONL file. Output lands in `data/verification/audit_research_data*.jsonl`,
one record per problem with the selected answer, the reason it was selected, and the flaw codes.

## The published metrics include a run that got worse

`docs/BASELINE_METRICS.md` reports two runs. The older trace set scored **6/8** on the problems
with known ground truth. The newer one, run through the full verification and selection pipeline,
scored **3/8**. The newer number is worse and it is the one at the top of the file.

The diagnosis is in the same document: the five misses are all `no_answer_extracted`. The
canonical-answer extract rate collapsed from 21.1% to 5.6% between the two runs, and the dominant
flaw shifted to `MISSING_FINAL_COMMIT` — the model derived an answer and then stated it in prose
instead of the `**ANSWER: N**` format the extractor requires. The selection logic was not the
problem; in every case where an answer was extracted at all, the confidence-weighted vote picked
the right one. The failure is at the extraction boundary.

I am leaving both numbers published. A metrics file that only shows the good run is not a metrics
file. The regression is also the most useful thing in the repo — it is what pointed at extraction
rather than at reasoning, which is where the next work goes.

## The solver (`agent/`, `notebook/`)

`agent/deep_researcher.py` is the sampling loop.

**Wave sampling with early consensus.** Instead of drawing N samples and voting once, it draws in
waves of 4 and checks after each wave whether the vote is already decisive — 75% agreement at 4
samples, 63% at 8, 58% at 12+. When a problem is easy the loop stops after one wave and hands the
saved compute to a harder problem.

**Per-problem wall-clock budgets.** `_compute_time_budget()` divides the remaining time by the
remaining problems, scales by a difficulty multiplier (0.6× easy through 2.0× extreme), caps any
single problem at 80% of what is left, and floors it at 60 seconds. A hard timer raises
`TimeLimitExceeded` and exits gracefully rather than getting killed mid-write, because the
competition kills the container at 3 hours regardless.

**Sandboxed execution of model-written code.** `agent/sandbox.py` runs code the model emitted in
a subprocess with a stripped environment: an import hook that blocks `os`, `subprocess`, `socket`,
`urllib`, `ctypes`, `threading` and others; `open()` replaced with a raiser; a 200-line print cap
to stop memory bombs; a hard timeout. The docstring says plainly what this is and is not — it
stops accidents (infinite loops, stray file writes), and a model deliberately trying to escape via
reflection or a C extension would get out. Calling it a security boundary would be a lie.

**Air-gapped deployment.** Kaggle runs with internet off, so every wheel has to be there in
advance. `supply_chain/download_vllm_wheels.py` pulls vLLM and its full dependency closure for
Linux x86_64 / Python 3.10 and writes MD5s; `supply_chain/verify_checksums.py` checks them before
upload. `notebook/kaggle_notebook.py` uninstalls the Kaggle image packages that conflict
(tensorflow, protobuf, cuda-python, fsspec), installs from the local wheel directory with
`--no-index`, and asserts the resulting `vllm.__version__` before touching the GPU — a silently
wrong vLLM version on a 3-hour run costs the whole run.

**Canary test.** Before committing to the 120B model, the notebook runs one synthetic problem with
a known answer (not a memorizable contest problem) to confirm the model is loaded and responding
in the expected format, and falls back to a 72B backup if it is not. `notebook/README.md`
documents the ways this canary is brittle.

## `scripts/scrape_candidate_notebooks.py`

I kept this one because the research it did shaped the solver.

To find out what actually works on this competition rather than guessing, I took the public AIMO3
leaderboard export, cut it to the top 1% of teams (`extract_top_leaderboard.py`), and used
Playwright to walk each of those users' public Kaggle profiles collecting every notebook they had
published (`scrape_candidate_notebooks.py`). `filter_notebooks.py` then keyword-filtered the
result down to the ones plausibly about this problem — vLLM, AWQ, TIR, self-consistency, and so
on — and discarded the unrelated Titanic and forecasting notebooks that clutter most profiles.

One of the survivors is checked in at `notebooks/44-50-aimo3-skills-optional-luck-required.ipynb`
— the filter's keyword list is explicitly tuned to find it. The point of the exercise was to read
what people scoring 44+/50 were actually running rather than invent an approach. The wave sizes
and consensus thresholds in `deep_researcher.py` are borrowed, not derived; the code credits
NemoSkills, the AIMO2 winner, in the docstrings.

It only touches public profile pages, it scrolls and sleeps a second between users rather than
hammering, and it collects notebook titles and links, not content. It is a one-off research script
with the paths I ran it with hardcoded, and it is kept as a record of how the design decisions were
made.

## Honest state of the repo

- **`src/solver/inference_engine.py`, `python_executor.py`, and `sampling_strategy.py` are stubs**
  that raise `NotImplementedError`. They were the planned clean-room re-implementation of the
  solver inside `src/`; that never happened. The working sandbox is `agent/sandbox.py` and the
  working sampling loop is `agent/deep_researcher.py`. `src/optimization/` is likewise a stub.
- **Thirteen scripts in `scripts/` hardcode `c:\Users\javen\...` paths.** They are one-off data
  processing run against local files. They will not run elsewhere without editing the constants at
  the top.
- **The tests do not mock LLM output.** They cover the sandbox rules, extraction patterns, the
  verification battery, and the selection logic — the deterministic half. The generation loop is
  exercised only as a dry run. `tests/README.md` lists this and the other test-suite weaknesses.
- **`docs/archive/`** holds two raw working transcripts (`evidence.md`, `evolution.md`) kept for
  provenance. They are where the `ConfidenceLevel` design argument happened. They are not
  documentation and one of them opens by disclaiming its own status claims.

## Layout

```
agent/           Solver: sampling loop, prompts, code sandbox
src/models/      Typed schemas: ConfidenceLevel, FlawCode, traces, reports
src/verification/  Parser, arithmetic recomputation, answer validation, pipeline
src/critique/    FlawDetector — offline flaw codes over trace text
src/solver/      AnswerSelector (implemented); inference/executor/sampling (stubs)
src/runner/      Per-problem and batch audit runners
notebook/        Kaggle H100 execution script
supply_chain/    Offline vLLM wheel download + MD5 verification
tests/           159 tests
docs/            Metrics, audits, plans, risk register
docs/archive/    Raw working transcripts, kept for provenance
scripts/         One-off data processing (mostly hardcoded local paths)
```

## Tooling note

This repo was developed with heavy use of [Claude Code](https://docs.claude.com/en/docs/claude-code),
and `.github/workflows/` wires it into PR review. Its documentation lives at Anthropic's site, not
in this repo.

## License

MIT — see [LICENSE](LICENSE).
