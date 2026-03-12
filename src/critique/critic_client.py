"""Client for communicating with models to generate critiques."""

from typing import Any, Dict, List, Optional, Tuple

# Assuming some basic type classes that will be defined elsewhere
class APIClient:
    pass

class Problem:
    pass

class SolutionTrace:
    pass

class CritiqueItem:
    pass

class Critique:
    pass


CRITIC_SYSTEM_PROMPT = """You are a ruthless mathematical peer reviewer for
competition mathematics (AMC/AIME/IMO level). Your job is to find errors,
not to praise.

For EACH logical step in the solution, you must:
- State whether the step is VALID or INVALID
- If INVALID: identify the specific flaw
- Rate severity: FATAL/MAJOR/MINOR/SUGGESTION

You MUST attempt to both validate AND attack the solution.
Output critique as JSON array. End with overall judgment and confidence."""


class CriticClient:
    """Client for generating natural language critiques of mathematical solutions."""

    def __init__(
        self,
        api_client: APIClient,
        default_model: str = "deepseek-v3.2-speciale",
        max_retries: int = 3,
    ) -> None:
        """Initialize the CriticClient.

        Args:
            api_client: API client instance for making requests.
            default_model: The default model to use for generating critiques.
            max_retries: The maximum number of retry attempts for failed requests.
        """
        self.api_client = api_client
        self.default_model = default_model
        self.max_retries = max_retries

    def critique(
        self,
        problem: Problem,
        trace: SolutionTrace,
        verification_report: Optional[Any] = None,
        model: Optional[str] = None,
    ) -> Critique:
        """Call frontier model to critique solution.

        Args:
            problem: The problem being solved.
            trace: The solution trace to critique.
            verification_report: Optional report from formal verification.
            model: Optional model to use instead of the default.

        Returns:
            The generated Critique object.
        """
        pass

    def _parse_critique_response(
        self, raw_response: str, model: str
    ) -> Tuple[list[CritiqueItem], str, float]:
        """Parse JSON response. Handle malformed JSON gracefully.

        Args:
            raw_response: The raw string response from the model.
            model: The name of the model that generated the response.

        Returns:
            A tuple containing a list of critique items, the overall judgment string,
            and the confidence score as a float.
        """
        pass
