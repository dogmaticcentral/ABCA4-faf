from faf28_workflows.flows.pipeline_class import Pipeline


# =============================================================================
# Pipeline Factory
# =============================================================================

def create_default_pipeline() -> Pipeline:
    """
    Create the default pipeline.

    This factory demonstrates how to configure a pipeline.
    For N jobs, add more add_job() calls.
    """
    from faf08_auto_preproc.faf0804_img_denoising import FafDenoising
    from faf08_auto_preproc.faf0805_img_recalibration import FafRecalibration
    from faf08_auto_preproc.faf0808_fovea_n_disc_location import FafFoveaDisc
    from faf12_fovea_and_disc_vis import FafFDVisualization

    pipeline = Pipeline(name="default_pipeline")

    # Add jobs in order - scales to any number of jobs
    pipeline.add_job(
        name="FafDenoising",
        job_class=FafDenoising,
        description="Denoise the input image",
    )

    pipeline.add_job(
        name="FafRecalibration",
        job_class=FafRecalibration,
        description="Locate the denoised version of the input image and recalibrate.",
    )

    description  = "Locate the recalibrated version of the input image and find the fovea and disc. "
    description += "Save the  fovea and disc locations in the project database"
    pipeline.add_job(
        name="FafFoveaDisc",
        job_class=FafFoveaDisc,
        description=description,
        config_factory=lambda: {"db-store": True}
    )

    description  = "For the input image retrieve the fovea and disc locations from the database. "
    description += "Create visualization, showing the location superpose on te original image"
    pipeline.add_job(
        name="FafFDVisualization",
        job_class=FafFDVisualization,
        description=description,
    )


    return pipeline

