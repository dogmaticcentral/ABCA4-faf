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
from scipy.signal import wiener
from skimage.io import imread
from skimage import exposure
from statistics import mean

from classes.faf_analysis import FafAnalysis
from faf00_settings import WORK_DIR, USE_AUTO
from utils.conventions import construct_workfile_path
from utils.image_utils import grayscale_img_path_to_255_ndarray, ndarray_to_int_png
from utils.utils import is_nonempty_file, read_simple_hist, scream, histogram_max


class FafDenoising(FafAnalysis):

    def __init__(self, new_max_location: int = 90, name_stem: str = "recal"):
        super().__init__(name_stem)
        self.new_max_location = new_max_location

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        original_image_path = Path(faf_img_dict['image_path'])
        for region_png in [original_image_path]:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()
        return [original_image_path]

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

    def denoise(self, input_filepath: Path | str, alias: str, eye: str, skip_if_exists=False) -> str:
        print(f"denoising {input_filepath}")
        outpng = construct_workfile_path(WORK_DIR, input_filepath, alias, self.name_stem, eye=eye, filetype='png')
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)
        orig_img  = imread(input_filepath, as_gray=True) # should be an array of floats, not ints
        # 'mysize' defines the window size (e.g., 3x3, 5x5, etc.)
        # If 'noise' is None, it is estimated from the local variance
        # h, w = orig_img.shape[:2]
        # y_center, x_center = h//2, w//2
        # core_img = orig_img[y_center-300:y_center+300, x_center-500:x_center+500]
        # print(f"Min: {core_img.min()}, Max: {core_img.max()}, Mean: {core_img.mean()}")
        # looks the best without mysize
        filtered = wiener(orig_img,)
        print(f"Min: {filtered.min()}, Max: {filtered.max()}, Mean: {filtered.mean()}")
        denoised_image = np.clip(filtered*255, 0, 255).astype(np.uint8)
        ndarray_to_int_png(denoised_image, outpng)
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
        [original_image_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict['case_id']['alias']
        eye   = faf_img_dict['eye']
        return self.denoise(original_image_path, alias, eye, skip_if_exists=skip_if_exists)


def main():
    db = db_connect()
    faf_analysis = FafDenoising(name_stem="denoised")
    db.close()
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
