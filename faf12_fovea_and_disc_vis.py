#!/usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from pathlib import Path

import numpy as np
from PIL import Image as PilImage
from PIL import ImageDraw

from faf_classes.faf_analysis import FafAnalysis
from faf00_settings import WORK_DIR, GEOMETRY
from utils.conventions import construct_workfile_path
from utils.fundus_geometry import disc_fovea_distance
from utils.image_utils import grayscale_img_path_to_255_ndarray, ndarray_to_int_png
from utils.utils import is_nonempty_file, shrug


class FafFDVisualization(FafAnalysis):
    """
    Create visualization of FAF images with fovea and disc locations marked.
    Fovea is marked with a green circle, disc with a red circle.
    """

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        """
        Validate that recalibrated images exist and fovea/disc coordinates are available.
        
        Args:
            faf_img_dict: Dictionary containing FAF image metadata from database
            
        Returns:
            List of input file paths required for processing
        """
        original_image_path = Path(faf_img_dict['image_path'])
        if not is_nonempty_file(original_image_path):
            raise FileNotFoundError(f"Recalibrated image not found: {original_image_path}")
        return [original_image_path]

    def create_annotated_image(self, faf_img_dict: dict, skip_if_exists=False) -> str:
        """
        Create an annotated image with fovea and disc circles.
        
        Args:
            faf_img_dict: Dictionary containing FAF image metadata
            skip_if_exists: Skip if output already exists
            
        Returns:
            Path to created image or error message
        """
        original_image_path = Path(faf_img_dict['image_path'])
        alias = faf_img_dict['case_id']['alias']
        eye = faf_img_dict['eye']
        
        # Construct output path
        output_path = construct_workfile_path(
            WORK_DIR, original_image_path, alias, 'fovea_disc_vis',
            eye=eye, filetype='png'
        )
        
        if skip_if_exists and is_nonempty_file(output_path):
            return str(output_path)
        
        # Check for null coordinates
        disc_x = faf_img_dict.get('disc_x')
        disc_y = faf_img_dict.get('disc_y')
        fovea_x = faf_img_dict.get('fovea_x')
        fovea_y = faf_img_dict.get('fovea_y')
        
        if None in [disc_x, disc_y, fovea_x, fovea_y]:
            warning_msg = f"Warning: Missing coordinates for {original_image_path} - skipping"
            shrug(warning_msg)
            return f"skipped: {original_image_path}"

        
        # Load the recalibrated image
        img_array = grayscale_img_path_to_255_ndarray(original_image_path)
        
        # Convert grayscale to RGB for colored circles
        rgb_array = np.stack([img_array, img_array, img_array], axis=-1)
        pil_image = PilImage.fromarray(rgb_array.astype(np.uint8))
        
        # Create drawing context
        draw = ImageDraw.Draw(pil_image)
        
        # Calculate circle radii based on disc-fovea distance
        disc_center = (disc_x, disc_y)
        fovea_center = (fovea_x, fovea_y)
        dist = disc_fovea_distance(disc_center, fovea_center)
        
        disc_radius = int(round(dist * GEOMETRY["disc_radius"]))
        fovea_radius = int(round(dist * GEOMETRY["fovea_radius"]))
        
        # Draw red circle around disc
        disc_bbox = [
            disc_x - disc_radius,
            disc_y - disc_radius,
            disc_x + disc_radius,
            disc_y + disc_radius
        ]
        draw.ellipse(disc_bbox, outline='red', width=8)
        
        # Draw green circle around fovea
        fovea_bbox = [
            fovea_x - fovea_radius,
            fovea_y - fovea_radius,
            fovea_x + fovea_radius,
            fovea_y + fovea_radius
        ]
        draw.ellipse(fovea_bbox, outline='green', width=8)
        
        # Convert back to numpy array and save
        annotated_array = np.array(pil_image)
        ndarray_to_int_png(annotated_array, output_path)

        if is_nonempty_file(output_path):
            return str(output_path)
        else:
            return f"{output_path} failed"

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        """
        Process a single image: create annotated visualization.
        
        Args:
            faf_img_dict: Dictionary containing FAF image metadata
            skip_if_exists: Skip if output already exists
            
        Returns:
            Path to created image or status message
        """

        return self.create_annotated_image(faf_img_dict, skip_if_exists)


def main():
    # description = "Create visualizations of recalibrated FAF images with fovea (green) and disc (red) circles."
    faf_analysis = FafFDVisualization(name_stem="fovea_disc_vis")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
