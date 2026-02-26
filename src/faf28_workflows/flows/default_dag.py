from faf15_background_hists import FafBgHistogram
from faf17_mask_creation import  FafFullMask
from faf22_roi_histograms import FafROIHistogram
from faf25_pixel_score import FafPixelScore
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
    dag.add_node(name="FafRecalibration", job_class=FafRecalibration)
    dag.add_node(name="FafFoveaDisc", job_class=FafFoveaDisc, config_factory=lambda: {"db_store": True})
    dag.add_node(name="FafAutoBg", job_class=FafAutoBg)
    
    dag.add_node(name="FafVasculature", job_class=FafVasculature)
    dag.add_node(name="FafInnerMask", job_class=FafFullMask, config_factory=lambda: {"outer_ellipse": False})
    dag.add_node(name="FafOuterMask", job_class=FafFullMask, config_factory=lambda: {"outer_ellipse": True})

    dag.add_node(name="FafBgHistogram", job_class=FafBgHistogram)
    dag.add_node(name="FafROIHistogram", job_class=FafROIHistogram)

    dag.add_node(name="FafPixelScore", job_class=FafPixelScore)

    ###################################################
    # 2. Define Edges (Dependencies)
    # FafDenoising -> FafRecalibration
    dag.add_edge("FafDenoising", "FafRecalibration")

    # FafRecalibration -> FafFoveaDisc
    dag.add_edge("FafRecalibration", "FafFoveaDisc")

    # FafRecalibration -> FafVasculature
    dag.add_edge("FafRecalibration", "FafVasculature")

    # mask components
    dag.add_edge("FafFoveaDisc", "FafInnerMask")
    dag.add_edge("FafVasculature", "FafInnerMask")

    dag.add_edge("FafInnerMask", "FafROIHistogram")

    # mask components
    dag.add_edge("FafFoveaDisc", "FafOuterMask")
    dag.add_edge("FafVasculature", "FafOuterMask")

    dag.add_edge("FafOuterMask", "FafAutoBg")

    dag.add_edge("FafAutoBg", "FafBgHistogram")
    dag.add_edge("FafOuterMask", "FafBgHistogram")

    dag.add_edge("FafROIHistogram", "FafPixelScore")
    dag.add_edge("FafBgHistogram", "FafPixelScore")

    return dag
