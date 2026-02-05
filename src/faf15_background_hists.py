#!/usr/bin/env python

"""
    © 2024-2026 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

import os
from pathlib import Path
from pprint import pprint

from scipy.sparse import eye_array

from faf00_settings import WORK_DIR, USE_AUTO, DEBUG
from faf_classes.faf_analysis import FafAnalysis
from utils.conventions import construct_workfile_path, original_2_aux_file_path
from utils.gaussian import gaussian_mixture
from utils.image_utils import rgba_255_path_to_255_ndarray, grayscale_img_path_to_255_ndarray
from utils.ndarray_utils import in_mask_histogram
from utils.plot_utils import plot_histogram
from utils.utils import is_nonempty_file, scream, shrug


class FafBgHistogram(FafAnalysis):

    def create_parser(self):
        super().create_parser()
        self.parser.add_argument("-v", '--clean_view_only',
                                 dest="clean_view_only", action="store_true",
                                 help="Use only images with the clean view of the ROI. Default: False")
        self.parser.add_argument("-d", '--denoised',
                                 dest="denoised", action="store_true",
                                 help="Use denoised images, rather that the original. Default: False")

    def input_manager(self, faf_img_dict: dict) -> list[Path | None]:
        """Check the presence of all input files that we need to create the composite img.
         :param faf_img_dict:
         :return: list[Path]
         """
        original_image_path = faf_img_dict['image_path']
        if not is_nonempty_file(original_image_path):
            msg = f"{original_image_path} not found."
            if self.args.dry_run:
                scream(msg)
            else:
                raise FileNotFoundError(msg)

        alias = faf_img_dict['case_id']['alias']
        eye   = faf_img_dict['eye']
        if self.args.denoised:
            analyzed_image_path  = construct_workfile_path(WORK_DIR, original_image_path, alias, "denoised", eye=eye, filetype='png')
        else:
            analyzed_image_path = original_image_path

        if not is_nonempty_file(analyzed_image_path):
            msg = f"{analyzed_image_path} does not exist (or may be empty)."
            if self.args.dry_run:
                scream(msg)
            else:
                raise FileNotFoundError(msg)


        if self.args.clean_view_only:
            if not faf_img_dict['clean_view']:
                if DEBUG: print(f"{ faf_img_dict['image_path']} has no clean view of the ROI")
                return [None, None, None]

        alias = faf_img_dict['case_id']['alias']
        if USE_AUTO:
            bg_sample_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "auto_bg", "png")
            # fallback on the manually determined one if auto does not exist
            if not is_nonempty_file(bg_sample_path):
                shrug(f"{bg_sample_path} does not exist (or may be empty) - falling back on the manual selection.")
                bg_sample_path = original_2_aux_file_path(original_image_path, ".bg_sample.png")
            if not is_nonempty_file(bg_sample_path):
                msg = f"Neither auto (preferred) no manual bg found for {original_image_path}"
                if self.args.dry_run:
                    scream(msg)
                else:
                    raise Exception(msg)
        else:
            bg_sample_path = original_2_aux_file_path(original_image_path, ".bg_sample.png")
            if not is_nonempty_file(bg_sample_path):
                shrug(f"{bg_sample_path} does not exist (or may be empty) - falling back on the automated selection.")
                bg_sample_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "auto_bg", "png")
                if not is_nonempty_file(bg_sample_path):
                    msg = f"Neither manual (preferred) nor auto bg found for {original_image_path}"
                    if self.args.dry_run:
                        scream(msg)
                    else:
                        raise Exception(msg)

        usable_region_path = original_2_aux_file_path(original_image_path, ".usable_region.png")
        if not is_nonempty_file(usable_region_path):
            shrug (f"{usable_region_path} does not exist (or may be empty). I'll assume no artifacts.")
            usable_region_path = None

        return [analyzed_image_path, usable_region_path, bg_sample_path]

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        original_image_path = faf_img_dict['image_path']
        alias = faf_img_dict['case_id']['alias']
        eye = faf_img_dict["eye"]
        try:
            [analyzed_image_path, usable_region_path, bg_sample_path] = self.input_manager(faf_img_dict)
        except Exception as e:
            scream(str(e))
            return str(e)

        name_stem = f"{self.name_stem}_denoised" if self.args.denoised else self.name_stem
        hist_path      = construct_workfile_path(WORK_DIR, original_image_path, alias, name_stem, eye=eye, filetype='txt')
        hist_img_path  = construct_workfile_path(WORK_DIR, original_image_path, alias, name_stem, eye=eye, filetype='png')
        if skip_if_exists and is_nonempty_file(hist_img_path):
            print(f"{os.getpid()} {hist_img_path} found")
            return str(hist_img_path)

        analyzed_image = grayscale_img_path_to_255_ndarray(analyzed_image_path)
        usable_region  = None if (usable_region_path is None) else rgba_255_path_to_255_ndarray(usable_region_path, channel=2)
        bg_region      = rgba_255_path_to_255_ndarray(bg_sample_path, channel=2)
        mask = usable_region*bg_region if (usable_region is not None) else bg_region
        histogram = in_mask_histogram(analyzed_image, mask, hist_path, skip_if_exists)

        try:
            (fitted_gaussians, weights) = gaussian_mixture(histogram, n_comps_to_try=[1])
        except Exception as e:
            msg = f"Gaussian fitting failed for {analyzed_image_path}: {e}\n"
            msg += f"=\tbg region: {bg_sample_path}"
            scream(msg)
            return msg

        plot_histogram(histogram, hist_img_path,
                       title="pixel intensity histogram (bg sample)",
                       fitted_gaussians=fitted_gaussians, weights=weights,
                       skip_if_exists=skip_if_exists)

        if is_nonempty_file(hist_img_path):
            print(f"{os.getpid()} {hist_img_path} done")
            return str(hist_img_path)
        else:
            print(f"{os.getpid()} {hist_img_path} failed")
            return f"bg histogram for {analyzed_image} failed"


def main():
    name_stem = "auto_bg_histogram" if USE_AUTO else "bg_histogram"
    faf_analysis = FafBgHistogram(name_stem=name_stem)
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()

