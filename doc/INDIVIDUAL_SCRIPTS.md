# Individual Scripts

This document provides a brief overview of the scripts and modules in the `src` directory, presented in their appearance order.

## Root Scripts

*   **`faf00_settings.py`**: Configuration settings for the project (paths, database config, etc.).
*   **`faf01_settings_sanity_check.py`**: Verifies that settings are valid and required resources are accessible.
*   **`faf02_db_tables.py`**: Defines and initializes database tables.
*   **`faf11_img_sanity_checks.py`**: Performs sanity checks on image data.
*   **`faf12_fovea_and_disc_vis.py`**: Visualizes fovea and optic disc locations on images.
*   **`faf13_plain_OS_OD_catalog.py`**: Generates a catalog (e.g., PowerPoint) of OS/OD images.
*   **`faf14_img_annot_composites.py`**: Creates composite images with annotations (fovea, disc, ROIs).
*   **`faf15_background_hists.py`**: Analyzes and plots background histograms.
*   **`faf17_mask_creation.py`**: Handles creation of image masks (e.g., elliptical masks).
*   **`faf22_roi_histograms.py`**: Generates histograms for Regions of Interest (ROIs).
*   **`faf23_gradient_correction.py`**: Performs gradient correction on images.
*   **`faf25_pixel_score.py`**: Logic for pixel scoring analysis.

## Subdirectories

### `faf03_db_loading`
Scripts responsible for loading data into the database.
*   `faf0301_load_image_info.py`: Loads basic image metadata.
*   `faf0302_fill_pair_info.py`: Populates information about image pairs.
*   `faf0303_load_image_pair_info.py`: Loads additional pair info.
*   `faf0305_load_faf123_label.py`: Loads FAF labels.
*   `faf0306_update_device_dilation.py`: Updates metadata regarding device and dilation.
*   `faf0308_load_optos_locations.py`: Loads Optos location data.

### `faf04_manual_preproc`
Tools for manual preprocessing and labelling.
*   `faf0401_disc_n_fovea_read_from_img.py`: Reads disc and fovea locations from manual annotations.

### `faf08_auto_preproc`
Automated preprocessing pipeline steps.
*   `faf0801_find_clean_view_imgs.py`: Identifies clean view images.
*   `faf0804_img_denoising.py`: Image denoising algorithms.
*   `faf0805_img_recalibration.py`: Image recalibration.
*   `faf0808_fovea_n_disc_location.py`: Auto-detection of fovea and disc.
*   `faf0810_auto_bg_regions.py`: Automated background region selection.
*   `faf0812_usable_region_hists.py`: Histograms of usable regions.
*   `faf0815_blood_vessel_detection.py`: Blood vessel detection.

### `faf10_image_qc`
Image Quality Control tools.
*   `faf1002_periodicity.py`, `faf1003_tiffinfo.py`: Technical image checks.
*   `faf1004_plot_brisque.py`, `faf1008_store_brisque.py`: BRISQUE score analysis.
*   `faf1005_ONH_gallery.py`, `faf1007_pixel_gallery.py`: Generates galleries for QC.
*   `faf1010_pixels_per_ellipse.py`: Analysis of pixels within elliptical regions.

### `faf28_workflows`
Contains the orchestration logic for the pipeline.
*   `bootstrap.py`: Entry point for setting up the Prefect environment.
*   `cli.py`: Command-line interface definition.
*   `flows/`, `tasks/`: Prefect flow and task definitions.

### `faf30_production`
Production-ready analysis and reporting scripts.
*   Generates various plots: `faf3001_score_vs_time_plot.py`, `faf3005_score_od_vs_os_plot.py`.
*   Comparisons and catalogs: `faf3006_score_comparison.py`, `faf3016_case_catalog.py`.

### `faf50_simulations`
Simulation scripts.
*   `faf5000_score_simulation.py`: Score simulation.
*   `faf5003_power_simulation.py`: Power analysis simulation.

### `models`
*   `abca4_faf_models.py`: Peewee ORM model definitions.

### `utils`
Shared utility functions for database, image processing, geometry, and plotting.
