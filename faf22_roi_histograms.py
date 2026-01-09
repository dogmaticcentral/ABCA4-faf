#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

import os
from pathlib import Path

from playhouse.shortcuts import model_to_dict

from faf00_settings import WORK_DIR
from classes.faf_analysis import FafAnalysis
from models.abca4_faf_models import FafImage, Case
from utils.conventions import construct_workfile_path
from utils.db_utils import db_connect
from utils.gaussian import gaussian_mixture
from utils.image_utils import grayscale_img_path_to_255_ndarray

from utils.ndarray_utils import in_mask_histogram
from utils.plot_utils import plot_histogram
from utils.utils import is_nonempty_file, scream


class FafBgHistograms(FafAnalysis):

    def create_parser(self):
        super().create_parser()
        self.parser.add_argument(
            "-c",
            "--ctrl_only",
            dest="ctrl_only",
            action="store_true",
            help="Run for control cases only. Default: False",
        )
        self.parser.add_argument(
            "-l",
            "--outer_ellipse",
            dest="outer_ellipse",
            action="store_true",
            help="Use the ring between the inner an the outer ellipse as the ROI. Default: False",
        )

    def argv_parse(self):
        super().argv_parse()
        if self.args.outer_ellipse:
            self.name_stem = "outer_roi_histogram"

    def get_all_faf_dicts(self):
        if self.args.ctrl_only:
            return list(
                model_to_dict(f)
                for f in FafImage.select().where(FafImage.usable == True).join(Case).where(Case.is_control==True)
            )
        else:
            return super().get_all_faf_dicts()

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        """Check the presence of all input files that we need to create the composite img.
        :param faf_img_dict:
        :return: list[Path]
        """
        original_image_path = Path(faf_img_dict["image_path"])
        alias = faf_img_dict["case_id"]["alias"]
        inner_ellipse_mask_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "elliptic_mask", "png",
                                                          should_exist=True)
        dependencies = [original_image_path, inner_ellipse_mask_path]
        if self.args.outer_ellipse:
            outer_ellipse_mask_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "outer_mask", "png")
            dependencies.append(outer_ellipse_mask_path)
        else:
            outer_ellipse_mask_path = Path("dummy")

        for region_png in dependencies:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()

        return [original_image_path, inner_ellipse_mask_path, outer_ellipse_mask_path]

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        [original_image_path, inner_ellipse_mask_path, outer_ellipse_mask_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict["case_id"]["alias"]
        hist_path = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, "txt")
        hist_img_path = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, "png")
        if skip_if_exists and is_nonempty_file(hist_img_path):
            print(f"{os.getpid()} {hist_img_path} found")
            return str(hist_img_path)

        original_image = grayscale_img_path_to_255_ndarray(original_image_path)
        roi_region = grayscale_img_path_to_255_ndarray(inner_ellipse_mask_path)
        if self.args.outer_ellipse:
            outer_ellipse_mask_path: Path
            if not outer_ellipse_mask_path.exists():
                raise Exception("If we go to here, the outer ellipse mask should not be emtpy")
            outer_roi_region = grayscale_img_path_to_255_ndarray(outer_ellipse_mask_path)
            mask = outer_roi_region - roi_region
        else:
            mask = roi_region

        histogram = in_mask_histogram(original_image, mask, hist_path, skip_if_exists)

        # (fitted_gaussians, weights) = gaussian_mixture(histogram, n_comps_to_try=[1])
        plot_histogram(
            histogram,
            hist_img_path,
            title="pixel intensity histogram",
            fitted_gaussians=None, #fitted_gaussians,
            weights=None, # weights,
            skip_if_exists=skip_if_exists,
        )

        if is_nonempty_file(hist_img_path):
            print(f"{os.getpid()} {hist_img_path} done")
            return str(hist_img_path)
        else:
            print(f"{os.getpid()} {hist_img_path} failed")
            return f"bg histogram for {original_image} failed"


def main():
    description = "Create pixel intensity histograms within ROI "
    description += "(inner or outer elliptical region, minus optic disc, fovea, blood vessels and artifacts). "
    description += "\nThe outer ellipse is used in controls, to find the difference in the location "
    description += "of peak intensities between the inner and the outer ellipse. This number can later be used "
    description += "to correct for the fact that in patients' images the background correction is estimated from "
    description += "the outer ellipse region."
    faf_analysis = FafBgHistograms(name_stem="roi_histogram")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
