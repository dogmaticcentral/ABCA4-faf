#!/usr/bin/env python3
"""
Pixel Per Ellipse Analysis

Counts the number of pixels within an elliptical mask for each usable, non-control image
in the database. Uses the elliptic_mask() function to create masks based on disc and fovea
centers for each fundus autofluorescence image.
"""

from pathlib import Path

import numpy as np
from playhouse.shortcuts import model_to_dict

from classes.faf_analysis import FafAnalysis
from faf00_settings import WORK_DIR
from models.abca4_faf_models import FafImage, Case
from utils.ndarray_utils import elliptic_mask
from utils.vector import Vector


class PixelsPerEllipse(FafAnalysis):
    """
    Analysis class to count pixels within elliptical masks for FAF images.
    """

    def __init__(self):
        super().__init__(
            name_stem="pixels_per_ellipse",
            description="Count pixels within elliptical masks for each usable FAF image."
        )

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        """
        Check that all required inputs exist for processing this image.

        Args:
            faf_img_dict: Dictionary containing FAF image metadata

        Returns:
            List of input file paths required for processing
        """
        image_path = Path(faf_img_dict['image_path'])
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Check required geometry parameters
        required_fields = ['disc_x', 'disc_y', 'fovea_x', 'fovea_y', 'width', 'height']
        for field in required_fields:
            if faf_img_dict.get(field) is None:
                raise ValueError(f"Missing required field '{field}' for {image_path}")
        
        return [image_path]

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool = False) -> tuple:
        """
        Process a single image: create elliptical mask and count pixels within it.

        Args:
            faf_img_dict: Dictionary containing FAF image metadata
            skip_if_exists: If True, skip processing if output already exists

        Returns:
            Tuple of (image_path, pixel_count) on success, or (image_path, None) on failure
        """
        try:
            # Get image metadata
            image_path = faf_img_dict['image_path']
            
            # Get geometry parameters
            width = faf_img_dict['width']
            height = faf_img_dict['height']
            disc_center = Vector(faf_img_dict['disc_x'], faf_img_dict['disc_y'])
            fovea_center = Vector(faf_img_dict['fovea_x'], faf_img_dict['fovea_y'])
            
            # Calculate distance between disc and fovea (used for scaling)
            dist = Vector.distance(disc_center, fovea_center)
            
            # Create elliptical mask
            mask = elliptic_mask(
                width=width,
                height=height,
                disc_center=disc_center,
                fovea_center=fovea_center,
                dist=dist,
                usable_img_region=None,  # Optional: can be provided if available
                vasculature=None,         # Optional: can be provided if available
                outer_ellipse=False
            )
            
            # Count pixels within the mask (non-zero pixels)
            pixel_count = np.count_nonzero(mask)
            
            return (image_path, pixel_count)
            
        except Exception as e:
            error_msg = f"failed: {faf_img_dict['image_path']} - {str(e)}"
            print(error_msg)
            return (faf_img_dict['image_path'], None)

    @staticmethod
    def get_all_faf_dicts():
        """
        Override parent method to get only usable images that are not controls.

        Returns:
            List of dictionaries containing FAF image metadata
        """
        return list(
            model_to_dict(f) for f in FafImage.select()
            .where(FafImage.usable == True)
            .join(Case)
            .where(Case.is_control == True)
        )

    def run(self):
        """
        Override parent run method to collect results and write TSV output.
        """
        from distributed import Client, LocalCluster
        from faf00_settings import DATABASES
        from utils.db_utils import db_connect
        from utils.utils import shrug
        
        self.create_parser()
        self.argv_parse()

        number_of_cpus = self.args.n_cpus
        img_path = self.args.image_path

        db = db_connect()
        if img_path:
            all_faf_img_dicts = list(model_to_dict(f) for f in FafImage.select().where(FafImage.image_path == img_path))
            number_of_cpus = 1
        else:
            all_faf_img_dicts = self.get_all_faf_dicts()
        db.close()

        # Enforce single CPU if using sqlite
        if DATABASES["default"] == DATABASES["sqlite"] and number_of_cpus > 1:
            shrug("Note: sqlite cannot handle multiple access.")
            shrug("The current implementation does not know how to deal with this.")
            shrug("Please use MySQL or PostgreSQL if you'd like to use the multi-cpu version.")
            shrug("For now, I am proceeding with the single cpu version.")
            number_of_cpus = 1

        # Process all images
        if number_of_cpus == 1:
            results = [self.single_image_job(fd, self.args.skip_xisting) for fd in all_faf_img_dicts]
        else:
            # Parallelization with dask
            cluster = LocalCluster(n_workers=number_of_cpus, processes=True, threads_per_worker=1)
            dask_client = cluster.get_client()
            other_args = {'skip_if_exists': self.args.skip_xisting}
            futures = dask_client.map(self.single_image_job, all_faf_img_dicts, **other_args)
            results = dask_client.gather(futures)
            dask_client.close()

        # Write results to TSV file
        output_file = WORK_DIR / f"{self.name_stem}_results.tsv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            # Write header
            f.write("image_path\tpixel_count\n")
            
            # Write results
            successful_count = 0
            failed_count = 0
            for image_path, pixel_count in results:
                if pixel_count is not None:
                    f.write(f"{image_path}\t{pixel_count}\n")
                    successful_count += 1
                else:
                    f.write(f"{image_path}\tFAILED\n")
                    failed_count += 1
        
        print(f"\nResults written to: {output_file}")
        print(f"Successfully processed: {successful_count} images")
        if failed_count > 0:
            print(f"Failed: {failed_count} images")


def main():
    """
    Main entry point for the pixel per ellipse analysis.
    """
    analysis = PixelsPerEllipse()
    analysis.run()


if __name__ == "__main__":
    main()
