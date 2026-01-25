import os
# Force ephemeral mode by removing API URL from env if present
# os.environ.pop("PREFECT_API_URL", None)

from typing import Any

from prefect import get_run_logger, flow

from faf28_workflows.flows.default_pipeline import create_default_pipeline
from faf28_workflows.flows.pipeline_class import Pipeline
from faf28_workflows.tasks.wrapper import FafStepResult, wrap_faf_analysis_step_as_task


class CentralPipeRunner:
    """
    Convenience class for running pipelines with stored configuration.

    Provides a clean API for pipeline execution with automatic
    database initialization and cleanup.
    """

    def __init__(
            self,
            log_level: str = "INFO",
            pipeline: Pipeline | None = None,
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
            skip_existing: bool = False
    ) -> FafStepResult[Any]| None:
        """
        Run a pipeline of jobs sequentially.

        This single flow handles all entry points by specifying
        start_from and stop_after parameters.
        """
        logger = get_run_logger()

        # Get the jobs to run
        jobs_to_run = self._pipeline.get_jobs_in_range(start_from, stop_after)
        job_names = [j.name for j in jobs_to_run]

        logger.info(f"Input data: {input_data}")
        logger.info(f"Pipeline '{self._pipeline.name}' executing jobs: {job_names}")

        if not jobs_to_run:
            logger.warning("No jobs to run")
            return None

        # Execute jobs sequentially
        result: FafStepResult[Any] | None = None

        for i, job_spec in enumerate(jobs_to_run):
            
            logger.info(f"Step {i + 1}/{len(jobs_to_run)}: {job_spec.name}")
            
            # Create and run the task
            # add the input image path to the internal_kwargs:
            pipeline_args =  {"i": str(input_data)}
            if skip_existing: pipeline_args["x"] = True
            job_kwargs = job_spec.config_factory() | pipeline_args
            job_task   = wrap_faf_analysis_step_as_task(job_spec.job_class, task_name=job_spec.name)
            result = job_task(job_kwargs=job_kwargs)

            if not result.success:
                logger.error(f"Pipeline errored out at job '{job_spec.name}': {result.error}")
                result.metadata["input_data"] = str(input_data)
                return result

        logger.info(f"Pipeline completed successfully")

        if result:
            result.metadata["input_data"] = str(input_data)

        return result

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


@flow(name="central-pipe-runner")
def central_pipe_flow(input_data: str, start_from: str|None, stop_after: str|None, skip_existing: bool):
    # This function handles the 'self' by instantiating the class here
    runner = CentralPipeRunner()
    return runner.run(
        input_data=input_data,
        start_from=start_from,
        stop_after=stop_after,
        skip_existing=skip_existing
    )
