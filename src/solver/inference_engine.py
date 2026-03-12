"""Inference engine module for AgentAIMO."""

from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List, Tuple, Any

Problem = Any
SolutionTrace = Any


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.95
    stop_sequences: list[str] = field(default_factory=list)
    system_prompt: str = ""
    few_shot_examples: list[Tuple[str, str]] = field(default_factory=list)
    tool_use_enabled: bool = True


class InferenceEngine(ABC):
    """Abstract base for model inference backends."""

    @abstractmethod
    def load_model(self, model_path: str, **kwargs: Any) -> None:
        """Load the model.

        Args:
            model_path: Path to the model.
            **kwargs: Additional model configuration.
        """
        raise NotImplementedError

    @abstractmethod
    def generate(self, problem: Problem, config: GenerationConfig) -> SolutionTrace:
        """Generate a solution trace for a problem.

        Args:
            problem: The problem to solve.
            config: Configuration for generation.

        Returns:
            A solution trace for the problem.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_batch(self, problem: Problem, configs: list[GenerationConfig]) -> list[SolutionTrace]:
        """Generate a batch of solution traces for a problem.

        Args:
            problem: The problem to solve.
            configs: Configurations for generation.

        Returns:
            A list of solution traces for the problem.
        """
        raise NotImplementedError

    @abstractmethod
    def unload_model(self) -> None:
        """Unload the model to free resources."""
        raise NotImplementedError

    @abstractmethod
    def get_vram_usage_gb(self) -> float:
        """Get the VRAM usage of the loaded model in GB.

        Returns:
            The VRAM usage in gigabytes.
        """
        raise NotImplementedError


class VLLMEngine(InferenceEngine):
    """vLLM backend for Kaggle H100."""

    def __init__(self, model_path: str = "", quantization: str = "mxfp4",
                 gpu_memory_utilization: float = 0.90, max_model_len: int = 8192,
                 tensor_parallel_size: int = 1):
        """Initialize the vLLM engine.

        Args:
            model_path: Path to the model.
            quantization: Quantization format.
            gpu_memory_utilization: GPU memory utilization factor.
            max_model_len: Maximum sequence length.
            tensor_parallel_size: Tensor parallel size.
        """
        self.model_path = model_path
        self.quantization = quantization
        self.gpu_memory_utilization = gpu_memory_utilization
        self.max_model_len = max_model_len
        self.tensor_parallel_size = tensor_parallel_size
        raise NotImplementedError

    def _build_prompt(self, problem: Problem, config: GenerationConfig) -> str:
        """Build a prompt string for generation.

        Args:
            problem: The problem to solve.
            config: Configuration for generation.

        Returns:
            A prompt string.
        """
        raise NotImplementedError

    def load_model(self, model_path: str, **kwargs: Any) -> None:
        """Load the model.

        Args:
            model_path: Path to the model.
            **kwargs: Additional model configuration.
        """
        raise NotImplementedError

    def generate(self, problem: Problem, config: GenerationConfig) -> SolutionTrace:
        """Generate a solution trace for a problem.

        Args:
            problem: The problem to solve.
            config: Configuration for generation.

        Returns:
            A solution trace for the problem.
        """
        raise NotImplementedError

    def generate_batch(self, problem: Problem, configs: list[GenerationConfig]) -> list[SolutionTrace]:
        """Generate a batch of solution traces for a problem.

        Args:
            problem: The problem to solve.
            configs: Configurations for generation.

        Returns:
            A list of solution traces for the problem.
        """
        raise NotImplementedError

    def unload_model(self) -> None:
        """Unload the model to free resources."""
        raise NotImplementedError

    def get_vram_usage_gb(self) -> float:
        """Get the VRAM usage of the loaded model in GB.

        Returns:
            The VRAM usage in gigabytes.
        """
        raise NotImplementedError
