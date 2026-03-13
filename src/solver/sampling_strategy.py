"""Sampling strategy module for AgentAIMO."""

from dataclasses import dataclass, field
from typing import List, Tuple
from src.solver.inference_engine import GenerationConfig


@dataclass
class SamplingConfig:
    """Configuration for solution sampling strategy."""
    num_samples: int = 8
    temperatures: List[float] = field(default_factory=lambda: [0.3, 0.5, 0.7, 0.9])
    system_prompt_variants: List[str] = field(default_factory=list)
    few_shot_sets: List[List[Tuple[str, str]]] = field(default_factory=list)
    max_tokens_per_sample: int = 4096


class SamplingStrategy:
    """Strategy for sampling multiple solutions."""

    def __init__(self, config: SamplingConfig):
        self.config = config
        raise NotImplementedError

    def build_generation_configs(self) -> List[GenerationConfig]:
        """Build N configs cycling through temperatures, prompts, few-shots."""
        raise NotImplementedError
