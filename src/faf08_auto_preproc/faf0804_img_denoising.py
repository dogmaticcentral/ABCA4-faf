#!/usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

import os
from pathlib import Path

import numpy as np
from scipy.signal import wiener
from skimage.io import imread

from faf00_settings import WORK_DIR, global_db_proxy
from faf_classes.faf_analysis import FafAnalysis
from utils.conventions import construct_workfile_path
from utils.db_utils import db_connect
from utils.image_utils import ndarray_to_int_png
from utils.utils import is_nonempty_file


class FafDenoising(FafAnalysis):

    def __init__(self, internal_kwargs: dict|None=None, name_stem: str = "denoised"):
        super().__init__(internal_kwargs=internal_kwargs, name_stem=name_stem)
        self.description = "Wiener denoising."

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        original_image_path = Path(faf_img_dict['image_path'])
        for region_png in [original_image_path]:
            if not is_nonempty_file(region_png):
                raise FileNotFoundError(f"{region_png} does not exist (or may be empty).")
        return [original_image_path]

    def denoise(self, input_filepath: Path | str, alias: str, eye: str, skip_if_exists=False) -> str:
        print(f"denoising {input_filepath}")
        outpng = construct_workfile_path(WORK_DIR, input_filepath, alias, self.name_stem, eye=eye, filetype='png')
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)
        orig_img  = imread(input_filepath, as_gray=True) # to use Wiener should be an array of floats, not ints
        # 'mysize' defines the window size (e.g., 3x3, 5x5, etc.)
        # If 'noise' is None, it is estimated from the local variance
        # looks the best without mysize
        filtered = wiener(orig_img)
        denoised_image = np.clip(filtered*255, 0, 255).astype(np.uint8)
        # to check the difference (there is some)
        # orig_img = grayscale_img_path_to_255_ndarray(input_filepath)
        # ndarray_to_int_png(np.abs(denoised_image-orig_img), outpng)
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


def test():
    if global_db_proxy.obj is None:
         db = db_connect()
    else:
         db = global_db_proxy
         db.connect(reuse_if_open=True)
    faf_analysis = FafDenoising(name_stem="denoised",
                                internal_kwargs={"i":"/media/ivana/portable/abca4/faf/all/Confused_Cloud/OD/CC_OD_12_1.tiff"})
    
    if not db.is_closed():
        db.close()
    faf_analysis.run()


def main():
    if global_db_proxy.obj is None:
         db = db_connect()
    else:
         db = global_db_proxy
         db.connect(reuse_if_open=True)
    faf_analysis = FafDenoising()
    
    if not db.is_closed():
        db.close()
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
