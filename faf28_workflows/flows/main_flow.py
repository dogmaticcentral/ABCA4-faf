from pathlib import Path

from faf28_workflows.flows.pipeline_def import PipelineDefinition


# =============================================================================
# Pipeline Factory
# =============================================================================

def create_default_pipeline(
        output_dir: Path | None = None,
        db_path: Path | None = None,
) -> PipelineDefinition:
    """
    Create the default pipeline.

    This factory demonstrates how to configure a pipeline.
    For N jobs, add more add_job() calls.
    """
    from faf08_auto_preproc.faf0804_img_denoising import FafDenoising

    pipeline = PipelineDefinition(name="default_pipeline")

    # Add jobs in order - scales to any number of jobs
    pipeline.add_job(
        name="FafDenoising",
        job_class=FafDenoising,
        description="Process input file and produce JSON",
    )

    return pipeline

