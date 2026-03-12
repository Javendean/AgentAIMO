"""Python execution module for AgentAIMO."""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List


@dataclass
class ExecutionResult:
    """Result of sandboxed Python code execution."""
    code: str
    stdout: str = ""
    stderr: str = ""
    return_code: int = -1
    timed_out: bool = False
    wall_time_seconds: float = 0.0

    @property
    def success(self) -> bool:
        """Return True if execution was successful and didn't time out."""
        return self.return_code == 0 and not self.timed_out


class PythonExecutor:
    """Sandboxed Python execution via subprocess."""

    def __init__(self, timeout_seconds: float = 30.0, max_output_chars: int = 10_000,
                 allowed_imports: Optional[List[str]] = None):
        """Initialize the Python executor.

        Args:
            timeout_seconds: Maximum time in seconds to allow code execution.
            max_output_chars: Maximum characters to capture from stdout and stderr.
            allowed_imports: Optional list of allowed module imports.
        """
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars
        self.allowed_imports = allowed_imports
        raise NotImplementedError

    def execute(self, code: str) -> ExecutionResult:
        """Write to tempfile, run subprocess, capture output.

        Args:
            code: Python code to execute.

        Returns:
            The result of code execution.
        """
        raise NotImplementedError

    def _validate_code(self, code: str) -> Tuple[bool, str]:
        """Reject: forbidden imports, open(), os.*, subprocess.*, network, eval/exec.

        Args:
            code: Python code to validate.

        Returns:
            A tuple of boolean indicating validity, and an error message if invalid.
        """
        raise NotImplementedError

    def execute_and_extract_result(self, code: str, result_variable: str = "result") -> Tuple[ExecutionResult, Optional[str]]:
        """Append print(repr(variable)), extract from last stdout line.

        Args:
            code: Python code to execute.
            result_variable: Name of variable to extract.

        Returns:
            A tuple of ExecutionResult and the extracted result string.
        """
        raise NotImplementedError
