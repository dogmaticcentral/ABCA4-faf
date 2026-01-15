"""Prefect task wrappers for job faf_classes."""

from __future__ import annotations


from typing import Any, Callable, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

from prefect import task, get_run_logger

from faf28_workflows.config import PipelineConfig
from faf_classes.faf_analysis import FafAnalysis

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")

@dataclass
class FafStepResult(Generic[OutputT]):
    """Result wrapper for job execution."""

    success: bool
    output: OutputT | None = None
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.completed_at is None:
            self.completed_at = datetime.now()


def wrap_faf_analysis_step_as_task(
        job_class: type[FafAnalysis[InputT, OutputT]],
        task_name: str | None = None,
        **task_kwargs: Any
) -> Callable[[Any], FafStepResult[OutputT]]:
    """
    Wrap a FafAnalysis's single_job() method as a Prefect task.

    This allows keeping the original class definitions clean
    without decorators while still using them in Prefect flows.

    Args:
        job_class: The job class to wrap
        task_name: Optional custom task name
        **task_kwargs: Additional arguments passed to @task decorator

    Returns:
        A Prefect task function
    """
    name = task_name or f"{job_class.__name__}_task"

    @task(name=name, **task_kwargs)
    def wrapped_task(input_data: Any, **job_init_kwargs: Any) -> FafStepResult[OutputT]:
        logger = get_run_logger()

        config = PipelineConfig()
        if config.log_level != "OFF":
            logger.info(f"Starting {name} with input: {input_data}")

        job_instance = job_class(**job_init_kwargs)
        result = job_instance.execute(input_data)

        if config.log_level != "OFF":
            if result.success:
                logger.info(f"{name} completed successfully")
            else:
                logger.error(f"{name} failed: {result.error}")

        return result

    return wrapped_task

