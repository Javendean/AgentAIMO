"""API client for making model requests with retry, timeout, and cost logging."""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx

from src.models.cost import APICallRecord


MODEL_PRICING = {
    "deepseek-v3.2-speciale": (0.50, 2.00),
    "gpt-5.4-pro": (2.50, 10.00),
    "gpt-5.4-thinking": (2.50, 10.00),
    "gpt-oss-120b": (0.0, 0.0),
    "gpt-oss-20b": (0.0, 0.0),
}


class BudgetExceededError(Exception):
    """Raised when the API cost budget is exceeded."""
    pass


class APIClient:
    """Client for making API requests to models with cost tracking and budget limits."""

    def __init__(
        self,
        cost_log_path: Path = Path("data/cost_log.jsonl"),
        max_retries: int = 3,
        base_timeout_seconds: float = 120.0,
        budget_limit_usd: Optional[float] = None,
    ) -> None:
        """Initialize the APIClient.

        Args:
            cost_log_path: Path to the JSONL file for logging costs.
            max_retries: Maximum number of retries for failed requests.
            base_timeout_seconds: Base timeout for API requests.
            budget_limit_usd: Optional budget limit in USD.
        """
        self.cost_log_path = cost_log_path
        self.max_retries = max_retries
        self.base_timeout_seconds = base_timeout_seconds
        self.budget_limit_usd = budget_limit_usd

    def chat_completion(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        purpose: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> Tuple[str, APICallRecord]:
        """Make API call with retry, timeout, cost logging, budget check.

        Args:
            model: The model to use for the completion.
            system_prompt: The system prompt to set the context.
            user_message: The user message to generate a completion for.
            purpose: The purpose of the call, useful for logging.
            temperature: The sampling temperature.
            max_tokens: The maximum number of tokens to generate.

        Returns:
            A tuple containing the generated completion string and the call record.

        Raises:
            BudgetExceededError: If the budget limit is exceeded.
        """
        raise NotImplementedError("Agent must implement this method.")

    def _make_request(self, model: str, payload: Dict[str, Any], timeout: float) -> Dict[str, Any]:
        """Route to correct API endpoint based on model name.

        Args:
            model: The model name.
            payload: The request payload.
            timeout: The timeout for the request.

        Returns:
            The raw response dictionary from the API.
        """
        raise NotImplementedError("Agent must implement this method.")

    def _estimate_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """Estimate the cost of an API call based on tokens and model pricing.

        Args:
            model: The model used.
            tokens_in: The number of input tokens.
            tokens_out: The number of output tokens.

        Returns:
            The estimated cost in USD.
        """
        raise NotImplementedError("Agent must implement this method.")

    def _log_call(self, record: APICallRecord) -> None:
        """Log the API call record to the cost log.

        Args:
            record: The API call record to log.
        """
        raise NotImplementedError("Agent must implement this method.")

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get a summary of the costs incurred so far.

        Returns:
            A dictionary containing the cost summary.
        """
        raise NotImplementedError("Agent must implement this method.")
