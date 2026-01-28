from faf28_workflows.flows.dag_class import DAG


# =============================================================================
# DAG Factory
# =============================================================================

def create_default_dag() -> DAG:
    """
    Create the default DAG.
    """
    from faf08_auto_preproc.faf0804_img_denoising import FafDenoising
    from faf08_auto_preproc.faf0805_img_recalibration import FafRecalibration
    from faf08_auto_preproc.faf0808_fovea_n_disc_location import FafFoveaDisc
    from faf08_auto_preproc.faf0810_auto_bg_regions import FafAutoBg
    # from faf12_fovea_and_disc_vis import FafFDVisualization # Optional

    dag = DAG(name="default_dag")

    # 1. Define Nodes
    dag.add_node(
        name="FafDenoising",
        job_class=FafDenoising,
        description="Denoise the input image",
    )

    dag.add_node(
        name="FafRecalibration",
        job_class=FafRecalibration,
        description="Locate the denoised version of the input image and recalibrate.",
    )

    description_fd  = "Locate the recalibrated version of the input image and find the fovea and disc. "
    description_fd += "Save the  fovea and disc locations in the project database"
    dag.add_node(
        name="FafFoveaDisc",
        job_class=FafFoveaDisc,
        description=description_fd,
        config_factory=lambda: {"db-store": True}
    )

    description_bg  = "For the input image retrieve the fovea and disc locations from the database. "
    description_bg += "Use heuristic to find a reference region."
    dag.add_node(
        name="FafAutoBg",
        job_class=FafAutoBg,
        description=description_bg,
    )

    # 2. Define Edges (Dependencies)
    # FafDenoising -> FafRecalibration
    dag.add_edge("FafDenoising", "FafRecalibration")

    # FafRecalibration -> FafFoveaDisc
    dag.add_edge("FafRecalibration", "FafFoveaDisc")

    # FafFoveaDisc -> FafAutoBg
    dag.add_edge("FafFoveaDisc", "FafAutoBg")
    


    return dag
