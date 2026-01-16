"""Prefect task wrappers for job faf_classes."""

from __future__ import annotations


from typing import Any, Callable, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

from prefect import task, get_run_logger

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
    def wrapped_task(**job_kwargs: Any) -> FafStepResult[OutputT]:
        logger = get_run_logger()

        logger.info(f"Running {name}")

        try:
            job_instance = job_class(internal_kwargs=job_kwargs)
            job_results = job_instance.run()

            # Determine success based on results
            # Similar to how FafAnalysis checks for "failed" in output
            has_failure = any("failed" in str(r) for r in job_results)

            if not has_failure:
                logger.info(f"{name} completed successfully")
                return FafStepResult(success=True, output=job_results)
            else:
                error_msg = f"Job reported failures: {job_results}"
                logger.error(f"{name} failed: {error_msg}")
                return FafStepResult(success=False, error=error_msg, output=job_results)

        except Exception as e:
            logger.error(f"{name} crashed: {str(e)}")
            return FafStepResult(success=False, error=str(e))

    return wrapped_task

