"""Configuration management for the pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from faf00_settings import WORK_DIR

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF"]


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for the pipeline."""

    database_path: Path = field(default_factory=lambda: Path("./data/pipeline.db"))
    output_directory: Path = field(default_factory=lambda: Path(WORK_DIR))
    log_level: LogLevel = "INFO"

    def __post_init__(self) -> None:
        """Ensure directories exist."""
        # Use object.__setattr__ because dataclass is frozen
        object.__setattr__(
            self,
            'output_directory',
            Path(self.output_directory)
        )
        self.output_directory.mkdir(parents=True, exist_ok=True)

    def get_numeric_log_level(self) -> int:
        """Convert log level string to numeric value."""
        if self.log_level == "OFF":
            return logging.CRITICAL + 10  # Higher than any standard level
        return getattr(logging, self.log_level)


def get_config() -> PipelineConfig:
    """Get the current configuration."""
    return PipelineConfig()
