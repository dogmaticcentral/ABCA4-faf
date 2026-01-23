"""Scalable Prefect flow definitions for sequential job pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Self

from faf_classes.faf_analysis import FafAnalysis


# =============================================================================
# Pipeline Definition Classes
# =============================================================================

@dataclass
class JobSpec:
    """Specification for a single job in the pipeline."""

    name: str
    job_class: type[FafAnalysis]
    config_factory: Callable[[], dict[str, Any]] = field(
        default_factory=lambda: lambda: {}
    )
    description: str = ""

    def create_instance(self) -> FafAnalysis:
        """Create a job instance with configuration."""
        config = self.config_factory()
        return self.job_class(**config)


class Pipeline:
    """
    Defines a sequence of jobs to be executed.

    This class is the core of the scalable design - it holds
    the job sequence and provides methods to query and slice it.
    """

    def __init__(self, name: str = "pipeline") -> None:
        self.name = name
        self._jobs: list[JobSpec] = []
        self._job_index: dict[str, int] = {}

    def add_job(
            self,
            name: str,
            job_class: type[FafAnalysis],
            config_factory: Callable[[], dict[str, Any]] | None = None,
            description: str = "",
    ) -> Self:
        """
        Add a job to the pipeline.

        Args:
            name: Unique identifier for the job
            job_class: The job class to instantiate
            config_factory: Callable that returns kwargs for job constructor
            description: Human-readable description

        Returns:
            Self for method chaining
        """
        if name in self._job_index:
            raise ValueError(f"Job '{name}' already exists in pipeline")

        spec = JobSpec(
            name=name,
            job_class=job_class,
            config_factory=config_factory or (lambda: {}),
            description=description,
        )

        self._job_index[name] = len(self._jobs)
        self._jobs.append(spec)
        return self

    @property
    def job_names(self) -> list[str]:
        """Get ordered list of job names."""
        return [job.name for job in self._jobs]

    @property
    def first_job(self) -> str:
        """Get the name of the first job."""
        if not self._jobs:
            raise ValueError("Pipeline has no jobs")
        return self._jobs[0].name

    @property
    def last_job(self) -> str:
        """Get the name of the last job."""
        if not self._jobs:
            raise ValueError("Pipeline has no jobs")
        return self._jobs[-1].name

    def __len__(self) -> int:
        return len(self._jobs)

    def __contains__(self, name: str) -> bool:
        return name in self._job_index

    def get_job_index(self, name: str) -> int:
        """Get the index of a job by name."""
        if name not in self._job_index:
            raise ValueError(
                f"Unknown job: '{name}'. Available jobs: {self.job_names}"
            )
        return self._job_index[name]

    def get_job(self, name: str) -> JobSpec:
        """Get a job specification by name."""
        return self._jobs[self.get_job_index(name)]

    def get_jobs_in_range(
            self,
            start_from: str | None = None,
            stop_after: str | None = None,
    ) -> list[JobSpec]:
        """
        Get jobs in the specified range (inclusive).

        Args:
            start_from: Job name to start from (None = first job)
            stop_after: Job name to stop after (None = last job)

        Returns:
            List of JobSpec in the range
        """
        if not self._jobs:
            return []

        start_idx = 0 if start_from is None else self.get_job_index(start_from)
        stop_idx = len(self._jobs) - 1 if stop_after is None else self.get_job_index(stop_after)

        if start_idx > stop_idx:
            raise ValueError(
                f"start_from ('{start_from}' @ {start_idx}) must come before "
                f"stop_after ('{stop_after}' @ {stop_idx})"
            )

        return self._jobs[start_idx:stop_idx + 1]

    def validate_range(
            self,
            start_from: str | None = None,
            stop_after: str | None = None,
    ) -> tuple[str, str]:
        """
        Validate and normalize a job range.

        Returns:
            Tuple of (start_job_name, stop_job_name)
        """
        start = start_from or self.first_job
        stop = stop_after or self.last_job

        # This will raise if invalid
        self.get_jobs_in_range(start, stop)

        return start, stop

