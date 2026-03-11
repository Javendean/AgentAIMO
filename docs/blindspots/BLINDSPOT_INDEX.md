# Blindspot Index

This index categorizes every identified blindspot in the DeepResearcher v2 codebase.

## Top 10 Most Urgent Blindspots

| ID | Title | Category | Severity | Confidence | Status | Primary Path | Blocking? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BS-VER-001 | Execution Conflated with Correctness | Verification | High | High | Fact | `agent/sandbox.py` | Yes |
| BS-ANS-001 | Raw String Vote Fracturing | Answer Pipeline | High | High | Fact | `agent/prompts.py` | Yes |
| BS-ARC-001 | Divergent Notebook Solver Loop | Architecture | High | High | Fact | `44-50-aimo3-skills-optional-luck-required.ipynb` | Yes |
| BS-EVA-001 | Proxy Metrics Drive Auto-Patching | Evaluation | High | High | Strong Inference | `analysis/analyze_results.py` | Yes |
| BS-VER-002 | Confirmation Bias in NL Verifier | Verification | High | High | Fact | `agent/deep_researcher.py` | No |
| BS-SEC-001 | Weak Python Sandbox Isolation | Security | High | High | Fact | `agent/sandbox.py` | No |
| BS-ANS-002 | Strict Regex Fails on Valid Prose | Answer Pipeline | Medium | High | Fact | `agent/prompts.py` | Yes |
| BS-ARC-002 | Unclear Package Entrypoint | Architecture | Medium | Medium | Strong Inference | `notebook/kaggle_notebook.py` | Yes |
| BS-TST-001 | Missing Answer Normalization Tests | Testing | Medium | High | Fact | `tests/test_agent.py` | Yes |
| BS-DAT-001 | Artifact Provenance Ambiguity | Data/Artifacts | Medium | Low | Weak Suspicion | `research_data.jsonl` | No |

## Top 5 Most Uncertain but Dangerous Blindspots

| ID | Title | Category | Severity | Confidence | Status | Primary Path | Blocking? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BS-UNK-001 | Does Kaggle Enforce Offline Wheels? | Known Unknowns | High | Low | Unresolved Unknown | `notebook/kaggle_notebook.py` | No |
| BS-UNK-002 | Is the `.jsonl` data tainted? | Data/Artifacts | High | Low | Unresolved Unknown | `*.jsonl` | No |
| BS-UNK-003 | Does GenSelect Handle Truncation Well? | Future/Reward | High | Low | Unresolved Unknown | `agent/deep_researcher.py` | No |
| BS-UNK-004 | Is the Fail-Fast Swap to 72B tested? | Architecture | High | Low | Unresolved Unknown | `notebook/kaggle_notebook.py` | No |
| BS-UNK-005 | Do analysis patches overfit? | Evaluation | High | Low | Unresolved Unknown | `analysis/analyze_results.py` | Yes |

## Full Index by Category

### Architecture
| ID | Title | Severity | Confidence | Status | Primary Path | Blocking? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BS-ARC-001 | Divergent Notebook Solver Loop | High | High | Fact | `44-50*.ipynb` | Yes |
| BS-ARC-002 | Unclear Package Entrypoint | Medium | Medium | Strong Inference | `notebook/kaggle_notebook.py` | Yes |

### Answer Pipeline
| ID | Title | Severity | Confidence | Status | Primary Path | Blocking? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BS-ANS-001 | Raw String Vote Fracturing | High | High | Fact | `agent/prompts.py` | Yes |
| BS-ANS-002 | Strict Regex Fails on Valid Prose | Medium | High | Fact | `agent/prompts.py` | Yes |
| BS-ANS-003 | GenSelect Truncation Penalty | Medium | Medium | Strong Inference | `agent/deep_researcher.py` | No |

### Verification
| ID | Title | Severity | Confidence | Status | Primary Path | Blocking? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BS-VER-001 | Execution Conflated with Correctness | High | High | Fact | `agent/sandbox.py` | Yes |
| BS-VER-002 | Confirmation Bias in NL Verifier | High | High | Fact | `agent/deep_researcher.py` | No |
| BS-VER-003 | Coarse Trace Schema | Medium | High | Fact | `agent/deep_researcher.py` | No |

### Evaluation and Metrics
| ID | Title | Severity | Confidence | Status | Primary Path | Blocking? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BS-EVA-001 | Proxy Metrics Drive Auto-Patching | High | High | Strong Inference | `analysis/analyze_results.py` | Yes |
| BS-EVA-002 | Missing Ground Truth Integration | High | High | Fact | `analysis/analyze_results.py` | No |

### Security and Sandbox
| ID | Title | Severity | Confidence | Status | Primary Path | Blocking? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BS-SEC-001 | Weak Python Sandbox Isolation | High | High | Fact | `agent/sandbox.py` | No |
| BS-SEC-002 | Execution Timeouts are Not Exact | Medium | High | Fact | `agent/sandbox.py` | No |

### Testing
| ID | Title | Severity | Confidence | Status | Primary Path | Blocking? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BS-TST-001 | Missing Answer Normalization Tests | Medium | High | Fact | `tests/test_agent.py` | Yes |
| BS-TST-002 | Tests Do Not Cover GenSelect Flow | Medium | High | Fact | `tests/test_agent.py` | No |

### Data and Artifacts
| ID | Title | Severity | Confidence | Status | Primary Path | Blocking? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BS-DAT-001 | Artifact Provenance Ambiguity | Medium | Low | Weak Suspicion | `research_data.jsonl` | No |
| BS-DAT-002 | Unstructured Text Dumps in Root | Low | High | Fact | Root `*.txt` | No |

### Notebook and Branch Divergence
| ID | Title | Severity | Confidence | Status | Primary Path | Blocking? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BS-DIV-001 | `notebook/` vs `44-50*.ipynb` Divergence | High | High | Fact | Root vs `notebook/` | Yes |
| BS-DIV-002 | Fail-Fast Logic Missing from Package | Medium | High | Fact | `notebook/kaggle_notebook.py` | No |

### Future Reward Hacking
| ID | Title | Severity | Confidence | Status | Primary Path | Blocking? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BS-RWD-001 | Syntactic Overfitting | High | High | Strong Inference | `agent/sandbox.py` | Yes |
| BS-RWD-002 | Patch Injection Vulnerability | Medium | High | Strong Inference | `notebook/kaggle_notebook.py` | Yes |
