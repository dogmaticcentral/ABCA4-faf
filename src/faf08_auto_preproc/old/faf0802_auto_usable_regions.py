#!/usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import os
import sys

sys.path.insert(0, "../../..")

import numpy as np

from faf00_settings import WORK_DIR

from pathlib import Path

from faf_classes.faf_analysis import FafAnalysis
from utils.conventions import construct_workfile_path, original_2_aux_file_path
from utils.image_utils import grayscale_img_path_to_255_ndarray, ndarray_to_int_png
from utils.utils import is_nonempty_file, scream


class FafAutoUsable(FafAnalysis):

    def __init__(self, name_stem: str = "faf_analysis", description: str = "Description not provided."):
        super().__init__(name_stem, description)

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        """Check the presence of all input files that we need to create the composite img.
        :param faf_img_dict:
        :return: list[Path]
        """
        original_image_path = Path(faf_img_dict["image_path"])
        usable_region_path  = original_2_aux_file_path(original_image_path, ".usable_region.png")

        for region_png in [original_image_path]:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()
        # TODO check that the outer ellipse and the orig image actually match
        return [original_image_path]

    def _write_png(self, original_image, outpng):
        (height, width) = original_image.shape
        # make empty matrix
        outmatrix = np.zeros((height, width, 4), dtype=np.uint8)

        # Calculate center and half-dimensions
        center_y, center_x = height // 2, width // 2
        radius_x = 350  # horizontal radius
        radius_y = 200   # vertical radius

        # Create coordinate grids
        y, x = np.ogrid[:height, :width]

        # Ellipse equation
        inside_ellipse = ((x - center_x)**2 / radius_x**2 +
                          (y - center_y)**2 / radius_y**2) <= 1

        # Set blue (channel 2) and alpha (channel 3) to 255 inside ellipse
        outmatrix[inside_ellipse, 2:4] = [255, 255]  # Blue

        ndarray_to_int_png(outmatrix, outpng)
        print(f"wrote {outpng}")

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:

        if self.args.ctrl_only and not faf_img_dict['case_id']['is_control']: return "ok"

        [original_image_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict['case_id']['alias']
        eye   = faf_img_dict['eye']
        outpng = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, eye=eye, filetype="png")
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)

        original_image = grayscale_img_path_to_255_ndarray(original_image_path)
        self._write_png(original_image, outpng)
        return f"{outpng} ok"


def main():

    faf_analysis = FafAutoUsable(name_stem="auto_usable")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
