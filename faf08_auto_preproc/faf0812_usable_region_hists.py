#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

import os
from pathlib import Path

from faf00_settings import WORK_DIR, USE_AUTO
from faf_classes.faf_analysis import FafAnalysis
from utils.conventions import construct_workfile_path, original_2_aux_file_path
from utils.image_utils import rgba_255_path_to_255_ndarray, grayscale_img_path_to_255_ndarray
from utils.ndarray_utils import in_mask_histogram
from utils.plot_utils import plot_histogram
from utils.utils import is_nonempty_file, scream


class FafHistograms(FafAnalysis):

    def create_parser(self):
        super().create_parser()
        self.parser.add_argument("-c", '--ctrl_only', dest="ctrl_only", action="store_true",
                                 help="Process only control images. Default: False.")


    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        """Check the presence of all input files that we need to create the composite img.
         :param faf_img_dict:
         :return: list[Path]
         """
        original_image_path  = Path(faf_img_dict['image_path'])
        stem  = "auto_usable" if USE_AUTO else "usable_regions"
        alias = faf_img_dict["case_id"]['alias']
        usable_region_path = construct_workfile_path(WORK_DIR, original_image_path, alias, stem, "png")
        for region_png in [original_image_path, usable_region_path]:
            if not is_nonempty_file(region_png):
                raise FileNotFoundError(f"{region_png} does not exist (or may be empty).")

        return [original_image_path, usable_region_path]

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        if self.args.ctrl_only and not faf_img_dict['case_id']['is_control']: return "ok"
        [original_image_path, usable_region_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict['case_id']['alias']
        hist_path      = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, 'txt')
        hist_img_path  = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, 'png')
        if skip_if_exists and is_nonempty_file(hist_img_path):
            print(f"{os.getpid()} {hist_img_path} found")
            return str(hist_img_path)

        original_image = grayscale_img_path_to_255_ndarray(original_image_path)
        mask = rgba_255_path_to_255_ndarray(usable_region_path, channel=2)
        histogram = in_mask_histogram(original_image, mask, hist_path, skip_if_exists)

        plot_histogram(histogram, hist_img_path, title="pixel intensity histogram (inner ellipse)", skip_if_exists=skip_if_exists)

        if is_nonempty_file(hist_img_path):
            print(f"{os.getpid()} {hist_img_path} done")
            return str(hist_img_path)
        else:
            print(f"{os.getpid()} {hist_img_path} failed")
            return f"vasculature detection in {original_image} failed"


def main():
    faf_analysis = FafHistograms(name_stem="histogram")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()


