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
    from faf08_auto_preproc.faf0815_blood_vessel_detection import FafVasculature
    # from faf12_fovea_and_disc_vis import FafFDVisualization # Optional

    dag = DAG(name="default_dag")

    ###################################################
    # 1. Define Nodes
    dag.add_node(name="FafDenoising", job_class=FafDenoising, description="Denoise the input image")

    description_recal = "Locate the denoised version of the input image and recalibrate."
    dag.add_node(name="FafRecalibration", job_class=FafRecalibration, description=description_recal)

    description_vd = "For the recalibrated input image find blood vessels, where possible."
    dag.add_node(name="FafVasculature", job_class=FafVasculature, description=description_vd)

    description_fd  = "Locate the recalibrated version of the input image and find the fovea and disc. "
    description_fd += "Save the  fovea and disc locations in the project database"
    dag.add_node(name="FafFoveaDisc", job_class=FafFoveaDisc, description=description_fd)

    description_bg  = "For the input image retrieve the fovea and disc locations from the database. "
    description_bg += "Use heuristic to find a reference region."
    dag.add_node( name="FafAutoBg", job_class=FafAutoBg, description=description_bg)


    ###################################################
    # 2. Define Edges (Dependencies)
    # FafDenoising -> FafRecalibration
    dag.add_edge("FafDenoising", "FafRecalibration")

    # FafRecalibration -> FafFoveaDisc
    dag.add_edge("FafRecalibration", "FafFoveaDisc")

    # FafRecalibration -> FafVasculature
    dag.add_edge("FafRecalibration", "FafVasculature")

    # mask components
    dag.add_edge("FafFoveaDisc", "FafMask")
    dag.add_edge("FafVasculature", "FafMask")
    dag.add_edge("FafMask", "FafROIHistogram")

    # mask components
    dag.add_edge("FafFoveaDisc", "FafOuterMask")
    dag.add_edge("FafVasculature", "FafOuterMask")

    dag.add_edge("FafOuterMask", "FafAutoBg")

    dag.add_edge("FafAutoBg", "FafBgHistogram")
    dag.add_edge("FafOuterMask", "FafBgHistogram")

    dag.add_edge("FaROIHistogram", "FafPixelScore")
    dag.add_edge("FaROIHistogram", "FafPIxelScore")

    return dag
