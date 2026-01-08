#!/usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import os
import sys
from statistics import mean, stdev

sys.path.insert(0, "..")

import numpy as np

from utils.elliptic import find_equipart_angles
from utils.gaussian import gaussian_mixture


from itertools import product
from math import sqrt, pi
from faf00_settings import GEOMETRY, WORK_DIR, DEBUG
from utils.vector import Vector


from pathlib import Path

from classes.faf_analysis import FafAnalysis
from utils.conventions import construct_workfile_path, original_2_aux_file_path
from utils.ndarray_utils import elliptic_mask
from utils.image_utils import grayscale_img_path_to_255_ndarray, ndarray_to_int_png, rgba_255_path_to_255_ndarray
from utils.utils import is_nonempty_file, scream


class FafAutoUsable(FafAnalysis):

    def __init__(self, name_stem: str = "faf_analysis", description: str = "Description not provided."):
        super().__init__(name_stem, description)

    def create_parser(self):
        super().create_parser()
        self.parser.add_argument("-v", '--clean_view_only',
                                 dest="clean_view_only", action="store_true",
                                 help="Use only images with the clean view of the ROI. Default: False")
        self.parser.add_argument("-c", '--ctrl_only', dest="ctrl_only", action="store_true",
                                 help="Process only control images. Default: False.")

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

    def _write_png(self, original_image, faf_img_dict, outpng):
        (height, width) = original_image.shape
        # make empty matrix
        outmatrix = np.zeros((height, width, 4))

        # Calculate center and half-dimensions
        center_y, center_x = height // 2, width // 2
        quarter_height, quarter_width = height // 4, width // 4

        # Define the region boundaries
        y_start = center_y - quarter_height
        y_end = center_y + quarter_height
        if width > 5000:
            x_start = center_x - quarter_width//2
            x_end   = center_x + quarter_width//2
        else:
            x_start = center_x - quarter_width
            x_end   = center_x + quarter_width


        # Fill blue channel (index 2) with 255
        outmatrix[y_start:y_end, x_start:x_end, 2:4] = [255, 255]
        ndarray_to_int_png(outmatrix, outpng)
        print(f"wrote {outpng}")

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:

        if self.args.clean_view_only and not faf_img_dict['clean_view']: return "ok"
        if self.args.ctrl_only and not faf_img_dict['case_id']['is_control']: return "ok"

        [original_image_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict['case_id']['alias']
        outpng = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, "png")
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)

        original_image = grayscale_img_path_to_255_ndarray(original_image_path)
        self._write_png(original_image, faf_img_dict, outpng)
        return f"{outpng} ok"


def main():

    faf_analysis = FafAutoUsable(name_stem="auto_usable")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
