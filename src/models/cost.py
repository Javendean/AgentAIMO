"""Billing and performance tracking models."""

from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class APICallRecord:
    """A log record for a single inference or tool API call.

    Attributes:
        model_name: The backend queried (e.g., gpt-4-turbo).
        endpoint: API URL hit.
        tokens_in: Prompt tokens used.
        tokens_out: Generated tokens.
        cost_usd: Estimated billed USD.
        wall_time_seconds: Network response time.
        success: Whether the request completed successfully.
        error_message: Any exceptions raised.
        purpose: Business reason for the call (e.g., 'critique').
        timestamp: Time the request was logged.
    """
    model_name: str
    endpoint: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    wall_time_seconds: float
    success: bool = True
    error_message: str = ""
    purpose: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def total_tokens(self) -> int:
        """Total tokens processed in the call.

        Returns:
            int: The sum of tokens in and out.
        """
        return self.tokens_in + self.tokens_out


@dataclass
class CostSummary:
    """An aggregated view of API usage over a session.

    Attributes:
        total_calls: Number of individual requests made.
        total_tokens_in: Aggregate prompt tokens.
        total_tokens_out: Aggregate generation tokens.
        total_cost_usd: Estimated aggregate billing.
        by_model: Costs breakdown per model identifier.
        by_purpose: Costs breakdown per business logic tag.
        budget_remaining_usd: If a cap exists, the remaining headroom.
    """
    total_calls: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0
    by_model: dict[str, float] = field(default_factory=dict)
    by_purpose: dict[str, float] = field(default_factory=dict)
    budget_remaining_usd: Optional[float] = None
