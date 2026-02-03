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
from faf_classes.faf_analysis import FafAnalysis
from models.abca4_faf_models import FafImage, Case
from utils.conventions import construct_workfile_path
from utils.db_utils import db_connect
from utils.gaussian import gaussian_mixture
from utils.image_utils import grayscale_img_path_to_255_ndarray

from utils.ndarray_utils import in_mask_histogram
from utils.plot_utils import plot_histogram
from utils.utils import is_nonempty_file, scream


class FafBgHistograms(FafAnalysis):


    def __init__(self, internal_kwargs: dict|None=None, name_stem: str = "roi_histogram"):
        super().__init__(internal_kwargs=internal_kwargs, name_stem=name_stem)
        description = "Create pixel intensity histograms within ROI "
        description += "(inner or outer elliptical region, minus optic disc, fovea, blood vessels and artifacts). "
        self.description = description

    def create_parser(self):
        super().create_parser()
        self.parser.add_argument(
            "-l",
            "--outer_ellipse",
            dest="outer_ellipse",
            action="store_true",
            help="Use the ring between the inner an the outer ellipse as the ROI. Default: False",
        )
        self.parser.add_argument("-d", '--denoised',
                                 dest="denoised", action="store_true",
                                 help="Use denoised images, rather that the original. Default: False")

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
        if not is_nonempty_file(original_image_path):
            msg = f"{original_image_path} not found."
            if self.args.dry_run:
                scream(msg)
            else:
                raise FileNotFoundError(msg)

        alias = faf_img_dict["case_id"]["alias"]
        eye = faf_img_dict["eye"]

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

        inner_ellipse_mask_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "inner_roi_mask",
                                                          eye=eye, filetype="png", should_exist=True)
        dependencies = [original_image_path, inner_ellipse_mask_path]
        if self.args.outer_ellipse:
            outer_ellipse_mask_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "outer_roi_mask",
                                                              eye=eye, filetype="png")
            dependencies.append(outer_ellipse_mask_path)
        else:
            outer_ellipse_mask_path = Path("dummy")

        for region_png in dependencies:
            if not is_nonempty_file(region_png):
                raise FileNotFoundError(f"{region_png} does not exist (or may be empty).")

        return [analyzed_image_path, inner_ellipse_mask_path, outer_ellipse_mask_path]


    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        [analyzed_image_path, inner_ellipse_mask_path, outer_ellipse_mask_path] = self.input_manager(faf_img_dict)
        original_image_path = Path(faf_img_dict["image_path"])
        alias = faf_img_dict["case_id"]["alias"]
        eye = faf_img_dict["eye"]

        name_stem = f"{self.name_stem}_denoised" if self.args.denoised else self.name_stem
        hist_path = construct_workfile_path(WORK_DIR, original_image_path, alias, name_stem,  eye=eye, filetype="txt")
        hist_img_path = construct_workfile_path(WORK_DIR, original_image_path, alias, name_stem,  eye=eye, filetype="png")
        if skip_if_exists and is_nonempty_file(hist_img_path):
            print(f"{os.getpid()} {hist_img_path} found")
            return str(hist_img_path)

        analyzed_image = grayscale_img_path_to_255_ndarray(analyzed_image_path)
        roi_region = grayscale_img_path_to_255_ndarray(inner_ellipse_mask_path)
        if self.args.outer_ellipse:
            outer_ellipse_mask_path: Path
            if not outer_ellipse_mask_path.exists():
                raise Exception("If we go to here, the outer ellipse mask should not be emtpy")
            outer_roi_region = grayscale_img_path_to_255_ndarray(outer_ellipse_mask_path)
            mask = outer_roi_region - roi_region
        else:
            mask = roi_region

        histogram = in_mask_histogram(analyzed_image, mask, hist_path, skip_if_exists)

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
            return f"counting histogram for {analyzed_image_path} failed"


def main():
    faf_analysis = FafBgHistograms()
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
