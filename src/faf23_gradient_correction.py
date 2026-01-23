#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import os
from pathlib import Path
from statistics import mean

from playhouse.shortcuts import model_to_dict

from faf_classes.faf_analysis import FafAnalysis
from models.abca4_faf_models import FafImage, Case
from utils.conventions import construct_workfile_path
from utils.db_utils import db_connect
from utils.utils import shrug, is_nonempty_file, scream, read_simple_hist, histogram_max
from faf00_settings import SCORE_PARAMS, WORK_DIR, DEBUG

"""
Find the difference in intensity distributions in the inner an the outer ellipse for
the control images.
"""


class FafGradCorrection(FafAnalysis):
    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        """Check the presence of all input files that we need to create the composite img.
        :param faf_img_dict:
        :return: list[Path]
        """
        original_image_path = Path(faf_img_dict["image_path"])
        alias = faf_img_dict["case_id"]["alias"]
        inner_ellipse_hist_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "roi_histogram", "txt")
        outer_ellipse_hist_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "outer_roi_histogram",
                                                          "txt")
        dependencies = [inner_ellipse_hist_path, outer_ellipse_hist_path]

        for region_png in dependencies:
            if not is_nonempty_file(region_png):
                raise FileNotFoundError(f"{region_png} does not exist (or may be empty).")

        return [inner_ellipse_hist_path, outer_ellipse_hist_path]

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        pass

    def get_all_faf_dicts(self):
        return list(
            model_to_dict(f)
            for f in FafImage.select().where(FafImage.usable == True).join(Case).where(Case.is_control==True)
        )

    def run(self):
        db = db_connect()
        faf_img_dicts = self.get_all_faf_dicts()
        db.close()

        differences = []
        for faf_img_dict in faf_img_dicts:
            [inner_ellipse_hist_path, outer_ellipse_hist_path] = self.input_manager(faf_img_dict)
            try:
                difference = histogram_max(inner_ellipse_hist_path) - histogram_max(outer_ellipse_hist_path)
                differences.append(difference)
            except Exception as e:
                shrug(f"{os.getpid()} grad correction failed: {e}, moving on")
        if DEBUG: print(differences)
        return mean(differences)

def main():
    # check if the diff in maxima stored in settings
    description = "C."
    faf_analysis = FafGradCorrection(name_stem="roi_histogram")
    mean_diff = faf_analysis.run()
    print(f"mean diff = {mean_diff:.2f}")


#################################
if __name__ == "__main__":
    main()
