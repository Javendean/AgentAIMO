---
description: Code quality standards for all AgentAIMO Python code
activation: always
---

# Code Standards

## Python
- Python 3.10+ with type hints on ALL function signatures
- Google-style docstrings on every public function (concise one-line summary, Args, Returns, Raises)
- Do not add filler docstrings to trivial code
- No wildcard imports
- Use pathlib.Path not os.path
- Use logging module, never bare print() in production code
- All numerical code must handle edge cases: zero, negative, very large inputs

## Testing
- Every module in src/ must have a corresponding test in tests/
- Tests must include at least 3 known-answer cases for math functions
- Include deliberately WRONG inputs to verify error detection
- Use pytest; no unittest.TestCase unless necessary
- Run pytest --tb=short before considering any task complete

## Cost Tracking
- Every external API call must go through src/utils/api_client.py
- Log: model_name, tokens_in, tokens_out, cost_usd, wall_time_seconds
- Cumulative cost written to data/cost_log.jsonl

## Git
- Conventional commits (feat:, fix:, refactor:, test:, docs:)
- No commits with failing tests
- No large binary files
