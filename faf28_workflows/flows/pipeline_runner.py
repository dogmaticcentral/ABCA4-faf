from pathlib import Path
from typing import Any

from prefect import get_run_logger

from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF"]

from faf28_workflows.flows.main_flow import create_default_pipeline
from faf28_workflows.flows.pipeline_def import PipelineDefinition
from faf28_workflows.tasks.wrapper import FafStepResult, wrap_faf_analysis_step_as_task


class PipelineRunner:
    """
    Convenience class for running pipelines with stored configuration.

    Provides a clean API for pipeline execution with automatic
    database initialization and cleanup.
    """

    def __init__(
            self,
            log_level: str = "INFO",
            pipeline: PipelineDefinition | None = None,
    ) -> None:
        """
        Initialize the pipeline runner.

        Args:
            log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'OFF')
            pipeline: Custom pipeline definition (uses default if None)
        """
        self.log_level = log_level

        # Create or use a provided pipeline
        self._pipeline = pipeline or create_default_pipeline()

    @property
    def available_jobs(self) -> list[str]:
        """Get list of available job names."""
        return self._pipeline.job_names

    def run(
            self,
            input_data: Any,
            start_from: str | None = None,
            stop_after: str | None = None,
    ) -> FafStepResult[Any]:
        """
        Run a pipeline of jobs sequentially.

        This single flow handles all entry points by specifying
        start_from and stop_after parameters.
        """
        logger = get_run_logger()

        # Get the jobs to run
        jobs_to_run = self._pipeline.get_jobs_in_range(start_from, stop_after)
        job_names = [j.name for j in jobs_to_run]

        if self.log_level != "OFF":
            logger.info(f"Pipeline '{self._pipeline.name}' executing jobs: {job_names}")

        if not jobs_to_run:
            logger.warning("No jobs to run")
            return FafStepResult(success=True, output=input_data)

        # Execute jobs sequentially
        current_data = input_data
        result: FafStepResult[Any] | None = None

        for i, spec in enumerate(jobs_to_run):
            if self.log_level != "OFF":
                logger.info(f"Step {i + 1}/{len(jobs_to_run)}: {spec.name}")

            # Create and run the task
            job_task = wrap_faf_analysis_step_as_task(spec)
            result = job_task(current_data)

            if not result.success:
                logger.error(f"Pipeline stopped at job '{spec.name}': {result.error}")
                return result

            # Output of this job becomes input to next job
            current_data = result.output

        if self.log_level != "OFF":
            logger.info(f"Pipeline completed successfully")

        return result  # type: ignore[return-value]

    # Convenience methods for common patterns
    def run_full(self, input_data: Any) -> FafStepResult[Any]:
        """Run the complete pipeline."""
        return self.run(input_data)

    def run_single(self, job_name: str, input_data: Any) -> FafStepResult[Any]:
        """Run a single job."""
        return self.run(input_data, start_from=job_name, stop_after=job_name)

    def run_from(self, job_name: str, input_data: Any) -> FafStepResult[Any]:
        """Run from a specific job to the end."""
        return self.run(input_data, start_from=job_name)

    def run_until(self, job_name: str, input_data: Any) -> FafStepResult[Any]:
        """Run from the beginning until a specific job."""
        return self.run(input_data, stop_after=job_name)
