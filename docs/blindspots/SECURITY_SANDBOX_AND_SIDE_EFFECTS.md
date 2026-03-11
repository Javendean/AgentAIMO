# Security Sandbox and Side Effects Blindspots

This document exposes sandbox assumptions, import blocking, side-effect risks, misleading claims, and environment dependencies.

- Blindspot ID: BS-SEC-001
- Title: Weak Python Sandbox Isolation
- Category: Security Sandbox and Side Effects
- Severity: high
- Confidence: high
- Status: fact
- Why this is a blindspot: The "sandbox" in `agent/sandbox.py` relies solely on a `SAFETY_PREAMBLE` injected into the user code that overwrites built-ins (`__import__`) and blocks modules (`os`, `subprocess`, `shutil`).
- Evidence:
  - `agent/sandbox.py:SAFETY_PREAMBLE`: `_BLOCKED_MODULES = {'os', 'subprocess', 'shutil', ...}`
  - The script is then executed via a standard `subprocess.run(timeout=...)` on the host machine.
- What could be misleading: The docstring claims it prevents "dangerous operations (file I/O, network, system commands)". While true for naïve Python code, this is not a true security sandbox (like a Docker container, gVisor, or unprivileged user account). It is a highly permeable AST/runtime patch that an advanced model could trivially bypass using reflection, `ctypes` (if not perfectly blocked), or other Python internals.
- Potential consequence: If the agent is allowed to execute arbitrary code (especially on a machine with network access or sensitive files), a sufficiently clever or hallucinating model could break out of the Python runtime and execute arbitrary bash commands or leak data. The Kaggle environment mitigates this somewhat, but local runs are vulnerable.
- How to verify or falsify it: Attempt a Python jailbreak (e.g., using `().__class__.__bases__[0].__subclasses__()`) in `test_sandbox_blocks_os` and observe if the model can execute a system command.
- Recommended next step: If true security is required (especially if moving beyond math problems), use a containerized sandbox or a more robust AST parser like `RestrictedPython`. Update the docstring to clarify it is merely a "safety rail," not a "security sandbox."
- Blocks future work? no

- Blindspot ID: BS-SEC-002
- Title: Execution Timeouts are Not Exact
- Category: Security Sandbox and Side Effects
- Severity: medium
- Confidence: high
- Status: fact
- Why this is a blindspot: The sandbox relies on `subprocess.run(timeout=...)`.
- Evidence:
  - `agent/sandbox.py:run_verification`: `subprocess.run(..., timeout=timeout)`
- What could be misleading: A reader might assume this strictly prevents the model from consuming more than the allotted time per attempt.
- Potential consequence: `subprocess.run` timeouts only apply to the wall-clock time of the child process. They do not account for CPU spin-up, memory allocation overhead, or the fact that a tight loop in C (e.g., via a library the model imports) might not cleanly terminate on a SIGTERM, potentially hanging the parent process. Furthermore, the docstring claims to prevent "memory bombs that could OOM the Kaggle container," but `subprocess.run` has no cgroup or `ulimit` memory restrictions.
- How to verify or falsify it: Write a test that attempts to allocate 100GB of memory in a single array and observe that it crashes the parent process rather than being caught by a sandbox memory limit.
- Recommended next step: Add `ulimit -v` (virtual memory limits) to the subprocess command or update the docs to remove the claim about preventing OOMs.
- Blocks future work? no