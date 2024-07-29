#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from utils.db_utils import db_connect

"""
Find and mark blood vessels inside the usable region.
"""
import os

import numpy as np

from pathlib import Path
from statistics import mean
from PIL import Image as PilImage
from PIL import ImageFilter, ImageOps
from skimage import morphology

from classes.faf_analysis import FafAnalysis
from faf00_settings import WORK_DIR
from utils.conventions import construct_workfile_path
from utils.image_utils import grayscale_img_path_to_255_ndarray, ndarray_to_int_png
from utils.utils import is_nonempty_file, read_simple_hist, scream, histogram_max


class FafRecalibration(FafAnalysis):

    def __init__(self, new_max_location: int = 90, name_stem: str = "recal"):
        super().__init__(name_stem)
        self.new_max_location = new_max_location

    def find_avg_location_of_max(self):
        all_faf_img_dicts = self.get_all_faf_dicts()
        hist_paths = []
        for faf_img_dict in all_faf_img_dicts:
            original_image_path  = Path(faf_img_dict['image_path'])
            alias = faf_img_dict['case_id']['alias']
            hist_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "bg_histogram", 'txt')
            if not is_nonempty_file(hist_path):
                raise Exception(f"{hist_path} does not exist or is empty")
            hist_paths.append(hist_path)
        self.new_max_location = int(mean([histogram_max(hist_path) for hist_path in hist_paths]))

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        original_image_path = Path(faf_img_dict['image_path'])
        alias = faf_img_dict['case_id']['alias']
        histogram_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "bg_histogram", 'txt')
        for region_png in [original_image_path, histogram_path]:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()
        return [original_image_path, histogram_path]

    def rescale(self, old_max_location: int, intensity: int) -> int:
        if intensity < old_max_location:
            if intensity == 0: return 0
            if old_max_location < 0: return 0  # not sure how this could have happened
            # rescaled_intensity / intensity = new_max / old_max
            rescaled_intensity = int(self.new_max_location/old_max_location*intensity)
        else:
            if intensity >= 255: return 255
            if old_max_location >= 255: return 255  # not sure how this could have happened
            # (255 - rescaled_intensity) / (255 - intensity) = (255 - new_max) /(255 - old_max)
            rescaled_intensity = 255 -  (255 - self.new_max_location)/(255 - old_max_location)*(255 - intensity)
        return rescaled_intensity

    def recalibrate(self, input_filepath: Path | str, hist_path: Path | str, alias: str,
                    shift_max_only=True, skip_if_exists=False) -> str:
        this_bg_histogram_max = int(np.argmax(read_simple_hist(hist_path)))
        orig_img: np.ndarray = grayscale_img_path_to_255_ndarray(input_filepath)
        outpng = construct_workfile_path(WORK_DIR, input_filepath, alias, self.name_stem, 'png')
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)
        recal_image = np.zeros(orig_img.shape, dtype=int)
        intensity_shift = self.new_max_location - this_bg_histogram_max
        for iy, ix in np.ndindex(orig_img.shape[0], orig_img.shape[1]):
            if shift_max_only:
                recal_image[iy, ix] = min(max(orig_img[iy, ix] + intensity_shift, 0), 255)
            else:
                recal_image[iy, ix] = self.rescale(this_bg_histogram_max, orig_img[iy, ix])
        ndarray_to_int_png(recal_image, outpng)
        return str(outpng)

    #######################################################################
    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        """ Inner content of the loop over  faf image data - a convenience for parallelization
        :param faf_img_dict: bool
        :param skip_if_exists:
            if a nonempty file with the expected name already exists, skip the job
        :return: str
            THe return string indicates success or failure - generated in compose() function
        """
        [original_image_path, histogram_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict['case_id']['alias']

        return self.recalibrate(original_image_path, histogram_path, alias,
                                shift_max_only=False, skip_if_exists=skip_if_exists)


def main():
    db = db_connect()
    faf_analysis = FafRecalibration()
    faf_analysis.find_avg_location_of_max()
    db.close()
    print(f"moving all maxima to {faf_analysis.new_max_location}")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()