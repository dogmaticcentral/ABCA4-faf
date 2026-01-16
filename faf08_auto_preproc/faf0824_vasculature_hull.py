#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import os
import sys
from itertools import product

import numpy as np

sys.path.insert(0, "..")

from utils.image_utils import grayscale_img_path_to_255_ndarray, ndarray_to_int_png, ndarray_boolean_to_255_png

from faf00_settings import GEOMETRY, WORK_DIR

from pathlib import Path

from faf_classes.faf_analysis import FafAnalysis
from utils.conventions import construct_workfile_path
from utils.utils import is_nonempty_file, scream
from skimage.morphology import convex_hull_image


class FafVascHull(FafAnalysis):

    def create_parser(self):
        super().create_parser()
        self.parser.add_argument("-c", '--ctrl_only', dest="ctrl_only", action="store_true",
                                 help="Process only control images. Default: False.")

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        """Check the presence of all input files that we need to create the composite img.
        :param faf_img_dict:
        :return: list[Path]
        """
        original_image_path = Path(faf_img_dict["image_path"])
        alias = faf_img_dict["case_id"]["alias"]
        vasculature_path  = construct_workfile_path(WORK_DIR, original_image_path, alias, "vasculature", "png")
        for region_png in [original_image_path, vasculature_path]:
            if not is_nonempty_file(region_png):
                raise FileNotFoundError(f"{region_png} does not exist (or may be empty).")
        # TODO check that the outer ellipse and the orig image actually match
        return [original_image_path, vasculature_path]

    @staticmethod
    def _remove_white_border(image: np.ndarray):

        (height, width) = image.shape
        lr_border = int(width*0.1)
        tb_border = int(height*0.1)
        for row, col in product(range(height), range(width)):
            if tb_border < row < height - tb_border and lr_border < col < width - lr_border: continue
            image[row, col] = 0

    def _find_hull(self, inverted_vasc_img_path, path_to_hull_img):
        inverted_vasc_img = grayscale_img_path_to_255_ndarray(inverted_vasc_img_path)
        # not sure where and how bur the image may have white borders, that the hull algorithm tries to encompass
        # the following is a hack to get rid of the white border
        self._remove_white_border(inverted_vasc_img)
        chull = convex_hull_image(inverted_vasc_img)
        ndarray_boolean_to_255_png(chull, path_to_hull_img)
        print(f"\t hull written to {path_to_hull_img}")

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        # if not faf_img_dict['clean_view']: return "ok"
        if self.args.ctrl_only and not faf_img_dict['case_id']['is_control']: return "ok"
        [original_image_path, vasculature_image_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict['case_id']['alias']
        outpng = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, "png")
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)
        self._find_hull(vasculature_image_path, outpng)
        return f"{outpng} ok"


def main():

    faf_analysis = FafVascHull(name_stem="hull")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
