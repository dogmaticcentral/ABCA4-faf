#!/usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from pprint import pprint

from utils.db_utils import db_connect
import os

import numpy as np

from pathlib import Path
from scipy.ndimage import median_filter, gaussian_filter
from skimage import exposure
from statistics import mean

from faf_classes.faf_analysis import FafAnalysis
from faf00_settings import WORK_DIR, USE_AUTO
from utils.conventions import construct_workfile_path
from utils.image_utils import grayscale_img_path_to_255_ndarray, ndarray_to_int_png
from utils.utils import is_nonempty_file, read_simple_hist, scream, histogram_max


class FafRecalibration(FafAnalysis):

    def __init__(self,internal_kwargs: dict|None=None, new_max_location: int = 90, name_stem: str = "recal"):
        super().__init__(internal_kwargs=internal_kwargs, name_stem=name_stem)
        self.new_max_location = new_max_location

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        original_image_path = Path(faf_img_dict['image_path'])
        alias = faf_img_dict['case_id']['alias']
        eye   = faf_img_dict['eye']
        denoised_img_path = construct_workfile_path(WORK_DIR, original_image_path, alias, 'denoised',
                                                    eye=eye, filetype='png')
        for region_png in [original_image_path, denoised_img_path]:
            if not is_nonempty_file(region_png):
                raise FileNotFoundError(f"{region_png} does not exist (or may be empty).")
        return [original_image_path, denoised_img_path]

    def recalibrate(self, input_filepath: Path | str, denoised_img_path: Path | str, alias: str, eye: str, skip_if_exists=False) -> str:
        print(f"recalibrating {input_filepath}")
        outpng = construct_workfile_path(WORK_DIR, input_filepath, alias, self.name_stem, eye=eye, filetype='png')
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)
        orig_img     = grayscale_img_path_to_255_ndarray(denoised_img_path)
        med_filtered = median_filter(orig_img, size=3)
        gauss_filtered = gaussian_filter(med_filtered, sigma=3)
        recal_image  = exposure.equalize_adapthist(gauss_filtered)*255  # CLAHE
        ndarray_to_int_png(recal_image, outpng)
        print(f"wrote output to {outpng}")
        return str(outpng)

    #######################################################################
    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        """ Inner content of the loop over faf image data - a convenience for parallelization
        :param faf_img_dict: bool
        :param skip_if_exists:
            if a nonempty file with the expected name already exists, skip the job
        :return: str
            THe return string indicates success or failure - generated in compose() function
        """
        if self.args.ctrl_only and not faf_img_dict['case_id']['is_control']: return "ok"
        [original_image_path, denoised_img_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict['case_id']['alias']
        eye   = faf_img_dict['eye']
        return self.recalibrate(original_image_path, denoised_img_path, alias, eye,  skip_if_exists=skip_if_exists)


def main():
    db = db_connect()
    faf_analysis = FafRecalibration()
    db.close()
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
