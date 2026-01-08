#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import os
import sys
sys.path.insert(0, "..")

from utils.clustering import  circular_cluster_detector
from utils.image_utils import grayscale_img_path_to_255_ndarray
from faf00_settings import WORK_DIR, USE_AUTO

from pathlib import Path

from classes.faf_analysis import FafAnalysis
from utils.conventions import construct_workfile_path
from utils.utils import is_nonempty_file, scream


class FafFoveaDisc(FafAnalysis):

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
                scream(f"{region_png} does not exist (or may be empty).")
                exit()

        return [original_image_path, usable_region_path]


    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        # if not faf_img_dict['clean_view']: return "ok"
        [original_image_path, usable_region_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict['case_id']['alias']
        outpng = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, "png")
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)

        print(f"looking for disc in {original_image_path}")
        eye = faf_img_dict['eye']
        circular_cluster_detector(original_image_path, usable_region_path, eye, outpng)
        return f"{outpng} ok"


def main():

    faf_analysis = FafFoveaDisc(name_stem="fovea_n_disc")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
