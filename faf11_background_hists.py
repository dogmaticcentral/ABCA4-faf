#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

import os
from pathlib import Path
from pprint import pprint

from faf00_settings import WORK_DIR, USE_AUTO
from classes.faf_analysis import FafAnalysis
from utils.conventions import construct_workfile_path, original_2_aux_file_path
from utils.gaussian import gaussian_mixture
from utils.image_utils import rgba_255_path_to_255_ndarray, grayscale_img_path_to_255_ndarray
from utils.ndarray_utils import in_mask_histogram
from utils.plot_utils import plot_histogram
from utils.utils import is_nonempty_file, scream


class FafBgHistograms(FafAnalysis):

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        """Check the presence of all input files that we need to create the composite img.
         :param faf_img_dict:
         :return: list[Path]
         """
        original_image_path  = Path(faf_img_dict['image_path'])
        if USE_AUTO:
            if not faf_img_dict['clean_view']: return [Path(""), Path(""), Path("")]
            alias = faf_img_dict['case_id']['alias']
            bg_sample_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "auto_bg", "png")
        else:
            bg_sample_path = original_2_aux_file_path(original_image_path, ".bg_sample.png")
        usable_region_path = original_2_aux_file_path(original_image_path, ".usable_region.png")
        for region_png in [original_image_path, usable_region_path, bg_sample_path]:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()

        return [original_image_path, usable_region_path, bg_sample_path]

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        if USE_AUTO and not faf_img_dict['clean_view']: return "ok"
        [original_image_path, usable_region_path, bg_sample_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict['case_id']['alias']
        hist_path      = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, 'txt')
        hist_img_path  = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, 'png')
        if skip_if_exists and is_nonempty_file(hist_img_path):
            print(f"{os.getpid()} {hist_img_path} found")
            return str(hist_img_path)

        original_image = grayscale_img_path_to_255_ndarray(original_image_path)
        usable_region  = rgba_255_path_to_255_ndarray(usable_region_path, channel=2)
        bg_region      = rgba_255_path_to_255_ndarray(bg_sample_path, channel=2)
        mask = usable_region*bg_region
        histogram = in_mask_histogram(original_image, mask, hist_path, skip_if_exists)
        (fitted_gaussians, weights) = gaussian_mixture(histogram, n_comps_to_try=[1])
        plot_histogram(histogram, hist_img_path,
                       title="pixel intensity histogram (bg sample)",
                       fitted_gaussians=fitted_gaussians, weights=weights,
                       skip_if_exists=skip_if_exists)

        if is_nonempty_file(hist_img_path):
            print(f"{os.getpid()} {hist_img_path} done")
            return str(hist_img_path)
        else:
            print(f"{os.getpid()} {hist_img_path} failed")
            return f"bg histogram for {original_image} failed"


def main():
    name_stem = "auto_bg_histogram" if USE_AUTO else "bg_histogram"
    faf_analysis = FafBgHistograms(name_stem=name_stem)
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()

