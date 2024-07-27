#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from skimage.io import ImageCollection

from utils.image_utils import ndarray_boolean_to_255_png

"""
Find and mark blood vessels inside the usable region.
"""
import os

import numpy as np

from pathlib import Path
from PIL import Image as PilImage
from PIL import ImageFilter, ImageOps
from skimage import morphology

from classes.faf_analysis import FafAnalysis
from faf00_settings import WORK_DIR
from third_party.hunan_segmentation import Segmentation
from utils.conventions import construct_workfile_path
from utils.pil_utils import extremize_pil
from utils.utils import is_nonempty_file, read_simple_hist, scream


class FafVasculature(FafAnalysis):

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        original_image_path = Path(faf_img_dict["image_path"])
        alias = faf_img_dict["case_id"]["alias"]
        recal_img_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "recal", "png")
        for region_png in [original_image_path, recal_img_path]:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()
        return [original_image_path, recal_img_path]

    def find_vasculature_fast_and_sloppy(
        self, original_img_filepath: Path | str, recal_img_filepath: Path | str, alias: str, skip_if_exists=False
    ) -> str:

        # note we ar using the original image path to construct the new png name
        outpng = construct_workfile_path(WORK_DIR, original_img_filepath, alias, self.name_stem, "png")
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)

        input_pil_image = PilImage.open(str(recal_img_filepath))

        print(f"{os.getpid()} {outpng} started")
        # this picks vasculature nicely, but with a lot of tiny artifacts around it
        # this could probably be optimized by reducing the image to the elliptic ROI (region of interest)
        im2 = input_pil_image.filter(ImageFilter.CONTOUR).filter(ImageFilter.ModeFilter())
        print("im2")
        im3 = ImageOps.grayscale(im2)
        print("im3")
        np_array_extremized = extremize_pil(im3, invert=False)  # not binary, but 0 or 255

        np_array_closed = morphology.area_closing(np_array_extremized.astype(bool), area_threshold=20, connectivity=3)

        np_array_dilated = morphology.dilation(~np_array_closed, morphology.disk(5))  # note the inversion here (~)
        print("dilation")

        # params that result in less vasculature and less false positives around:  area_threshold=100, connectivity=3
        # params that result in more vasculature and more false positives around:  area_threshold=500, connectivity=0
        np_array_closed_2 = morphology.area_closing(~np_array_dilated, area_threshold=500, connectivity=0)

        PilImage.fromarray(~np_array_closed_2).save(outpng)
        if is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} done")
            return str(outpng)
        else:
            print(f"{os.getpid()} {outpng} failed")
            return f"vasculature detection in {recal_img_filepath} failed"

    def find_vasculature_hunan(
        self, original_img_filepath: Path | str, recal_img_filepath: Path | str, alias: str, skip_if_exists=False
    ) -> str:

        # note we ar using the original image path to construct the new png name
        outpng = construct_workfile_path(WORK_DIR, original_img_filepath, alias, self.name_stem, "png")
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)

        width, height = ImageCollection(recal_img_filepath)[0].shape[:2]
        mask = np.zeros((width, height))
        for y in range(height):
            if y <  0.4*height: continue
            if y >  0.6*height: continue
            for x in range(width):
                if y < width * 0.4: continue
                if y > width * 0.6: continue
                mask[y, x] = 1

        sgmt = Segmentation(recal_img_filepath, mask)
        sgmt.binThreshold()
        sgmt.denoising(sgmt.binthresholdimg)
        sgmt.tracing()
        sgmt.denoising(sgmt.tracingimg)
        sgmt.union()

        ndarray_boolean_to_255_png(sgmt.unionimg, outpng)

        if is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} done")
            return str(outpng)
        else:
            print(f"{os.getpid()} {outpng} failed")
            return f"vasculature detection in {recal_img_filepath} failed"



    #######################################################################
    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        """Inner content of the loop over  faf image data - a convenience for parallelization
        :param faf_img_dict: bool
        :param skip_if_exists:
            if a nonempty file with the expected name already exists, skip the job
        :return: str
            THe return string indicates success or failure - generated in compose() function
        """
        [original_image_path, recalibrated_img_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict["case_id"]["alias"]

        find_vasculature =  self.find_vasculature_fast_and_sloppy
        return find_vasculature(original_image_path, recalibrated_img_path, alias, skip_if_exists)


def main():
    faf_analysis = FafVasculature(name_stem="vasculature")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()
