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
    from faf08_auto_preproc.faf0810_auto_bg_regions import FafAutoBg
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

    # here can run vasc detection and fovea and disc detection - they are independent

    description  = "Locate the recalibrated version of the input image and find the fovea and disc. "
    description += "Save the  fovea and disc locations in the project database"
    pipeline.add_job(
        name="FafFoveaDisc",
        job_class=FafFoveaDisc,
        description=description,
        config_factory=lambda: {"db-store": True}
    )

    # here can run mask creation (needs usable region [manual or ellipse], fovea/disc and vasculature)
    # and FafAutoBg (needs usable region and  fovea/disc)

    # TODO this should be a "side job", FafAutoBg does not depend on it
    # description  = "For the input image retrieve the fovea and disc locations from the database. "
    # description += "Create visualization, showing the location superimposed on te original image."
    # pipeline.add_job(
    #     name="FafFDVisualization",
    #     job_class=FafFDVisualization,
    #     description=description,
    # )

    description  = "For the input image retrieve the fovea and disc locations from the database. "
    description += "Use heuristic to find a reference region."
    pipeline.add_job(
        name="FafAutoBg",
        job_class=FafAutoBg,
        description=description,
    )

    # here can run bg histograms - need ref region, auto or otherwise, and mask
    #  also cen run roi histograms -need mask

    return pipeline

