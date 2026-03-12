# AgentAIMO

Research code and data for an AI agent targeting the [AI Mathematical Olympiad (AIMO)](https://aimoprize.com/) competition.

## Structure

```
AgentAIMO/
├── agent/              # Core agent code
│   ├── deep_researcher.py  # Main multi-agent reasoning loop
│   ├── prompts.py          # Prompt templates
│   └── sandbox.py          # Python code execution sandbox
├── tests/              # Test suite
├── docs/               # Codebase analysis and blindspot documentation
├── scripts/            # One-off data processing utilities
├── notebooks/          # Exploratory Jupyter notebooks
├── data/               # Research data (gitignored — large files)
│   ├── research/       # Papers, extracted text, research JSONL
│   ├── dpo/            # DPO correction datasets
│   ├── chat_context/   # Chat transcripts used as context
│   └── raw/            # Downloads, logs, leaderboard data
├── supply_chain/       # vLLM wheel download/verify scripts
├── corpus/             # (gitignored) External corpora
└── youtube/            # (gitignored) YouTube transcript cache
```

## Setup

```bash
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/
```

## Key Agent Architecture

The agent in `agent/deep_researcher.py` implements a multi-step reasoning loop:
1. **Problem parsing** — Classify and extract structure from AIMO problems
2. **Chain-of-thought generation** — Generate candidate solutions via LLM
3. **Code execution** — Run Python/SymPy to verify symbolic computations
4. **Verification** — Cross-check answers using canary tests and regex extraction
5. **Answer selection** — Voting across multiple solution candidates

> **Note:** See `docs/CODEBASE_ANALYSIS.md` for a comprehensive analysis of the architecture and its known failure modes.

## Known Issues

- Execution success ≠ mathematical correctness (documented blindspot)
- Canary test brittleness (documented in `docs/`)
- `sympy` import in sandbox is currently blocklisted — see `tests/test_agent.py`
